"""Wizard API — chat endpoint, session management, and confirmation flow."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.conversation import (
    ChatRequest,
    ChatResponse,
    SessionStatus,
    WizardSession,
)
from app.models.template import (
    AgentRole,
    GeneratedPackage,
    GenerateRequest,
    MCPServerConfig,
)
from app.services.code_generator import generate_mcp_wrapper, generate_package
from app.services.orchestrator import process_message
from app.services.session_store import sessions
from app.services.template_registry import get_template_for_framework

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wizard", tags=["wizard"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Process a single turn of the wizard conversation.

    - If session_id is omitted, a new session is created.
    - Returns the assistant reply, updated requirements, and (once ready) a recommendation.
    """
    return await process_message(
        session_id=body.session_id,
        user_message=body.message,
    )


@router.get("/sessions", response_model=List[WizardSession])
async def list_sessions():
    """List all active wizard sessions."""
    return sessions.list_sessions()


@router.get("/sessions/{session_id}", response_model=WizardSession)
async def get_session(session_id: str):
    """Get a single wizard session with full conversation history."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a wizard session."""
    deleted = sessions.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


# ---------- Confirmation & Code Generation ----------


class ConfirmRequest(BaseModel):
    """Optional overrides when the user confirms the recommendation."""
    project_name: str = "my-agent"
    config: dict = Field(default_factory=dict)


@router.post("/sessions/{session_id}/confirm", response_model=GeneratedPackage)
async def confirm_and_generate(session_id: str, body: Optional[ConfirmRequest] = None):
    """Confirm the recommendation and generate the agent package.

    The session must have status=confirmed (i.e., the wizard produced a recommendation).
    Returns a GeneratedPackage with all files ready to download.
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in (SessionStatus.CONFIRMED, SessionStatus.RECOMMENDING):
        raise HTTPException(
            status_code=400,
            detail=f"Session is in '{session.status.value}' state — needs a confirmed recommendation first.",
        )

    rec = session.recommendation
    if not rec:
        raise HTTPException(status_code=400, detail="No recommendation on this session")

    # Resolve template from the recommended framework
    template = get_template_for_framework(rec.framework)
    if not template:
        raise HTTPException(
            status_code=500,
            detail=f"No template found for framework '{rec.framework.value}'",
        )

    body = body or ConfirmRequest()

    # Build MCP server configs from recommendation
    mcp_servers = [
        MCPServerConfig(**s) if isinstance(s, dict) else s
        for s in (rec.mcp_servers or [])
    ]

    # Build agent roles from recommendation
    agents = [
        AgentRole(**a) if isinstance(a, dict) else a
        for a in (rec.agents or [])
    ]

    # Transition state
    session.status = SessionStatus.GENERATING
    sessions.save(session)

    try:
        # --- Repo-to-MCP wrapper path ---
        if session.requirements.repo_url and session.requirements.repo_analysis:
            logger.info("Generating MCP wrapper for repo: %s", session.requirements.repo_url)
            package = generate_mcp_wrapper(
                repo_analysis=session.requirements.repo_analysis,
                project_name=body.project_name,
                deployment=rec.deployment,
            )
        else:
            # --- Standard template-based generation ---
            req = GenerateRequest(
                template_id=template.id,
                config=body.config,
                deployment=rec.deployment,
                project_name=body.project_name,
                mcp_servers=mcp_servers,
                agents=agents,
            )
            package = generate_package(req)
    except Exception as exc:
        logger.exception("Code generation failed: %s", exc)
        session.status = SessionStatus.CONFIRMED  # roll back
        sessions.save(session)
        raise HTTPException(status_code=500, detail=f"Code generation failed: {exc}") from exc

    session.status = SessionStatus.COMPLETE
    sessions.save(session)

    return package

