import os

import httpx
import pytest


pytestmark = pytest.mark.skipif(
    not os.getenv("LIVE_E2E"),
    reason="Set LIVE_E2E=1 to run against Docker services",
)


def test_live_api_runs_full_no_ai_diagnostic_flow() -> None:
    base_url = os.getenv("LIVE_API_URL", "http://127.0.0.1:8122")

    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        domains = client.get("/domains")
        assert domains.status_code == 200
        assert domains.json()[0]["id"] == "drone_inspection"

        systems = client.get("/systems", params={"domain_id": "drone_inspection"})
        assert systems.status_code == 200
        assert systems.json()[0]["id"] == "DRN-INSPECT-01"

        signals = client.get(
            "/systems/DRN-INSPECT-01/signals",
            params={"domain_id": "drone_inspection"},
        )
        assert signals.status_code == 200
        assert signals.json()["current"]["esc_temp_c"] == 82

        ingest = client.post("/documents/ingest", json={"domain_id": "drone_inspection"})
        assert ingest.status_code == 200
        assert ingest.json()["chunks_indexed"] >= 4

        diagnosis = client.post(
            "/agent/diagnose",
            json={
                "domain_id": "drone_inspection",
                "system_id": "DRN-INSPECT-01",
                "question": "What does E-204 mean and should the mission continue?",
            },
        )
        assert diagnosis.status_code == 200
        diagnosis_json = diagnosis.json()
        assert diagnosis_json["risk_level"] in {"medium", "high"}
        assert diagnosis_json["evidence"]
        assert diagnosis_json["tool_calls"][0]["tool_name"] == "get_system_signals"

        ticket = client.post(
            "/actions/tickets",
            json={
                "domain_id": "drone_inspection",
                "system_id": "DRN-INSPECT-01",
                "title": "Live e2e maintenance ticket",
                "severity": "medium",
                "summary": diagnosis_json["diagnosis"],
            },
        )
        assert ticket.status_code == 200
        assert ticket.json()["status"] == "open"


def test_live_api_verifies_real_nasa_cmapss_expected_rul() -> None:
    base_url = os.getenv("LIVE_API_URL", "http://127.0.0.1:8122")

    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        signals = client.get(
            "/systems/FD001-UNIT-001/signals",
            params={"domain_id": "nasa_cmapss_turbofan"},
        )
        assert signals.status_code == 200
        assert signals.json()["current"]["ground_truth_rul_cycles"] == 112

        ingest = client.post("/documents/ingest", json={"domain_id": "nasa_cmapss_turbofan"})
        assert ingest.status_code == 200
        assert ingest.json()["documents_indexed"] >= 3
        assert ingest.json()["chunks_indexed"] >= 20

        diagnosis = client.post(
            "/agent/diagnose",
            json={
                "domain_id": "nasa_cmapss_turbofan",
                "system_id": "FD001-UNIT-001",
                "question": "Use the NASA ground truth to verify remaining useful life.",
            },
        )

    assert diagnosis.status_code == 200
    payload = diagnosis.json()
    assert payload["risk_level"] in {"low", "medium"}
    assert "112" in payload["diagnosis"]
    assert any(item["source_path"].startswith("documents/") for item in payload["evidence"])
    assert any(item["source_label"] for item in payload["evidence"])
    assert any(item["source_url"].startswith("http") for item in payload["evidence"])
    assert any(item["source_authority"] == "nasa_official" for item in payload["evidence"])
