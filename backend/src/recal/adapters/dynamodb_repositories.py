from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from recal.domain.entities import (
    Opportunity,
    OpportunityStatus,
    OpportunityType,
    RunStatus,
    UserProfile,
    WatchRun,
    WatchSettings,
    WatchState,
)


def _to_decimal(value: float) -> Decimal:
    """boto3 refuse les floats vers DynamoDB ; conversion explicite requise."""
    return Decimal(str(value))


# Durées de rétention TTL (secondes) : une opportunité expirée reste
# consultable pendant la période de grâce puis est purgée par DynamoDB.
EXPIRED_GRACE_SECONDS = 30 * 24 * 3600
NO_DEADLINE_KEEP_SECONDS = 90 * 24 * 3600


def _ttl_timestamp(opportunity: Opportunity) -> int:
    """Timestamp epoch pour la purge TTL DynamoDB."""
    if opportunity.deadline is not None:
        expiry = datetime.combine(opportunity.deadline, datetime.min.time()).replace(
            tzinfo=UTC
        )
        return int(expiry.timestamp()) + EXPIRED_GRACE_SECONDS
    verified = opportunity.verified_at
    if verified.tzinfo is None:
        verified = verified.replace(tzinfo=UTC)
    return int(verified.timestamp()) + NO_DEADLINE_KEEP_SECONDS


class DynamoDBProfileRepository:
    def __init__(self, table: Any) -> None:
        self.table = table

    async def get_default(self) -> UserProfile:
        response = self.table.get_item(Key={"id": "default"})
        item = response.get("Item")
        if not item:
            return UserProfile(interests=["software engineering"])
        watch_data = item.get("watch", {})
        if not isinstance(watch_data, dict):
            watch_data = {}
        return UserProfile(
            id=item["id"],
            full_name=item.get("full_name", ""),
            language=item.get("language", "fr"),
            interests=item.get("interests", []),
            countries=item.get("countries", []),
            mobility_countries=item.get("mobility_countries", []),
            study_level=item.get("study_level", ""),
            skills=item.get("skills", []),
            relevance_threshold=float(item.get("relevance_threshold", 70)),
            watch=WatchSettings(
                enabled=watch_data.get("enabled", True),
                frequency_minutes=int(watch_data.get("frequency_minutes", 60)),
                allowed_domains=list(watch_data.get("allowed_domains", [])),
                opportunity_types=list(watch_data.get("opportunity_types", [])),
                max_queries_per_run=int(watch_data.get("max_queries_per_run", 3)),
                max_results_per_query=int(watch_data.get("max_results_per_query", 5)),
                minimum_relevance_score=(
                    float(watch_data["minimum_relevance_score"])
                    if watch_data.get("minimum_relevance_score") is not None
                    else None
                ),
                daily_max_runs=int(watch_data.get("daily_max_runs", 12)),
            ),
        )

    async def save(self, profile: UserProfile) -> UserProfile:
        self.table.put_item(
            Item={
                "id": profile.id,
                "full_name": profile.full_name,
                "language": profile.language,
                "interests": profile.interests,
                "countries": profile.countries,
                "mobility_countries": profile.mobility_countries,
                "study_level": profile.study_level,
                "skills": profile.skills,
                "relevance_threshold": profile.relevance_threshold,
                "watch": {
                    "enabled": profile.watch.enabled,
                    "frequency_minutes": profile.watch.frequency_minutes,
                    "allowed_domains": profile.watch.allowed_domains,
                    "opportunity_types": profile.watch.opportunity_types,
                    "max_queries_per_run": profile.watch.max_queries_per_run,
                    "max_results_per_query": profile.watch.max_results_per_query,
                    "minimum_relevance_score": profile.watch.minimum_relevance_score,
                    "daily_max_runs": profile.watch.daily_max_runs,
                },
            }
        )
        return profile


class DynamoDBOpportunityRepository:
    def __init__(self, table: Any) -> None:
        self.table = table

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        min_score: float | None = None,
        status: str | None = None,
        since: datetime | None = None,
    ) -> tuple[Sequence[Opportunity], int]:
        # Le MVP utilise Scan. Une table de production pourra ajouter des GSI
        # pour filtrer par statut, score et date sans scanner toute la table.
        response = self.table.scan()
        items = [self._deserialize(item) for item in response.get("Items", [])]
        if since is not None:
            items = [item for item in items if item.verified_at >= since]
        if min_score is not None:
            items = [item for item in items if item.relevance_score >= min_score]
        if status is not None:
            items = [item for item in items if item.status.value == status]
        items.sort(key=lambda item: item.relevance_score, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def get(self, opportunity_id: str) -> Opportunity | None:
        response = self.table.get_item(Key={"id": opportunity_id})
        item = response.get("Item")
        return None if item is None else self._deserialize(item)

    async def save_if_new(self, opportunity: Opportunity) -> bool:
        try:
            self.table.put_item(
                Item=self._serialize(opportunity),
                ConditionExpression="attribute_not_exists(id)",
            )
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    async def update(self, opportunity: Opportunity) -> Opportunity:
        self.table.put_item(Item=self._serialize(opportunity))
        return opportunity

    @staticmethod
    def _serialize(opportunity: Opportunity) -> dict[str, Any]:
        return {
            "id": opportunity.id,
            "type": opportunity.type.value,
            "title": opportunity.title,
            "organization": opportunity.organization,
            "summary": opportunity.summary,
            "source_url": opportunity.source_url,
            "relevance_score": _to_decimal(opportunity.relevance_score),
            "confidence_score": _to_decimal(opportunity.confidence_score),
            "relevance_reasons": opportunity.relevance_reasons,
            "deadline": opportunity.deadline.isoformat() if opportunity.deadline else None,
            "eligibility": opportunity.eligibility,
            "verified_at": opportunity.verified_at.isoformat(),
            "status": opportunity.status.value,
            "ttl": _ttl_timestamp(opportunity),
        }

    @staticmethod
    def _deserialize(item: dict[str, Any]) -> Opportunity:
        return Opportunity(
            id=item["id"],
            type=OpportunityType(item["type"]),
            title=item["title"],
            organization=item.get("organization", ""),
            summary=item["summary"],
            source_url=item["source_url"],
            relevance_score=float(item["relevance_score"]),
            confidence_score=float(item["confidence_score"]),
            relevance_reasons=item.get("relevance_reasons", []),
            deadline=date.fromisoformat(item["deadline"]) if item.get("deadline") else None,
            eligibility=item.get("eligibility", {}),
            verified_at=datetime.fromisoformat(item["verified_at"]),
            status=OpportunityStatus(item.get("status", "new")),
        )


class DynamoDBRunRepository:
    def __init__(self, table: Any) -> None:
        self.table = table

    async def save(self, run: WatchRun) -> WatchRun:
        self.table.put_item(
            Item={
                "id": str(run.id),
                "status": run.status.value,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "opportunities_found": run.opportunities_found,
                "error_message": run.error_message,
                "urls_processed": run.urls_processed,
            }
        )
        return run

    async def get(self, run_id: str) -> WatchRun | None:
        response = self.table.get_item(Key={"id": run_id})
        item = response.get("Item")
        if not item:
            return None
        return self._deserialize(item)

    async def get_active(self) -> WatchRun | None:
        # Scan filtré côté client : les cycles actifs sont rares, la table
        # reste petite. Un GSI sur status pourra remplacer ce scan en prod.
        response = self.table.scan(
            FilterExpression="#s IN (:queued, :running)",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":queued": "queued", ":running": "running"},
        )
        items = response.get("Items", [])
        if not items:
            return None
        runs = [self._deserialize(item) for item in items]
        return max(runs, key=lambda run: run.created_at)

    @staticmethod
    def _deserialize(item: dict[str, Any]) -> WatchRun:
        return WatchRun(
            id=UUID(item["id"]),
            status=RunStatus(item["status"]),
            created_at=datetime.fromisoformat(item["created_at"]),
            completed_at=(
                datetime.fromisoformat(item["completed_at"])
                if item.get("completed_at")
                else None
            ),
            opportunities_found=int(item.get("opportunities_found", 0)),
            error_message=item.get("error_message"),
            urls_processed=list(item.get("urls_processed", [])),
        )


class DynamoDBWatchStateRepository:
    def __init__(self, table: Any) -> None:
        self.table = table

    async def get(self) -> WatchState:
        response = self.table.get_item(Key={"id": "default"})
        item = response.get("Item")
        if not item:
            return WatchState()
        return WatchState(
            last_run_at=(
                datetime.fromisoformat(item["last_run_at"]) if item.get("last_run_at") else None
            ),
            next_run_at=(
                datetime.fromisoformat(item["next_run_at"]) if item.get("next_run_at") else None
            ),
            last_successful_run_at=(
                datetime.fromisoformat(item["last_successful_run_at"])
                if item.get("last_successful_run_at")
                else None
            ),
            runs_today=int(item.get("runs_today", 0)),
            runs_today_date=(
                date.fromisoformat(item["runs_today_date"])
                if item.get("runs_today_date")
                else None
            ),
            processed_urls=list(item.get("processed_urls", [])),
        )

    async def save(self, state: WatchState) -> WatchState:
        self.table.put_item(
            Item={
                "id": "default",
                "last_run_at": state.last_run_at.isoformat() if state.last_run_at else None,
                "next_run_at": state.next_run_at.isoformat() if state.next_run_at else None,
                "last_successful_run_at": (
                    state.last_successful_run_at.isoformat()
                    if state.last_successful_run_at
                    else None
                ),
                "runs_today": state.runs_today,
                "runs_today_date": (
                    state.runs_today_date.isoformat() if state.runs_today_date else None
                ),
                "processed_urls": state.processed_urls,
            }
        )
        return state
