"""Example CRUD API that can be called by a DeerFlow agent skill."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.gateway.authz import require_permission
from app.gateway.internal_auth import get_trusted_internal_owner_user_id
from deerflow.config.paths import make_safe_user_id
from deerflow.persistence.agent_api_notes.model import AgentApiNoteRow
from deerflow.persistence.engine import get_session_factory
from deerflow.runtime.user_context import get_effective_user_id

router = APIRouter(prefix="/api/agent-notes", tags=["agent-api-demo"])


class AgentNoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)


class AgentNoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=10000)


class AgentNoteResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class AgentNoteListResponse(BaseModel):
    items: list[AgentNoteResponse]
    total: int
    limit: int
    offset: int


def _owner_id(request: Request) -> str:
    """Resolve the normal user or trusted internal channel owner."""
    raw_owner = get_trusted_internal_owner_user_id(request)
    if raw_owner:
        return make_safe_user_id(raw_owner)
    user = getattr(request.state, "user", None)
    if user is not None:
        return str(user.id)
    return get_effective_user_id()


def _session_factory():
    session_factory = get_session_factory()
    if session_factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent notes require database.backend=sqlite or postgres",
        )
    return session_factory


def _response(row: AgentApiNoteRow) -> AgentNoteResponse:
    return AgentNoteResponse(
        id=row.id,
        title=row.title,
        content=row.content,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=AgentNoteListResponse, summary="Query agent notes")
@require_permission("threads", "read")
async def list_agent_notes(
    request: Request,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AgentNoteListResponse:
    """List notes owned by the current user, optionally searching title/content."""
    owner_id = _owner_id(request)
    session_factory = _session_factory()
    async with session_factory() as session:
        stmt = select(AgentApiNoteRow).where(AgentApiNoteRow.user_id == owner_id)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where((AgentApiNoteRow.title.ilike(pattern)) | (AgentApiNoteRow.content.ilike(pattern)))
        result = await session.execute(stmt.order_by(AgentApiNoteRow.updated_at.desc(), AgentApiNoteRow.id))
        rows = list(result.scalars())
        return AgentNoteListResponse(
            items=[_response(row) for row in rows[offset : offset + limit]],
            total=len(rows),
            limit=limit,
            offset=offset,
        )


@router.get("/{note_id}", response_model=AgentNoteResponse, summary="Get one agent note")
@require_permission("threads", "read")
async def get_agent_note(note_id: str, request: Request) -> AgentNoteResponse:
    owner_id = _owner_id(request)
    session_factory = _session_factory()
    async with session_factory() as session:
        row = await session.get(AgentApiNoteRow, note_id)
        if row is None or row.user_id != owner_id:
            raise HTTPException(status_code=404, detail="Agent note not found")
        return _response(row)


@router.post("", response_model=AgentNoteResponse, status_code=201, summary="Create an agent note")
@require_permission("threads", "write")
async def create_agent_note(request: Request, body: AgentNoteCreate) -> AgentNoteResponse:
    owner_id = _owner_id(request)
    session_factory = _session_factory()
    now = datetime.now(UTC)
    row = AgentApiNoteRow(
        id=f"note-{uuid.uuid4().hex}",
        user_id=owner_id,
        title=body.title,
        content=body.content,
        created_at=now,
        updated_at=now,
    )
    async with session_factory() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return _response(row)


@router.patch("/{note_id}", response_model=AgentNoteResponse, summary="Modify an agent note")
@require_permission("threads", "write")
async def update_agent_note(note_id: str, request: Request, body: AgentNoteUpdate) -> AgentNoteResponse:
    updates: dict[str, Any] = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="At least one of title or content is required")
    owner_id = _owner_id(request)
    session_factory = _session_factory()
    async with session_factory() as session:
        row = await session.get(AgentApiNoteRow, note_id)
        if row is None or row.user_id != owner_id:
            raise HTTPException(status_code=404, detail="Agent note not found")
        for field_name, value in updates.items():
            setattr(row, field_name, value)
        row.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(row)
        return _response(row)


@router.delete("/{note_id}", status_code=204, summary="Delete an agent note")
@require_permission("threads", "delete")
async def delete_agent_note(note_id: str, request: Request) -> None:
    owner_id = _owner_id(request)
    session_factory = _session_factory()
    async with session_factory() as session:
        row = await session.get(AgentApiNoteRow, note_id)
        if row is None or row.user_id != owner_id:
            raise HTTPException(status_code=404, detail="Agent note not found")
        await session.delete(row)
        await session.commit()
