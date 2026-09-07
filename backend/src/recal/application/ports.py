"""Ports applicatifs : contrats que les adaptateurs externes doivent implémenter."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from recal.domain.entities import Opportunity, UserProfile, WatchRun


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    content: str
    source: str = "tavily"


class WebSearchPort(Protocol):
    async def search(self, query: str, *, max_results: int = 5) -> Sequence[SearchResult]:
        """Rechercher des pages publiques correspondant à une requête."""


class OpportunityAnalysisPort(Protocol):
    async def analyze(
        self,
        search_results: Sequence[SearchResult],
        profile: UserProfile,
    ) -> Sequence[Opportunity]:
        """Extraire et analyser des opportunités à partir de résultats web."""


class ProfileRepository(Protocol):
    async def get_default(self) -> UserProfile: ...

    async def save(self, profile: UserProfile) -> UserProfile: ...


class OpportunityRepository(Protocol):
    async def list(
        self,
        *,
        page: int,
        page_size: int,
        min_score: float | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Opportunity], int]: ...

    async def get(self, opportunity_id: str) -> Opportunity | None: ...

    async def save_if_new(self, opportunity: Opportunity) -> bool: ...

    async def update(self, opportunity: Opportunity) -> Opportunity: ...


class RunRepository(Protocol):
    async def save(self, run: WatchRun) -> WatchRun: ...

    async def get(self, run_id: str) -> WatchRun | None: ...


class WatchRunner(Protocol):
    async def execute(self, run: WatchRun, profile: UserProfile) -> WatchRun: ...
