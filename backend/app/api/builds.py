"""Builds API — browse and search the archive of generated MCP/SDK packages."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.nanda_client import nanda

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
    try:
        return await nanda.list_builds(q=q, framework=framework, limit=limit, skip=skip)
    except Exception as exc:
        logger.exception("Failed to fetch builds: %s", exc)
        raise HTTPException(status_code=502, detail="Build archive unavailable") from exc


@router.get("/{build_id}")
async def get_build(build_id: str):
    """Get a single archived build by ID, including full file contents."""
    try:
        return await nanda.get_build(build_id)
    except Exception as exc:
        logger.exception("Failed to fetch build %s: %s", build_id, exc)
        raise HTTPException(status_code=502, detail="Build archive unavailable") from exc

