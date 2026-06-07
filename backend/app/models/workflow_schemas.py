from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.schemas import ActionTicketRead, EvidenceItem, RiskLevel


class WorkflowDiagnosisRequest(BaseModel):
    domain_id: str
    system_id: str
    question: str
    create_ticket: bool = True


class TraceEvent(BaseModel):
    step: str
    status: Literal["started", "completed", "failed"] = "completed"
    summary: str
    started_at: datetime
    completed_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowDiagnosisResponse(BaseModel):
    run_id: str
    domain_id: str
    system_id: str
    question: str
    situation: dict[str, Any] = Field(default_factory=dict)
    diagnosis: str
    risk_level: RiskLevel
    evidence: list[EvidenceItem]
    recommended_actions: list[str]
    expected_label: dict[str, Any]
    trace: list[TraceEvent]
    validation: dict[str, Any]
    ticket: ActionTicketRead | None
    ai_model: str | None = None
    ai_usage: dict[str, int] = Field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )
