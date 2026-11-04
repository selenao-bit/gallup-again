"""Root dotenv configuration with process-environment precedence and safe errors."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class ConfigurationError(ValueError):
    """A safe startup error that may be displayed to a developer."""


class Settings(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True, frozen=True)

    database_url: SecretStr
    demo_identity_enabled: bool = False
    demo_diagnostics: bool = False
    assistant_mode: Literal["simulated", "openai", "azure"] = "simulated"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    azure_openai_key: SecretStr | None = None
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    azure_api_version: str = "2025-03-01-preview"
    azure_reasoning_effort: Literal["none","low","medium","high"] | None = None

    @field_validator("azure_endpoint")
    @classmethod
    def validate_azure_endpoint(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        try:
            url = urlsplit(value.strip())
            domains = ('.openai.azure.com', '.cognitiveservices.azure.com', '.services.ai.azure.com')
            if (url.scheme != 'https' or not url.hostname or not url.hostname.endswith(domains)
                    or url.username or url.password or url.port not in (None,443)
                    or url.path not in ('','/') or url.query or url.fragment):
                raise ValueError
        except ValueError:
            raise ValueError('Azure endpoint must be an HTTPS Azure resource root URL') from None
        return value.strip().rstrip('/') + '/'

    @property
    def assistant_available(self) -> bool:
        if self.assistant_mode == 'azure':
            return bool(self.azure_openai_key and self.azure_openai_key.get_secret_value().strip()
                        and self.azure_endpoint and self.azure_deployment and self.azure_deployment.strip())
        return bool(self.assistant_mode == 'openai' and self.openai_api_key
                    and self.openai_api_key.get_secret_value().strip())

    @property
    def assistant_model(self) -> str:
        return (self.azure_deployment or '').strip() if self.assistant_mode == 'azure' else self.openai_model


    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
                raise ValueError
            if not url.host or not url.username or not url.database:
                raise ValueError
            if any(character.isspace() for character in url.host) or "," in url.host:
                raise ValueError
            if url.port is not None and not 1 <= url.port <= 65535:
                raise ValueError
            # Do not permit URL options to override read-only mode or timeouts.
            if set(url.query) - {"sslmode"}:
                raise ValueError
            if "sslmode" in url.query and url.query["sslmode"] not in {
                "disable", "allow", "prefer", "require", "verify-ca", "verify-full"
            }:
                raise ValueError
        except (ArgumentError, ValueError, TypeError):
            raise ValueError("DATABASE_URL must be a valid single-host PostgreSQL URL") from None
        return value

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "Settings":
        environment = os.environ if environment is None else environment
        if "DATABASE_URL" in environment:
            # Even an explicitly empty value overrides the file and fails validation.
            value = environment["DATABASE_URL"]
        else:
            try:
                value = dotenv_values(ROOT_ENV_PATH, interpolate=False).get("DATABASE_URL")
            except (OSError, UnicodeError):
                raise ConfigurationError(
                    "Unable to read the project root .env; check file access and UTF-8 encoding."
                ) from None
        if not value:
            raise ConfigurationError("DATABASE_URL is required; configure it before startup.")
        try:
            file_values = dotenv_values(ROOT_ENV_PATH, interpolate=False)
            def setting(name: str, default=None):
                return environment.get(name, file_values.get(name, default))
            def alias(*names, default=None):
                for name in names:
                    if name in environment:
                        return environment[name]
                for name in names:
                    if name in file_values:
                        return file_values[name]
                return default
            endpoint = alias('AZURE_OPENAI_ENDPOINT')
            resource = alias('GW_AZURE_RESOURCE')
            if not endpoint and resource:
                import re
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', resource):
                    raise ValueError('Invalid Azure resource name')
                endpoint = f'https://{resource}.openai.azure.com/'
            return cls(
                database_url=SecretStr(value),
                demo_identity_enabled=setting("DEMO_IDENTITY_ENABLED", "false"),
                demo_diagnostics=setting("DEMO_DIAGNOSTICS", "false"),
                assistant_mode=setting("ASSISTANT_MODE", "simulated"),
                openai_api_key=setting("OPENAI_API_KEY"),
                openai_model=setting("OPENAI_MODEL", "gpt-4.1-mini"),
                azure_openai_key=alias('GW_AZURE_OPENAI_KEY','AZURE_OPENAI_API_KEY'),
                azure_endpoint=endpoint,
                azure_deployment=alias('GW_AZURE_MODEL','AZURE_OPENAI_DEPLOYMENT'),
                azure_api_version=alias('AZURE_OPENAI_API_VERSION',default='2025-03-01-preview'),
                azure_reasoning_effort=alias('AZURE_OPENAI_REASONING_EFFORT'),
            )
        except (ValidationError, ValueError):
            raise ConfigurationError(
                "DATABASE_URL is invalid or demo/assistant settings are invalid; use a "
                "single-host PostgreSQL URL and documented configuration values. "
                "Only the sslmode URL option is supported."
            ) from None
