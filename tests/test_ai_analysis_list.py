"""REQ-PRED-002 isolated service/repository tests; no real MySQL required.

Run after installing project dependencies:
  uv run --with pytest --with pytest-asyncio pytest tests/test_ai_analysis_list.py -q
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import mysql

from app.models.ai_analysis_results import AIAnalysisResult
from app.repositories import ai_analysis_list_repository
from app.services import ai_analysis_list_service


def analysis(**kwargs):
    row = dict(
        id=21,
        record_id=5,
        is_pneumonia=True,
        confidence=Decimal("97.68"),
        heatmap_url="/media/heatmaps/example.png",
        ai_model="resnet18-E1b",
        created_at=datetime(2026, 10, 28, 15, 20),
    )
    row.update(kwargs)
    return SimpleNamespace(**row)


@pytest.mark.asyncio
async def test_nonexistent_record_returns_404(monkeypatch):
    monkeypatch.setattr(
        ai_analysis_list_service.medical_record_repository,
        "get_by_id",
        AsyncMock(return_value=None),
    )
    get_list = AsyncMock()
    monkeypatch.setattr(
        ai_analysis_list_service.ai_analysis_list_repository,
        "list_by_record_id",
        get_list,
    )
    with pytest.raises(HTTPException) as exc:
        await ai_analysis_list_service.list_analyses(AsyncMock(), 999)
    assert exc.value.status_code == 404
    get_list.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_record_without_results_returns_empty_array(monkeypatch):
    monkeypatch.setattr(
        ai_analysis_list_service.medical_record_repository,
        "get_by_id",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        ai_analysis_list_service.ai_analysis_list_repository,
        "list_by_record_id",
        AsyncMock(return_value=[]),
    )
    assert await ai_analysis_list_service.list_analyses(AsyncMock(), 5) == []


@pytest.mark.asyncio
async def test_existing_record_returns_saved_values(monkeypatch):
    monkeypatch.setattr(
        ai_analysis_list_service.medical_record_repository,
        "get_by_id",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        ai_analysis_list_service.ai_analysis_list_repository,
        "list_by_record_id",
        AsyncMock(return_value=[analysis()]),
    )
    results = await ai_analysis_list_service.list_analyses(AsyncMock(), 5)
    assert len(results) == 1
    assert results[0].confidence == 97.68
    assert results[0].ai_model == "resnet18-E1b"
    assert results[0].heatmap_url == "/media/heatmaps/example.png"


@pytest.mark.asyncio
async def test_nullable_api_heatmap(monkeypatch):
    monkeypatch.setattr(
        ai_analysis_list_service.medical_record_repository,
        "get_by_id",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        ai_analysis_list_service.ai_analysis_list_repository,
        "list_by_record_id",
        AsyncMock(return_value=[analysis(heatmap_url=None)]),
    )
    results = await ai_analysis_list_service.list_analyses(AsyncMock(), 5)
    assert results[0].heatmap_url is None


@pytest.mark.asyncio
async def test_repository_filters_and_orders_newest_first():
    class Result:
        def scalars(self):
            return self
        def all(self):
            return [analysis(id=23), analysis(id=21)]

    db = SimpleNamespace(execute=AsyncMock(return_value=Result()))
    rows = await ai_analysis_list_repository.list_by_record_id(db, 5)
    assert [r.id for r in rows] == [23, 21]
    statement = db.execute.await_args.args[0]
    sql = str(statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "ai_analysis_results.record_id = 5" in sql
    assert "ai_analysis_results.created_at DESC" in sql
    assert "ai_analysis_results.id DESC" in sql


def test_schema_rejects_invalid_confidence():
    from pydantic import ValidationError
    from app.schemas.ai_analysis_list import AIAnalysisListItem
    with pytest.raises(ValidationError):
        AIAnalysisListItem.model_validate(analysis(confidence=Decimal("110.00")))
