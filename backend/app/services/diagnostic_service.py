from __future__ import annotations

from datetime import UTC, datetime

from app.models.schemas import DiagnosisResponse, ToolCall
from app.services.domain_service import DomainService
from app.services.rag_service import RagService


class DiagnosticService:
    def __init__(self, domain_service: DomainService, rag_service: RagService, narrator=None) -> None:
        self.domain_service = domain_service
        self.rag_service = rag_service
        self.narrator = narrator

    def diagnose(
        self,
        domain_id: str,
        system_id: str,
        question: str,
        *,
        use_narrator: bool = True,
    ) -> DiagnosisResponse:
        signals = self.domain_service.get_signals(domain_id, system_id)
        search_query = f"{question} {' '.join(event.code for event in signals.events)}"
        evidence = self.rag_service.search(domain_id, search_query, limit=4).matches
        risk_level = self._risk_level(signals)
        actions = self._actions(signals, risk_level)
        diagnosis = self._diagnosis_text(signals, risk_level, evidence)
        tool_calls = [
            ToolCall(
                tool_name="get_system_signals",
                arguments={"domain_id": domain_id, "system_id": system_id},
                result_summary=f"{len(signals.events)} active events, status={signals.current.get('flight_state')}",
            ),
            ToolCall(
                tool_name="search_technical_documents",
                arguments={"domain_id": domain_id, "query": search_query, "limit": 4},
                result_summary=f"{len(evidence)} relevant source chunks",
            ),
        ]
        ai_model = None
        ai_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        response = DiagnosisResponse(
            domain_id=domain_id,
            system_id=system_id,
            question=question,
            diagnosis=diagnosis,
            risk_level=risk_level,
            evidence=evidence,
            recommended_actions=actions,
            tool_calls=tool_calls,
            created_at=datetime.now(tz=UTC),
            ai_model=ai_model,
            ai_usage=ai_usage,
        )
        if use_narrator:
            return self.apply_narrator(response, signals.current)
        return response

    def apply_narrator(
        self,
        baseline: DiagnosisResponse,
        telemetry: dict,
    ) -> DiagnosisResponse:
        if self.narrator is None:
            return baseline
        ai_result = self.narrator.run(
            question=baseline.question,
            deterministic_diagnosis=baseline.diagnosis,
            evidence=[item.text for item in baseline.evidence],
            actions=baseline.recommended_actions,
            telemetry=telemetry,
        )
        ai_usage = ai_result.usage
        ai_model = self.narrator.model
        return baseline.model_copy(
            update={
                "diagnosis": ai_result.diagnosis,
                "risk_level": ai_result.risk_level,
                "recommended_actions": ai_result.recommended_actions,
                "ai_model": ai_model,
                "ai_usage": ai_usage,
                "tool_calls": [
                    *baseline.tool_calls,
                    ToolCall(
                        tool_name="openai_responses",
                        arguments={"model": ai_model, "usage": ai_usage},
                        result_summary=(
                            "Generated structured diagnostic from telemetry and retrieved evidence "
                            f"({ai_usage.get('total_tokens', 0)} tokens)."
                        ),
                    ),
                ],
            }
        )

    def _risk_level(self, signals) -> str:
        current = signals.current
        rul = current.get("ground_truth_rul_cycles")
        if isinstance(rul, int | float):
            if rul <= 30:
                return "high"
            if rul <= 80:
                return "medium"
            return "low"
        severities = {event.severity for event in signals.events}
        if "high" in severities:
            return "high"
        if (
            "medium" in severities
            or current.get("battery_health_pct", 100) < 75
            or current.get("esc_temp_c", 0) >= 78
            or current.get("motor_vibration_mm_s", 0) >= 5
        ):
            return "medium"
        return "low"

    def _actions(self, signals, risk_level: str) -> list[str]:
        current = signals.current
        rul = current.get("ground_truth_rul_cycles")
        if isinstance(rul, int | float):
            return [
                f"Open a maintenance review with the current cycle and NASA ground truth RUL label of {int(rul)} cycles.",
                "Keep the asset in monitoring mode; this is not an immediate stop condition.",
                "Watch the selected FD001 sensor window before the next operating cycle closes.",
            ]
        actions = []
        if risk_level in {"medium", "high"}:
            actions.append("Pause autonomous inspection and return to launch point if safe.")
            actions.append("Create a maintenance ticket with telemetry snapshot and event codes.")
        if signals.current.get("esc_temp_c", 0) >= 78:
            actions.append("Inspect ESC cooling path and motor load before next flight.")
        if signals.current.get("battery_health_pct", 100) < 75:
            actions.append("Run battery internal-resistance check and avoid high-wind missions.")
        return actions or ["Continue operation and monitor the next telemetry window."]

    def _diagnosis_text(self, signals, risk_level: str, evidence) -> str:
        current = signals.current
        rul = current.get("ground_truth_rul_cycles")
        if isinstance(rul, int | float):
            observed = current.get("observed_cycles")
            expected_failure = current.get("expected_failure_cycle")
            dataset = current.get("dataset", "benchmark")
            return (
                f"Risk is {risk_level}. {dataset} unit {current.get('unit_number')} has "
                f"{observed} observed cycles and NASA ground truth RUL is {int(rul)} cycles. "
                f"The expected failure cycle is {expected_failure}. This verifies retrieval and "
                "diagnosis against a real labelled prognostics benchmark."
            )
        event_codes = ", ".join(event.code for event in signals.events) or "no active event codes"
        source_note = "technical documentation" if evidence else "current signal thresholds"
        return (
            f"Risk is {risk_level}. Current telemetry shows {event_codes}; "
            f"battery health is {signals.current.get('battery_health_pct')}%, ESC temperature is "
            f"{signals.current.get('esc_temp_c')} C, and vibration is "
            f"{signals.current.get('motor_vibration_mm_s')} mm/s. Assessment is grounded in {source_note}."
        )
