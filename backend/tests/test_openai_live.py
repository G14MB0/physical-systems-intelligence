import os

import pytest

from app.services.openai_service import OPENAI_NANO_MODEL, OpenAIDiagnosticAgent


pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_LIVE_E2E"),
    reason="Set OPENAI_LIVE_E2E=1 and OPENAI_API_KEY to run OpenAI-backed tests",
)


def test_openai_live_uses_gpt_5_4_nano_only() -> None:
    api_key = os.environ["OPENAI_API_KEY"]
    agent = OpenAIDiagnosticAgent(api_key=api_key, timeout_seconds=180.0)

    result = agent.run(
        question="Should a drone continue after E-204?",
        deterministic_diagnosis="Risk is medium. E-204 indicates battery sag.",
        evidence=["Manual: E-204 means battery voltage sag under load."],
        actions=["Return to launch."],
        telemetry={"event_code": "E-204", "battery_health_pct": 71},
    )

    assert agent.model == OPENAI_NANO_MODEL
    assert agent.model == "gpt-5.4-nano"
    assert result.diagnosis
    assert result.usage["total_tokens"] > 0
    assert "E-204" in result.diagnosis or "battery" in result.diagnosis.lower()
