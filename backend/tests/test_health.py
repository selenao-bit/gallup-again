from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.database import Database, DatabaseUnavailable
from app.main import create_app
from app.routes import get_database


@pytest.fixture
def settings():
    return Settings(database_url=SecretStr(
        "postgresql://test_user:credential-sentinel@127.0.0.1:1/test_database"
    ))


def test_startup_health_and_shutdown_do_not_connect(settings, monkeypatch):
    database = Mock(spec=Database)
    monkeypatch.setattr("app.main.Database", lambda settings: database)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        database.check.assert_not_called()
        database.close.assert_not_called()
    database.close.assert_called_once_with()


@pytest.mark.parametrize("available", [True, False])
def test_database_route_with_controlled_dependency(settings, available, caplog):
    app = create_app(settings)
    database = Mock(spec=Database)
    if not available:
        database.check.side_effect = DatabaseUnavailable(
            "postgresql://test_user:credential-sentinel@private-host/test_database"
        )
    app.dependency_overrides[get_database] = lambda: database
    with TestClient(app) as client:
        response = client.get("/health/db")
        assert response.status_code == (200 if available else 503)
        assert response.json() == (
            {"status": "ok"} if available else {"detail": "Database unavailable"}
        )
        # Database failure does not change application liveness.
        assert client.get("/health").status_code == 200
    database.check.assert_called_once_with()
    for secret in ("credential-sentinel", "test_user", "private-host", "postgresql://"):
        assert secret not in response.text + caplog.text


def test_startup_uses_environment_configuration(settings, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", settings.database_url.get_secret_value())
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
