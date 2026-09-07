from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any
from uuid import UUID

from recal.domain.entities import (
    Opportunity,
    OpportunityStatus,
    OpportunityType,
    UserProfile,
    WatchRun,
)


class DynamoDBProfileRepository:
    def __init__(self, table: Any) -> None:
        self.table = table

    async def get_default(self) -> UserProfile:
        response = self.table.get_item(Key={"id": "default"})
        item = response.get("Item")
        if not item:
            return UserProfile(interests=["software engineering"])
        return UserProfile(
            id=item["id"],
            interests=item.get("interests", []),
            countries=item.get("countries", []),
            study_level=item.get("study_level", ""),
            skills=item.get("skills", []),
            relevance_threshold=float(item.get("relevance_threshold", 70)),
        )

    async def save(self, profile: UserProfile) -> UserProfile:
        self.table.put_item(
            Item={
                "id": profile.id,
                "interests": profile.interests,
                "countries": profile.countries,
                "study_level": profile.study_level,
                "skills": profile.skills,
                "relevance_threshold": profile.relevance_threshold,
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
    ) -> tuple[Sequence[Opportunity], int]:
        # Le MVP utilise Scan. Une table de production pourra ajouter des GSI
        # pour filtrer par statut et score sans scanner toute la table.
        response = self.table.scan(Limit=page_size)
        items = [self._deserialize(item) for item in response.get("Items", [])]
        if min_score is not None:
            items = [item for item in items if item.relevance_score >= min_score]
        if status is not None:
            items = [item for item in items if item.status.value == status]
        return items, len(items)

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
            "relevance_score": opportunity.relevance_score,
            "confidence_score": opportunity.confidence_score,
            "relevance_reasons": opportunity.relevance_reasons,
            "deadline": opportunity.deadline.isoformat() if opportunity.deadline else None,
            "eligibility": opportunity.eligibility,
            "verified_at": opportunity.verified_at.isoformat(),
            "status": opportunity.status.value,
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
            }
        )
        return run

    async def get(self, run_id: str) -> WatchRun | None:
        response = self.table.get_item(Key={"id": run_id})
        item = response.get("Item")
        if not item:
            return None
        from recal.domain.entities import RunStatus

        return WatchRun(
            id=UUID(item["id"]),
            status=RunStatus(item["status"]),
            created_at=datetime.fromisoformat(item["created_at"]),
            completed_at=(
                datetime.fromisoformat(item["completed_at"]) if item.get("completed_at") else None
            ),
            opportunities_found=int(item.get("opportunities_found", 0)),
            error_message=item.get("error_message"),
        )
