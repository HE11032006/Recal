from __future__ import annotations

from dataclasses import dataclass

from recal.adapters.in_memory import FakeOpportunityAnalyzer, NoopWatchRunner
from recal.adapters.sqlite_repositories import (
    SQLiteOpportunityRepository,
    SQLiteProfileRepository,
    SQLiteRunRepository,
    SQLiteStore,
    SQLiteWatchStateRepository,
)
from recal.application.ports import (
    OpportunityAnalysisPort,
    OpportunityRepository,
    ProfileRepository,
    RunRepository,
    WatchRunner,
    WatchStateRepository,
    WebSearchPort,
)
from recal.application.use_cases import (
    ListOpportunities,
    StartWatchRun,
    SubmitFeedback,
    SystemClock,
    UpdateProfile,
)
from recal.infrastructure.config import Settings, get_settings


@dataclass(slots=True)
class AppContainer:
    profiles: ProfileRepository
    opportunities: OpportunityRepository
    runs: RunRepository
    watch_state: WatchStateRepository
    search: WebSearchPort | None
    analyzer: OpportunityAnalysisPort | None
    update_profile: UpdateProfile
    list_opportunities: ListOpportunities
    submit_feedback: SubmitFeedback
    start_watch_run: StartWatchRun


def build_search_adapter(settings: Settings) -> WebSearchPort | None:
    if settings.search_provider == "parallel":
        from recal.adapters.parallel_search import ParallelSearchAdapter

        return ParallelSearchAdapter(endpoint=settings.parallel_search_endpoint)
    if settings.search_provider == "tavily":
        if not settings.tavily_api_key:
            return None
        from recal.adapters.tavily_search import TavilySearchAdapter

        return TavilySearchAdapter(settings.tavily_api_key)
    return None


def build_analyzer(settings: Settings) -> OpportunityAnalysisPort:
    if settings.analyzer_provider == "strands":
        from recal.adapters.strands_analyzer import StrandsOpportunityAnalyzer

        return StrandsOpportunityAnalyzer(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
        )
    return FakeOpportunityAnalyzer()


def build_watch_runner(
    settings: Settings,
    search: WebSearchPort | None,
    analyzer: OpportunityAnalysisPort | None,
    opportunities: OpportunityRepository,
) -> WatchRunner:
    if search is None or analyzer is None:
        return NoopWatchRunner()
    from recal.application.watch_runner import OpportunityWatchRunner

    return OpportunityWatchRunner(
        search=search,
        analyzer=analyzer,
        opportunities=opportunities,
        max_searches=settings.agent_max_tool_calls,
        max_results_per_search=settings.tavily_max_results,
    )


def _build_sqlite_repositories(
    settings: Settings,
) -> tuple[ProfileRepository, OpportunityRepository, RunRepository, WatchStateRepository]:
    database_path = ":memory:" if settings.app_env == "test" else "recal.db"
    store = SQLiteStore(database_path)
    return (
        SQLiteProfileRepository(store),
        SQLiteOpportunityRepository(store),
        SQLiteRunRepository(store),
        SQLiteWatchStateRepository(store),
    )


def _build_dynamodb_repositories(
    settings: Settings,
) -> tuple[ProfileRepository, OpportunityRepository, RunRepository, WatchStateRepository]:
    import boto3

    from recal.adapters.dynamodb_repositories import (
        DynamoDBOpportunityRepository,
        DynamoDBProfileRepository,
        DynamoDBRunRepository,
        DynamoDBWatchStateRepository,
    )

    resource = boto3.resource("dynamodb", region_name=settings.aws_region)
    return (
        DynamoDBProfileRepository(resource.Table(settings.dynamodb_table_profiles)),
        DynamoDBOpportunityRepository(resource.Table(settings.dynamodb_table_opportunities)),
        DynamoDBRunRepository(resource.Table(settings.dynamodb_table_runs)),
        DynamoDBWatchStateRepository(resource.Table(settings.dynamodb_table_watch_state)),
    )


def build_container(settings: Settings | None = None) -> AppContainer:
    settings = settings or get_settings()
    if settings.persistence_provider == "dynamodb":
        profiles, opportunities, runs, watch_state = _build_dynamodb_repositories(settings)
    else:
        profiles, opportunities, runs, watch_state = _build_sqlite_repositories(settings)
    search = build_search_adapter(settings)
    analyzer = build_analyzer(settings)
    return AppContainer(
        profiles=profiles,
        opportunities=opportunities,
        runs=runs,
        watch_state=watch_state,
        search=search,
        analyzer=analyzer,
        update_profile=UpdateProfile(profiles),
        list_opportunities=ListOpportunities(opportunities),
        submit_feedback=SubmitFeedback(opportunities),
        start_watch_run=StartWatchRun(
            profiles,
            runs,
            build_watch_runner(settings, search, analyzer, opportunities),
            watch_state,
            SystemClock(),
        ),
    )
