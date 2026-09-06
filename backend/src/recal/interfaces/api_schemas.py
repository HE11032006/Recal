from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from recal.domain.entities import (
    FeedbackAction,
    OpportunityStatus,
    OpportunityType,
    RunStatus,
)


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "recal-api"
    version: str = "0.1.0"


class UserProfileUpdate(BaseModel):
    interests: list[str] = Field(min_length=1)
    countries: list[str] = Field(default_factory=list)
    study_level: str = ""
    skills: list[str] = Field(default_factory=list)
    relevance_threshold: float = Field(default=70, ge=0, le=100)


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
    comment: str | None = None


class FeedbackResponse(BaseModel):
    opportunity_id: str
    action: FeedbackAction
    recorded_at: datetime


class RunResponse(BaseModel):
    id: UUID
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None
    opportunities_found: int = 0
    error_message: str | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)
