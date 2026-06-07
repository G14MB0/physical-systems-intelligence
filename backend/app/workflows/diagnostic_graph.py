from __future__ import annotations

from datetime import UTC, datetime
import uuid

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.models.schemas import ActionTicketCreate
from app.models.workflow_schemas import (
    TraceEvent,
    WorkflowDiagnosisRequest,
    WorkflowDiagnosisResponse,
)
from app.services.diagnostic_service import DiagnosticService
from app.services.domain_service import DomainService
from app.services.eval_service import EvalService
from app.services.rag_service import RagService
from app.services.ticket_service import TicketService
from app.workflows.state import DiagnosticGraphState


class DiagnosticWorkflow:
    def __init__(
        self,
        *,
        domain_service: DomainService,
        rag_service: RagService,
        diagnostic_service: DiagnosticService,
        eval_service: EvalService,
    ) -> None:
        self.domain_service = domain_service
        self.rag_service = rag_service
        self.diagnostic_service = diagnostic_service
        self.eval_service = eval_service
        self.graph = self._build_graph()

    def run(
        self,
        payload: WorkflowDiagnosisRequest | dict,
        db: Session,
    ) -> WorkflowDiagnosisResponse:
        request = (
            payload
            if isinstance(payload, WorkflowDiagnosisRequest)
            else WorkflowDiagnosisRequest.model_validate(payload)
        )
        final_state = self.graph.invoke(
            {
                "request": request,
                "run_id": str(uuid.uuid4()),
                "db": db,
                "trace": [],
            }
        )

        baseline = final_state["baseline"]
        validation = final_state["validation"]
        return WorkflowDiagnosisResponse(
            run_id=final_state["run_id"],
            domain_id=request.domain_id,
            system_id=request.system_id,
            question=request.question,
            situation=_situation_payload(final_state["signals"].current),
            diagnosis=baseline.diagnosis,
            risk_level=baseline.risk_level,
            evidence=baseline.evidence,
            recommended_actions=baseline.recommended_actions,
            expected_label=validation["expected"],
            trace=final_state["trace"],
            validation=validation,
            ticket=final_state.get("ticket"),
            ai_model=baseline.ai_model,
            ai_usage=baseline.ai_usage,
        )

    def _build_graph(self):
        builder = StateGraph(DiagnosticGraphState)
        builder.add_node("load_signals", self._load_signals)
        builder.add_node("retrieve_docs", self._retrieve_docs)
        builder.add_node("compute_baseline", self._compute_baseline)
        builder.add_node("ai_diagnose", self._ai_diagnose)
        builder.add_node("validate_expected", self._validate_expected)
        builder.add_node("create_ticket", self._create_ticket)
        builder.add_edge(START, "load_signals")
        builder.add_edge("load_signals", "retrieve_docs")
        builder.add_edge("retrieve_docs", "compute_baseline")
        builder.add_edge("compute_baseline", "ai_diagnose")
        builder.add_edge("ai_diagnose", "validate_expected")
        builder.add_edge("validate_expected", "create_ticket")
        builder.add_edge("create_ticket", END)
        return builder.compile()

    def _load_signals(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        request = state["request"]
        signals = self.domain_service.get_signals(request.domain_id, request.system_id)
        return {
            "signals": signals,
            "trace": [
                *state["trace"],
                _event(
                    "load_signals",
                    f"Loaded {request.system_id} with {len(signals.events)} active events.",
                    {
                        "observed_cycles": signals.current.get("observed_cycles"),
                        "ground_truth_rul_cycles": signals.current.get("ground_truth_rul_cycles"),
                    },
                ),
            ],
        }

    def _retrieve_docs(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        request = state["request"]
        if not self.rag_service.search(request.domain_id, request.question, limit=1).matches:
            self.rag_service.ingest_domain(request.domain_id)
        evidence = self.rag_service.search(request.domain_id, request.question, limit=4).matches
        return {
            "evidence": evidence,
            "trace": [
                *state["trace"],
                _event(
                    "retrieve_docs",
                    f"Retrieved {len(evidence)} evidence chunks.",
                    {"sources": [item.source_path for item in evidence]},
                ),
            ],
        }

    def _compute_baseline(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        request = state["request"]
        baseline = self.diagnostic_service.diagnose(
            domain_id=request.domain_id,
            system_id=request.system_id,
            question=request.question,
            use_narrator=False,
        )
        return {
            "baseline": baseline,
            "trace": [
                *state["trace"],
                _event(
                    "compute_baseline",
                    f"Baseline risk is {baseline.risk_level}.",
                    {"actions": baseline.recommended_actions, "ai_model": baseline.ai_model},
                ),
            ],
        }

    def _ai_diagnose(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        baseline = self.diagnostic_service.apply_narrator(
            state["baseline"],
            state["signals"].current,
        )
        return {
            "baseline": baseline,
            "trace": [
                *state["trace"],
                _event(
                    "ai_diagnose",
                    "Generated structured diagnosis with configured AI path."
                    if baseline.ai_model
                    else "AI disabled; deterministic diagnosis retained.",
                    {"ai_model": baseline.ai_model, "ai_usage": baseline.ai_usage},
                ),
            ]
        }

    def _validate_expected(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        request = state["request"]
        validation = self.eval_service.validate_expected(
            domain_id=request.domain_id,
            system_id=request.system_id,
            signals=state["signals"],
            evidence=state["baseline"].evidence,
        )
        return {
            "validation": validation,
            "trace": [
                *state["trace"],
                _event(
                    "validate_expected",
                    "Validated against expected benchmark label."
                    if validation["passed"]
                    else "Benchmark validation failed.",
                    validation,
                ),
            ],
        }

    def _create_ticket(self, state: DiagnosticGraphState) -> DiagnosticGraphState:
        request = state["request"]
        baseline = state["baseline"]
        ticket = None
        if request.create_ticket:
            ticket = TicketService(state["db"]).create(
                ActionTicketCreate(
                    domain_id=request.domain_id,
                    system_id=request.system_id,
                    title=f"Review {request.system_id} diagnostic run",
                    severity=baseline.risk_level,
                    summary=baseline.diagnosis,
                )
            )
        return {
            "ticket": ticket,
            "trace": [
                *state["trace"],
                _event(
                    "create_ticket",
                    f"Created ticket {ticket.id}." if ticket else "Ticket creation skipped.",
                    {"ticket_id": ticket.id if ticket else None},
                ),
            ],
        }


def _event(step: str, summary: str, payload: dict) -> TraceEvent:
    now = datetime.now(tz=UTC)
    return TraceEvent(
        step=step,
        status="completed",
        summary=summary,
        started_at=now,
        completed_at=now,
        payload=payload,
    )


def _situation_payload(current: dict) -> dict:
    return {
        "scenario_name": current.get("scenario_name", "Physical system health gate replay"),
        "trigger": current.get("autonomous_trigger", "Telemetry window closed"),
        "physical_condition": current.get("physical_condition", "Latest physical-system telemetry is available."),
        "decision_required": current.get(
            "decision_required",
            "Decide whether to continue operation or create a maintenance review.",
        ),
        "qdrant_role": current.get(
            "qdrant_role",
            "Retrieve operating context and maintenance policy from domain documents.",
        ),
        "signal_window": current.get("sample_rows", []),
        "asset_type": current.get("asset_type"),
        "fault_mode": current.get("fault_mode"),
        "operating_condition": current.get("operating_condition"),
    }
