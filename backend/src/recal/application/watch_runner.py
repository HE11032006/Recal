from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from recal.application.ports import (
    OpportunityAnalysisPort,
    OpportunityRepository,
    SearchResult,
    WebSearchPort,
)
from recal.domain.catalog import default_allowed_domains, is_url_allowed
from recal.domain.entities import UserProfile, WatchRun


@dataclass(slots=True)
class OpportunityWatchRunner:
    search: WebSearchPort
    analyzer: OpportunityAnalysisPort
    opportunities: OpportunityRepository
    max_searches: int = 3
    max_results_per_search: int = 5

    async def execute(
        self,
        run: WatchRun,
        profile: UserProfile,
        *,
        processed_urls: Sequence[str] = (),
    ) -> WatchRun:
        queries = self._build_queries(profile)[: self.max_searches]
        effective_domains = list(profile.watch.allowed_domains) or default_allowed_domains(
            profile.watch.opportunity_types
        )
        all_results: list[SearchResult] = []
        seen_urls: set[str] = set()
        previously_processed = {self._normalize(url) for url in processed_urls}
        for query in queries:
            for result in await self.search.search(query, max_results=self.max_results_per_search):
                normalized = self._normalize(result.url)
                if not normalized or normalized in seen_urls:
                    continue
                if previously_processed and normalized in previously_processed:
                    continue
                if not is_url_allowed(result.url, effective_domains):
                    continue
                seen_urls.add(normalized)
                all_results.append(result)
        run.urls_processed = sorted(seen_urls)
        analyzed = await self.analyzer.analyze(all_results, profile)
        threshold = (
            profile.watch.minimum_relevance_score
            if profile.watch.minimum_relevance_score is not None
            else profile.relevance_threshold
        )
        saved_count = 0
        for opportunity in analyzed:
            if opportunity.relevance_score < threshold:
                continue
            if await self.opportunities.save_if_new(opportunity):
                saved_count += 1
        run.opportunities_found = saved_count
        return run

    @staticmethod
    def _normalize(url: str) -> str:
        return url.strip().lower().rstrip("/")

    @staticmethod
    def _build_queries(profile: UserProfile) -> list[str]:
        """Requêtes ciblant des pages d’événements, pas des agrégateurs.

        Les requêtes génériques (« hackathons for students ») ramènent des
        pages de listing que l’analyseur doit rejeter. Des mots-clés
        d’action (« registration », « apply », « deadline ») orientent la
        recherche vers des pages d’opportunités individuelles.
        """
        interests = " ".join(profile.interests[:3]) or "tech"
        countries = " ".join(profile.countries[:2])
        queries_by_type = {
            "hackathon": f"student hackathon {interests} {countries} 2026 registration open",
            "internship": f"{interests} internship {countries} 2026 apply deadline students",
            "fellowship": f"{interests} fellowship 2026 application deadline students",
            "scholarship": f"{interests} scholarship 2026 apply deadline students",
            "conference": f"{interests} tech conference 2026 call for papers registration",
            "certification": f"{interests} certification 2026 free training enroll",
        }
        queries = [
            query
            for opportunity_type, query in queries_by_type.items()
            if opportunity_type in profile.watch.opportunity_types
        ]
        queries.append(f"{interests} {countries} 2026 opportunity registration apply")
        return queries
