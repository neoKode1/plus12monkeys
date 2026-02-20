"""Tests for the code generation engine."""

import pytest

from app.models.conversation import DeploymentTarget, FrameworkChoice
from app.models.template import (
    AgentRole,
    GeneratedPackage,
    GenerateRequest,
    MCPServerConfig,
)
from app.services.code_generator import (
    _build_context,
    _collect_env_vars,
    _is_go,
    _is_rust,
    _is_typescript,
    _safe_name,
    generate_mcp_wrapper,
    generate_package,
)
from app.services.template_registry import get_template


# ---------- Language detection helpers ----------

def test_is_typescript_vercel():
    assert _is_typescript(FrameworkChoice.VERCEL_AI) is True

def test_is_typescript_langgraph():
    assert _is_typescript(FrameworkChoice.LANGGRAPH) is False

def test_is_rust_rig():
    assert _is_rust(FrameworkChoice.RIG) is True

def test_is_rust_crewai():
    assert _is_rust(FrameworkChoice.CREWAI) is False

def test_is_go_adk():
    assert _is_go(FrameworkChoice.ADK_GO) is True

def test_is_go_langgraph():
    assert _is_go(FrameworkChoice.LANGGRAPH) is False


# ---------- _collect_env_vars ----------

def test_collect_env_vars_empty():
    result = _collect_env_vars([])
    assert result == ["ANTHROPIC_API_KEY"]

def test_collect_env_vars_deduplicates():
    servers = [
        MCPServerConfig(name="a", command="npx", required_env=["KEY_A", "KEY_B"]),
        MCPServerConfig(name="b", command="npx", required_env=["KEY_B", "KEY_C"]),
    ]
    result = _collect_env_vars(servers)
    assert result == ["ANTHROPIC_API_KEY", "KEY_A", "KEY_B", "KEY_C"]

def test_collect_env_vars_no_duplicate_anthropic():
    servers = [
        MCPServerConfig(name="a", command="npx", required_env=["ANTHROPIC_API_KEY"]),
    ]
    result = _collect_env_vars(servers)
    assert result.count("ANTHROPIC_API_KEY") == 1


# ---------- _safe_name ----------

def test_safe_name_basic():
    assert _safe_name("my-repo") == "my_repo"

def test_safe_name_dots():
    assert _safe_name("org.project.name") == "org_project_name"

def test_safe_name_strips_leading_trailing():
    assert _safe_name("---hello---") == "hello"

def test_safe_name_uppercase():
    assert _safe_name("MyRepo") == "myrepo"


# ---------- _build_context ----------

def test_build_context_basic():
    template = get_template("customer-service")
    assert template is not None
    req = GenerateRequest(template_id="customer-service", project_name="test-project")
    ctx = _build_context(template, req)
    assert ctx["project_name"] == "test-project"
    assert ctx["framework"] == "crewai"
    assert ctx["deployment"] == "local"
    assert len(ctx["agents"]) > 0
    assert "ANTHROPIC_API_KEY" in ctx["env_vars"]

def test_build_context_custom_agents_override():
    template = get_template("customer-service")
    assert template is not None
    custom = [AgentRole(role="bot", goal="Do stuff")]
    req = GenerateRequest(
        template_id="customer-service",
        project_name="test",
        agents=[custom[0]],
    )
    ctx = _build_context(template, req)
    assert len(ctx["agents"]) == 1
    assert ctx["agents"][0]["role"] == "bot"

def test_build_context_target_app():
    template = get_template("customer-service")
    assert template is not None
    req = GenerateRequest(
        template_id="customer-service",
        project_name="test",
        config={"target_app": {"name": "my-app", "language": "python"}},
    )
    ctx = _build_context(template, req)
    assert ctx["target_app"]["name"] == "my-app"


# ---------- generate_package ----------

def test_generate_package_crewai():
    req = GenerateRequest(template_id="customer-service", project_name="test-pkg")
    pkg = generate_package(req)
    assert isinstance(pkg, GeneratedPackage)
    assert pkg.project_name == "test-pkg"
    assert pkg.framework == FrameworkChoice.CREWAI
    paths = [f.path for f in pkg.files]
    assert "agent.py" in paths
    assert "requirements.txt" in paths
    assert "README.md" in paths
    assert ".env.example" in paths

def test_generate_package_langgraph():
    req = GenerateRequest(template_id="research", project_name="research-pkg")
    pkg = generate_package(req)
    assert pkg.framework == FrameworkChoice.LANGGRAPH
    assert len(pkg.files) > 0
    assert len(pkg.setup_instructions) > 0

def test_generate_package_invalid_template():
    req = GenerateRequest(template_id="nonexistent-xyz", project_name="test")
    with pytest.raises(ValueError, match="not found"):
        generate_package(req)


# ---------- generate_mcp_wrapper ----------

def test_generate_mcp_wrapper():
    analysis = {
        "name": "cool-repo",
        "url": "https://github.com/owner/cool-repo",
        "owner": "owner",
        "description": "A cool repo",
        "primary_language": "python",
        "entry_points": ["main.py"],
    }
    pkg = generate_mcp_wrapper(analysis, project_name="cool-mcp")
    assert isinstance(pkg, GeneratedPackage)
    assert pkg.project_name == "cool-mcp"
    paths = [f.path for f in pkg.files]
    assert "mcp_server.py" in paths
    assert "mcp-config.json" in paths
    assert ".env.example" in paths

def test_generate_mcp_wrapper_default_name():
    analysis = {"name": "my-lib", "url": "https://github.com/x/my-lib", "owner": "x"}
    pkg = generate_mcp_wrapper(analysis)
    assert pkg.project_name == "my-lib-mcp"

