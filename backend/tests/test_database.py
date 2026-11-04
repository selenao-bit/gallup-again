from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from app.config import Settings
from app.database import Database, DatabaseUnavailable


@pytest.mark.parametrize("failure_stage", [None, "connect", "query", "result"])
def test_read_only_probe_timeouts_cleanup_and_sanitized_failure(monkeypatch, caplog, failure_stage):
    engine = MagicMock()
    factory = MagicMock(return_value=engine)
    monkeypatch.setattr("app.database.create_engine", factory)
    error = OperationalError("SELECT 1", None, Exception("credential-sentinel"))
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalar_one.return_value = 1
    if failure_stage == "connect":
        engine.connect.side_effect = error
    elif failure_stage == "query":
        connection.execute.side_effect = error
    elif failure_stage == "result":
        connection.execute.return_value.scalar_one.return_value = 0

    database = Database(Settings(database_url=SecretStr(
        "postgresql://user:credential-sentinel@host/db"
    )))
    _, options = factory.call_args
    assert options["poolclass"] is NullPool
    assert options["echo"] is False
    assert options["hide_parameters"] is True
    assert options["connect_args"] == {
        "connect_timeout": 3,
        "options": "-c default_transaction_read_only=on -c statement_timeout=2000 -c lock_timeout=2000",
    }
    assert factory.call_args.args[0].drivername == "postgresql+psycopg"

    if failure_stage:
        with pytest.raises(DatabaseUnavailable, match="^Database unavailable$") as failure:
            database.check()
        assert "credential-sentinel" not in str(failure.value) + caplog.text
        if failure_stage in {"connect", "query"}:
            assert failure.value.__suppress_context__
    else:
        database.check()

    if failure_stage != "connect":
        statement = connection.execute.call_args.args[0]
        assert str(statement) == "SELECT 1"
        connection.execute.assert_called_once()
        engine.connect.return_value.__exit__.assert_called_once()
    connection.commit.assert_not_called()
    database.close()
    engine.dispose.assert_called_once_with()
