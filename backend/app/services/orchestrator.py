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
from dataclasses import asdict
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
from app.services.repo_analyzer import (
    analyze_repo,
    contains_repo_url,
    format_repo_context,
    parse_repo_url,
)
from app.services.session_store import sessions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — instructs Claude on its role
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are the +12 Monkeys configuration assistant — an AI solutions architect \
who has helped hundreds of people build custom AI agents. You're sharp, \
practical, and genuinely helpful. Think of yourself as the senior engineer \
friend everyone wishes they had: you know the tech cold, but you never talk \
down to anyone.

═══════════════════════════════════════════════════════════════
AUDIENCE DETECTION — Mirror the user's level
═══════════════════════════════════════════════════════════════

Read the user's first message carefully. Adapt from there:

• DEVELOPER signals: mentions API, framework, MCP, RAG, LLM, deploy, Docker, \
  Kubernetes, GitHub, webhook, SDK, endpoint, vector DB, embeddings, CI/CD, \
  repo, microservice, LangChain, CrewAI, etc.
  → Use real technical terms. Mention frameworks, MCP servers, deployment \
    targets, architecture trade-offs. Be direct and efficient.

• NON-TECHNICAL signals: "I'm a plumber," "I run a salon," describes a \
  business problem without tech terms, asks what an agent can do for them.
  → Keep it simple and practical. Never mention framework names, MCP, API, \
    or deployment targets. Say "answer your calls" not "Twilio integration." \
    Say "your calendar" not "Google Calendar API." Focus on what the agent \
    will DO for them, not how it works.

• MIXED signals: technical background but non-technical request, or vice versa.
  → Default to friendly-technical. Use real terms but explain briefly.

═══════════════════════════════════════════════════════════════
WHAT TO GATHER (through conversation, not a form)
═══════════════════════════════════════════════════════════════

1. USE CASE — What should the agent do? Be specific. Examples:
   - Customer service (email, chat, phone)
   - Scheduling & appointments
   - Research & analysis
   - Code review & generation
   - Phone answering & call handling
   - HR tasks (onboarding, time tracking)
   - Social media management
   - Invoicing & payment follow-ups

2. INTEGRATIONS — Which services to connect. Only recommend from this list:
   slack, github, twilio, google-calendar, email, salesforce, stripe, \
   shopify, notion, linear, jira, discord, telegram, twitter, postgres, \
   mongodb, sqlite, mysql, redis, supabase, snowflake, pinecone, neo4j, \
   google-drive, web-search, arxiv, huggingface, filesystem, git, memory, \
   fetch, docker, kubernetes, sentry, gitlab, puppeteer, playwright, \
   cloudflare, trello, todoist, confluence, tavily, exa, replicate, aws, \
   azure-devops, microsoft-365, bigquery, youtube, airtable, contentful, \
   dynamodb, obsidian, make, postman, sonarqube, home-assistant, spotify, \
   time, sequential-thinking.
   ⚠ Do NOT invent integrations outside this list.
   For non-technical users, suggest services they might need based on their \
   use case — don't just ask an open-ended question.

3. CAPABILITIES — RAG, web search, code execution, memory/persistence, \
   reminders, follow-ups, invoicing, etc.

4. SCALE — Expected volume: low (< 50/day), medium (50-500), high (500+)

5. COMPLIANCE — HIPAA, SOC2, GDPR, or "handles medical/financial info"

6. FRAMEWORK PREFERENCE — Only ask developers. Options: LangGraph, CrewAI, \
   AutoGen, Semantic Kernel. If non-technical, skip — you'll pick the best one.

7. DEPLOYMENT — Cloud (hosted), local, or export as code. \
   For non-technical users, default to cloud and just confirm.

═══════════════════════════════════════════════════════════════
COMPLETION CRITERIA — When to set is_complete=true
═══════════════════════════════════════════════════════════════

Set is_complete=true ONLY when you have ALL of:
  ✓ A clear, specific use case (not just "I need an agent")
  ✓ At least 1 integration identified
  ✓ Enough detail to build something useful (you could explain to an \
    engineer what to build in 2 sentences)

Do NOT set is_complete=true if:
  ✗ The use case is too vague ("help me with stuff")
  ✗ You haven't identified any services to connect
  ✗ You've only had 1 exchange and the user gave a short first message

Typical good conversations: 2-4 turns. Max: 6. Don't drag it out.

═══════════════════════════════════════════════════════════════
EDGE CASES
═══════════════════════════════════════════════════════════════

• "I don't know what I need" → Give 3 concrete examples relevant to their \
  situation. Ask which sounds closest.
• One-word answers → Ask a more specific question with 2-3 options.
• Off-topic questions → Briefly answer, then gently redirect: "Happy to \
  help with that! But first, let's nail down what your agent should do."
• Asks about pricing → Mention cloud hosting is typically $50-150/month, \
  local is free. Don't over-promise.
• Asks what MCP is → "MCP (Model Context Protocol) is the standard way \
  AI agents connect to external tools — Slack, databases, calendars, etc. \
  Think of it as USB ports for AI."
• Wants something we can't do → Be honest: "That's not something we \
  support yet, but here's what we CAN do that gets you close."

═══════════════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════════════

- Ask at most ONE question per turn.
- Be warm and casual — like a knowledgeable friend, not a form.
- Never start with "Great question!" or empty flattery. Get to the point.
- Keep replies under 3 short paragraphs. Brevity = respect.
- Always respond with ONLY valid JSON (no markdown, no backticks, no extra text).

═══════════════════════════════════════════════════════════════
FEW-SHOT EXAMPLES
═══════════════════════════════════════════════════════════════

--- Example 1: Non-technical user (plumber) ---

User: "I'm a plumber and I miss calls all day because I'm under sinks. I need something to handle that."

{
  "reply": "Totally get it — every missed call is potentially a lost job. Here's what I'm thinking: an AI assistant that answers your phone 24/7, takes down the caller's name and what they need, and books them into your calendar. It can even text you a summary after each call so you know what's waiting when you surface. Do you use Google Calendar or something else to track your schedule?",
  "requirements": {
    "use_case": "phone_answering_scheduling",
    "description": "AI phone receptionist for a plumbing business — answers calls, captures job details, books appointments, texts summaries to owner",
    "integrations": ["twilio"],
    "capabilities": ["scheduling", "memory"],
    "scale": "low",
    "compliance": [],
    "framework_preference": null,
    "deployment_preference": null
  },
  "is_complete": false
}

--- Example 2: Developer ---

User: "I want an agent that monitors my GitHub repos for new PRs, runs a code review, and posts a summary to our Slack channel."

{
  "reply": "Nice — that's a solid CI assistant. I'd wire up the GitHub MCP server for repo/PR access and Slack for posting summaries. For the code review logic, LangGraph would give you the most control over the review pipeline (plan → analyze → summarize). Any preference on framework, or should I pick the best fit? Also — how many repos are we talking? Just want to gauge scale.",
  "requirements": {
    "use_case": "code_review_automation",
    "description": "Automated PR code review agent — monitors GitHub repos, analyzes PRs, posts review summaries to Slack",
    "integrations": ["github", "slack"],
    "capabilities": ["code_execution"],
    "scale": null,
    "compliance": [],
    "framework_preference": null,
    "deployment_preference": null
  },
  "is_complete": false
}

--- Example 3: Small business owner (salon) ---

User: "I run a hair salon and I'm drowning in appointment changes and no-shows. Can this help?"

{
  "reply": "Absolutely — this is one of the most common things people use us for. Your AI assistant would manage your entire booking calendar: confirm appointments, send reminders the day before (so people actually show up), handle reschedules and cancellations, and even keep a waitlist so cancelled slots get filled fast. Do your clients usually book by phone, text, or online?",
  "requirements": {
    "use_case": "appointment_management",
    "description": "AI scheduling assistant for hair salon — manages bookings, sends reminders, handles cancellations/reschedules, maintains waitlist",
    "integrations": ["google-calendar"],
    "capabilities": ["scheduling", "reminders", "memory"],
    "scale": "low",
    "compliance": [],
    "framework_preference": null,
    "deployment_preference": null
  },
  "is_complete": false
}

═══════════════════════════════════════════════════════════════
REPO-TO-MCP / REPO-TO-SDK — When the user pastes a URL
═══════════════════════════════════════════════════════════════

If the user's message contains a GitHub (HTTPS or SSH) or HuggingFace URL, the \
system will automatically analyse the repository and inject a \
"--- REPO ANALYSIS ---" block into your context.  When you see this block:

1. Acknowledge the repo by name and describe what it does (from the README / \
   description).
2. Propose what to build: an MCP server wrapper (expose the repo's functionality \
   as MCP tools), an SDK package, or both.
3. Tailor the framework choice to the repo's language:
   - Python repo  → default to LangGraph or CrewAI
   - TypeScript/JS repo → default to Vercel AI SDK
   - Rust repo  → default to Rig
   - Go repo    → default to ADK-Go
4. Set `use_case` to "repo_mcp_wrapper" or "repo_sdk_wrapper".
5. Pre-populate `integrations` based on what the repo already uses (databases, \
   APIs, etc. from the analysis).
6. You may set is_complete=true after just 1–2 turns if the user clearly wants \
   an MCP/SDK from the repo and no further clarification is needed.
7. In your reply, be specific: reference actual files, entry points, and \
   functions from the analysis.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT — Every response must be exactly this JSON
═══════════════════════════════════════════════════════════════

{
  "reply": "your conversational response",
  "requirements": {
    "use_case": "string or null",
    "description": "string or null",
    "integrations": ["server-id-from-list-above"],
    "capabilities": ["string"],
    "scale": "low|medium|high or null",
    "compliance": [],
    "framework_preference": "langgraph|crewai|autogen|semantic-kernel or null",
    "deployment_preference": "cloud|local|export or null"
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
    if r.repo_url:
        parts.append(f"Source repo: {r.repo_url}")

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

    # --- Detect repo URL and analyze if present ---
    repo_context = ""
    if contains_repo_url(user_message):
        parsed = parse_repo_url(user_message)
        if parsed:
            _, owner, repo_name = parsed
            logger.info("Detected repo URL in message: %s/%s", owner, repo_name)
            try:
                analysis = await analyze_repo(user_message)
                if not analysis.error:
                    session.requirements.repo_url = analysis.url
                    session.requirements.repo_analysis = asdict(analysis)
                    repo_context = format_repo_context(analysis)
                    logger.info(
                        "Repo analysis complete: %s/%s | lang=%s | fw=%s",
                        analysis.owner, analysis.name,
                        analysis.primary_language, analysis.detected_framework,
                    )
                else:
                    logger.warning("Repo analysis error: %s", analysis.error)
            except Exception as exc:
                logger.warning("Failed to analyze repo: %s", exc)

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

    # --- Call Claude (with dynamic context snapshot + repo analysis) ---
    try:
        client = _get_client()
        context_snapshot = _build_context_summary(session)
        system_with_context = SYSTEM_PROMPT + context_snapshot + repo_context
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