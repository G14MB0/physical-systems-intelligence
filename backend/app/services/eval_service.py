from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.schemas import EvidenceItem, SignalSnapshot


class EvalService:
    def __init__(self, domains_root: Path) -> None:
        self.domains_root = domains_root

    def validate_nasa_cmapss(
        self,
        *,
        domain_id: str,
        system_id: str,
        signals: SignalSnapshot,
        evidence: list[EvidenceItem],
    ) -> dict[str, Any]:
        expected = self._load_expected(domain_id, system_id)
        observed = {
            "ground_truth_rul_cycles": signals.current.get("ground_truth_rul_cycles"),
            "expected_failure_cycle": signals.current.get("expected_failure_cycle"),
        }
        checks = [
            {
                "name": "rul_ground_truth_present",
                "passed": observed["ground_truth_rul_cycles"]
                == expected["ground_truth_rul_cycles"],
            },
            {
                "name": "failure_cycle_matches",
                "passed": observed["expected_failure_cycle"] == expected["expected_failure_cycle"],
            },
            {
                "name": "evidence_contains_rul_context",
                "passed": any(
                    "RUL" in item.text or "remaining useful life" in item.text.lower()
                    for item in evidence
                ),
            },
        ]
        return {
            "case_id": system_id,
            "passed": all(check["passed"] for check in checks),
            "expected": {
                "ground_truth_rul_cycles": expected["ground_truth_rul_cycles"],
                "expected_failure_cycle": expected["expected_failure_cycle"],
            },
            "observed": observed,
            "checks": checks,
        }

    def validate_expected(
        self,
        *,
        domain_id: str,
        system_id: str,
        signals: SignalSnapshot,
        evidence: list[EvidenceItem],
    ) -> dict[str, Any]:
        if not (self.domains_root / domain_id / "evals" / f"{system_id}.expected.json").exists():
            return {
                "case_id": system_id,
                "passed": True,
                "expected": {},
                "observed": {},
                "checks": [
                    {
                        "name": "expected_label_not_configured",
                        "passed": True,
                    }
                ],
            }
        if domain_id == "nasa_cmapss_turbofan":
            return self.validate_nasa_cmapss(
                domain_id=domain_id,
                system_id=system_id,
                signals=signals,
                evidence=evidence,
            )
        expected = self._load_expected(domain_id, system_id)
        return {
            "case_id": system_id,
            "passed": True,
            "expected": expected,
            "observed": {},
            "checks": [{"name": "expected_label_loaded", "passed": True}],
        }

    def _load_expected(self, domain_id: str, system_id: str) -> dict[str, Any]:
        path = self.domains_root / domain_id / "evals" / f"{system_id}.expected.json"
        return json.loads(path.read_text(encoding="utf-8"))
