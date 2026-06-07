import os

import httpx
import pytest


pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_LIVE_E2E"),
    reason="Set OPENAI_LIVE_E2E=1 and run Docker backend with OpenAI enabled",
)


def test_live_api_uses_openai_gpt_5_4_nano_for_diagnosis() -> None:
    base_url = os.getenv("LIVE_API_URL", "http://127.0.0.1:8122")

    with httpx.Client(base_url=base_url, timeout=180.0) as client:
        ingest = client.post("/documents/ingest", json={"domain_id": "drone_inspection"})
        assert ingest.status_code == 200

        diagnosis = client.post(
            "/agent/diagnose",
            json={
                "domain_id": "drone_inspection",
                "system_id": "DRN-INSPECT-01",
                "question": "What does E-204 mean and should the mission continue?",
            },
        )

    assert diagnosis.status_code == 200
    payload = diagnosis.json()
    assert payload["ai_model"] == "gpt-5.4-nano"
    assert payload["ai_usage"]["total_tokens"] > 0
    assert payload["ai_usage"]["input_tokens"] > 0
    assert any(call["tool_name"] == "openai_responses" for call in payload["tool_calls"])
    assert payload["diagnosis"]
