"""Direct generation API — bypass the conversation flow.

Exposes a single POST endpoint that takes a repo URL + output type
and returns a GeneratedPackage directly. This is the backend for the
+12 Monkeys SDK client.
"""

import logging
from dataclasses import asdict
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.conversation import DeploymentTarget
from app.models.template import GeneratedPackage
from app.services.code_generator import generate_mcp_wrapper, generate_sdk_package
from app.services.repo_analyzer import analyze_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


# ---------- Request / Response models ----------

class OutputType(str, Enum):
    MCP = "mcp"
    SDK = "sdk"


class GenerateDirectRequest(BaseModel):
    """Request body for direct generation."""
    repo_url: str = Field(..., description="GitHub or HuggingFace repo URL")
    output_type: OutputType = Field(OutputType.MCP, description="'mcp' for MCP server, 'sdk' for SDK package")
    project_name: Optional[str] = Field(None, description="Override the auto-generated project name")
    deployment: DeploymentTarget = Field(DeploymentTarget.EXPORT, description="Deployment target")


class GenerateDirectResponse(BaseModel):
    """Wraps GeneratedPackage with analysis metadata."""
    package: GeneratedPackage
    repo_name: str
    repo_owner: str
    repo_description: str
    primary_language: str


# ---------- Endpoint ----------

@router.post("", response_model=GenerateDirectResponse)
async def generate_direct(body: GenerateDirectRequest):
    """Analyze a repo and generate an MCP server or SDK package in one call.

    This is the programmatic API used by the +12 Monkeys SDK.
    No conversation session required.
    """
    # 1. Analyze the repo
    logger.info("Direct generate: %s → %s", body.repo_url, body.output_type.value)
    try:
        analysis = await analyze_repo(body.repo_url)
    except Exception as exc:
        logger.exception("Repo analysis failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Failed to analyze repo: {exc}") from exc

    if analysis.error:
        raise HTTPException(status_code=422, detail=f"Repo analysis error: {analysis.error}")

    # 2. Convert dataclass → dict for the generator
    analysis_dict = asdict(analysis)

    # 3. Generate
    try:
        if body.output_type == OutputType.MCP:
            package = generate_mcp_wrapper(
                repo_analysis=analysis_dict,
                project_name=body.project_name,
                deployment=body.deployment,
            )
        else:
            package = generate_sdk_package(
                repo_analysis=analysis_dict,
                project_name=body.project_name,
                deployment=body.deployment,
            )
    except Exception as exc:
        logger.exception("Code generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc

    return GenerateDirectResponse(
        package=package,
        repo_name=analysis.name,
        repo_owner=analysis.owner,
        repo_description=analysis.description,
        primary_language=analysis.primary_language,
    )

