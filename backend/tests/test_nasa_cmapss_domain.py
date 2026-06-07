from pathlib import Path
import json

from app.services.diagnostic_service import DiagnosticService
from app.services.domain_service import DomainService
from app.services.rag_service import InMemoryVectorStore, RagService


def test_nasa_cmapss_domain_loads_real_rul_ground_truth() -> None:
    service = DomainService(Path("app/domains"))

    domain = service.get_domain("nasa_cmapss_turbofan")
    signals = service.get_signals("nasa_cmapss_turbofan", "FD001-UNIT-001")

    assert domain.name == "NASA C-MAPSS Turbofan FD001"
    assert signals.current["asset_type"] == "turbofan_engine"
    assert signals.current["observed_cycles"] == 31
    assert signals.current["ground_truth_rul_cycles"] == 112
    assert signals.current["expected_failure_cycle"] == 143
    assert signals.current["last_cycle"]["sensor_11"] == 47.23


def test_nasa_cmapss_expected_label_file_is_machine_readable() -> None:
    expected_path = Path(
        "app/domains/nasa_cmapss_turbofan/evals/FD001-UNIT-001.expected.json"
    )

    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    assert expected == {
        "domain_id": "nasa_cmapss_turbofan",
        "system_id": "FD001-UNIT-001",
        "dataset": "FD001",
        "unit_number": 1,
        "observed_cycles": 31,
        "ground_truth_rul_cycles": 112,
        "expected_failure_cycle": 143,
        "source": "NASA C-MAPSS RUL_FD001 first row",
    }


def test_nasa_cmapss_diagnosis_reports_expected_rul_and_uses_nasa_docs() -> None:
    domain_service = DomainService(Path("app/domains"))
    rag = RagService(Path("app/domains"), vector_store=InMemoryVectorStore())
    rag.ingest_domain("nasa_cmapss_turbofan")
    diagnostics = DiagnosticService(domain_service=domain_service, rag_service=rag)

    result = diagnostics.diagnose(
        domain_id="nasa_cmapss_turbofan",
        system_id="FD001-UNIT-001",
        question="Use the NASA ground truth to verify remaining useful life for this engine.",
    )

    assert result.risk_level == "low"
    assert "112" in result.diagnosis
    assert any("cmapss_reference.md" in item.source_path for item in result.evidence)
    assert any("ground truth RUL" in action for action in result.recommended_actions)
