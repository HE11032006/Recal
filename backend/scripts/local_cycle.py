"""Cycle local complet : vrai Parallel Search + analyseur heuristique local.

Vérifie le pipeline réel (recherche, filtrage domaines, scoring, dédup,
persistance SQLite) sans dépendre d’AWS ni d’une clé API.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from recal.adapters.in_memory import FakeOpportunityAnalyzer
from recal.adapters.parallel_search import ParallelSearchAdapter
from recal.adapters.sqlite_repositories import (
    SQLiteOpportunityRepository,
    SQLiteProfileRepository,
    SQLiteRunRepository,
    SQLiteStore,
    SQLiteWatchStateRepository,
)
from recal.application.use_cases import StartWatchRun, SystemClock
from recal.application.watch_runner import OpportunityWatchRunner
from recal.domain.entities import RunTrigger


async def main() -> None:
    store = SQLiteStore(":memory:")
    profiles = SQLiteProfileRepository(store)
    opportunities = SQLiteOpportunityRepository(store)
    runs = SQLiteRunRepository(store)
    watch_state = SQLiteWatchStateRepository(store)
    search = ParallelSearchAdapter()
    analyzer = FakeOpportunityAnalyzer()
    runner = OpportunityWatchRunner(search=search, analyzer=analyzer, opportunities=opportunities)
    use_case = StartWatchRun(
        profiles,
        runs,
        runner,
        watch_state,
        SystemClock(),
    )
    run = await use_case.execute(trigger=RunTrigger.MANUAL)
    print(f"run_id={run.id}")
    print(f"status={run.status.value}")
    print(f"opportunities_found={run.opportunities_found}")
    print(f"urls_processed={len(run.urls_processed)}")
    for url in run.urls_processed[:10]:
        print(f"  {url}")
    items, total = await opportunities.list(page=1, page_size=10, min_score=None)
    print(f"total_saved={total}")
    for item in items:
        print(f"  [{item.type.value}] {item.title[:60]} score={item.relevance_score}")
    await search.aclose()


if __name__ == "__main__":
    asyncio.run(main())
