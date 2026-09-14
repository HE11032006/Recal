from datetime import UTC, date, datetime, timedelta

import pytest

from recal.adapters.parallel_search import ParallelSearchAdapter
from recal.adapters.sqlite_repositories import (
    SQLiteOpportunityRepository,
    SQLiteProfileRepository,
    SQLiteRunRepository,
    SQLiteStore,
    SQLiteWatchStateRepository,
)
from recal.domain.entities import (
    Opportunity,
    OpportunityType,
    RunStatus,
    RunTrigger,
    UserProfile,
    WatchRun,
    WatchSettings,
    WatchState,
)


@pytest.fixture
def store() -> SQLiteStore:
    return SQLiteStore(":memory:")


@pytest.mark.asyncio
async def test_opportunity_list_pagination_returns_saved_rows(store: SQLiteStore) -> None:
    repository = SQLiteOpportunityRepository(store)
    for index in range(3):
        opportunity = Opportunity(
            id=f"op-{index}",
            type=OpportunityType.HACKATHON,
            title=f"Op {index}",
            summary="Relevant",
            source_url=f"https://devpost.com/{index}",
            relevance_score=70.0 + index,
            confidence_score=90.0,
        )
        assert await repository.save_if_new(opportunity)

    items, total = await repository.list(page=1, page_size=2)
    assert total == 3
    assert len(items) == 2

    items, total = await repository.list(page=2, page_size=2)
    assert total == 3
    assert len(items) == 1


@pytest.mark.asyncio
async def test_opportunity_list_filters_since(store: SQLiteStore) -> None:
    repository = SQLiteOpportunityRepository(store)
    older = Opportunity(
        id="older",
        type=OpportunityType.HACKATHON,
        title="Old",
        summary="Past",
        source_url="https://devpost.com/old",
        relevance_score=80.0,
        confidence_score=90.0,
        verified_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer = Opportunity(
        id="newer",
        type=OpportunityType.HACKATHON,
        title="New",
        summary="Recent",
        source_url="https://devpost.com/new",
        relevance_score=85.0,
        confidence_score=90.0,
        verified_at=datetime(2026, 2, 1, tzinfo=UTC),
    )
    await repository.save_if_new(older)
    await repository.save_if_new(newer)

    items, total = await repository.list(
        page=1, page_size=10, since=datetime(2026, 1, 15, tzinfo=UTC)
    )
    assert total == 1
    assert items[0].id == "newer"

    items, total = await repository.list(page=1, page_size=10)
    assert total == 2


@pytest.mark.asyncio
async def test_watch_state_roundtrip(store: SQLiteStore) -> None:
    repository = SQLiteWatchStateRepository(store)
    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(
        last_run_at=now,
        next_run_at=now + timedelta(minutes=60),
        last_successful_run_at=now,
        runs_today=3,
        runs_today_date=now.date(),
        processed_urls=["https://devpost.com/a", "https://devpost.com/b"],
    )

    await repository.save(state)
    loaded = await repository.get()

    assert loaded == state


@pytest.mark.asyncio
async def test_watch_state_defaults_when_empty(store: SQLiteStore) -> None:
    repository = SQLiteWatchStateRepository(store)

    state = await repository.get()

    assert state.last_run_at is None
    assert state.runs_today == 0
    assert state.processed_urls == []


@pytest.mark.asyncio
async def test_profile_roundtrip_with_watch_settings(store: SQLiteStore) -> None:
    repository = SQLiteProfileRepository(store)
    profile = UserProfile(interests=["AI"], countries=["CI"], study_level="Licence 3")
    profile.watch.allowed_domains = ["devpost.com"]
    profile.watch.frequency_minutes = 30
    profile.watch.minimum_relevance_score = 80

    await repository.save(profile)
    loaded = await repository.get_default()

    assert isinstance(loaded.watch, WatchSettings)
    assert loaded.watch.allowed_domains == ["devpost.com"]
    assert loaded.watch.frequency_minutes == 30
    assert loaded.watch.minimum_relevance_score == 80


@pytest.mark.asyncio
async def test_run_get_active_returns_only_unfinished(store: SQLiteStore) -> None:
    repository = SQLiteRunRepository(store)
    running = WatchRun(trigger=RunTrigger.SCHEDULED, status=RunStatus.RUNNING)
    done = WatchRun(trigger=RunTrigger.MANUAL, status=RunStatus.COMPLETED)
    await repository.save(running)
    await repository.save(done)

    active = await repository.get_active()

    assert active is not None
    assert active.id == running.id
    assert active.status is RunStatus.RUNNING


@pytest.mark.asyncio
async def test_run_roundtrip_keeps_urls_processed(store: SQLiteStore) -> None:
    repository = SQLiteRunRepository(store)
    run = WatchRun(trigger=RunTrigger.SCHEDULED)
    run.urls_processed = ["https://devpost.com/a"]

    await repository.save(run)
    loaded = await repository.get(str(run.id))

    assert loaded is not None
    assert loaded.urls_processed == ["https://devpost.com/a"]


def test_parallel_adapter_parses_json_response() -> None:
    class FakeResponse:
        headers = {"content-type": "application/json"}
        text = ""

        @staticmethod
        def json():
            return {
                "jsonrpc": "2.0",
                "id": 3,
                "result": {
                    "structuredContent": {
                        "results": [
                            {
                                "url": "https://devpost.com/x",
                                "title": "Hackathon",
                                "publish_date": "2026-09-01",
                                "excerpts": ["excerpt one", "excerpt two"],
                            }
                        ]
                    }
                },
            }

    adapter = ParallelSearchAdapter()
    message = adapter._parse_message(FakeResponse())  # noqa: SLF001
    assert message["result"]["structuredContent"]["results"][0]["url"] == "https://devpost.com/x"


@pytest.mark.asyncio
async def test_parallel_adapter_search_extracts_results() -> None:
    import httpx

    raw = (
        b'{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"ok"}],'
        b'"structuredContent":{"results":[{"url":"https://devpost.com/y",'
        b'"title":"AI Hackathon","excerpts":["content"]}]}}}'
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "mcp-session-id": "session-1",
            },
            content=raw,
        )
    )
    adapter = ParallelSearchAdapter(client=httpx.AsyncClient(transport=transport))

    results = await adapter.search("hackathon 2026", max_results=5)

    assert len(results) == 1
    assert results[0].url == "https://devpost.com/y"
    assert results[0].source == "parallel"


def test_parallel_adapter_rejects_empty_endpoint() -> None:
    with pytest.raises(ValueError, match="obligatoire"):
        ParallelSearchAdapter(endpoint=" ")


def test_dynamodb_ttl_with_deadline_extends_grace_period() -> None:
    from recal.adapters.dynamodb_repositories import (
        EXPIRED_GRACE_SECONDS,
        DynamoDBOpportunityRepository,
    )

    opportunity = Opportunity(
        id="ttl-1",
        type=OpportunityType.HACKATHON,
        title="Expiring",
        summary="Soon gone",
        source_url="https://devpost.com/x",
        relevance_score=80.0,
        confidence_score=90.0,
        deadline=date(2027, 1, 1),
    )
    payload = DynamoDBOpportunityRepository._serialize(opportunity)

    expected = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp()) + EXPIRED_GRACE_SECONDS
    assert payload["ttl"] == expected


def test_dynamodb_ttl_without_deadline_uses_verified_at() -> None:
    from recal.adapters.dynamodb_repositories import (
        NO_DEADLINE_KEEP_SECONDS,
        DynamoDBOpportunityRepository,
    )

    opportunity = Opportunity(
        id="ttl-2",
        type=OpportunityType.INTERNSHIP,
        title="No deadline",
        summary="Evergreen",
        source_url="https://linkedin.com/jobs/x",
        relevance_score=75.0,
        confidence_score=80.0,
        verified_at=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
    )
    payload = DynamoDBOpportunityRepository._serialize(opportunity)

    expected = int(datetime(2026, 9, 1, 12, 0, tzinfo=UTC).timestamp()) + NO_DEADLINE_KEEP_SECONDS
    assert payload["ttl"] == expected
