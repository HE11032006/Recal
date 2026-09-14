from datetime import UTC, date, datetime, timedelta

import pytest

from recal.adapters.in_memory import (
    InMemoryOpportunityRepository,
    InMemoryProfileRepository,
    InMemoryRunRepository,
    InMemoryWatchStateRepository,
    NoopWatchRunner,
)
from recal.application.use_cases import (
    ListOpportunities,
    StartWatchRun,
    SubmitFeedback,
    UpdateProfile,
)
from recal.domain.entities import (
    Feedback,
    FeedbackAction,
    Opportunity,
    OpportunityStatus,
    OpportunityType,
    RunStatus,
    RunTrigger,
    UserProfile,
    WatchRun,
    WatchState,
)
from recal.domain.errors import WatchSkippedError


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


def _start_use_case(
    *,
    profile: UserProfile | None = None,
    state: WatchState | None = None,
    now: datetime | None = None,
    runner=NoopWatchRunner(),
) -> StartWatchRun:
    return StartWatchRun(
        profiles=InMemoryProfileRepository(profile),
        runs=InMemoryRunRepository(),
        runner=runner,
        watch_state=InMemoryWatchStateRepository(state),
        clock=FixedClock(now or datetime(2026, 9, 7, 12, 0, tzinfo=UTC)),
    )


@pytest.mark.asyncio
async def test_update_profile_rejects_empty_interests() -> None:
    repository = InMemoryProfileRepository()
    use_case = UpdateProfile(repository)

    with pytest.raises(ValueError, match="au moins un intérêt"):
        await use_case.execute(UserProfile(interests=[]))


@pytest.mark.asyncio
async def test_list_opportunities_filters_by_score() -> None:
    repository = InMemoryOpportunityRepository(
        [
            Opportunity(
                id="high",
                type=OpportunityType.HACKATHON,
                title="High",
                summary="Relevant",
                source_url="https://example.com/high",
                relevance_score=90,
                confidence_score=90,
            ),
            Opportunity(
                id="low",
                type=OpportunityType.INTERNSHIP,
                title="Low",
                summary="Less relevant",
                source_url="https://example.com/low",
                relevance_score=40,
                confidence_score=90,
            ),
        ]
    )

    items, total = await ListOpportunities(repository).execute(min_score=70)

    assert total == 1
    assert items[0].id == "high"


@pytest.mark.asyncio
async def test_feedback_updates_saved_status() -> None:
    opportunity = Opportunity(
        id="op-1",
        type=OpportunityType.HACKATHON,
        title="Hackathon",
        summary="A relevant hackathon",
        source_url="https://example.com/hackathon",
        relevance_score=80,
        confidence_score=95,
        deadline=date(2030, 1, 1),
    )
    repository = InMemoryOpportunityRepository([opportunity])

    await SubmitFeedback(repository).execute(
        "op-1", Feedback(opportunity_id="op-1", action=FeedbackAction.SAVED)
    )

    assert repository.items["op-1"].status is OpportunityStatus.SAVED


@pytest.mark.asyncio
async def test_watch_run_is_completed_and_persisted() -> None:
    use_case = _start_use_case()
    state_repo = use_case.watch_state

    run = await use_case.execute()

    assert run.status is RunStatus.COMPLETED
    assert run.trigger is RunTrigger.MANUAL
    state = await state_repo.get()
    assert state.last_successful_run_at is not None
    assert state.runs_today == 1


@pytest.mark.asyncio
async def test_scheduled_watch_run_keeps_scheduled_trigger() -> None:
    use_case = _start_use_case()

    run = await use_case.execute(trigger=RunTrigger.SCHEDULED)

    assert run.trigger is RunTrigger.SCHEDULED


@pytest.mark.asyncio
async def test_scheduled_run_skipped_when_watch_disabled() -> None:
    profile = UserProfile(interests=["AI"], countries=["Benin"])
    profile.watch.enabled = False
    use_case = _start_use_case(profile=profile)

    with pytest.raises(WatchSkippedError, match="watch_disabled"):
        await use_case.execute(trigger=RunTrigger.SCHEDULED)


@pytest.mark.asyncio
async def test_scheduled_run_skipped_when_frequency_not_respected() -> None:
    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(next_run_at=now + timedelta(minutes=30))
    use_case = _start_use_case(state=state, now=now)

    with pytest.raises(WatchSkippedError, match="frequency_not_respected"):
        await use_case.execute(trigger=RunTrigger.SCHEDULED)


@pytest.mark.asyncio
async def test_scheduled_run_skipped_when_daily_quota_exceeded() -> None:
    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(
        runs_today=12,
        runs_today_date=now.date(),
        next_run_at=now - timedelta(minutes=60),
    )
    use_case = _start_use_case(state=state, now=now)

    with pytest.raises(WatchSkippedError, match="daily_quota_exceeded"):
        await use_case.execute(trigger=RunTrigger.SCHEDULED)


@pytest.mark.asyncio
async def test_scheduled_run_skipped_when_another_run_active() -> None:
    from uuid import uuid4

    use_case = _start_use_case()
    stuck = RunStatus.RUNNING
    # Injection d’un cycle bloqué en cours (running) dans le dépôt.
    use_case.runs.items[str(uuid4())] = WatchRun(
        id=uuid4(), status=stuck, trigger=RunTrigger.SCHEDULED
    )

    with pytest.raises(WatchSkippedError, match="run_already_active"):
        await use_case.execute(trigger=RunTrigger.SCHEDULED)


@pytest.mark.asyncio
async def test_frequency_allows_run_when_next_run_in_past() -> None:
    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(next_run_at=now - timedelta(minutes=1))
    use_case = _start_use_case(state=state, now=now)

    run = await use_case.execute(trigger=RunTrigger.SCHEDULED)

    assert run.status is RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_failed_run_persists_error_and_does_not_update_success_state() -> None:
    class FailingRunner:
        async def execute(self, run, profile, *, processed_urls=()):
            raise RuntimeError("boom")

    use_case = _start_use_case(runner=FailingRunner())
    state_repo = use_case.watch_state

    with pytest.raises(RuntimeError, match="boom"):
        await use_case.execute()

    state = await state_repo.get()
    assert state.last_successful_run_at is None
    assert state.runs_today == 1
