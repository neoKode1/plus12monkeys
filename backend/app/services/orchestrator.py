"""Wizard Orchestrator — drives the multi-turn conversation with an LLM.

Flow:
1. User sends a message.
2. Orchestrator feeds the full conversation + a system prompt to Claude.
3. Claude responds with a JSON payload:  { reply, requirements, is_complete }
4. If is_complete → call recommender.build_recommendation() and present result.
5. Otherwise → return the clarifying question to the user.
"""

import json
import logging
from typing import Optional

import anthropic

from app.core.config import settings
from app.models.conversation import (
    ChatResponse,
    ExtractedRequirements,
    Message,
    Recommendation,
    Role,
    SessionStatus,
    WizardSession,
)
from app.services.recommender import build_recommendation
from app.services.session_store import sessions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — instructs Claude on its role
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are the My-Agent-Too configuration wizard. Your job is to help a developer \
describe the AI agent they want to build, then produce a structured requirements \
summary so the platform can generate the agent automatically.

Gather these requirements through friendly conversation:
1. **Use case** — What will the agent do? (customer service, research, coding, etc.)
2. **Integrations** — Which services should the agent connect to? \
   (Slack, Salesforce, GitHub, Postgres, email, web search, MongoDB, Notion, \
   Google Drive, Discord, etc.)
3. **Capabilities** — Special abilities needed (RAG, code execution, web browsing, etc.)
4. **Scale** — Expected load: low / medium / high
5. **Compliance** — Any regulatory needs (HIPAA, SOC2, GDPR, etc.)
6. **Framework preference** — Does the user want a specific framework? \
   (LangGraph, CrewAI, AutoGen, Semantic Kernel) or leave it to you?
7. **Deployment** — local, cloud, or export as code?

Rules:
- Ask at most ONE clarifying question per turn.
- Be concise but warm.
- When you have enough info (at least use_case + 1 integration), set is_complete=true.
- Always respond with ONLY valid JSON (no markdown, no extra text):
{
  "reply": "your conversational response to the user",
  "requirements": {
    "use_case": "...",
    "description": "...",
    "integrations": ["slack", "github"],
    "capabilities": ["rag"],
    "scale": "medium",
    "compliance": [],
    "framework_preference": null,
    "deployment_preference": null
  },
  "is_complete": false
}
"""


def _get_client() -> anthropic.Anthropic:
    """Lazy-init the Anthropic client."""
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _build_messages(session: WizardSession) -> list[dict]:
    """Convert session messages to Anthropic API format."""
    return [
        {"role": m.role.value, "content": m.content}
        for m in session.messages
        if m.role in (Role.USER, Role.ASSISTANT)
    ]


def _parse_llm_response(raw: str) -> dict:
    """Parse the JSON response from Claude, handling common issues."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return json.loads(text.strip())


async def process_message(
    session_id: Optional[str], user_message: str
) -> ChatResponse:
    """Process one turn of the wizard conversation.

    Returns a ChatResponse with the assistant reply and updated state.
    """
    # Get or create session
    if session_id:
        session = sessions.get(session_id)
        if not session:
            session = sessions.create()
    else:
        session = sessions.create()

    # Append user message
    session.messages.append(Message(role=Role.USER, content=user_message))

    # --- Guard: API key ---
    if not settings.anthropic_api_key:
        reply_text = (
            "⚠️ The Anthropic API key is not configured. "
            "Please set ANTHROPIC_API_KEY in your .env file."
        )
        session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))
        sessions.save(session)
        return ChatResponse(
            session_id=session.session_id,
            reply=reply_text,
            status=session.status,
        )

    # --- Call Claude ---
    try:
        client = _get_client()
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=_build_messages(session),
        )
        raw_reply = response.content[0].text
        parsed = _parse_llm_response(raw_reply)
    except (anthropic.AuthenticationError, TypeError):
        logger.error("Anthropic API key missing or invalid")
        reply_text = (
            "⚠️ The Anthropic API key is invalid. "
            "Please check your ANTHROPIC_API_KEY in .env."
        )
        session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))
        sessions.save(session)
        return ChatResponse(
            session_id=session.session_id,
            reply=reply_text,
            status=session.status,
        )
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning("Failed to parse LLM response: %s", exc)
        reply_text = (
            "I had a small hiccup processing that — could you rephrase? "
            "Tell me what kind of agent you'd like to build."
        )
        session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))
        sessions.save(session)
        return ChatResponse(
            session_id=session.session_id,
            reply=reply_text,
            status=session.status,
        )
    except Exception as exc:
        logger.exception("Unexpected error calling LLM: %s", exc)
        reply_text = "Something went wrong on my end. Please try again."
        session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))
        sessions.save(session)
        return ChatResponse(
            session_id=session.session_id,
            reply=reply_text,
            status=session.status,
        )

    # --- Update requirements from LLM output ---
    reply_text = parsed.get("reply", "")
    llm_reqs = parsed.get("requirements", {})
    is_complete = parsed.get("is_complete", False)

    # Merge LLM-extracted requirements into session
    if llm_reqs:
        for field in (
            "use_case", "description", "scale",
            "framework_preference", "deployment_preference",
        ):
            val = llm_reqs.get(field)
            if val:
                setattr(session.requirements, field, val)
        for list_field in ("integrations", "capabilities", "compliance"):
            vals = llm_reqs.get(list_field, [])
            if vals:
                existing = set(getattr(session.requirements, list_field))
                existing.update(vals)
                setattr(session.requirements, list_field, sorted(existing))

    # Append assistant reply
    session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))

    # --- If complete, produce recommendation ---
    recommendation: Optional[Recommendation] = None
    if is_complete:
        session.status = SessionStatus.RECOMMENDING
        recommendation = build_recommendation(session.requirements)
        session.recommendation = recommendation
        session.status = SessionStatus.CONFIRMED

    sessions.save(session)

    return ChatResponse(
        session_id=session.session_id,
        reply=reply_text,
        status=session.status,
        requirements=session.requirements,
        recommendation=recommendation,
    )