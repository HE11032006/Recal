"""Cas d’usage applicatifs de Recal.

Les cas d’usage orchestrent les ports sans connaître FastAPI, boto3, Tavily ou
le framework d’agent. Ils pourront donc être utilisés par l’API et par Lambda.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from recal.application.ports import (
    OpportunityRepository,
    ProfileRepository,
    RunRepository,
    WatchRunner,
)
from recal.domain.entities import (
    Feedback,
    FeedbackAction,
    OpportunityStatus,
    RunStatus,
    RunTrigger,
    UserProfile,
    WatchRun,
)


class ResourceNotFoundError(Exception):
    """Ressource demandée absente."""


@dataclass(slots=True)
class UpdateProfile:
    profiles: ProfileRepository

    async def execute(self, profile: UserProfile) -> UserProfile:
        profile.validate()
        return await self.profiles.save(profile)


@dataclass(slots=True)
class ListOpportunities:
    opportunities: OpportunityRepository

    async def execute(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        min_score: float | None = None,
        status: str | None = None,
    ):
        if page < 1:
            raise ValueError("page doit être supérieur ou égal à 1")
        if not 1 <= page_size <= 100:
            raise ValueError("page_size doit être compris entre 1 et 100")
        return await self.opportunities.list(
            page=page,
            page_size=page_size,
            min_score=min_score,
            status=status,
        )


@dataclass(slots=True)
class SubmitFeedback:
    opportunities: OpportunityRepository

    async def execute(self, opportunity_id: str, feedback: Feedback) -> Feedback:
        opportunity = await self.opportunities.get(opportunity_id)
        if opportunity is None:
            raise ResourceNotFoundError(f"Opportunité introuvable : {opportunity_id}")
        if feedback.action is FeedbackAction.SAVED:
            opportunity.status = OpportunityStatus.SAVED
        elif feedback.action is FeedbackAction.DISMISSED:
            opportunity.status = OpportunityStatus.DISMISSED
        elif feedback.action is FeedbackAction.INTERESTED:
            opportunity.status = OpportunityStatus.SEEN
        await self.opportunities.update(opportunity)
        return feedback


@dataclass(slots=True)
class StartWatchRun:
    profiles: ProfileRepository
    runs: RunRepository
    runner: WatchRunner

    async def execute(self, *, trigger: RunTrigger = RunTrigger.MANUAL) -> WatchRun:
        profile = await self.profiles.get_default()
        run = WatchRun(trigger=trigger)
        await self.runs.save(run)
        run.status = RunStatus.RUNNING
        await self.runs.save(run)
        try:
            run = await self.runner.execute(run, profile)
        except Exception as exc:  # noqa: BLE001 — statut persisté avant propagation
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            await self.runs.save(run)
            raise
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now(UTC)
        await self.runs.save(run)
        return run
