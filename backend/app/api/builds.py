"""Builds API — browse and search the archive of generated MCP/SDK packages.

Reads/writes directly to MongoDB (motor) instead of proxying through NANDA.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("")
async def list_builds(
    q: Optional[str] = None,
    framework: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    """List archived builds with optional search and framework filter.

    Returns metadata only (no file contents) for performance.
    """
    db = get_db()
    mongo_filter: Dict[str, Any] = {}
    if q:
        mongo_filter["$or"] = [
            {"project_name": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
            {"framework": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    if framework:
        mongo_filter["framework"] = {"$regex": framework, "$options": "i"}

    cursor = (
        db.builds.find(mongo_filter, {"_id": 0, "files": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(min(limit, 200))
    )
    results = await cursor.to_list(length=min(limit, 200))
    total = await db.builds.count_documents(mongo_filter)
    return {"builds": results, "total": total, "limit": limit, "skip": skip}


@router.get("/{build_id}")
async def get_build(build_id: str):
    """Get a single archived build by ID, including full file contents."""
    db = get_db()
    doc = await db.builds.find_one({"build_id": build_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Build not found")
    return doc


@router.post("")
async def create_build(data: Dict[str, Any]):
    """Store a generated build (MCP/SDK package) for future reference."""
    db = get_db()
    build_id = data.get("build_id") or uuid4().hex[:12]
    doc = {
        "build_id": build_id,
        "project_name": data.get("project_name", "unknown"),
        "template_id": data.get("template_id", ""),
        "framework": data.get("framework", ""),
        "deployment": data.get("deployment", "local"),
        "summary": data.get("summary", ""),
        "agents": data.get("agents", []),
        "mcp_servers": data.get("mcp_servers", []),
        "files": data.get("files", []),
        "repo_url": data.get("repo_url"),
        "repo_intent": data.get("repo_intent"),
        "session_id": data.get("session_id"),
        "tags": data.get("tags", []),
        "created_at": data.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }
    await db.builds.replace_one({"build_id": build_id}, doc, upsert=True)
    return {"status": "stored", "build_id": build_id}

