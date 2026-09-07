"""Entités métier du domaine Recal.

Ce module ne dépend ni de FastAPI, ni de boto3, ni de Strands afin de rester
facilement testable et réutilisable par l'API comme par le worker planifié.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class OpportunityType(StrEnum):
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    SCHOLARSHIP = "scholarship"
    OTHER = "other"


class OpportunityStatus(StrEnum):
    NEW = "new"
    SEEN = "seen"
    SAVED = "saved"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class FeedbackAction(StrEnum):
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    SAVED = "saved"
    DISMISSED = "dismissed"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunTrigger(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass(slots=True)
class UserProfile:
    id: str = "default"
    interests: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    study_level: str = ""
    skills: list[str] = field(default_factory=list)
    relevance_threshold: float = 70.0

    def validate(self) -> None:
        if not 0 <= self.relevance_threshold <= 100:
            raise ValueError("relevance_threshold doit être compris entre 0 et 100")
        if not self.interests:
            raise ValueError("Le profil doit contenir au moins un intérêt")


@dataclass(slots=True)
class Opportunity:
    id: str
    type: OpportunityType
    title: str
    summary: str
    source_url: str
    relevance_score: float
    confidence_score: float
    organization: str = ""
    relevance_reasons: list[str] = field(default_factory=list)
    deadline: date | None = None
    eligibility: dict[str, Any] = field(default_factory=dict)
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: OpportunityStatus = OpportunityStatus.NEW

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("Le titre de l’opportunité est obligatoire")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url doit être une URL HTTP(S)")
        if not 0 <= self.relevance_score <= 100:
            raise ValueError("relevance_score doit être compris entre 0 et 100")
        if not 0 <= self.confidence_score <= 100:
            raise ValueError("confidence_score doit être compris entre 0 et 100")

    @property
    def is_expired(self) -> bool:
        return self.deadline is not None and self.deadline < date.today()


@dataclass(frozen=True, slots=True)
class Feedback:
    opportunity_id: str
    action: FeedbackAction
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    comment: str | None = None


@dataclass(slots=True)
class WatchRun:
    id: UUID = field(default_factory=uuid4)
    trigger: RunTrigger = RunTrigger.MANUAL
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    opportunities_found: int = 0
    error_message: str | None = None
