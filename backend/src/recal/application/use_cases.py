"""Cas d’usage applicatifs de Recal.

Les cas d’usage orchestrent les ports sans connaître FastAPI, boto3, Tavily ou
le framework d’agent. Ils pourront donc être utilisés par l’API et par Lambda.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from recal.application.ports import (
    Clock,
    OpportunityRepository,
    ProfileRepository,
    RunRepository,
    WatchRunner,
    WatchStateRepository,
)
from recal.domain.entities import (
    Feedback,
    FeedbackAction,
    OpportunityStatus,
    RunStatus,
    RunTrigger,
    UserProfile,
    WatchRun,
    WatchState,
)
from recal.domain.errors import WatchSkippedError


class ResourceNotFoundError(Exception):
    """Ressource demandée absente."""


class SystemClock:
    """Horloge réelle utilisée hors des tests."""

    def now(self) -> datetime:
        return datetime.now(UTC)


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
        since: datetime | None = None,
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
            since=since,
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
    watch_state: WatchStateRepository
    clock: Clock

    async def execute(self, *, trigger: RunTrigger = RunTrigger.MANUAL) -> WatchRun:
        profile = await self.profiles.get_default()
        state = await self.watch_state.get()
        now = self.clock.now()
        if trigger is RunTrigger.SCHEDULED:
            await self._check_scheduled_guards(profile, state, now)
        state.register_run(
            now,
            daily_max_runs=profile.watch.daily_max_runs,
            frequency_minutes=profile.watch.frequency_minutes,
            is_scheduled=trigger is RunTrigger.SCHEDULED,
        )
        await self.watch_state.save(state)
        run = WatchRun(trigger=trigger)
        await self.runs.save(run)
        run.status = RunStatus.RUNNING
        await self.runs.save(run)
        try:
            run = await self.runner.execute(run, profile, processed_urls=state.processed_urls)
        except Exception as exc:  # noqa: BLE001 — statut persisté avant propagation
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            await self.runs.save(run)
            raise
        run.status = RunStatus.COMPLETED
        run.completed_at = now
        await self.runs.save(run)
        state.record_processed_urls(run.urls_processed)
        state.last_successful_run_at = now
        state.next_run_at = now + timedelta(minutes=profile.watch.frequency_minutes)
        await self.watch_state.save(state)
        return run

    async def _check_scheduled_guards(
        self, profile: UserProfile, state: WatchState, now: datetime
    ) -> None:
        if not profile.watch.enabled:
            raise WatchSkippedError("watch_disabled")
        active = await self.runs.get_active()
        if active is not None:
            raise WatchSkippedError("run_already_active")
        if state.next_run_at is not None and now < state.next_run_at:
            raise WatchSkippedError("frequency_not_respected")
        remaining = state.quota_remaining(now, daily_max_runs=profile.watch.daily_max_runs)
        if remaining is not None and remaining <= 0:
            raise WatchSkippedError("daily_quota_exceeded")
