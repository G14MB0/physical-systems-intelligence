from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.services.diagnostic_service import DiagnosticService
from app.services.domain_service import DomainService
from app.services.eval_service import EvalService
from app.services.rag_service import InMemoryVectorStore, RagService
from app.workflows.diagnostic_graph import DiagnosticWorkflow


class FakeNarrator:
    model = "gpt-5.4-nano"

    def run(self, *, question, deterministic_diagnosis, evidence, actions, telemetry):
        assert question
        assert deterministic_diagnosis
        assert evidence
        assert actions
        assert telemetry
        return type(
            "Result",
            (),
            {
                "diagnosis": "AI node produced the final structured diagnosis.",
                "risk_level": "medium",
                "recommended_actions": ["AI node action."],
                "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18},
            },
        )()


def test_diagnostic_workflow_uses_langgraph_and_expected_trace() -> None:
    domain_service = DomainService(Path("app/domains"))
    rag_service = RagService(Path("app/domains"), vector_store=InMemoryVectorStore())
    diagnostic_service = DiagnosticService(domain_service, rag_service)
    workflow = DiagnosticWorkflow(
        domain_service=domain_service,
        rag_service=rag_service,
        diagnostic_service=diagnostic_service,
        eval_service=EvalService(Path("app/domains")),
    )
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        response = workflow.run(
            {
                "domain_id": "nasa_cmapss_turbofan",
                "system_id": "FD001-UNIT-001",
                "question": "What is the engine health status and what should maintenance do?",
                "create_ticket": True,
            },
            session,
        )

    assert workflow.graph is not None
    assert [event.step for event in response.trace] == [
        "load_signals",
        "retrieve_docs",
        "compute_baseline",
        "ai_diagnose",
        "validate_expected",
        "create_ticket",
    ]
    assert response.expected_label["ground_truth_rul_cycles"] == 112


def test_workflow_ai_node_owns_narrator_call() -> None:
    domain_service = DomainService(Path("app/domains"))
    rag_service = RagService(Path("app/domains"), vector_store=InMemoryVectorStore())
    diagnostic_service = DiagnosticService(domain_service, rag_service, narrator=FakeNarrator())
    workflow = DiagnosticWorkflow(
        domain_service=domain_service,
        rag_service=rag_service,
        diagnostic_service=diagnostic_service,
        eval_service=EvalService(Path("app/domains")),
    )
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        response = workflow.run(
            {
                "domain_id": "nasa_cmapss_turbofan",
                "system_id": "FD001-UNIT-001",
                "question": "What is the engine health status and what should maintenance do?",
                "create_ticket": False,
            },
            session,
        )

    compute_event = next(event for event in response.trace if event.step == "compute_baseline")
    ai_event = next(event for event in response.trace if event.step == "ai_diagnose")
    assert compute_event.payload["ai_model"] is None
    assert ai_event.payload["ai_model"] == "gpt-5.4-nano"
    assert ai_event.payload["ai_usage"]["total_tokens"] == 18
    assert response.diagnosis == "AI node produced the final structured diagnosis."
