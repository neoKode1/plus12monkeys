"""Tests for the agent template registry."""

from app.models.conversation import FrameworkChoice
from app.models.template import AgentTemplate
from app.services.template_registry import (
    get_template,
    get_template_for_framework,
    list_templates,
)


# ---------- list_templates ----------

def test_list_templates_returns_all():
    templates = list_templates()
    assert len(templates) >= 10  # We know there are 20 registered templates
    assert all(isinstance(t, AgentTemplate) for t in templates)


def test_list_templates_unique_ids():
    templates = list_templates()
    ids = [t.id for t in templates]
    assert len(ids) == len(set(ids)), "Template IDs must be unique"


# ---------- get_template ----------

def test_get_template_exists():
    tmpl = get_template("customer-service")
    assert tmpl is not None
    assert tmpl.id == "customer-service"
    assert tmpl.name == "Customer Service Agent"
    assert tmpl.framework == FrameworkChoice.CREWAI


def test_get_template_missing():
    assert get_template("nonexistent_template_xyz") is None


# ---------- get_template_for_framework ----------

def test_get_template_for_langgraph():
    tmpl = get_template_for_framework(FrameworkChoice.LANGGRAPH)
    assert tmpl is not None
    assert tmpl.framework == FrameworkChoice.LANGGRAPH


def test_get_template_for_crewai():
    tmpl = get_template_for_framework(FrameworkChoice.CREWAI)
    assert tmpl is not None
    assert tmpl.framework == FrameworkChoice.CREWAI


def test_get_template_for_autogen():
    tmpl = get_template_for_framework(FrameworkChoice.AUTOGEN)
    assert tmpl is not None
    assert tmpl.framework == FrameworkChoice.AUTOGEN


def test_get_template_for_vercel_ai_none():
    """No built-in templates use Vercel AI SDK yet."""
    tmpl = get_template_for_framework(FrameworkChoice.VERCEL_AI)
    assert tmpl is None


def test_get_template_for_rig_none():
    """No built-in templates use Rig yet."""
    tmpl = get_template_for_framework(FrameworkChoice.RIG)
    assert tmpl is None


def test_get_template_for_adk_go_none():
    """No built-in templates use ADK-Go yet."""
    tmpl = get_template_for_framework(FrameworkChoice.ADK_GO)
    assert tmpl is None


# ---------- Template data quality ----------

def test_templates_have_required_fields():
    """Every template must have id, name, description, category, framework, and agents."""
    for tmpl in list_templates():
        assert tmpl.id, f"Template missing id"
        assert tmpl.name, f"Template {tmpl.id} missing name"
        assert tmpl.description, f"Template {tmpl.id} missing description"
        assert tmpl.category is not None, f"Template {tmpl.id} missing category"
        assert tmpl.framework is not None, f"Template {tmpl.id} missing framework"
        assert len(tmpl.agents) > 0, f"Template {tmpl.id} has no agents"


def test_agents_have_role_and_goal():
    """Every agent in every template must have a role and goal."""
    for tmpl in list_templates():
        for agent in tmpl.agents:
            assert agent.role, f"Template {tmpl.id}: agent missing role"
            assert agent.goal, f"Template {tmpl.id}: agent {agent.role} missing goal"


def test_well_known_templates_exist():
    """Verify key template IDs exist."""
    expected = [
        "customer-service",
        "research",
        "code-generation",
        "data-analysis",
    ]
    for tid in expected:
        assert get_template(tid) is not None, f"Expected template '{tid}' to exist"

