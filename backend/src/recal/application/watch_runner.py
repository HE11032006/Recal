from __future__ import annotations

from dataclasses import dataclass

from recal.application.ports import (
    OpportunityAnalysisPort,
    OpportunityRepository,
    SearchResult,
    WebSearchPort,
)
from recal.domain.entities import UserProfile, WatchRun


@dataclass(slots=True)
class OpportunityWatchRunner:
    search: WebSearchPort
    analyzer: OpportunityAnalysisPort
    opportunities: OpportunityRepository
    max_searches: int = 3
    max_results_per_search: int = 5

    async def execute(self, run: WatchRun, profile: UserProfile) -> WatchRun:
        queries = self._build_queries(profile)[: self.max_searches]
        all_results: list[SearchResult] = []
        for query in queries:
            all_results.extend(
                await self.search.search(query, max_results=self.max_results_per_search)
            )
        analyzed = await self.analyzer.analyze(all_results, profile)
        saved_count = 0
        for opportunity in analyzed:
            if opportunity.relevance_score < profile.relevance_threshold:
                continue
            if await self.opportunities.save_if_new(opportunity):
                saved_count += 1
        run.opportunities_found = saved_count
        return run

    @staticmethod
    def _build_queries(profile: UserProfile) -> list[str]:
        interests = " ".join(profile.interests[:4])
        countries = " ".join(profile.countries[:3])
        return [
            f"tech hackathon {interests} open to students {countries} 2026",
            f"software engineering internship {interests} students {countries} 2026",
            f"technology fellowship scholarship {interests} international students 2026",
        ]
