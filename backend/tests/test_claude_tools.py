"""Tests for Claude tool execution (search, details, templates, recommend).

Tests exercise the tool executors against the real registries — no mocks needed
since the MCP registry and template registry are in-memory data structures.
The analyze_repository tool is skipped because it requires network access.
"""

import json

import pytest

from app.services.claude_tools import TOOLS, execute_tool


# ---------- Tool definitions schema ----------

def test_tools_list_has_five_tools():
    assert len(TOOLS) == 5

def test_tool_names():
    names = {t["name"] for t in TOOLS}
    assert names == {
        "search_mcp_servers",
        "get_mcp_server_details",
        "search_templates",
        "analyze_repository",
        "get_framework_recommendation",
    }

def test_tool_schemas_valid():
    """Each tool must have name, description, and input_schema."""
    for t in TOOLS:
        assert "name" in t
        assert "description" in t
        assert "input_schema" in t
        assert t["input_schema"]["type"] == "object"


# ---------- execute_tool: search_mcp_servers ----------

@pytest.mark.anyio
async def test_exec_search_mcp_servers():
    result = await execute_tool("search_mcp_servers", {"query": "postgres"})
    data = json.loads(result)
    assert "servers" in data
    assert data["total"] >= 1
    assert any("postgres" in s["id"].lower() or "postgres" in s["name"].lower() for s in data["servers"])

@pytest.mark.anyio
async def test_exec_search_mcp_servers_with_category():
    result = await execute_tool("search_mcp_servers", {"query": "", "category": "data"})
    data = json.loads(result)
    assert all(s["category"] == "data" for s in data["servers"])

@pytest.mark.anyio
async def test_exec_search_mcp_servers_empty():
    result = await execute_tool("search_mcp_servers", {"query": "zzz_nonexistent_999"})
    data = json.loads(result)
    assert data["total"] == 0


# ---------- execute_tool: get_mcp_server_details ----------

@pytest.mark.anyio
async def test_exec_get_mcp_server_details_exists():
    result = await execute_tool("get_mcp_server_details", {"server_id": "slack"})
    data = json.loads(result)
    assert data["id"] == "slack"
    assert data["name"] == "Slack"
    assert "SLACK_BOT_TOKEN" in data["required_env"]
    assert data["is_official"] is True

@pytest.mark.anyio
async def test_exec_get_mcp_server_details_missing():
    result = await execute_tool("get_mcp_server_details", {"server_id": "nonexistent_xyz"})
    data = json.loads(result)
    assert "error" in data


# ---------- execute_tool: search_templates ----------

@pytest.mark.anyio
async def test_exec_search_templates_all():
    result = await execute_tool("search_templates", {})
    data = json.loads(result)
    assert data["total"] >= 10
    assert len(data["templates"]) > 0

@pytest.mark.anyio
async def test_exec_search_templates_with_query():
    result = await execute_tool("search_templates", {"query": "customer"})
    data = json.loads(result)
    assert data["total"] >= 1
    assert any("customer" in t["name"].lower() for t in data["templates"])


# ---------- execute_tool: get_framework_recommendation ----------

@pytest.mark.anyio
async def test_exec_get_recommendation():
    result = await execute_tool("get_framework_recommendation", {
        "use_case": "customer support",
        "integrations": ["slack"],
    })
    data = json.loads(result)
    assert "framework" in data
    assert "agents" in data
    assert "summary" in data
    assert data["framework"] == "crewai"

@pytest.mark.anyio
async def test_exec_get_recommendation_with_preference():
    result = await execute_tool("get_framework_recommendation", {
        "use_case": "anything",
        "framework_preference": "langgraph",
    })
    data = json.loads(result)
    assert data["framework"] == "langgraph"

@pytest.mark.anyio
async def test_exec_get_recommendation_custom_agents():
    result = await execute_tool("get_framework_recommendation", {
        "use_case": "research",
        "agents": [
            {"role": "researcher", "goal": "Find papers"},
            {"role": "writer", "goal": "Write summaries"},
        ],
    })
    data = json.loads(result)
    assert len(data["agents"]) == 2


# ---------- execute_tool: unknown tool ----------

@pytest.mark.anyio
async def test_exec_unknown_tool():
    result = await execute_tool("nonexistent_tool", {})
    data = json.loads(result)
    assert "error" in data
    assert "Unknown tool" in data["error"]

