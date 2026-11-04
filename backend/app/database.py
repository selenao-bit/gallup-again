"""A fixed read-only connectivity probe, with no corporate-data queries."""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from .config import Settings


CONNECT_TIMEOUT_SECONDS = 3
STATEMENT_TIMEOUT_MS = 2000


class DatabaseUnavailable(Exception):
    """Sanitized failure of the database connectivity probe."""


class Database:
    def __init__(self, settings: Settings) -> None:
        url = make_url(settings.database_url.get_secret_value()).set(
            drivername="postgresql+psycopg"
        )
        self._engine = create_engine(
            url,
            poolclass=NullPool,
            echo=False,
            hide_parameters=True,
            connect_args={
                "connect_timeout": CONNECT_TIMEOUT_SECONDS,
                "options": (
                    "-c default_transaction_read_only=on "
                    f"-c statement_timeout={STATEMENT_TIMEOUT_MS} "
                    f"-c lock_timeout={STATEMENT_TIMEOUT_MS}"
                ),
            },
        )

    def check(self) -> None:
        try:
            # Closing rolls back the read transaction and NullPool closes the socket.
            with self._engine.connect() as connection:
                if connection.execute(text("SELECT 1")).scalar_one() != 1:
                    raise DatabaseUnavailable("Database unavailable")
        except SQLAlchemyError:
            # Driver exceptions may contain connection details; never return or log them.
            raise DatabaseUnavailable("Database unavailable") from None

    def close(self) -> None:
        self._engine.dispose()

    @contextmanager
    def read(self):
        """Bounded read-only transaction; sanitize all driver failures."""
        try:
            with self._engine.connect() as connection:
                yield connection
        except SQLAlchemyError:
            raise DatabaseUnavailable("Database unavailable") from None
