from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.domain_service import DomainService
from app.services.eval_service import EvalService
from app.services.rag_service import InMemoryVectorStore, RagService


def test_eval_service_passes_for_nasa_fd001_unit_001() -> None:
    domains_root = Path("app/domains")
    domain_service = DomainService(domains_root)
    rag = RagService(domains_root=domains_root, vector_store=InMemoryVectorStore())
    rag.ingest_domain("nasa_cmapss_turbofan")

    signals = domain_service.get_signals("nasa_cmapss_turbofan", "FD001-UNIT-001")
    evidence = rag.search("nasa_cmapss_turbofan", "RUL expected failure cycle", limit=4).matches
    result = EvalService(domains_root).validate_nasa_cmapss(
        domain_id="nasa_cmapss_turbofan",
        system_id="FD001-UNIT-001",
        signals=signals,
        evidence=evidence,
    )

    assert result["passed"] is True
    assert result["expected"]["ground_truth_rul_cycles"] == 112
    assert result["expected"]["expected_failure_cycle"] == 143


def test_eval_endpoint_runs_nasa_case(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'eval.db'}")
    monkeypatch.setenv("DOMAINS_ROOT", str(Path("app/domains")))
    monkeypatch.setenv("VECTOR_BACKEND", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    client = TestClient(create_app())

    response = client.post("/evals/nasa-cmapss/fd001-unit-001")

    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is True
    assert data["case_id"] == "FD001-UNIT-001"
