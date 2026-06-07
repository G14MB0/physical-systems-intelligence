from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.models.schemas import ActionTicketRead, DiagnosisResponse, EvidenceItem, SignalSnapshot
from app.models.workflow_schemas import TraceEvent, WorkflowDiagnosisRequest


class ValidationPayload(TypedDict, total=False):
    case_id: str
    passed: bool
    expected: dict[str, Any]
    observed: dict[str, Any]
    checks: list[dict[str, Any]]


class DiagnosticGraphState(TypedDict, total=False):
    request: WorkflowDiagnosisRequest
    run_id: str
    db: Session
    signals: SignalSnapshot
    evidence: list[EvidenceItem]
    baseline: DiagnosisResponse
    validation: ValidationPayload
    ticket: ActionTicketRead | None
    trace: list[TraceEvent]
