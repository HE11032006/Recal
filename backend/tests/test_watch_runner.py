from datetime import date

import pytest

from recal.adapters.in_memory import (
    InMemoryOpportunityRepository,
    StaticSearchAdapter,
)
from recal.application.ports import SearchResult
from recal.application.watch_runner import OpportunityWatchRunner
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
