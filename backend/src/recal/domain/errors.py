"""Erreurs métier du domaine Recal.

Elles ne portent aucune dépendance technique afin de rester utilisables par
l’API, le worker planifié et les tests.
"""

from __future__ import annotations


class WatchSkippedError(Exception):
    """Un cycle planifié a été volontairement ignoré (garde-fou de veille)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Cycle de veille ignoré : {reason}")


class DailyQuotaExceededError(WatchSkippedError):
    """Le quota quotidien de cycles a été atteint."""
