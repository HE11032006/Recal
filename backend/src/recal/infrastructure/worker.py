from __future__ import annotations

from typing import Any

from recal.domain.entities import RunTrigger
from recal.infrastructure.dependencies import build_container


async def run_watch_cycle() -> dict[str, Any]:
    """Exécuter un cycle de veille et retourner un résultat sérialisable."""
    container = build_container()
    run = await container.start_watch_run.execute(trigger=RunTrigger.SCHEDULED)
    return {
        "run_id": str(run.id),
        "status": run.status.value,
        "opportunities_found": run.opportunities_found,
        "error_message": run.error_message,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Point d’entrée Lambda prévu pour EventBridge Scheduler.

    L’adaptateur synchrone sera exécuté avec asyncio.run dans le runtime Lambda.
    """
    import asyncio

    return asyncio.run(run_watch_cycle())
