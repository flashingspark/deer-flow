from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.gateway.routers import agent_api_notes
from deerflow.persistence.agent_api_notes.model import AgentApiNoteRow
from deerflow.persistence.base import Base


@pytest.fixture()
def notes_client(monkeypatch) -> Iterator[TestClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def setup() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, tables=[AgentApiNoteRow.__table__])

    async def cleanup() -> None:
        await engine.dispose()

    asyncio.run(setup())
    monkeypatch.setattr(agent_api_notes, "get_session_factory", lambda: session_factory)
    app = FastAPI()
    app.include_router(agent_api_notes.router)
    with TestClient(app) as client:
        yield client
    asyncio.run(cleanup())


def test_agent_notes_crud(notes_client: TestClient) -> None:
    created = notes_client.post("/api/agent-notes", json={"title": "初始标题", "content": "初始内容"})
    assert created.status_code == 201
    note_id = created.json()["id"]

    listed = notes_client.get("/api/agent-notes", params={"q": "初始"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = notes_client.patch(f"/api/agent-notes/{note_id}", json={"content": "修改后的内容"})
    assert updated.status_code == 200
    assert updated.json()["content"] == "修改后的内容"

    deleted = notes_client.delete(f"/api/agent-notes/{note_id}")
    assert deleted.status_code == 204
    assert notes_client.get(f"/api/agent-notes/{note_id}").status_code == 404
