from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]


class SystemProfile(BaseModel):
    id: str
    name: str
    type: str
    location: str
    status: str
    description: str


class DomainManifest(BaseModel):
    id: str
    name: str
    description: str
    primary_system_id: str
    systems: list[SystemProfile]


class SignalEvent(BaseModel):
    timestamp: str
    code: str
    severity: RiskLevel
    message: str


class SignalSnapshot(BaseModel):
    system_id: str
    timestamp: str
    current: dict[str, Any]
    events: list[SignalEvent] = Field(default_factory=list)


class DocumentIngestRequest(BaseModel):
    domain_id: str


class DocumentIngestResponse(BaseModel):
    domain_id: str
    documents_indexed: int
    chunks_indexed: int


class EvidenceItem(BaseModel):
    source_path: str
    title: str
    text: str
    score: float
    section_title: str | None = None
    source_label: str | None = None
    source_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    source_type: str | None = None
    source_authority: str | None = None
    chunk_id: str = ""
    retrieval_rank: int = 0
    embedding_provider: str = "hash"


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result_summary: str


class DiagnosisRequest(BaseModel):
    domain_id: str
    system_id: str
    question: str


class DiagnosisResponse(BaseModel):
    domain_id: str
    system_id: str
    question: str
    diagnosis: str
    risk_level: RiskLevel
    evidence: list[EvidenceItem]
    recommended_actions: list[str]
    tool_calls: list[ToolCall]
    created_at: datetime
    ai_model: str | None = None
    ai_usage: dict[str, int] = Field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )


class ActionTicketCreate(BaseModel):
    domain_id: str
    system_id: str
    title: str
    severity: RiskLevel
    summary: str


class ActionTicketRead(ActionTicketCreate):
    id: int
    status: str
    created_at: datetime
