from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status

from recal.domain.entities import Opportunity, OpportunityStatus, OpportunityType, UserProfile
from recal.interfaces.api_schemas import (
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    OpportunityPageResponse,
    OpportunityResponse,
    RunResponse,
    UserProfileResponse,
    UserProfileUpdate,
)

app = FastAPI(
    title="Recal API",
    version="0.1.0",
    description="API du backend agentique de veille d’opportunités Recal.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

_profile = UserProfile(
    interests=["artificial intelligence", "software engineering"],
    countries=["Benin"],
    study_level="student",
    skills=["Python"],
    relevance_threshold=70,
)
_opportunities: dict[str, Opportunity] = {}


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/v1/profile", response_model=UserProfileResponse, tags=["Profile"])
async def get_profile() -> UserProfileResponse:
    return UserProfileResponse(**asdict(_profile))


@app.put("/api/v1/profile", response_model=UserProfileResponse, tags=["Profile"])
async def update_profile(payload: UserProfileUpdate) -> UserProfileResponse:
    global _profile
    _profile = UserProfile(id=_profile.id, **payload.model_dump())
    _profile.validate()
    return UserProfileResponse(**asdict(_profile))


@app.get("/api/v1/opportunities", response_model=OpportunityPageResponse, tags=["Opportunities"])
async def list_opportunities(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    min_score: Annotated[float | None, Query(ge=0, le=100)] = None,
    opportunity_status: Annotated[OpportunityStatus | None, Query(alias="status")] = None,
) -> OpportunityPageResponse:
    items = list(_opportunities.values())
    if min_score is not None:
        items = [item for item in items if item.relevance_score >= min_score]
    if opportunity_status is not None:
        items = [item for item in items if item.status == opportunity_status]
    total = len(items)
    start = (page - 1) * page_size
    return OpportunityPageResponse(
        items=[OpportunityResponse.model_validate(item) for item in items[start : start + page_size]],
        page=page,
        page_size=page_size,
        total=total,
    )


@app.get("/api/v1/opportunities/{opportunity_id}", response_model=OpportunityResponse, tags=["Opportunities"])
async def get_opportunity(opportunity_id: str) -> OpportunityResponse:
    opportunity = _opportunities.get(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Opportunité introuvable"})
    return OpportunityResponse.model_validate(opportunity)


@app.post("/api/v1/opportunities/{opportunity_id}/feedback", response_model=FeedbackResponse, tags=["Opportunities"])
async def submit_feedback(opportunity_id: str, payload: FeedbackRequest) -> FeedbackResponse:
    opportunity = _opportunities.get(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Opportunité introuvable"})
    status_by_action = {"saved": OpportunityStatus.SAVED, "dismissed": OpportunityStatus.DISMISSED}
    if payload.action.value in status_by_action:
        opportunity.status = status_by_action[payload.action.value]
    return FeedbackResponse(
        opportunity_id=opportunity_id,
        action=payload.action,
        recorded_at=datetime.now(timezone.utc),
    )


@app.post("/api/v1/runs", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Runs"])
async def create_run() -> RunResponse:
    # Le worker Strands sera branché dans la prochaine étape.
    from recal.domain.entities import WatchRun

    run = WatchRun()
    return RunResponse(
        id=run.id,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        opportunities_found=run.opportunities_found,
    )
