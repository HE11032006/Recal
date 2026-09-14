"""Entités métier du domaine Recal.

Ce module ne dépend ni de FastAPI, ni de boto3, ni de Strands afin de rester
facilement testable et réutilisable par l'API comme par le worker planifié.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from recal.domain.errors import DailyQuotaExceededError


class OpportunityType(StrEnum):
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    SCHOLARSHIP = "scholarship"
    CONFERENCE = "conference"
    CERTIFICATION = "certification"
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
class WatchSettings:
    enabled: bool = True
    frequency_minutes: int = 60
    allowed_domains: list[str] = field(default_factory=list)
    opportunity_types: list[str] = field(
        default_factory=lambda: [
            OpportunityType.HACKATHON.value,
            OpportunityType.INTERNSHIP.value,
            OpportunityType.FELLOWSHIP.value,
            OpportunityType.SCHOLARSHIP.value,
            OpportunityType.CONFERENCE.value,
            OpportunityType.CERTIFICATION.value,
        ]
    )
    max_queries_per_run: int = 3
    max_results_per_query: int = 5
    minimum_relevance_score: float | None = None
    daily_max_runs: int = 12

    def validate(self) -> None:
        if not 15 <= self.frequency_minutes <= 10080:
            raise ValueError("frequency_minutes doit être compris entre 15 et 10080")
        if not 1 <= self.max_queries_per_run <= 10:
            raise ValueError("max_queries_per_run doit être compris entre 1 et 10")
        if not 1 <= self.max_results_per_query <= 10:
            raise ValueError("max_results_per_query doit être compris entre 1 et 10")
        if not 1 <= self.daily_max_runs <= 96:
            raise ValueError("daily_max_runs doit être compris entre 1 et 96")
        if (
            self.minimum_relevance_score is not None
            and not 0 <= self.minimum_relevance_score <= 100
        ):
            raise ValueError("minimum_relevance_score doit être compris entre 0 et 100")
        self.allowed_domains = list(
            dict.fromkeys(
                domain.strip().lower() for domain in self.allowed_domains if domain.strip()
            )
        )
        self.opportunity_types = list(
            dict.fromkeys(item.strip().lower() for item in self.opportunity_types if item.strip())
        )


@dataclass(slots=True)
class WatchState:
    """État d’exécution de la veille, distinct de sa configuration.

    Persistance séparée du profil : ces champs changent à chaque cycle et ne
    doivent jamais être modifiés par l’utilisateur.
    """

    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_successful_run_at: datetime | None = None
    runs_today: int = 0
    runs_today_date: date | None = None
    processed_urls: list[str] = field(default_factory=list)

    def register_run(
        self,
        now: datetime,
        *,
        daily_max_runs: int,
        frequency_minutes: int,
        is_scheduled: bool = True,
    ) -> None:
        """Enregistrer le début d’un cycle : compteur quotidien et verrou temporel.

        Le quota quotidien ne bloque que les cycles planifiés : l’utilisateur
        doit toujours pouvoir déclencher un cycle manuel, le rate limiter de
        l’API suffit à protéger l’abus.
        """
        if self.runs_today_date != now.date():
            self.runs_today = 0
            self.runs_today_date = now.date()
        if is_scheduled and self.runs_today >= daily_max_runs:
            raise DailyQuotaExceededError(
                f"Quota quotidien dépassé : {self.runs_today}/{daily_max_runs} cycles"
            )
        self.runs_today += 1
        self.last_run_at = now
        self.next_run_at = now + timedelta(minutes=frequency_minutes)

    def record_processed_urls(self, urls: Sequence[str], *, cap: int = 200) -> None:
        self.processed_urls = list(dict.fromkeys(urls))[-cap:]

    def quota_remaining(self, now: datetime, *, daily_max_runs: int) -> int | None:
        if self.runs_today_date != now.date():
            return daily_max_runs
        return max(0, daily_max_runs - self.runs_today)


@dataclass(slots=True)
class UserProfile:
    id: str = "default"
    full_name: str = ""
    language: str = "fr"
    interests: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    mobility_countries: list[str] = field(default_factory=list)
    study_level: str = ""
    skills: list[str] = field(default_factory=list)
    relevance_threshold: float = 70.0
    watch: WatchSettings = field(default_factory=WatchSettings)

    def validate(self) -> None:
        if not 0 <= self.relevance_threshold <= 100:
            raise ValueError("relevance_threshold doit être compris entre 0 et 100")
        if not self.interests:
            raise ValueError("Le profil doit contenir au moins un intérêt")
        if self.language not in ("fr", "en"):
            raise ValueError("language doit être 'fr' ou 'en'")
        if len(self.full_name) > 120:
            raise ValueError("full_name ne peut pas dépasser 120 caractères")
        self.watch.validate()


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
    urls_processed: list[str] = field(default_factory=list)
