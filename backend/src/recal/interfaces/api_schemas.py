from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from recal.domain.entities import (
    FeedbackAction,
    OpportunityStatus,
    OpportunityType,
    RunStatus,
    RunTrigger,
)


def _clean_list(values: list[str]) -> list[str]:
    cleaned = [value.strip() for value in values if value.strip()]
    return list(dict.fromkeys(cleaned))


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "recal-api"
    version: str = "0.1.0"


class UserProfileUpdate(BaseModel):
    interests: list[str] = Field(min_length=1, max_length=20)
    countries: list[str] = Field(default_factory=list, max_length=20)
    study_level: str = Field(default="", max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=30)
    relevance_threshold: float = Field(default=70, ge=0, le=100)

    @field_validator("interests", "countries", "skills")
    @classmethod
    def normalize_lists(cls, values: list[str]) -> list[str]:
        cleaned = _clean_list(values)
        if not cleaned and cls.model_fields.get("interests"):
            # Le champ interests est contrôlé par min_length ; ce garde-fou
            # documente la règle métier pour les appels directs au modèle.
            return cleaned
        return cleaned

    @field_validator("study_level")
    @classmethod
    def normalize_study_level(cls, value: str) -> str:
        return value.strip()


class UserProfileResponse(UserProfileUpdate):
    id: str


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: OpportunityType
    title: str
    organization: str = ""
    summary: str
    relevance_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=100)
    relevance_reasons: list[str] = Field(default_factory=list)
    deadline: date | None = None
    eligibility: dict = Field(default_factory=dict)
    source_url: HttpUrl
    verified_at: datetime
    status: OpportunityStatus


class OpportunityPageResponse(BaseModel):
    items: list[OpportunityResponse]
    page: int
    page_size: int
    total: int


class FeedbackRequest(BaseModel):
    action: FeedbackAction
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class FeedbackResponse(BaseModel):
    opportunity_id: str
    action: FeedbackAction
    recorded_at: datetime


class RunResponse(BaseModel):
    id: UUID
    trigger: RunTrigger = RunTrigger.MANUAL
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None
    opportunities_found: int = 0
    error_message: str | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)
