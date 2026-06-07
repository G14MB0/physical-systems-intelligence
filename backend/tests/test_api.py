from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

DOMAINS_ROOT = Path(__file__).resolve().parents[1] / "app" / "domains"


def test_api_exposes_domain_signals_diagnosis_and_ticket(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("DOMAINS_ROOT", str(DOMAINS_ROOT))
    monkeypatch.setenv("VECTOR_BACKEND", "memory")

    app = create_app()
    client = TestClient(app)

    assert client.get("/health").json()["status"] == "ok"

    domains = client.get("/domains").json()
    assert domains[0]["id"] == "drone_inspection"

    ingest = client.post("/documents/ingest", json={"domain_id": "drone_inspection"}).json()
    assert ingest["chunks_indexed"] > 0

    signals = client.get("/systems/DRN-INSPECT-01/signals?domain_id=drone_inspection").json()
    assert signals["current"]["battery_health_pct"] == 71

    diagnosis = client.post(
        "/agent/diagnose",
        json={
            "domain_id": "drone_inspection",
            "system_id": "DRN-INSPECT-01",
            "question": "What does E-204 mean and should the mission continue?",
        },
    ).json()
    assert diagnosis["risk_level"] in {"medium", "high"}
    assert diagnosis["evidence"]

    ticket = client.post(
        "/actions/tickets",
        json={
            "domain_id": "drone_inspection",
            "system_id": "DRN-INSPECT-01",
            "title": "Investigate E-204 warning",
            "severity": "medium",
            "summary": "Created from API test.",
        },
    ).json()
    assert ticket["id"] >= 1
    assert ticket["status"] == "open"


def test_system_id_path_traversal_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("DOMAINS_ROOT", str(DOMAINS_ROOT))
    monkeypatch.setenv("VECTOR_BACKEND", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")

    client = TestClient(create_app())

    signals = client.get(
        "/systems/../evals/FD001-UNIT-001.expected/signals?domain_id=nasa_cmapss_turbofan"
    )
    diagnosis = client.post(
        "/agent/diagnose",
        json={
            "domain_id": "nasa_cmapss_turbofan",
            "system_id": "../evals/FD001-UNIT-001.expected",
            "question": "Should this run?",
        },
    )
    workflow = client.post(
        "/workflows/diagnose",
        json={
            "domain_id": "nasa_cmapss_turbofan",
            "system_id": "../evals/FD001-UNIT-001.expected",
            "question": "Should this run?",
            "create_ticket": False,
        },
    )

    assert signals.status_code == 404
    assert diagnosis.status_code == 404
    assert workflow.status_code == 404


def test_nasa_ingest_reports_materially_larger_real_document_corpus(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'nasa-ingest.db'}")
    monkeypatch.setenv("DOMAINS_ROOT", str(DOMAINS_ROOT))
    monkeypatch.setenv("VECTOR_BACKEND", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")

    client = TestClient(create_app())

    ingest = client.post("/documents/ingest", json={"domain_id": "nasa_cmapss_turbofan"})

    assert ingest.status_code == 200
    data = ingest.json()
    assert data["domain_id"] == "nasa_cmapss_turbofan"
    assert data["documents_indexed"] >= 3
    assert data["chunks_indexed"] >= 20
    assert data["chunks_indexed"] > data["documents_indexed"] * 5
