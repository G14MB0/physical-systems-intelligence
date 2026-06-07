from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

DOMAINS_ROOT = Path(__file__).resolve().parents[1] / "app" / "domains"


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'workflow.db'}")
    monkeypatch.setenv("DOMAINS_ROOT", str(DOMAINS_ROOT))
    monkeypatch.setenv("VECTOR_BACKEND", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    return TestClient(create_app())


def _assert_ordered_steps(trace: list[dict[str, object]], required_steps: list[str]) -> None:
    trace_steps = [str(event["step"]) for event in trace]
    start_index = 0
    for step in required_steps:
        next_index = trace_steps.index(step, start_index)
        start_index = next_index + 1


def test_workflow_api_returns_trace_validation_and_ticket(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/workflows/diagnose",
        json={
            "domain_id": "nasa_cmapss_turbofan",
            "system_id": "FD001-UNIT-001",
            "question": "What is the engine health status and what should maintenance do?",
            "create_ticket": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"]
    assert data["expected_label"]["ground_truth_rul_cycles"] == 112
    assert data["expected_label"]["expected_failure_cycle"] == 143
    _assert_ordered_steps(data["trace"], [
        "load_signals",
        "retrieve_docs",
        "compute_baseline",
        "ai_diagnose",
        "validate_expected",
        "create_ticket",
    ])
    assert data["validation"]["passed"] is True
    assert data["validation"]["expected"]["ground_truth_rul_cycles"] == 112
    assert data["validation"]["expected"]["expected_failure_cycle"] == 143
    assert data["ticket"]["id"] >= 1
    assert data["evidence"]
    assert "health gate replay" in data["situation"]["scenario_name"].lower()
    assert "cycle 31" in data["situation"]["trigger"].lower()
    assert "telemetry window closed" in data["situation"]["trigger"].lower()
    assert "maintenance" in data["situation"]["decision_required"].lower()
    assert any(
        phrase in data["situation"]["decision_required"].lower()
        for phrase in ("keep monitoring", "open", "review")
    )
    assert "retrieve" in data["situation"]["qdrant_role"].lower()
    assert "domain documents" in data["situation"]["qdrant_role"].lower()
    assert data["situation"]["signal_window"][-1]["cycle"] == 31


def test_workflow_run_can_be_reloaded(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/workflows/diagnose",
        json={
            "domain_id": "nasa_cmapss_turbofan",
            "system_id": "FD001-UNIT-001",
            "question": "What is the engine health status and what should maintenance do?",
            "create_ticket": True,
        },
    ).json()

    fetched = client.get(f"/workflows/runs/{created['run_id']}").json()

    assert fetched["run_id"] == created["run_id"]
    assert fetched["trace"][0]["step"] == "load_signals"
    assert fetched["validation"]["passed"] is True


def test_workflow_without_expected_label_returns_non_benchmark_validation(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/workflows/diagnose",
        json={
            "domain_id": "drone_inspection",
            "system_id": "DRN-INSPECT-01",
            "question": "What does E-204 mean?",
            "create_ticket": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["passed"] is True
    assert data["validation"]["case_id"] == "DRN-INSPECT-01"
    assert data["expected_label"] == {}


def test_workflow_api_returns_source_backed_nasa_evidence(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/workflows/diagnose",
        json={
            "domain_id": "nasa_cmapss_turbofan",
            "system_id": "FD001-UNIT-001",
            "question": "What is FD001 and what does remaining useful life mean here?",
            "create_ticket": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["evidence"]
    assert all(item["source_label"] for item in data["evidence"])
    assert all(item["source_url"].startswith("http") for item in data["evidence"])
    assert all(item["section_title"] for item in data["evidence"])
    assert all(isinstance(item["source_urls"], list) for item in data["evidence"])
    assert all(item["source_authority"] for item in data["evidence"])
    assert all(isinstance(item["source_authority"], str) for item in data["evidence"])
    assert any(item["source_urls"] for item in data["evidence"])


def test_missing_workflow_run_returns_404(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.get("/workflows/runs/missing-run")

    assert response.status_code == 404


def test_path_traversal_domain_id_is_rejected(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/documents/ingest",
        json={"domain_id": "../nasa_cmapss_turbofan"},
    )

    assert response.status_code == 404
