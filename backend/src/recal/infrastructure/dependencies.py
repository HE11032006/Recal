from __future__ import annotations

from dataclasses import dataclass

from recal.adapters.in_memory import NoopWatchRunner
from recal.adapters.sqlite_repositories import (
    SQLiteOpportunityRepository,
    SQLiteProfileRepository,
    SQLiteRunRepository,
    SQLiteStore,
)
from recal.application.use_cases import (
    ListOpportunities,
    StartWatchRun,
    SubmitFeedback,
    UpdateProfile,
)
from recal.infrastructure.config import Settings, get_settings


@dataclass(slots=True)
class AppContainer:
    store: SQLiteStore
    profiles: SQLiteProfileRepository
    opportunities: SQLiteOpportunityRepository
    runs: SQLiteRunRepository
    update_profile: UpdateProfile
    list_opportunities: ListOpportunities
    submit_feedback: SubmitFeedback
    start_watch_run: StartWatchRun


def build_container(settings: Settings | None = None) -> AppContainer:
    settings = settings or get_settings()
    database_path = ":memory:" if settings.app_env == "test" else "recal.db"
    store = SQLiteStore(database_path)
    profiles = SQLiteProfileRepository(store)
    opportunities = SQLiteOpportunityRepository(store)
    runs = SQLiteRunRepository(store)
    return AppContainer(
        store=store,
        profiles=profiles,
        opportunities=opportunities,
        runs=runs,
        update_profile=UpdateProfile(profiles),
        list_opportunities=ListOpportunities(opportunities),
        submit_feedback=SubmitFeedback(opportunities),
        start_watch_run=StartWatchRun(profiles, runs, NoopWatchRunner()),
    )
