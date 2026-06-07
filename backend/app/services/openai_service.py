from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import re
from typing import Any

import httpx

OPENAI_NANO_MODEL = "gpt-5.4-nano"


@dataclass(frozen=True)
class OpenAIDiagnosticResult:
    risk_level: str
    diagnosis: str
    recommended_actions: list[str]
    usage: dict[str, int]
    confidence: float | None = None


class OpenAIDiagnosticAgent:
    model = OPENAI_NANO_MODEL

    def __init__(
        self,
        api_key: str,
        post: Callable[..., Any] | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.post = post or httpx.post
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        *,
        question: str,
        deterministic_diagnosis: str,
        evidence: list[str],
        actions: list[str],
        telemetry: dict[str, Any],
    ) -> OpenAIDiagnosticResult:
        prompt = (
            "You are a physical-systems diagnostic agent. Use only the telemetry and "
            "retrieved evidence below. Return strict JSON with keys: risk_level "
            "(low|medium|high), diagnosis, recommended_actions, confidence. Do not "
            "invent facts. Preserve numeric values and cite source facts in the diagnosis.\n\n"
            f"Question: {question}\n"
            f"Telemetry JSON: {json.dumps(telemetry, sort_keys=True)}\n"
            f"Deterministic diagnosis: {deterministic_diagnosis}\n"
            f"Retrieved evidence chunks: {json.dumps(evidence, ensure_ascii=False)}\n"
            f"Candidate actions: {json.dumps(actions, ensure_ascii=False)}\n"
        )
        response = self.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": prompt,
                "max_output_tokens": 700,
                "reasoning": {"effort": "none"},
                "text": {"format": _diagnostic_response_format()},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        raw_text = data.get("output_text")
        if not isinstance(raw_text, str) or not raw_text.strip():
            raw_text = _extract_text(data)
        parsed = _parse_json_text(raw_text)
        usage = _normalize_usage(data.get("usage"))
        return OpenAIDiagnosticResult(
            risk_level=str(parsed.get("risk_level") or "medium"),
            diagnosis=str(parsed.get("diagnosis") or deterministic_diagnosis),
            recommended_actions=[
                str(item) for item in parsed.get("recommended_actions", []) if str(item).strip()
            ]
            or actions,
            confidence=float(parsed["confidence"]) if parsed.get("confidence") is not None else None,
            usage=usage,
        )


# Backwards-compatible alias for old imports/docs.
OpenAIDiagnosticNarrator = OpenAIDiagnosticAgent


def _extract_text(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _normalize_usage(raw_usage: Any) -> dict[str, int]:
    if not isinstance(raw_usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    input_tokens = int(raw_usage.get("input_tokens") or raw_usage.get("prompt_tokens") or 0)
    output_tokens = int(raw_usage.get("output_tokens") or raw_usage.get("completion_tokens") or 0)
    total_tokens = int(raw_usage.get("total_tokens") or input_tokens + output_tokens)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _diagnostic_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "name": "diagnostic_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "diagnosis": {"type": "string"},
                "recommended_actions": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
            },
            "required": ["risk_level", "diagnosis", "recommended_actions", "confidence"],
            "additionalProperties": False,
        },
    }
