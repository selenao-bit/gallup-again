"""Explicit opt-in from the repository root:

.venv/bin/python -m pytest -c backend/pytest.ini backend/checks/test_live_database.py -q
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.integration
def test_live_database_connectivity():
    # No fixtures, corporate table reads, schema setup, or data writes.
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/health/db")
        assert response.status_code == 200, "Read-only database connectivity failed"
        assert response.json() == {"status": "ok"}
