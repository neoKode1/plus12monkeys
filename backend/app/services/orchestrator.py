"""Wizard Orchestrator — drives the multi-turn conversation with Claude.

Flow (with Tool Use):
1. User sends a message.
2. Orchestrator feeds the full conversation + system prompt + tools to Claude.
3. Claude may call tools (search MCP registry, analyze repos, get recommendations)
   or respond with text.
4. Tool results are fed back — loop until Claude returns a final text response.
5. If Claude called get_framework_recommendation, we extract the recommendation.
6. Return the assistant reply + updated state to the frontend.

Features: Tool Use, Prompt Caching, Extended Thinking (architecture decisions).
"""

import json
import logging
from typing import Any, Dict, List, Optional

import anthropic

from app.core.config import settings
from app.models.conversation import (
    ChatResponse,
    ExtractedRequirements,
    FrameworkChoice,
    DeploymentTarget,
    Message,
    Recommendation,
    Role,
    SessionStatus,
    WizardSession,
)
from app.services.claude_tools import TOOLS, execute_tool
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

8. EXISTING APPLICATION (proactive — ask early!) — \
   Before diving deep into framework/integration details, ask: \
   "Do you have an existing app you'd like to plug this agent into? \
   If so, share a GitHub or HuggingFace link and I'll tailor the build \
   to fit your stack." \
   If they share a link, call analyze_repository immediately. Then use \
   the results to: \
   - Match the agent's language to the app (Python app → Python agent). \
   - Suggest integrations that align with the app's existing services \
     (e.g., if the app uses PostgreSQL, recommend the Postgres MCP). \
   - Shape agent roles to complement what the app already does. \
   If they don't have an app (or want a standalone agent), that's fine — \
   skip this and continue as normal.

═══════════════════════════════════════════════════════════════
COMPLETION CRITERIA — When to call get_framework_recommendation
═══════════════════════════════════════════════════════════════

Call the get_framework_recommendation tool ONLY when you have ALL of:
  ✓ A clear, specific use case (not just "I need an agent")
  ✓ At least 1 integration identified (use search_mcp_servers to verify)
  ✓ Enough detail to build something useful (you could explain to an \
    engineer what to build in 2 sentences)

Do NOT call get_framework_recommendation if:
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
- Respond with natural text — NOT JSON. Use the provided tools for \
  structured actions (searching servers, analyzing repos, recommending).

═══════════════════════════════════════════════════════════════
TOOLS YOU HAVE ACCESS TO
═══════════════════════════════════════════════════════════════

You have real-time access to these tools — use them proactively:

• search_mcp_servers — Look up available integrations by keyword or category. \
  Use this to verify server IDs before recommending them.
• get_mcp_server_details — Get full details (env vars, docs URL) for a server.
• search_templates — Find pre-built agent templates matching a use case.
• analyze_repository — Analyze a GitHub/HuggingFace repo URL. Use this when \
  the user pastes a repo link.
• get_framework_recommendation — Generate a full recommendation once you have \
  enough information. This produces the final architecture plan.

IMPORTANT: When calling get_framework_recommendation, include ALL relevant \
integrations as server IDs. After calling it, present the results to the user \
in a clear summary and ask them to confirm.

═══════════════════════════════════════════════════════════════
REPO-TO-MCP / REPO-TO-SDK — When the user pastes a URL
═══════════════════════════════════════════════════════════════

If the user's message contains a GitHub or HuggingFace URL:

1. Call the analyze_repository tool with the URL.
2. Acknowledge the repo by name and describe what it does.
3. Determine intent — does the user want to:
   a) WRAP this repo as an MCP server / SDK package?
   b) BUILD AN AGENT FOR this existing app (integrate into it)?
   If unclear, ask: "Would you like me to build an MCP wrapper around \
   this repo, or build an agent designed to integrate INTO this app?"
4. For WRAPPING (a): Propose an MCP server wrapper / SDK package.
5. For INTEGRATING INTO (b): Use the repo analysis to shape agent design:
   - Match the agent language to the app's primary language.
   - Suggest MCP servers that align with the app's detected services \
     (e.g., if the app uses postgres → recommend postgres MCP).
   - Design agent roles that complement the app's existing functionality.
   - Reference specific files, models, and patterns from the repo.
6. Tailor the framework choice to the repo's language:
   - Python repo  → default to LangGraph or CrewAI
   - TypeScript/JS repo → default to Vercel AI SDK
   - Rust repo  → default to Rig
   - Go repo    → default to ADK-Go
7. You may call get_framework_recommendation after just 1–2 turns if the \
   user clearly wants an MCP/SDK from the repo.
8. In your reply, be specific: reference actual files, entry points, and \
   functions from the analysis.
"""


_async_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> anthropic.AsyncAnthropic:
    """Lazy-init the async Anthropic client (reused across requests)."""
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _async_client


async def close_client() -> None:
    """Close the shared Anthropic client. Call on app shutdown."""
    global _async_client
    if _async_client is not None:
        await _async_client.close()
        _async_client = None


def _build_context_summary(session: WizardSession) -> str:
    """Build a dynamic context snapshot of gathered requirements."""
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
    )


def _build_messages(session: WizardSession) -> list[dict]:
    """Convert session messages to Anthropic API format."""
    return [
        {"role": m.role.value, "content": m.content}
        for m in session.messages
        if m.role in (Role.USER, Role.ASSISTANT)
    ]


def _build_system_prompt(session: WizardSession) -> list[dict]:
    """Build a system prompt with prompt caching.

    Returns a list of content blocks with cache_control on the static
    portion so it only gets billed once per session.
    """
    context_snapshot = _build_context_summary(session)
    blocks = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},  # Cache the large static prompt
        },
    ]
    if context_snapshot:
        blocks.append({"type": "text", "text": context_snapshot})
    return blocks


async def process_message(
    session_id: Optional[str], user_message: str
) -> ChatResponse:
    """Process one turn of the wizard conversation with tool use.

    Claude can call tools (search MCP servers, analyze repos, etc.)
    during the conversation. We loop until Claude returns a final text.
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

    # --- Call Claude with tool use loop ---
    try:
        client = _get_client()
        system_blocks = _build_system_prompt(session)
        api_messages = _build_messages(session)

        turn_count = len([m for m in session.messages if m.role == Role.USER])
        logger.info("Turn %d | session=%s", turn_count, session.session_id)

        recommendation: Optional[Recommendation] = None
        reply_text = ""
        max_tool_rounds = 5  # safety limit

        # Enable extended thinking after the first turn (when there's
        # enough context for deeper architectural reasoning).
        use_thinking = turn_count > 1

        for tool_round in range(max_tool_rounds):
            create_kwargs: Dict[str, Any] = dict(
                model=settings.llm_model,
                max_tokens=16000 if use_thinking else 2048,
                system=system_blocks,
                messages=api_messages,
                tools=TOOLS,
            )
            if use_thinking:
                create_kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 8000,
                }

            response = await client.messages.create(**create_kwargs)

            # Collect text blocks and tool_use blocks from response
            # (skip thinking blocks — they're internal reasoning)
            text_parts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                # thinking blocks are silently skipped

            # If no tool calls, Claude is done — extract final text
            if not tool_calls:
                reply_text = "\n".join(text_parts)
                break

            # Execute tool calls and build tool results
            logger.info(
                "Tool round %d: %s",
                tool_round + 1,
                [tc["name"] for tc in tool_calls],
            )

            # Append Claude's response (with tool_use blocks) to messages
            api_messages.append({"role": "assistant", "content": response.content})

            # Build tool_result messages
            tool_results = []
            for tc in tool_calls:
                result_str = await execute_tool(tc["name"], tc["input"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result_str,
                })

                # Extract recommendation if this was the recommendation tool
                if tc["name"] == "get_framework_recommendation":
                    recommendation = _extract_recommendation(result_str, tc["input"], session)

                # Extract repo analysis if this was the analyze tool
                if tc["name"] == "analyze_repository":
                    _extract_repo_analysis(result_str, session, tc["input"])

            api_messages.append({"role": "user", "content": tool_results})
        else:
            # Exhausted tool rounds — use whatever text we have
            reply_text = reply_text or "I gathered a lot of information. Let me summarize what I found."

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

    # Append assistant reply
    session.messages.append(Message(role=Role.ASSISTANT, content=reply_text))

    # If recommendation was produced, update session
    if recommendation:
        session.status = SessionStatus.RECOMMENDING
        session.recommendation = recommendation

    sessions.save(session)

    return ChatResponse(
        session_id=session.session_id,
        reply=reply_text,
        status=session.status,
        requirements=session.requirements,
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Streaming version — yields SSE event dicts
# ---------------------------------------------------------------------------

async def process_message_stream(
    session_id: Optional[str], user_message: str
):
    """Streaming version of process_message.

    Yields dicts like:
        {"event": "status",  "data": "Searching MCP servers..."}
        {"event": "delta",   "data": "partial text"}
        {"event": "done",    "data": <full ChatResponse JSON>}
    """
    # Get or create session
    if session_id:
        session = sessions.get(session_id)
        if not session:
            session = sessions.create()
    else:
        session = sessions.create()

    session.messages.append(Message(role=Role.USER, content=user_message))

    if not settings.anthropic_api_key:
        reply = "⚠️ The Anthropic API key is not configured."
        session.messages.append(Message(role=Role.ASSISTANT, content=reply))
        sessions.save(session)
        yield {"event": "delta", "data": reply}
        yield {"event": "done", "data": json.dumps({
            "session_id": session.session_id, "reply": reply,
            "status": session.status.value, "requirements": None, "recommendation": None,
        })}
        return

    try:
        client = _get_client()
        system_blocks = _build_system_prompt(session)
        api_messages = _build_messages(session)
        turn_count = len([m for m in session.messages if m.role == Role.USER])
        use_thinking = turn_count > 1

        recommendation: Optional[Recommendation] = None
        full_text = ""
        max_tool_rounds = 5

        _TOOL_STATUS = {
            "search_mcp_servers": "🔍 Searching MCP servers…",
            "get_mcp_server_details": "📋 Fetching server details…",
            "search_templates": "📑 Searching templates…",
            "analyze_repository": "🔬 Analyzing repository…",
            "get_framework_recommendation": "⚙️ Building recommendation…",
        }

        for tool_round in range(max_tool_rounds):
            create_kwargs: Dict[str, Any] = dict(
                model=settings.llm_model,
                max_tokens=16000 if use_thinking else 2048,
                system=system_blocks,
                messages=api_messages,
                tools=TOOLS,
            )
            if use_thinking:
                create_kwargs["thinking"] = {"type": "enabled", "budget_tokens": 8000}

            # Use streaming for the API call
            streamed_text_parts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []
            current_tool_input = ""
            current_tool_name = ""
            current_tool_id = ""

            final_message = None
            async with client.messages.stream(**create_kwargs) as stream:
                async for event in stream:
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            current_tool_name = block.name
                            current_tool_id = block.id
                            current_tool_input = ""
                            status_msg = _TOOL_STATUS.get(block.name, f"🔧 Using {block.name}…")
                            yield {"event": "status", "data": status_msg}
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            streamed_text_parts.append(delta.text)
                            yield {"event": "delta", "data": delta.text}
                        elif delta.type == "input_json_delta":
                            current_tool_input += delta.partial_json
                    elif event.type == "content_block_stop":
                        if current_tool_name:
                            try:
                                parsed_input = json.loads(current_tool_input) if current_tool_input else {}
                            except json.JSONDecodeError:
                                parsed_input = {}
                            tool_calls.append({
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": parsed_input,
                            })
                            current_tool_name = ""
                # Get the accumulated message before exiting async with
                final_message = await stream.get_final_message()

            # If no tool calls, we're done
            if not tool_calls:
                full_text = "".join(streamed_text_parts)
                break

            # Execute tools (non-streaming) and feed results back
            api_messages.append({"role": "assistant", "content": final_message.content})

            tool_results = []
            for tc in tool_calls:
                result_str = await execute_tool(tc["name"], tc["input"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result_str,
                })
                if tc["name"] == "get_framework_recommendation":
                    recommendation = _extract_recommendation(result_str, tc["input"], session)
                if tc["name"] == "analyze_repository":
                    _extract_repo_analysis(result_str, session, tc["input"])

            api_messages.append({"role": "user", "content": tool_results})
        else:
            full_text = full_text or "I gathered a lot of information. Let me summarize what I found."
            yield {"event": "delta", "data": full_text}

    except Exception as exc:
        logger.exception("Streaming error: %s", exc)
        full_text = "Something went wrong on my end. Please try again."
        session.messages.append(Message(role=Role.ASSISTANT, content=full_text))
        sessions.save(session)
        yield {"event": "delta", "data": full_text}
        yield {"event": "done", "data": json.dumps({
            "session_id": session.session_id, "reply": full_text,
            "status": session.status.value, "requirements": None, "recommendation": None,
        })}
        return

    # Finalize session
    session.messages.append(Message(role=Role.ASSISTANT, content=full_text))
    if recommendation:
        session.status = SessionStatus.RECOMMENDING
        session.recommendation = recommendation
    sessions.save(session)

    # Send the final done event with full structured response
    done_data = {
        "session_id": session.session_id,
        "reply": full_text,
        "status": session.status.value,
        "requirements": None,
        "recommendation": None,
    }
    if session.requirements:
        done_data["requirements"] = {
            "use_case": session.requirements.use_case,
            "description": session.requirements.description,
            "integrations": session.requirements.integrations,
            "capabilities": session.requirements.capabilities,
            "scale": session.requirements.scale,
            "compliance": session.requirements.compliance,
            "framework_preference": session.requirements.framework_preference.value if session.requirements.framework_preference else None,
            "deployment_preference": session.requirements.deployment_preference.value if session.requirements.deployment_preference else None,
        }
    if recommendation:
        done_data["recommendation"] = {
            "framework": recommendation.framework.value,
            "framework_reason": recommendation.framework_reason,
            "agents": recommendation.agents,
            "mcp_servers": recommendation.mcp_servers,
            "deployment": recommendation.deployment.value,
            "estimated_monthly_cost": recommendation.estimated_monthly_cost,
            "summary": recommendation.summary,
        }
    yield {"event": "done", "data": json.dumps(done_data)}


# ---------------------------------------------------------------------------
# Helpers for extracting structured data from tool results
# ---------------------------------------------------------------------------

def _extract_recommendation(
    result_str: str, tool_input: Dict[str, Any], session: WizardSession
) -> Optional[Recommendation]:
    """Parse the get_framework_recommendation tool result into a Recommendation."""
    try:
        data = json.loads(result_str)
        if "error" in data:
            return None

        # Also update session requirements from the tool input
        if tool_input.get("use_case"):
            session.requirements.use_case = tool_input["use_case"]
        if tool_input.get("description"):
            session.requirements.description = tool_input["description"]
        if tool_input.get("integrations"):
            existing = set(session.requirements.integrations)
            existing.update(tool_input["integrations"])
            session.requirements.integrations = sorted(existing)
        if tool_input.get("capabilities"):
            existing = set(session.requirements.capabilities)
            existing.update(tool_input["capabilities"])
            session.requirements.capabilities = sorted(existing)
        if tool_input.get("scale"):
            session.requirements.scale = tool_input["scale"]
        if tool_input.get("compliance"):
            existing = set(session.requirements.compliance)
            existing.update(tool_input["compliance"])
            session.requirements.compliance = sorted(existing)
        if tool_input.get("framework_preference"):
            try:
                session.requirements.framework_preference = FrameworkChoice(tool_input["framework_preference"])
            except ValueError:
                pass
        if tool_input.get("deployment_preference"):
            try:
                session.requirements.deployment_preference = DeploymentTarget(tool_input["deployment_preference"])
            except ValueError:
                pass
        if tool_input.get("agents"):
            session.requirements.custom_agents = tool_input["agents"]

        return Recommendation(
            framework=FrameworkChoice(data["framework"]),
            framework_reason=data.get("framework_reason", ""),
            agents=data.get("agents", []),
            mcp_servers=data.get("mcp_servers", []),
            deployment=DeploymentTarget(data.get("deployment", "cloud")),
            estimated_monthly_cost=data.get("estimated_monthly_cost"),
            summary=data.get("summary", ""),
        )
    except Exception as exc:
        logger.warning("Failed to extract recommendation: %s", exc)
        return None


def _extract_repo_analysis(result_str: str, session: WizardSession, tool_input: Optional[Dict[str, Any]] = None) -> None:
    """Store repo analysis results and repo intent in the session."""
    try:
        data = json.loads(result_str)
        if data.get("error"):
            return
        session.requirements.repo_url = data.get("url", "")
        session.requirements.repo_analysis = data
        # Extract intent from the tool input (Claude decides "wrap" vs "integrate")
        if tool_input:
            session.requirements.repo_intent = tool_input.get("intent", "wrap")
    except Exception as exc:
        logger.warning("Failed to extract repo analysis: %s", exc)