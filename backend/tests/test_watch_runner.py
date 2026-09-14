from datetime import UTC, date, datetime, timedelta

import pytest

from recal.adapters.in_memory import (
    FakeOpportunityAnalyzer,
    InMemoryOpportunityRepository,
    StaticSearchAdapter,
)
from recal.application.ports import SearchResult
from recal.application.watch_runner import OpportunityWatchRunner
from recal.domain.catalog import default_allowed_domains, is_url_allowed
from recal.domain.entities import Opportunity, OpportunityType, UserProfile, WatchRun


class FakeAnalyzer:
    async def analyze(self, search_results, profile):
        return [
            Opportunity(
                id="new-opportunity",
                type=OpportunityType.HACKATHON,
                title="AI Hackathon",
                summary="A good opportunity",
                source_url="https://example.com/ai-hackathon",
                relevance_score=85,
                confidence_score=95,
                deadline=date(2030, 1, 1),
            ),
            Opportunity(
                id="low-score",
                type=OpportunityType.INTERNSHIP,
                title="Low score internship",
                summary="Not a fit",
                source_url="https://example.com/low-score",
                relevance_score=30,
                confidence_score=95,
            ),
        ]


@pytest.mark.asyncio
async def test_runner_saves_only_relevant_new_opportunities() -> None:
    repository = InMemoryOpportunityRepository()
    runner = OpportunityWatchRunner(
        search=StaticSearchAdapter([SearchResult("Result", "https://example.com", "content")]),
        analyzer=FakeAnalyzer(),
        opportunities=repository,
    )

    run = await runner.execute(
        WatchRun(),
        UserProfile(interests=["AI"], countries=["Benin"], relevance_threshold=70),
    )

    assert run.opportunities_found == 1
    assert list(repository.items) == ["new-opportunity"]


@pytest.mark.asyncio
async def test_runner_filters_disallowed_domains() -> None:
    repository = InMemoryOpportunityRepository()
    runner = OpportunityWatchRunner(
        search=StaticSearchAdapter(
            [
                SearchResult("Ok", "https://devpost.com/hackathon", "content"),
                SearchResult("Blocked", "https://spam.example.org/hackathon", "content"),
            ]
        ),
        analyzer=FakeOpportunityAnalyzer(),
        opportunities=repository,
    )
    profile = UserProfile(interests=["AI"])
    profile.watch.allowed_domains = ["devpost.com"]

    run = await runner.execute(WatchRun(), profile)

    assert run.urls_processed == ["https://devpost.com/hackathon"]


@pytest.mark.asyncio
async def test_runner_deduplicates_urls_across_queries() -> None:
    repository = InMemoryOpportunityRepository()
    same_url = "https://devpost.com/hackathon"

    class TwoQuerySearch:
        def __init__(self) -> None:
            self.calls = 0

        async def search(self, query, *, max_results=5):
            self.calls += 1
            return [SearchResult("Title", same_url, "content")]

    search = TwoQuerySearch()
    runner = OpportunityWatchRunner(
        search=search,
        analyzer=FakeOpportunityAnalyzer(),
        opportunities=repository,
    )

    run = await runner.execute(WatchRun(), UserProfile(interests=["AI"]))

    assert search.calls == 3
    assert run.urls_processed == [same_url]


@pytest.mark.asyncio
async def test_runner_skips_previously_processed_urls() -> None:
    repository = InMemoryOpportunityRepository()
    runner = OpportunityWatchRunner(
        search=StaticSearchAdapter(
            [
                SearchResult("Old", "https://devpost.com/old", "content"),
                SearchResult("New", "https://devpost.com/new", "content"),
            ]
        ),
        analyzer=FakeAnalyzer(),
        opportunities=repository,
    )
    profile = UserProfile(interests=["AI"])
    profile.watch.allowed_domains = ["devpost.com"]

    run = await runner.execute(WatchRun(), profile, processed_urls=["https://devpost.com/old/"])

    assert run.urls_processed == ["https://devpost.com/new"]


@pytest.mark.asyncio
async def test_fake_analyzer_scoring_and_types() -> None:
    analyzer = FakeOpportunityAnalyzer()
    results = [
        SearchResult("AI Hackathon 2026", "https://devpost.com/x", "great hackathon"),
        SearchResult("Random page", "https://blog.example.org", "nothing here"),
    ]
    profile = UserProfile(interests=["AI"])
    profile.watch.allowed_domains = ["devpost.com"]

    opportunities = await analyzer.analyze(results, profile)

    assert len(opportunities) == 2
    hackathon = opportunities[0]
    assert hackathon.type is OpportunityType.HACKATHON
    assert hackathon.relevance_score == 85.0
    other = opportunities[1]
    assert other.type is OpportunityType.OTHER
    assert other.relevance_score == 40.0


def test_is_url_allowed_suffix_match() -> None:
    assert is_url_allowed("https://devpost.com/x", ["devpost.com"])
    assert is_url_allowed("https://www.devpost.com/x", ["devpost.com"])
    assert not is_url_allowed("https://notdevpost.com/x", ["devpost.com"])
    assert not is_url_allowed("https://evil.com/devpost.com", ["devpost.com"])
    assert is_url_allowed("https://anything.example", [])


def test_default_allowed_domains_deduplicates() -> None:
    domains = default_allowed_domains(["hackathon", "internship", "hackathon"])
    assert domains.count("devpost.com") == 1
    assert "handshake.com" in domains


def test_default_allowed_domains_always_include_shared_aggregators() -> None:
    for types in (["hackathon"], ["scholarship"], ["conference"], ["certification"]):
        domains = default_allowed_domains(types)
        assert "youthop.com" in domains
        assert "opportunitydesk.org" in domains
        assert "polenexus.com" in domains


def test_default_allowed_domains_cover_new_sources() -> None:
    hackathons = default_allowed_domains(["hackathon"])
    assert "zindi.africa" in hackathons
    assert "kaggle.com" in hackathons
    assert "hackathon.com" in hackathons
    internships = default_allowed_domains(["internship"])
    assert "remoteok.com" in internships
    assert "careers.un.org" in internships
    fellowships = default_allowed_domains(["fellowship"])
    assert "summerofcode.withgoogle.com" in fellowships
    assert "outreachy.org" in fellowships
    scholarships = default_allowed_domains(["scholarship"])
    assert "campusfrance.org" in scholarships
    assert "eacea.ec.europa.eu" in scholarships
    conferences = default_allowed_domains(["conference"])
    assert "lu.ma" in conferences
    assert "africatechsummit.com" in conferences
    certifications = default_allowed_domains(["certification"])
    assert "netacad.com" in certifications
    assert "training.linuxfoundation.org" in certifications


@pytest.mark.asyncio
async def test_watch_state_register_run_enforces_daily_quota() -> None:
    from recal.domain.entities import WatchState
    from recal.domain.errors import DailyQuotaExceededError

    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(runs_today=2, runs_today_date=now.date())

    state.register_run(now, daily_max_runs=3, frequency_minutes=60, is_scheduled=True)

    assert state.runs_today == 3
    assert state.next_run_at == now + timedelta(minutes=60)

    with pytest.raises(DailyQuotaExceededError):
        state.register_run(now, daily_max_runs=3, frequency_minutes=60, is_scheduled=True)


@pytest.mark.asyncio
async def test_watch_state_manual_run_bypasses_daily_quota() -> None:
    from recal.domain.entities import WatchState

    now = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    state = WatchState(runs_today=12, runs_today_date=now.date())

    state.register_run(now, daily_max_runs=12, frequency_minutes=60, is_scheduled=False)

    assert state.runs_today == 13


@pytest.mark.asyncio
async def test_watch_state_resets_counter_on_new_day() -> None:
    from recal.domain.entities import WatchState

    yesterday = datetime(2026, 9, 6, 23, 59, tzinfo=UTC)
    today = datetime(2026, 9, 7, 0, 1, tzinfo=UTC)
    state = WatchState(runs_today=12, runs_today_date=yesterday.date())

    state.register_run(today, daily_max_runs=12, frequency_minutes=60)

    assert state.runs_today == 1
