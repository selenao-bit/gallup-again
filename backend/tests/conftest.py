"""Keep the default suite independent of the developer's private root configuration."""

import pytest


@pytest.fixture(autouse=True)
def root_env_path(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.setattr("app.config.ROOT_ENV_PATH", path)
    return path
