from datetime import date

import pytest

from recal.adapters.in_memory import (
    InMemoryOpportunityRepository,
    InMemoryProfileRepository,
    InMemoryRunRepository,
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
    runs = InMemoryRunRepository()
    use_case = StartWatchRun(
        profiles=InMemoryProfileRepository(),
        runs=runs,
        runner=NoopWatchRunner(),
    )

    run = await use_case.execute()

    assert run.status is RunStatus.COMPLETED
    assert run.trigger is RunTrigger.MANUAL
    assert str(run.id) in runs.items


@pytest.mark.asyncio
async def test_scheduled_watch_run_keeps_scheduled_trigger() -> None:
    use_case = StartWatchRun(
        profiles=InMemoryProfileRepository(),
        runs=InMemoryRunRepository(),
        runner=NoopWatchRunner(),
    )

    run = await use_case.execute(trigger=RunTrigger.SCHEDULED)

    assert run.trigger is RunTrigger.SCHEDULED
