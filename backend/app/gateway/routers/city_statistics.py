"""City statistics CRUD, following the existing agent-notes router pattern."""

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from app.gateway.authz import require_permission
from city_statistics_store import database, models

router = APIRouter(prefix="/api/city-statistics", tags=["city-statistics"])
CityStatisticBatch = models.CityStatisticBatch


async def _call(function, *args):
    try:
        return await run_in_threadpool(function, *args)
    except KeyError:
        raise HTTPException(404, "City statistic not found") from None
    except sqlite3.IntegrityError:
        raise HTTPException(409, "City statistic conflicts with an existing record") from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/schema")
@require_permission("threads", "read")
async def schema(request: Request):
    return {"schema": CityStatisticBatch.model_json_schema(), "indicators": [{"indicator_code": code, "dimension": dim, "indicator_name": name} for code, (dim, name) in models.DIMENSIONS.items()]}


@router.get("")
@require_permission("threads", "read")
async def query(request: Request, city_name: str | None = None, year: int | None = None, limit: int = Query(100, ge=1, le=500)):
    return await _call(database.query_city_statistics, city_name, year, limit)


@router.post("")
@require_permission("threads", "write")
async def save(request: Request, body: CityStatisticBatch):
    return await _call(database.save_city_statistics, [row.model_dump() for row in body.records])


@router.get("/{record_id}")
@require_permission("threads", "read")
async def get(record_id: int, request: Request):
    return await _call(database.get_city_statistic, record_id)


@router.patch("/{record_id}")
@require_permission("threads", "write")
async def update(record_id: int, request: Request, changes: dict[str, Any] = Body(...)):
    return await _call(database.update_city_statistic, record_id, changes)


@router.delete("/{record_id}")
@require_permission("threads", "delete")
async def delete(record_id: int, request: Request):
    return await _call(database.delete_city_statistic, record_id)
