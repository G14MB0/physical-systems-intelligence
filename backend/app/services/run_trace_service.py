from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import DiagnosticRun, DiagnosticTraceEvent
from app.models.workflow_schemas import WorkflowDiagnosisResponse


class RunTraceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, response: WorkflowDiagnosisResponse) -> None:
        payload = response.model_dump(mode="json")
        run = DiagnosticRun(
            run_id=response.run_id,
            domain_id=response.domain_id,
            system_id=response.system_id,
            question=response.question,
            payload=json.dumps(payload),
        )
        self.db.add(run)
        for index, event in enumerate(response.trace, start=1):
            self.db.add(
                DiagnosticTraceEvent(
                    run_id=response.run_id,
                    sequence=index,
                    step=event.step,
                    status=event.status,
                    summary=event.summary,
                    payload=json.dumps(event.model_dump(mode="json")),
                )
            )
        self.db.commit()

    def get(self, run_id: str) -> WorkflowDiagnosisResponse:
        run = self.db.query(DiagnosticRun).filter(DiagnosticRun.run_id == run_id).one_or_none()
        if run is None:
            raise KeyError(f"Unknown workflow run {run_id!r}")
        return WorkflowDiagnosisResponse.model_validate(json.loads(run.payload))

    def list(self) -> list[WorkflowDiagnosisResponse]:
        runs = self.db.query(DiagnosticRun).order_by(DiagnosticRun.created_at.desc()).all()
        return [WorkflowDiagnosisResponse.model_validate(json.loads(run.payload)) for run in runs]
