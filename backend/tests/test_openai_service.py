from app.services.openai_service import OPENAI_NANO_MODEL, OpenAIDiagnosticAgent


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "output_text": (
                '{"risk_level":"medium","diagnosis":"AI structured diagnosis from nano.",'
                '"recommended_actions":["Return to launch."],"confidence":0.82}'
            ),
            "usage": {"input_tokens": 1200, "output_tokens": 80, "total_tokens": 1280},
        }


def test_openai_narrator_uses_only_gpt_5_4_nano() -> None:
    captured: dict = {}

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    agent = OpenAIDiagnosticAgent(api_key="test-key", post=fake_post)
    result = agent.run(
        question="What should I do?",
        deterministic_diagnosis="Risk is medium.",
        evidence=["manual says return to launch"],
        actions=["Return to launch"],
        telemetry={"battery_health_pct": 71},
    )

    assert result.diagnosis == "AI structured diagnosis from nano."
    assert result.risk_level == "medium"
    assert result.recommended_actions == ["Return to launch."]
    assert result.usage["total_tokens"] == 1280
    assert captured["json"]["model"] == OPENAI_NANO_MODEL
    assert captured["json"]["model"] == "gpt-5.4-nano"
    assert captured["json"]["text"]["format"]["type"] == "json_schema"
    assert captured["json"]["text"]["format"]["strict"] is True
    assert "manual says return to launch" in captured["json"]["input"]
    assert "battery_health_pct" in captured["json"]["input"]
    assert "test-key" in captured["headers"]["Authorization"]
