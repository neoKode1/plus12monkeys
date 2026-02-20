"""Agent CRUD endpoints — thin proxy to NANDA Index with validation."""

from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.models.agent import (
    AgentCreateRequest,
    AgentResponse,
    AgentStatusUpdate,
    RegistrationResult,
)
from app.services.nanda_client import nanda

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=RegistrationResult)
async def create_agent(body: AgentCreateRequest):
    """Register a new agent in NANDA Index."""
    try:
        result = await nanda.register_agent(
            agent_id=body.agent_id,
            agent_url=body.agent_url,
            api_url=body.api_url,
        )
        # After registration, push extra metadata (capabilities, tags) via status update
        meta: dict = {}
        if body.capabilities:
            meta["capabilities"] = body.capabilities
        if body.tags:
            meta["tags"] = body.tags
        if meta:
            await nanda.update_agent_status(body.agent_id, meta)

        return RegistrationResult(
            status="success",
            message=f"Agent {body.agent_id} registered",
        )
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NANDA error: {exc}") from exc


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    q: Optional[str] = Query(None, description="Substring search on agent_id"),
    capabilities: Optional[str] = Query(None, description="Comma-separated capabilities filter"),
    tags: Optional[str] = Query(None, description="Comma-separated tags filter"),
):
    """Search / list agents (delegates to NANDA /search)."""
    try:
        caps = [c.strip() for c in capabilities.split(",")] if capabilities else None
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        results = await nanda.search_agents(q=q, capabilities=caps, tags=tag_list)
        return [AgentResponse(**a) for a in results]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NANDA error: {exc}") from exc


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a single agent's details."""
    try:
        data = await nanda.get_agent(agent_id)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return AgentResponse(**data)
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NANDA error: {exc}") from exc


@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_status(agent_id: str, body: AgentStatusUpdate):
    """Update an agent's runtime status (alive, capabilities, tags)."""
    try:
        payload = body.model_dump(exclude_none=True)
        result = await nanda.update_agent_status(agent_id, payload)
        agent_data = result.get("agent", result)
        return AgentResponse(**agent_data)
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NANDA error: {exc}") from exc


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Remove an agent from the registry."""
    try:
        result = await nanda.delete_agent(agent_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"NANDA error: {exc}") from exc

