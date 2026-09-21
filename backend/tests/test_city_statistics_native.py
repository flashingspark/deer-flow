import asyncio

import httpx
from fastapi import FastAPI

import city_statistics_tools as tools
from app.gateway.auth_middleware import AuthMiddleware
from app.gateway.csrf_middleware import CSRFMiddleware
from app.gateway.routers import city_statistics
from city_statistics_store import database


def test_native_tools_http_crud(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "api.db")
    app = FastAPI()
    app.include_router(city_statistics.router)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(AuthMiddleware)
    transport = httpx.ASGITransport(app=app)
    monkeypatch.setattr(tools, "_client", lambda: httpx.AsyncClient(transport=transport, base_url="http://localhost"))

    async def scenario():
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
            assert (await client.get("/api/city-statistics")).status_code == 401
        assert len((await tools.city_statistics_schema.ainvoke({}))["indicators"]) == 30
        row = dict(
            city_name="合成测试市",
            year=2024,
            indicator_code="gdp_total",
            indicator_name="地区生产总值",
            dimension="经济发展",
            value=1,
            unit="亿元",
            scope="全市；现价",
            time_point="全年",
            status="verified",
            source_name="合成测试",
            source_url="https://tjj.beijing.gov.cn/test-only",
            source_quote="合成数据",
        )
        for _ in range(2):
            assert (await tools.save_city_statistics.ainvoke({"records": [row]}))["written_count"] == 1
        found = await tools.query_city_statistics.ainvoke({"city_name": "合成测试市", "year": 2024})
        assert found["count"] == 1
        rid = found["records"][0]["id"]
        assert (await tools.update_city_statistic.ainvoke({"record_id": rid, "changes": {"value": 2}}))["value"] == 2
        assert (await tools._request("GET", f"/{rid}"))["value"] == 2
        for changes in ({}, {"title": "错误"}, {"city_name": None}, {"value": None}):
            assert (await tools.update_city_statistic.ainvoke({"record_id": rid, "changes": changes}))["status_code"] == 422
        bad = await tools.save_city_statistics.ainvoke({"records": [row | {"city_name": "另一个市"}, row | {"source_quote": ""}]})
        assert bad["status_code"] == 422
        assert (await tools.query_city_statistics.ainvoke({}))["count"] == 1
        assert (await tools.delete_city_statistic.ainvoke({"record_id": rid}))["success"]
        assert (await tools._request("GET", f"/{rid}"))["status_code"] == 404
        assert (await tools.delete_city_statistic.ainvoke({"record_id": rid}))["status_code"] == 404

    asyncio.run(scenario())
