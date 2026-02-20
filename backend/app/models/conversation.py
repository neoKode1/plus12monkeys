"""Models for the conversational wizard – sessions, messages, and extracted requirements."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------- Enums ----------

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    GATHERING = "gathering"       # Still collecting requirements
    RECOMMENDING = "recommending" # Ready to present recommendation
    CONFIRMED = "confirmed"       # User accepted the recommendation
    GENERATING = "generating"     # Code generation in progress
    COMPLETE = "complete"         # Done


class FrameworkChoice(str, Enum):
    LANGGRAPH = "langgraph"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    SEMANTIC_KERNEL = "semantic-kernel"
    VERCEL_AI = "vercel-ai"
    RIG = "rig"           # Rust — rig crate (async AI agent framework)
    ADK_GO = "adk-go"     # Go — Google Agent Development Kit


class DeploymentTarget(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    EXPORT = "export"


# ---------- Sub-models ----------

class Message(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractedRequirements(BaseModel):
    """Structured requirements extracted from conversation by the orchestrator."""
    use_case: Optional[str] = None
    description: Optional[str] = None
    integrations: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    scale: Optional[str] = None          # low, medium, high
    compliance: List[str] = Field(default_factory=list)
    framework_preference: Optional[FrameworkChoice] = None
    deployment_preference: Optional[DeploymentTarget] = None
    additional_notes: Optional[str] = None
    # Repo-to-MCP/SDK fields
    repo_url: Optional[str] = None
    repo_analysis: Optional[Dict[str, Any]] = None


class Recommendation(BaseModel):
    """Architecture recommendation produced by the orchestrator."""
    framework: FrameworkChoice
    framework_reason: str
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    mcp_servers: List[Dict[str, Any]] = Field(default_factory=list)
    deployment: DeploymentTarget
    estimated_monthly_cost: Optional[str] = None
    summary: str


# ---------- Session ----------

class WizardSession(BaseModel):
    """Full state of a single wizard conversation."""
    session_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    status: SessionStatus = SessionStatus.GATHERING
    messages: List[Message] = Field(default_factory=list)
    requirements: ExtractedRequirements = Field(default_factory=ExtractedRequirements)
    recommendation: Optional[Recommendation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------- API request / response ----------

class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    session_id: Optional[str] = None   # None = start new session
    message: str


class ChatResponse(BaseModel):
    """Response returned to the frontend."""
    session_id: str
    reply: str
    status: SessionStatus
    requirements: Optional[ExtractedRequirements] = None
    recommendation: Optional[Recommendation] = None

