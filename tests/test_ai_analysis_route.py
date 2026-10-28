"""HTTP contract tests with dependency/method mocks, no running MySQL server.

Run with:
  uv run --with pytest --with pytest-asyncio pytest tests/test_ai_analysis_route.py -q
"""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-for-unit-tests")

from app.core import dependencies
from app.main import app
from app.models.enums import Role
from app.services import ai_analysis_list_service


URL = "/api/v1/medical-records/5/analyses"


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_missing_auth_returns_401(client):
    assert client.get(URL).status_code == 401


def test_pending_user_returns_403(client, monkeypatch):
    monkeypatch.setattr(dependencies, "decode_token", lambda *a, **kw: 7)
    monkeypatch.setattr(
        dependencies.user_repository, "get_by_id",
        AsyncMock(return_value=SimpleNamespace(role=Role.PENDING, is_active=True)),
    )
    response = client.get(URL, headers={"Authorization": "Bearer dummy"})
    assert response.status_code == 403


def test_authorized_staff_gets_empty_array(client, monkeypatch):
    app.dependency_overrides[dependencies.get_current_staff] = (
        lambda: SimpleNamespace(role=Role.STAFF)
    )
    read = AsyncMock(return_value=[])
    monkeypatch.setattr(ai_analysis_list_service, "list_analyses", read)
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == []
    read.assert_awaited_once()


def test_not_found_returns_404(client, monkeypatch):
    app.dependency_overrides[dependencies.get_current_staff] = (
        lambda: SimpleNamespace(role=Role.STAFF)
    )
    monkeypatch.setattr(
        ai_analysis_list_service,
        "list_analyses",
        AsyncMock(side_effect=HTTPException(status_code=404, detail="missing")),
    )
    assert client.get(URL).status_code == 404


@pytest.mark.parametrize("record_id", ["0", "not-an-id"])
def test_invalid_record_id_returns_422(client, record_id):
    app.dependency_overrides[dependencies.get_current_staff] = (
        lambda: SimpleNamespace(role=Role.STAFF)
    )
    assert client.get(f"/api/v1/medical-records/{record_id}/analyses").status_code == 422
