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
You are the My-Agent-Too setup assistant. Your job is to help someone describe \
the AI assistant they need, then produce a structured summary so the platform \
can build it for them. The user may not be technical — speak in plain, friendly \
English. Never mention framework names, code, or developer jargon.

Gather these details through a warm, simple conversation:
1. **What they need help with** — What should the assistant do? \
   (answer phone calls, schedule appointments, reply to emails, handle customer \
   questions, manage social media, etc.)
2. **Services to connect** — What tools or accounts should it work with? \
   (their phone line, Google Calendar, email, social media, payment system, etc.) \
   Help them think of ones they might not realize they need.
3. **Special abilities** — Anything extra? (look up information, remember \
   returning customers, send reminders, etc.)
4. **How busy** — How many calls/messages per day? (a few, dozens, hundreds)
5. **Privacy needs** — Any special privacy rules? (medical info, financial data, etc.)
6. **How to access** — Do they want it hosted online (easiest) or on their own computer?

Rules:
- Ask at most ONE question per turn.
- Be warm, supportive, and encouraging — like a helpful friend.
- Use everyday language. Say "answer calls" not "telephony". Say "calendar" not "integration".
- Give examples the user can relate to (hairdresser, plumber, small shop owner).
- When you have enough info (at least what they need + 1 connected service), set is_complete=true.
- Always respond with ONLY valid JSON (no markdown, no extra text):
{
  "reply": "your conversational response to the user",
  "requirements": {
    "use_case": "...",
    "description": "...",
    "integrations": ["twilio", "google-calendar"],
    "capabilities": ["scheduling"],
    "scale": "low",
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


def _build_context_summary(session: WizardSession) -> str:
    """Build a dynamic context snapshot of gathered requirements.

    This is appended to the system prompt on every turn so Claude always
    has a clear picture of the current state — even if the conversation
    is long and earlier details would otherwise drift out of focus.
    """
    r = session.requirements
    parts: list[str] = []
    if r.use_case:
        parts.append(f"Use case: {r.use_case}")
    if r.description:
        parts.append(f"Description: {r.description}")
    if r.integrations:
        parts.append(f"Integrations: {', '.join(r.integrations)}")
    if r.capabilities:
        parts.append(f"Capabilities: {', '.join(r.capabilities)}")
    if r.scale:
        parts.append(f"Scale: {r.scale}")
    if r.compliance:
        parts.append(f"Compliance: {', '.join(r.compliance)}")
    if r.framework_preference:
        parts.append(f"Framework preference: {r.framework_preference.value}")
    if r.deployment_preference:
        parts.append(f"Deployment preference: {r.deployment_preference.value}")
    if r.additional_notes:
        parts.append(f"Notes: {r.additional_notes}")

    if not parts:
        return ""

    return (
        "\n\n--- CONTEXT SNAPSHOT (gathered so far) ---\n"
        + "\n".join(f"• {p}" for p in parts)
        + "\n--- END SNAPSHOT ---\n"
        "Use this snapshot to stay grounded. Update requirements to include "
        "any new details the user provides this turn."
    )


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

    # --- Call Claude (with dynamic context snapshot) ---
    try:
        client = _get_client()
        context_snapshot = _build_context_summary(session)
        system_with_context = SYSTEM_PROMPT + context_snapshot
        logger.info(
            "Turn %d | session=%s | context_fields=%d",
            len([m for m in session.messages if m.role == Role.USER]),
            session.session_id,
            sum(1 for v in [
                session.requirements.use_case,
                session.requirements.integrations,
                session.requirements.capabilities,
                session.requirements.scale,
            ] if v),
        )
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            system=system_with_context,
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