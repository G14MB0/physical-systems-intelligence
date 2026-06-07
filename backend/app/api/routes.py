from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import session_dependency
from app.models.schemas import (
    ActionTicketCreate,
    ActionTicketRead,
    DiagnosisRequest,
    DiagnosisResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    DomainManifest,
    SignalSnapshot,
)
from app.models.workflow_schemas import WorkflowDiagnosisRequest, WorkflowDiagnosisResponse
from app.services.diagnostic_service import DiagnosticService
from app.services.domain_service import DomainService
from app.services.embedding_service import build_embedding_provider
from app.services.eval_service import EvalService
from app.services.openai_service import OpenAIDiagnosticAgent
from app.services.rag_service import InMemoryVectorStore, QdrantVectorStore, RagService
from app.services.run_trace_service import RunTraceService
from app.services.ticket_service import TicketService
from app.workflows.diagnostic_graph import DiagnosticWorkflow


def build_router(settings: Settings, session_factory) -> APIRouter:
    router = APIRouter()
    domain_service = DomainService(Path(settings.domains_root))
    embedding_provider = build_embedding_provider(
        provider_name=settings.embedding_provider,
        model_name=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        openai_api_key=settings.openai_api_key,
        openai_model_name=settings.openai_embedding_model,
    )
    vector_store = (
        InMemoryVectorStore()
        if settings.vector_backend == "memory"
        else QdrantVectorStore(
            settings.qdrant_url,
            settings.qdrant_collection,
            vector_size=embedding_provider.dimensions,
            embedding_provider_name=embedding_provider.name,
            embedding_model_name=embedding_provider.model_name,
        )
    )
    rag_service = RagService(
        Path(settings.domains_root),
        vector_store=vector_store,
        embedding_provider=embedding_provider,
    )
    narrator = (
        OpenAIDiagnosticAgent(settings.openai_api_key)
        if settings.openai_diagnostics_enabled and settings.openai_api_key
        else None
    )
    diagnostic_service = DiagnosticService(
        domain_service=domain_service,
        rag_service=rag_service,
        narrator=narrator,
    )
    eval_service = EvalService(Path(settings.domains_root))
    diagnostic_workflow = DiagnosticWorkflow(
        domain_service=domain_service,
        rag_service=rag_service,
        diagnostic_service=diagnostic_service,
        eval_service=eval_service,
    )

    def get_db() -> Iterator[Session]:
        yield from session_dependency(session_factory)

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    @router.get("/domains", response_model=list[DomainManifest])
    def list_domains() -> list[DomainManifest]:
        return domain_service.list_domains()

    @router.get("/systems")
    def list_systems(domain_id: str = "drone_inspection") -> list[dict[str, str]]:
        try:
            return [system.model_dump() for system in domain_service.get_domain(domain_id).systems]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/systems/{system_id}/signals", response_model=SignalSnapshot)
    def get_signals(system_id: str, domain_id: str = "drone_inspection") -> SignalSnapshot:
        try:
            return domain_service.get_signals(domain_id, system_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/documents/ingest", response_model=DocumentIngestResponse)
    def ingest_documents(payload: DocumentIngestRequest) -> DocumentIngestResponse:
        try:
            return rag_service.ingest_domain(payload.domain_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/agent/diagnose", response_model=DiagnosisResponse)
    def diagnose(payload: DiagnosisRequest) -> DiagnosisResponse:
        try:
            if not rag_service.search(payload.domain_id, payload.question, limit=1).matches:
                rag_service.ingest_domain(payload.domain_id)
            return diagnostic_service.diagnose(
                domain_id=payload.domain_id,
                system_id=payload.system_id,
                question=payload.question,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/actions/tickets", response_model=ActionTicketRead)
    def create_ticket(payload: ActionTicketCreate, db: Session = Depends(get_db)) -> ActionTicketRead:
        return TicketService(db).create(payload)

    @router.post("/workflows/diagnose", response_model=WorkflowDiagnosisResponse)
    def run_workflow(
        payload: WorkflowDiagnosisRequest,
        db: Session = Depends(get_db),
    ) -> WorkflowDiagnosisResponse:
        try:
            response = diagnostic_workflow.run(payload, db)
            RunTraceService(db).save(response)
            return response
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/workflows/runs", response_model=list[WorkflowDiagnosisResponse])
    def list_workflow_runs(db: Session = Depends(get_db)) -> list[WorkflowDiagnosisResponse]:
        return RunTraceService(db).list()

    @router.get("/workflows/runs/{run_id}", response_model=WorkflowDiagnosisResponse)
    def get_workflow_run(
        run_id: str,
        db: Session = Depends(get_db),
    ) -> WorkflowDiagnosisResponse:
        try:
            return RunTraceService(db).get(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/evals/nasa-cmapss/fd001-unit-001")
    def run_nasa_cmapss_eval() -> dict:
        domain_id = "nasa_cmapss_turbofan"
        system_id = "FD001-UNIT-001"
        rag_service.ingest_domain(domain_id)
        signals = domain_service.get_signals(domain_id, system_id)
        evidence = rag_service.search(domain_id, "RUL expected failure cycle", limit=4).matches
        return eval_service.validate_nasa_cmapss(
            domain_id=domain_id,
            system_id=system_id,
            signals=signals,
            evidence=evidence,
        )

    return router
