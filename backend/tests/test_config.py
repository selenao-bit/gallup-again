import os
import traceback

import pytest
from pydantic import SecretStr, ValidationError

from app.config import ConfigurationError, Settings
from app.main import create_app


@pytest.mark.parametrize("environment", [{}, {"DATABASE_URL": ""}])
def test_missing_configuration(environment):
    with pytest.raises(ConfigurationError, match="DATABASE_URL is required"):
        Settings.from_environment(environment)


@pytest.mark.parametrize("value", [
    "credential-sentinel",
    "sqlite:///credential-sentinel",
    "postgresql://user:credential-sentinel@host:bad/db",
    "postgresql://user:credential-sentinel@host:70000/db",
    "postgresql://user:credential-sentinel@host/",
    "postgresql://user:credential-sentinel@/db",
    "postgresql://host/db",
    "postgresql://user:credential-sentinel@host,other/db",
    "postgresql://user:credential-sentinel@host/db?options=unsafe",
    "postgresql://user:credential-sentinel@host/db?connect_timeout=0",
    "postgresql://user:credential-sentinel@host/db?sslmode=invalid",
    "postgresql://user:credential-sentinel@host/db?sslmode=require&sslmode=disable",
])
def test_invalid_configuration_is_sanitized(value):
    with pytest.raises(ConfigurationError, match="DATABASE_URL is invalid") as error:
        Settings.from_environment({"DATABASE_URL": value})
    rendered = "".join(traceback.format_exception(error.value))
    assert "credential-sentinel" not in rendered
    assert value not in rendered


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_valid_configuration_remains_secret(scheme):
    settings = Settings.from_environment({
        "DATABASE_URL": f"{scheme}://user:credential-sentinel@host/db?sslmode=require"
    })
    assert "credential-sentinel" not in repr(settings)
    assert "credential-sentinel" not in settings.model_dump_json()


def test_direct_validation_error_hides_input():
    with pytest.raises(ValidationError) as error:
        Settings(database_url=SecretStr("credential-sentinel"))
    assert "credential-sentinel" not in str(error.value)


def test_missing_configuration_prevents_startup(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ConfigurationError, match="DATABASE_URL is required"):
        create_app()


def test_root_dotenv_is_loaded_regardless_of_working_directory(root_env_path, tmp_path, monkeypatch):
    url = "postgresql://file_user:credential-sentinel@host/db"
    root_env_path.write_text(f"DATABASE_URL='{url}'\n", encoding="utf-8")
    other_directory = tmp_path / "different-working-directory"
    other_directory.mkdir()
    (other_directory / ".env").write_text("DATABASE_URL=invalid-cwd-value\n", encoding="utf-8")
    monkeypatch.chdir(other_directory)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings.from_environment().database_url.get_secret_value() == url
    assert "DATABASE_URL" not in os.environ


def test_process_environment_takes_precedence(root_env_path, monkeypatch):
    root_env_path.write_text("DATABASE_URL=invalid-file-value\n", encoding="utf-8")
    url = "postgresql://process_user:credential-sentinel@host/db"
    monkeypatch.setenv("DATABASE_URL", url)
    assert Settings.from_environment().database_url.get_secret_value() == url


@pytest.mark.parametrize("value", ["", "invalid-environment-value"])
def test_explicit_invalid_environment_never_falls_back_to_file(root_env_path, value):
    root_env_path.write_text(
        "DATABASE_URL=postgresql://file_user:credential-sentinel@host/db\n", encoding="utf-8"
    )
    with pytest.raises(ConfigurationError):
        Settings.from_environment({"DATABASE_URL": value})


def test_dotenv_values_are_literal_and_not_interpolated(root_env_path, monkeypatch):
    url = "postgresql://user:literal-${PASSWORD_PART}@host/db"
    root_env_path.write_text(f"DATABASE_URL='{url}'\n", encoding="utf-8")
    monkeypatch.setenv("PASSWORD_PART", "must-not-be-substituted")
    assert Settings.from_environment({}).database_url.get_secret_value() == url


def test_invalid_dotenv_value_is_sanitized(root_env_path, caplog):
    root_env_path.write_text("DATABASE_URL=credential-sentinel\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="DATABASE_URL is invalid") as error:
        Settings.from_environment({})
    assert "credential-sentinel" not in "".join(traceback.format_exception(error.value)) + caplog.text


def test_dotenv_read_error_is_sanitized(monkeypatch):
    def fail_read(*args, **kwargs):
        raise PermissionError("credential-sentinel")

    monkeypatch.setattr("app.config.dotenv_values", fail_read)
    with pytest.raises(ConfigurationError, match="Unable to read the project root .env") as error:
        Settings.from_environment({})
    assert "credential-sentinel" not in "".join(traceback.format_exception(error.value))


def test_startup_accepts_root_dotenv(root_env_path, monkeypatch):
    from fastapi.testclient import TestClient

    root_env_path.write_text(
        "DATABASE_URL=postgresql://user:credential-sentinel@127.0.0.1:1/db\n", encoding="utf-8"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Liveness must not require a real database, even when configured through dotenv.
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
