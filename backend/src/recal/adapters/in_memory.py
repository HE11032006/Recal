from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from recal.application.ports import SearchResult
from recal.domain.entities import Opportunity, UserProfile, WatchRun


class InMemoryProfileRepository:
    def __init__(self, profile: UserProfile | None = None) -> None:
        self.profile = profile or UserProfile(interests=["software engineering"])

    async def get_default(self) -> UserProfile:
        return self.profile

    async def save(self, profile: UserProfile) -> UserProfile:
        self.profile = profile
        return self.profile


class InMemoryOpportunityRepository:
    def __init__(self, opportunities: Sequence[Opportunity] | None = None) -> None:
        self.items: dict[str, Opportunity] = {item.id: item for item in opportunities or []}

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        min_score: float | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Opportunity], int]:
        items = list(self.items.values())
        if min_score is not None:
            items = [item for item in items if item.relevance_score >= min_score]
        if status is not None:
            items = [item for item in items if item.status.value == status]
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def get(self, opportunity_id: str) -> Opportunity | None:
        return self.items.get(opportunity_id)

    async def save_if_new(self, opportunity: Opportunity) -> bool:
        if opportunity.id in self.items:
            return False
        self.items[opportunity.id] = opportunity
        return True

    async def update(self, opportunity: Opportunity) -> Opportunity:
        self.items[opportunity.id] = opportunity
        return opportunity


class InMemoryRunRepository:
    def __init__(self) -> None:
        self.items: dict[str, WatchRun] = {}

    async def save(self, run: WatchRun) -> WatchRun:
        self.items[str(run.id)] = replace(run)
        return run

    async def get(self, run_id: str) -> WatchRun | None:
        return self.items.get(run_id)


class NoopWatchRunner:
    async def execute(self, run: WatchRun, profile: UserProfile) -> WatchRun:
        run.opportunities_found = 0
        return run


class StaticSearchAdapter:
    def __init__(self, results: Sequence[SearchResult] | None = None) -> None:
        self.results = list(results or [])

    async def search(self, query: str, *, max_results: int = 5) -> Sequence[SearchResult]:
        return self.results[:max_results]
