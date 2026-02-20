"""Async HTTP client for the NANDA Index registry API."""

from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class NANDAClient:
    """Thin async wrapper around the NANDA Index REST API (port 6900)."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.nanda_url).rstrip("/")

    # ---- health / stats ----

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()

    # ---- agent CRUD ----

    async def register_agent(
        self,
        agent_id: str,
        agent_url: str,
        api_url: str,
    ) -> Dict[str, Any]:
        """POST /register – create or update an agent entry."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/register",
                json={
                    "agent_id": agent_id,
                    "agent_url": agent_url,
                    "api_url": api_url,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """GET /agents/<agent_id>"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/agents/{agent_id}")
            resp.raise_for_status()
            return resp.json()

    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """DELETE /agents/<agent_id>"""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self.base_url}/agents/{agent_id}")
            resp.raise_for_status()
            return resp.json()

    async def update_agent_status(
        self, agent_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PUT /agents/<agent_id>/status"""
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.base_url}/agents/{agent_id}/status",
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    async def list_agents(self) -> Dict[str, str]:
        """GET /list – returns {agent_id: agent_url, …}"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/list")
            resp.raise_for_status()
            return resp.json()

    async def search_agents(
        self,
        q: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """GET /search with optional query params."""
        params: Dict[str, str] = {}
        if q:
            params["q"] = q
        if capabilities:
            params["capabilities"] = ",".join(capabilities)
        if tags:
            params["tags"] = ",".join(tags)

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/search", params=params)
            resp.raise_for_status()
            return resp.json()

    # ---- builds archive ----

    async def log_build(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /builds — store a generated package in the archive."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/builds",
                json=build_data,
            )
            resp.raise_for_status()
            return resp.json()

    async def list_builds(
        self,
        q: Optional[str] = None,
        framework: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """GET /builds — list stored builds with optional search/filter."""
        params: Dict[str, Any] = {"limit": limit, "skip": skip}
        if q:
            params["q"] = q
        if framework:
            params["framework"] = framework
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/builds", params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_build(self, build_id: str) -> Dict[str, Any]:
        """GET /builds/<build_id> — get a single build with full file contents."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/builds/{build_id}")
            resp.raise_for_status()
            return resp.json()


# Module-level singleton for convenience
nanda = NANDAClient()

