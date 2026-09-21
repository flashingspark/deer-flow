"""Native agent tools -> authenticated FastAPI HTTP -> existing SQLite store."""

import secrets
from typing import Any

import httpx
from langchain_core.tools import tool

from app.gateway.config import get_gateway_config
from app.gateway.internal_auth import create_internal_auth_headers
from deerflow.runtime.user_context import get_effective_user_id


def _client():
    # Fixed loopback destination: never send the internal credential to caller URLs.
    return httpx.AsyncClient(base_url=f"http://127.0.0.1:{get_gateway_config().port}", timeout=40, trust_env=False)


async def _request(method: str, path: str = "", *, payload: dict | None = None, params: dict | None = None) -> dict:
    csrf = secrets.token_urlsafe(32)
    headers = create_internal_auth_headers(owner_user_id=get_effective_user_id())
    headers.update({"X-CSRF-Token": csrf, "Cookie": f"csrf_token={csrf}"})
    try:
        async with _client() as client:
            response = await client.request(method, f"/api/city-statistics{path}", json=payload, params=params, headers=headers)
        data = response.json()
        if response.is_error:
            return {"success": False, "status_code": response.status_code, "error": data.get("detail", data)}
        return data
    except (httpx.HTTPError, ValueError) as exc:
        return {"success": False, "error": f"城市统计HTTP接口调用失败：{exc}"}


@tool
async def city_statistics_schema() -> dict:
    """通过FastAPI获取城市统计JSON字段约束和指标字典。"""
    return await _request("GET", "/schema")


@tool
async def save_city_statistics(records: list[dict[str, Any]]) -> dict:
    """调用FastAPI校验并批量入库；同键更新。来源必须核实，返回success和written_count。"""
    return await _request("POST", payload={"records": records})


@tool
async def query_city_statistics(city_name: str | None = None, year: int | None = None, limit: int = 100) -> dict:
    """调用FastAPI按城市、年份查询SQLite记录及id，用于核对入库结果。"""
    params = {k: v for k, v in {"city_name": city_name, "year": year, "limit": limit}.items() if v is not None}
    return await _request("GET", params=params)


@tool
async def update_city_statistic(record_id: int, changes: dict[str, Any]) -> dict:
    """调用FastAPI按id修改指定统计字段，合并后重新校验。先查询确认目标记录，仅在用户要求修改时调用。"""
    return await _request("PATCH", f"/{record_id}", payload=changes)


@tool
async def delete_city_statistic(record_id: int) -> dict:
    """调用FastAPI按id删除记录。先查询确认目标，仅在用户明确要求删除时调用。"""
    return await _request("DELETE", f"/{record_id}")
