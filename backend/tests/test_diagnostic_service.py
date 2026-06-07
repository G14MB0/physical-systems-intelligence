from pathlib import Path

from app.services.diagnostic_service import DiagnosticService
from app.services.domain_service import DomainService
from app.services.rag_service import InMemoryVectorStore, RagService


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
                "diagnosis": "AI-assisted structured diagnosis from gpt-5.4-nano.",
                "risk_level": "medium",
                "recommended_actions": ["AI action from evidence."],
                "usage": {"input_tokens": 900, "output_tokens": 70, "total_tokens": 970},
            },
        )()


def test_diagnosis_combines_signals_sources_and_recommended_action() -> None:
    domain_service = DomainService(Path("app/domains"))
    rag = RagService(Path("app/domains"), vector_store=InMemoryVectorStore())
    rag.ingest_domain("drone_inspection")
    diagnostics = DiagnosticService(domain_service=domain_service, rag_service=rag)

    result = diagnostics.diagnose(
        domain_id="drone_inspection",
        system_id="DRN-INSPECT-01",
        question="Battery sag and ESC temperature warning during bridge inspection. What should I do?",
    )

    assert result.domain_id == "drone_inspection"
    assert result.system_id == "DRN-INSPECT-01"
    assert result.risk_level in {"medium", "high"}
    assert result.evidence
    assert result.recommended_actions
    assert any(call.tool_name == "get_system_signals" for call in result.tool_calls)
    assert any(call.tool_name == "search_technical_documents" for call in result.tool_calls)


def test_diagnosis_can_use_openai_nano_narrator_without_changing_tools() -> None:
    domain_service = DomainService(Path("app/domains"))
    rag = RagService(Path("app/domains"), vector_store=InMemoryVectorStore())
    rag.ingest_domain("drone_inspection")
    diagnostics = DiagnosticService(
        domain_service=domain_service,
        rag_service=rag,
        narrator=FakeNarrator(),
    )

    result = diagnostics.diagnose(
        domain_id="drone_inspection",
        system_id="DRN-INSPECT-01",
        question="Should the drone continue?",
    )

    assert result.diagnosis == "AI-assisted structured diagnosis from gpt-5.4-nano."
    assert result.recommended_actions == ["AI action from evidence."]
    assert result.ai_model == "gpt-5.4-nano"
    assert result.ai_usage["total_tokens"] == 970
    assert any(call.tool_name == "openai_responses" for call in result.tool_calls)
