"""Backfill TTL : attribue `ttl` aux opportunités DynamoDB existantes sans ce champ.

Les items sans `ttl` ne seront jamais purgés automatiquement. Ce script
applique les mêmes règles que les nouvelles écritures :
- avec deadline : deadline + 30 jours
- sans deadline : verified_at + 90 jours

Usage (depuis backend/) :
    python scripts/backfill_ttl.py --dry-run   # aperçu, zéro écriture
    python scripts/backfill_ttl.py --apply      # écrit les champs ttl

Warning: les items dont le TTL calculé est déjà dépassé seront supprimés
par DynamoDB sous ~48 h après l'application.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import boto3

from recal.adapters.dynamodb_repositories import (
    DynamoDBOpportunityRepository,
    _ttl_timestamp,
)
from recal.infrastructure.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="aperçu sans écriture")
    parser.add_argument("--apply", action="store_true", help="écrit les champs ttl")
    args = parser.parse_args()
    if not (args.dry_run ^ args.apply):
        parser.error("précise --dry-run OU --apply")

    settings = get_settings()
    table = boto3.resource("dynamodb", region_name=settings.aws_region).Table(
        settings.dynamodb_table_opportunities
    )

    scanned = 0
    missing = 0
    updated = 0
    already_past = 0
    exclusive_start_key = None
    while True:
        scan_kwargs: dict = {}
        if exclusive_start_key:
            scan_kwargs["ExclusiveStartKey"] = exclusive_start_key
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            scanned += 1
            if "ttl" in item:
                continue
            missing += 1
            opportunity = DynamoDBOpportunityRepository._deserialize(item)
            ttl = _ttl_timestamp(opportunity)
            ttl_date = datetime.fromtimestamp(ttl, tz=UTC).date().isoformat()
            past = ttl < int(datetime.now(UTC).timestamp())
            if past:
                already_past += 1
            tag = "PURGE SOUS ~48H" if past else f"purge le {ttl_date}"
            title = str(item.get("title", "?"))[:60]
            print(
                f"[{'APPLY ' if args.apply else 'DRYRUN'}] {opportunity.id[:8]} | {title} | {tag}"
            )
            if args.apply:
                table.update_item(
                    Key={"id": opportunity.id},
                    UpdateExpression="SET #t = :t",
                    ExpressionAttributeNames={"#t": "ttl"},
                    ExpressionAttributeValues={":t": ttl},
                )
                updated += 1
        exclusive_start_key = response.get("LastEvaluatedKey")
        if not exclusive_start_key:
            break

    print(f"\nscannés={scanned} sans_ttl={missing} déjà_dépassés={already_past}", end="")
    print(f" mis_à_jour={updated}" if args.apply else " (aucune écriture)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
