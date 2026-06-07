import os

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("OPENAI_LIVE_E2E") != "1",
    reason="set OPENAI_LIVE_E2E=1 for live OpenAI workflow test",
)


def test_live_workflow_uses_openai_and_validates_nasa_case() -> None:
    base_url = os.getenv("LIVE_API_URL", "http://127.0.0.1:8122")

    with httpx.Client(timeout=180.0) as client:
        response = client.post(
            f"{base_url}/workflows/diagnose",
            json={
                "domain_id": "nasa_cmapss_turbofan",
                "system_id": "FD001-UNIT-001",
                "question": "What is the engine health status and what should maintenance do?",
                "create_ticket": True,
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ai_model"] == "gpt-5.4-nano"
    assert data["ai_usage"]["total_tokens"] > 0
    assert "ai_diagnose" in [event["step"] for event in data["trace"]]
    assert data["validation"]["passed"] is True
    assert data["ticket"]["id"] >= 1
