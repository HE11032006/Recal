from __future__ import annotations

import logging
import os
from typing import Any

from sentry_sdk.types import Event, Hint


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = "-"
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s run_id=%(run_id)s %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestContextFilter())


_SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "token",
    "api_key",
    "secret",
    "tavily_api_key",
}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[Filtered]" if key.lower() in _SENSITIVE_KEYS else _scrub(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def before_send(event: Event, hint: Hint) -> Event:
    """Retirer les secrets connus avant l’envoi d’un événement Sentry."""
    return _scrub(event)


def init_sentry() -> None:
    """Initialiser Sentry uniquement si DSN est configuré.

    Sentry collecte les exceptions et performances techniques. Les données
    métier sensibles ne sont jamais placées dans les tags ou le contexte.
    """
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FastApiIntegration(), StarletteIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
            before_send=before_send,
            environment=os.getenv("APP_ENV", "development"),
            release=os.getenv("APP_VERSION", "0.1.0"),
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN est défini mais sentry-sdk n’est pas installé"
        )


def capture_exception(exc: BaseException, *, operation: str, run_id: str | None = None) -> None:
    """Envoyer une exception sans inclure le profil ou le contenu des annonces."""
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("operation", operation)
            if run_id:
                scope.set_tag("run_id", run_id)
            sentry_sdk.capture_exception(exc)
    except ImportError:
        logging.getLogger(__name__).exception("Erreur dans %s", operation, exc_info=exc)
