"""Pydantic models for the MCP integration layer."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPCategory(str, Enum):
    DATA = "data"
    COMMUNICATION = "communication"
    DEV_TOOLS = "dev-tools"
    PRODUCTIVITY = "productivity"
    SEARCH = "search"
    AI_ML = "ai-ml"
    FINANCE = "finance"
    INTELLIGENCE = "intelligence"
    CUSTOM = "custom"


class MCPServerStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    CHECKING = "checking"


class ToolSafetyLevel(str, Enum):
    """Safety classification for tool auto-run decisions (inspired by Windsurf)."""
    SAFE = "safe"            # Read-only: search, view, list — auto-run OK
    MODERATE = "moderate"    # Additive: create file, add code — auto-run with logging
    DANGEROUS = "dangerous"  # Destructive: delete, deploy, push — require confirmation


class MCPToolSchema(BaseModel):
    """Schema for a single tool exposed by an MCP server."""
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    safety_level: ToolSafetyLevel = ToolSafetyLevel.SAFE
    task_name_active: Optional[str] = None   # UI label while running (v0 pattern)
    task_name_complete: Optional[str] = None  # UI label when done (v0 pattern)


class MCPServerEntry(BaseModel):
    """Full metadata for a single MCP server in the registry."""
    id: str
    name: str
    description: str
    category: MCPCategory
    command: str = "npx"
    args: List[str] = Field(default_factory=list)
    endpoint_url: Optional[str] = None  # For HTTP/SSE MCP servers (non-stdio)
    required_env: List[str] = Field(default_factory=list)
    optional_env: List[str] = Field(default_factory=list)
    npm_package: Optional[str] = None
    documentation_url: Optional[str] = None
    icon: Optional[str] = None  # emoji or icon name
    tags: List[str] = Field(default_factory=list)
    status: MCPServerStatus = MCPServerStatus.UNKNOWN
    tools: List[MCPToolSchema] = Field(default_factory=list)
    last_health_check: Optional[datetime] = None
    is_official: bool = False


class MCPHealthResult(BaseModel):
    """Result of a health check against an MCP server."""
    server_id: str
    status: MCPServerStatus
    tools_count: int = 0
    tools: List[MCPToolSchema] = Field(default_factory=list)
    response_time_ms: float = 0
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CredentialEntry(BaseModel):
    """A single environment variable credential for a project."""
    key: str
    value: str  # encrypted at rest
    server_id: str  # which MCP server this belongs to


class ProjectCredentials(BaseModel):
    """All credentials for a specific project/session."""
    project_id: str
    credentials: List[CredentialEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- API request / response ----------

class CredentialSetRequest(BaseModel):
    """Request to set credentials for a project."""
    project_id: str
    credentials: Dict[str, str]  # {ENV_VAR_NAME: value}
    server_id: str


class MCPServerListResponse(BaseModel):
    """Paginated list of MCP servers."""
    servers: List[MCPServerEntry]
    total: int
    categories: List[str] = Field(default_factory=list)

