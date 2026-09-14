"""Tests du middleware clé API (clé partagée anti-abus, endpoint public)."""

from __future__ import annotations

import importlib
import os

from fastapi.testclient import TestClient


def load_app(api_key: str = "") -> TestClient:
    os.environ["APP_ENV"] = "test"
    os.environ["PERSISTENCE_PROVIDER"] = "sqlite"
    os.environ["SEARCH_PROVIDER"] = "none"
    os.environ["ANALYZER_PROVIDER"] = "fake"
    if api_key:
        os.environ["API_KEY"] = api_key
    else:
        os.environ.pop("API_KEY", None)
    import recal.main as main_module
    from recal.infrastructure.config import get_settings

    get_settings.cache_clear()
    reloaded = importlib.reload(main_module)
    return TestClient(reloaded.app, raise_server_exceptions=False)


def test_api_open_without_key_when_unconfigured() -> None:
    client = load_app()

    assert client.get("/api/v1/opportunities").status_code == 200
    assert client.get("/api/v1/health").status_code == 200


def test_api_rejects_missing_key_when_configured() -> None:
    client = load_app(api_key="secret-jury")

    response = client.get("/api/v1/opportunities")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_api_rejects_wrong_key() -> None:
    client = load_app(api_key="secret-jury")

    response = client.get("/api/v1/opportunities", headers={"x-api-key": "mauvaise"})

    assert response.status_code == 401


def test_api_accepts_correct_key() -> None:
    client = load_app(api_key="secret-jury")

    response = client.get("/api/v1/opportunities", headers={"x-api-key": "secret-jury"})

    assert response.status_code == 200


def test_health_stays_open_with_key_configured() -> None:
    client = load_app(api_key="secret-jury")

    assert client.get("/api/v1/health").status_code == 200


def test_preflight_without_key_is_not_rejected() -> None:
    client = load_app(api_key="secret-jury")

    response = client.options(
        "/api/v1/opportunities",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code != 401
