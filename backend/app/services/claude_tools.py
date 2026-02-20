"""Claude Tool Use definitions and executor.

Defines the tools Claude can call during the wizard conversation,
and routes tool calls to the actual backend functions.
"""

import json
import logging
from dataclasses import asdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions (Anthropic tool_use JSON Schema format)
# ---------------------------------------------------------------------------

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "search_mcp_servers",
        "description": (
            "Search the MCP server registry for available integrations. "
            "Returns servers matching the query, optionally filtered by category. "
            "Use this to find specific MCP servers the user might need "
            "(e.g. Slack, GitHub, Postgres, Twilio)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (e.g. 'slack', 'database', 'email')",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter",
                    "enum": [
                        "data", "communication", "dev-tools",
                        "productivity", "search", "ai-ml",
                        "finance", "intelligence", "custom",
                    ],
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_mcp_server_details",
        "description": (
            "Get full details for a specific MCP server by its ID. "
            "Returns name, description, required environment variables, "
            "npm package, documentation URL, and available tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "The server ID (e.g. 'slack', 'postgres', 'github')",
                },
            },
            "required": ["server_id"],
        },
    },
    {
        "name": "search_templates",
        "description": (
            "Search available agent templates. Returns templates with their "
            "framework, category, agent roles, and MCP server configurations. "
            "Use this to find pre-built templates that match the user's needs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to filter templates by name, description, or tags",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g. 'customer-service', 'research')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "analyze_repository",
        "description": (
            "Analyze a GitHub or HuggingFace repository URL. Fetches repo metadata, "
            "detects language/framework, identifies entry points, and reads key files. "
            "Use this when the user pastes a repo URL and wants to build an MCP server "
            "or SDK from it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "GitHub HTTPS/SSH URL or HuggingFace model URL",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "get_framework_recommendation",
        "description": (
            "Get a framework and deployment recommendation based on extracted requirements. "
            "Returns the recommended framework, deployment target, agent roles, "
            "MCP server configs, and cost estimate. Call this when you have enough "
            "information to make a recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "use_case": {"type": "string", "description": "The use case identifier"},
                "description": {"type": "string", "description": "Description of what the agent should do"},
                "integrations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of MCP server IDs to integrate",
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required capabilities (e.g. 'rag', 'web_search', 'memory')",
                },
                "scale": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Expected volume",
                },
                "compliance": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Compliance requirements (e.g. 'hipaa', 'soc2')",
                },
                "framework_preference": {
                    "type": "string",
                    "description": "User's preferred framework, if any",
                },
                "deployment_preference": {
                    "type": "string",
                    "enum": ["cloud", "local", "export"],
                    "description": "User's preferred deployment target",
                },
                "agents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "description": "Agent role name (snake_case, e.g. 'script_analyst')"},
                            "goal": {"type": "string", "description": "What this agent does"},
                            "backstory": {"type": "string", "description": "Optional backstory / persona for the agent"},
                        },
                        "required": ["role", "goal"],
                    },
                    "description": (
                        "Custom agent roles extracted from the user's request. "
                        "Each agent needs a role (snake_case identifier) and a goal. "
                        "If the user described specific agents, pass them here — "
                        "otherwise omit this field to use sensible defaults."
                    ),
                },
            },
            "required": ["use_case", "description", "integrations"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor — routes tool calls to real backend functions
# ---------------------------------------------------------------------------

async def execute_tool(name: str, input_data: Dict[str, Any]) -> str:
    """Execute a tool call and return the JSON-serialised result string."""
    try:
        if name == "search_mcp_servers":
            return await _exec_search_mcp_servers(input_data)
        elif name == "get_mcp_server_details":
            return await _exec_get_mcp_server_details(input_data)
        elif name == "search_templates":
            return await _exec_search_templates(input_data)
        elif name == "analyze_repository":
            return await _exec_analyze_repository(input_data)
        elif name == "get_framework_recommendation":
            return await _exec_get_framework_recommendation(input_data)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as exc:
        logger.exception("Tool execution error for %s: %s", name, exc)
        return json.dumps({"error": str(exc)})


async def _exec_search_mcp_servers(inp: Dict[str, Any]) -> str:
    from app.services.mcp_registry import list_servers
    from app.models.mcp import MCPCategory

    category = None
    if inp.get("category"):
        try:
            category = MCPCategory(inp["category"])
        except ValueError:
            pass

    servers = list_servers(
        category=category,
        search=inp.get("query"),
    )
    # Return a compact summary (not full objects)
    result = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category.value,
            "required_env": s.required_env,
            "tags": s.tags,
        }
        for s in servers[:15]  # cap at 15 to stay within context
    ]
    return json.dumps({"servers": result, "total": len(servers)})


async def _exec_get_mcp_server_details(inp: Dict[str, Any]) -> str:
    from app.services.mcp_registry import get_server

    server = get_server(inp["server_id"])
    if not server:
        return json.dumps({"error": f"Server '{inp['server_id']}' not found"})
    return json.dumps({
        "id": server.id,
        "name": server.name,
        "description": server.description,
        "category": server.category.value,
        "command": server.command,
        "args": server.args,
        "required_env": server.required_env,
        "optional_env": server.optional_env,
        "npm_package": server.npm_package,
        "documentation_url": server.documentation_url,
        "tags": server.tags,
        "is_official": server.is_official,
    })


async def _exec_search_templates(inp: Dict[str, Any]) -> str:
    from app.services.template_registry import list_templates

    templates = list_templates()
    query = (inp.get("query") or "").lower()
    category = (inp.get("category") or "").lower()

    if query or category:
        filtered = []
        for t in templates:
            if category and t.category.value.lower() != category:
                continue
            if query and query not in t.name.lower() and query not in t.description.lower() and query not in " ".join(t.tags).lower():
                continue
            filtered.append(t)
        templates = filtered

    result = [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category.value,
            "framework": t.framework.value,
            "tags": t.tags,
        }
        for t in templates[:15]
    ]
    return json.dumps({"templates": result, "total": len(templates)})


async def _exec_analyze_repository(inp: Dict[str, Any]) -> str:
    from app.services.repo_analyzer import analyze_repo

    analysis = await analyze_repo(inp["url"])
    return json.dumps(asdict(analysis))


async def _exec_get_framework_recommendation(inp: Dict[str, Any]) -> str:
    from app.models.conversation import ExtractedRequirements, FrameworkChoice, DeploymentTarget
    from app.services.recommender import build_recommendation

    # Build ExtractedRequirements from tool input
    fw_pref = None
    if inp.get("framework_preference"):
        try:
            fw_pref = FrameworkChoice(inp["framework_preference"])
        except ValueError:
            pass

    deploy_pref = None
    if inp.get("deployment_preference"):
        try:
            deploy_pref = DeploymentTarget(inp["deployment_preference"])
        except ValueError:
            pass

    # Normalise custom agents from tool input (if provided)
    custom_agents = inp.get("agents") or []

    reqs = ExtractedRequirements(
        use_case=inp.get("use_case"),
        description=inp.get("description"),
        integrations=inp.get("integrations", []),
        capabilities=inp.get("capabilities", []),
        scale=inp.get("scale"),
        compliance=inp.get("compliance", []),
        framework_preference=fw_pref,
        deployment_preference=deploy_pref,
        custom_agents=custom_agents,
    )
    rec = build_recommendation(reqs)
    return json.dumps({
        "framework": rec.framework.value,
        "framework_reason": rec.framework_reason,
        "agents": rec.agents,
        "mcp_servers": rec.mcp_servers,
        "deployment": rec.deployment.value,
        "estimated_monthly_cost": rec.estimated_monthly_cost,
        "summary": rec.summary,
    })

