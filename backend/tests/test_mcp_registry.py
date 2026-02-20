"""Tests for the MCP server registry."""

from app.models.mcp import MCPCategory, MCPServerEntry, MCPServerStatus
from app.services.mcp_registry import (
    get_categories,
    get_server,
    list_servers,
    server_count,
    update_server_health,
)


# ---------- list_servers ----------

def test_list_servers_returns_all():
    servers = list_servers()
    assert len(servers) > 0
    assert all(isinstance(s, MCPServerEntry) for s in servers)


def test_list_servers_filter_by_category():
    data_servers = list_servers(category=MCPCategory.DATA)
    assert len(data_servers) > 0
    assert all(s.category == MCPCategory.DATA for s in data_servers)


def test_list_servers_search():
    results = list_servers(search="postgres")
    assert len(results) >= 1
    names = [s.name.lower() for s in results]
    assert any("postgres" in n for n in names)


def test_list_servers_search_no_results():
    results = list_servers(search="zzz_nonexistent_xyz_999")
    assert results == []


def test_list_servers_official_only():
    officials = list_servers(official_only=True)
    assert all(s.is_official for s in officials)


def test_list_servers_combined_filters():
    results = list_servers(category=MCPCategory.DATA, search="sql")
    assert all(s.category == MCPCategory.DATA for s in results)


# ---------- get_server ----------

def test_get_server_exists():
    server = get_server("postgres")
    assert server is not None
    assert server.id == "postgres"
    assert server.name == "PostgreSQL"
    assert "DATABASE_URL" in server.required_env


def test_get_server_missing():
    assert get_server("nonexistent_server_xyz") is None


# ---------- get_categories ----------

def test_get_categories():
    cats = get_categories()
    assert isinstance(cats, list)
    assert len(cats) > 0
    assert "data" in cats


def test_get_categories_sorted():
    cats = get_categories()
    assert cats == sorted(cats)


# ---------- server_count ----------

def test_server_count():
    count = server_count()
    assert count > 20  # We know there are many registered servers


# ---------- update_server_health ----------

def test_update_server_health():
    update_server_health("postgres", MCPServerStatus.HEALTHY, tools=["query"])
    server = get_server("postgres")
    assert server is not None
    assert server.status == MCPServerStatus.HEALTHY
    assert server.last_health_check is not None
    # Reset for other tests
    update_server_health("postgres", MCPServerStatus.UNKNOWN)


def test_update_server_health_nonexistent():
    # Should not raise
    update_server_health("nonexistent_xyz", MCPServerStatus.HEALTHY)


# ---------- Well-known servers exist ----------

def test_well_known_servers():
    """Verify a sample of important servers are registered."""
    expected_ids = [
        "postgres", "slack", "github", "filesystem",
        "fetch", "memory", "redis", "stripe",
    ]
    for sid in expected_ids:
        server = get_server(sid)
        assert server is not None, f"Expected server '{sid}' to be registered"
        assert server.id == sid
        assert len(server.name) > 0
        assert len(server.description) > 0


def test_server_entry_fields():
    """Verify that server entries have all required fields populated."""
    server = get_server("slack")
    assert server is not None
    assert server.command in ("npx", "uvx", "docker", "node")
    assert isinstance(server.args, list)
    assert isinstance(server.required_env, list)
    assert isinstance(server.tags, list)
    assert server.category is not None

