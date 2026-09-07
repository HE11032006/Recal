from __future__ import annotations

from dataclasses import asdict
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from recal.application.use_cases import ResourceNotFoundError
from recal.domain.entities import Feedback, UserProfile
from recal.infrastructure.dependencies import AppContainer, build_container
from recal.infrastructure.observability import configure_logging, init_sentry
from recal.infrastructure.rate_limit import InMemoryRateLimiter
from recal.interfaces.api_schemas import (
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

configure_logging()
init_sentry()
_container = build_container()
_run_rate_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Les données envoyées sont invalides.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Le détail interne reste dans Sentry/logs, jamais dans la réponse client.
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "Une erreur interne est survenue.",
            "details": {},
        },
    )


def get_container() -> AppContainer:
    return _container


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/v1/profile", response_model=UserProfileResponse, tags=["Profile"])
async def get_profile(
    container: Annotated[AppContainer, Depends(get_container)],
) -> UserProfileResponse:
    profile = await container.profiles.get_default()
    return UserProfileResponse(**asdict(profile))


@app.put("/api/v1/profile", response_model=UserProfileResponse, tags=["Profile"])
async def update_profile(
    payload: UserProfileUpdate,
    container: Annotated[AppContainer, Depends(get_container)],
) -> UserProfileResponse:
    profile = await container.update_profile.execute(
        UserProfile(id="default", **payload.model_dump())
    )
    return UserProfileResponse(**asdict(profile))


@app.get("/api/v1/opportunities", response_model=OpportunityPageResponse, tags=["Opportunities"])
async def list_opportunities(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    min_score: Annotated[float | None, Query(ge=0, le=100)] = None,
    opportunity_status: Annotated[str | None, Query(alias="status")] = None,
    container: AppContainer = Depends(get_container),
) -> OpportunityPageResponse:
    items, total = await container.list_opportunities.execute(
        page=page,
        page_size=page_size,
        min_score=min_score,
        status=opportunity_status,
    )
    return OpportunityPageResponse(
        items=[OpportunityResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@app.get(
    "/api/v1/opportunities/{opportunity_id}",
    response_model=OpportunityResponse,
    tags=["Opportunities"],
)
async def get_opportunity(
    opportunity_id: str,
    container: Annotated[AppContainer, Depends(get_container)],
) -> OpportunityResponse:
    opportunity = await container.opportunities.get(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunité introuvable")
    return OpportunityResponse.model_validate(opportunity)


@app.post(
    "/api/v1/opportunities/{opportunity_id}/feedback",
    response_model=FeedbackResponse,
    tags=["Opportunities"],
)
async def submit_feedback(
    opportunity_id: str,
    payload: FeedbackRequest,
    container: Annotated[AppContainer, Depends(get_container)],
) -> FeedbackResponse:
    try:
        feedback = await container.submit_feedback.execute(
            opportunity_id,
            Feedback(
                opportunity_id=opportunity_id,
                action=payload.action,
                comment=payload.comment,
            ),
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FeedbackResponse(
        opportunity_id=feedback.opportunity_id,
        action=feedback.action,
        recorded_at=feedback.recorded_at,
    )


@app.post(
    "/api/v1/runs", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Runs"]
)
async def create_run(
    request: Request,
    container: Annotated[AppContainer, Depends(get_container)],
) -> RunResponse | JSONResponse:
    client_key = request.client.host if request.client else "unknown"
    decision = _run_rate_limiter.check(client_key)
    if not decision.allowed:
        response = JSONResponse(
            status_code=429,
            content={
                "code": "rate_limit_exceeded",
                "message": "Trop de cycles demandés. Réessayez plus tard.",
                "details": {"retry_after_seconds": decision.retry_after_seconds},
            },
        )
        response.headers["Retry-After"] = str(decision.retry_after_seconds)
        return response
    run = await container.start_watch_run.execute()
    return RunResponse(
        id=run.id,
        trigger=run.trigger,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        opportunities_found=run.opportunities_found,
        error_message=run.error_message,
    )


@app.get("/api/v1/runs/{run_id}", response_model=RunResponse, tags=["Runs"])
async def get_run(
    run_id: str,
    container: Annotated[AppContainer, Depends(get_container)],
) -> RunResponse:
    run = await container.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Cycle introuvable")
    return RunResponse(
        id=run.id,
        trigger=run.trigger,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        opportunities_found=run.opportunities_found,
        error_message=run.error_message,
    )
