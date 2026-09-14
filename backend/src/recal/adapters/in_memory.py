from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime

from recal.application.ports import SearchResult
from recal.domain.entities import (
    Opportunity,
    RunStatus,
    UserProfile,
    WatchRun,
    WatchState,
)


class InMemoryProfileRepository:
    def __init__(self, profile: UserProfile | None = None) -> None:
        self.profile = profile or UserProfile(
            full_name="",
            language="fr",
            interests=["software engineering"],
        )

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
        since: datetime | None = None,
    ) -> tuple[Sequence[Opportunity], int]:
        items = list(self.items.values())
        if since is not None:
            items = [item for item in items if item.verified_at >= since]
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

    async def get_active(self) -> WatchRun | None:
        active = [
            run
            for run in self.items.values()
            if run.status in (RunStatus.QUEUED, RunStatus.RUNNING)
        ]
        return max(active, key=lambda run: run.created_at) if active else None


class InMemoryWatchStateRepository:
    def __init__(self, state: WatchState | None = None) -> None:
        self.state = state or WatchState()

    async def get(self) -> WatchState:
        return self.state

    async def save(self, state: WatchState) -> WatchState:
        self.state = state
        return state


class NoopWatchRunner:
    async def execute(
        self,
        run: WatchRun,
        profile: UserProfile,
        *,
        processed_urls: Sequence[str] = (),
    ) -> WatchRun:
        run.opportunities_found = 0
        return run


class StaticSearchAdapter:
    def __init__(self, results: Sequence[SearchResult] | None = None) -> None:
        self.results = list(results or [])

    async def search(self, query: str, *, max_results: int = 5) -> Sequence[SearchResult]:
        return self.results[:max_results]


class FakeOpportunityAnalyzer:
    """Analyseur déterministe sans modèle, pour le cycle local complet.

    Score heuristique : mots-clés du titre + bonus domaine autorisé.
    Sert à valider le pipeline (recherche, filtrage, scoring, déduplication)
    avant de brancher Claude Haiku via Strands.
    """

    _KEYWORDS: dict[str, str] = {
        "hackathon": "hackathon",
        "internship": "internship",
        "fellowship": "fellowship",
        "scholarship": "scholarship",
    }

    async def analyze(
        self,
        search_results: Sequence[SearchResult],
        profile: UserProfile,
    ) -> list[Opportunity]:
        from recal.domain.catalog import is_url_allowed
        from recal.domain.entities import OpportunityType

        opportunities: list[Opportunity] = []
        for result in search_results:
            title_lower = result.title.lower()
            matched_type = OpportunityType.OTHER
            base = 40.0
            for keyword, value in self._KEYWORDS.items():
                if keyword in title_lower or keyword in result.content.lower():
                    matched_type = OpportunityType(value)
                    base = 75.0
                    break
            domain_bonus = (
                10.0 if is_url_allowed(result.url, profile.watch.allowed_domains) else 0.0
            )
            if not result.url.startswith(("http://", "https://")):
                continue
            opportunity = Opportunity(
                id=result.url,
                type=matched_type,
                title=result.title[:200] or "Opportunité sans titre",
                summary=result.content[:500],
                source_url=result.url,
                relevance_score=min(100.0, base + domain_bonus),
                confidence_score=60.0,
                relevance_reasons=["Correspondance heuristique de mots-clés locale"],
            )
            opportunities.append(opportunity)
        return opportunities
