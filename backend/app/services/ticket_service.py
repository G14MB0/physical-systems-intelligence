from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Ticket
from app.models.schemas import ActionTicketCreate, ActionTicketRead


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: ActionTicketCreate) -> ActionTicketRead:
        ticket = Ticket(**payload.model_dump(), status="open")
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ActionTicketRead.model_validate(
            {
                "id": ticket.id,
                "domain_id": ticket.domain_id,
                "system_id": ticket.system_id,
                "title": ticket.title,
                "severity": ticket.severity,
                "summary": ticket.summary,
                "status": ticket.status,
                "created_at": ticket.created_at,
            }
        )
