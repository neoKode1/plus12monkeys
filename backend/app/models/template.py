"""Models for agent templates and code generation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.conversation import DeploymentTarget, FrameworkChoice


# ---------- Enums ----------

class TemplateCategory(str, Enum):
    CUSTOMER_SERVICE = "customer-service"
    RESEARCH = "research"
    DATA_ANALYSIS = "data-analysis"
    CODE_GENERATION = "code-generation"
    MULTI_AGENT = "multi-agent"
    SALES_MARKETING = "sales-marketing"
    CONTENT_CREATION = "content-creation"
    E_COMMERCE = "e-commerce"
    OPERATIONS = "operations"
    HEALTHCARE = "healthcare"
    REAL_ESTATE = "real-estate"
    EDUCATION = "education"
    STEM_EDUCATION = "stem-education"
    FINANCE = "finance"
    MILITARY = "military"
    MEDICAL = "medical"
    CUSTOM = "custom"


# ---------- Sub-models ----------

class AgentRole(BaseModel):
    """A single role within a multi-agent template."""
    role: str
    goal: str
    backstory: Optional[str] = None
    tools: List[str] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    """MCP server configuration within a template."""
    name: str
    command: str
    args: List[str] = Field(default_factory=list)
    required_env: List[str] = Field(default_factory=list)
    category: str = "tools"


class TemplateField(BaseModel):
    """A configurable field within a template."""
    name: str
    label: str
    field_type: str = "text"  # text, select, multiselect, boolean, number
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[str]] = None
    description: Optional[str] = None


# ---------- Core template model ----------

class AgentTemplate(BaseModel):
    """A reusable agent template definition."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    framework: FrameworkChoice
    version: str = "1.0.0"
    agents: List[AgentRole] = Field(default_factory=list)
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    deployment_options: List[DeploymentTarget] = Field(
        default_factory=lambda: [DeploymentTarget.LOCAL, DeploymentTarget.CLOUD, DeploymentTarget.EXPORT]
    )
    required_fields: List[TemplateField] = Field(default_factory=list)
    optional_fields: List[TemplateField] = Field(default_factory=list)
    estimated_cost: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------- Generation request / response ----------

class GenerateRequest(BaseModel):
    """Request to generate an agent package from a template."""
    template_id: str
    config: Dict[str, Any] = Field(default_factory=dict)
    deployment: DeploymentTarget = DeploymentTarget.LOCAL
    project_name: str = "my-agent"
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    agents: List[AgentRole] = Field(default_factory=list)


class GeneratedFile(BaseModel):
    """A single file in the generated package."""
    path: str
    content: str
    language: str = "python"


class GeneratedPackage(BaseModel):
    """The complete generated agent package."""
    project_name: str
    template_id: str
    framework: FrameworkChoice
    deployment: DeploymentTarget
    files: List[GeneratedFile] = Field(default_factory=list)
    summary: str = ""
    setup_instructions: List[str] = Field(default_factory=list)
    env_vars: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

