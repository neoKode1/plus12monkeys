"""Code generation engine — renders agent templates into deployable packages.

Uses Jinja2 templates to produce framework-specific code in Python, TypeScript,
Rust, or Go, plus Docker configs, Kubernetes manifests, AWS SAM templates,
cloud deployment configs, environment files, and setup instructions.

Supported languages / frameworks:
  Python     — LangGraph, CrewAI, AutoGen, Semantic Kernel
  TypeScript — Vercel AI SDK
  Rust       — Rig (async AI agent framework)
  Go         — Google ADK-Go
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.conversation import DeploymentTarget, FrameworkChoice
from app.models.template import (
    AgentRole,
    AgentTemplate,
    GeneratedFile,
    GeneratedPackage,
    GenerateRequest,
    MCPServerConfig,
)
from app.services.template_registry import get_template

logger = logging.getLogger(__name__)

# Jinja2 environment — looks for *.j2 files in app/templates/
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape([]),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def _render(template_name: str, ctx: Dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context."""
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**ctx)


def _build_context(
    template: AgentTemplate,
    req: GenerateRequest,
) -> Dict[str, Any]:
    """Build the Jinja2 rendering context from template + request."""
    agents = req.agents if req.agents else template.agents
    mcp_servers = req.mcp_servers if req.mcp_servers else template.mcp_servers
    ctx = {
        "project_name": req.project_name,
        "framework": template.framework.value,
        "deployment": req.deployment.value,
        "category": template.category.value,
        "template_name": template.name,
        "template_description": template.description,
        "agents": [a.model_dump() for a in agents],
        "mcp_servers": [s.model_dump() for s in mcp_servers],
        "config": req.config,
        "env_vars": _collect_env_vars(mcp_servers),
    }
    # When integrating into an existing app, surface target app info so
    # templates can reference it (e.g. in comments, README, config).
    target_app = req.config.get("target_app") if isinstance(req.config, dict) else None
    if target_app:
        ctx["target_app"] = target_app
    return ctx


def _collect_env_vars(servers: List[MCPServerConfig]) -> List[str]:
    """Collect all required env vars across MCP servers."""
    env_vars = ["ANTHROPIC_API_KEY"]
    seen = set(env_vars)
    for s in servers:
        for var in s.required_env:
            if var not in seen:
                env_vars.append(var)
                seen.add(var)
    return env_vars


# ---------------------------------------------------------------------------
# Language detection helpers
# ---------------------------------------------------------------------------
_TS_FRAMEWORKS = {FrameworkChoice.VERCEL_AI}
_RS_FRAMEWORKS = {FrameworkChoice.RIG}
_GO_FRAMEWORKS = {FrameworkChoice.ADK_GO}


def _is_typescript(framework: FrameworkChoice) -> bool:
    """Return True if the framework targets TypeScript/Node.js."""
    return framework in _TS_FRAMEWORKS


def _is_rust(framework: FrameworkChoice) -> bool:
    """Return True if the framework targets Rust."""
    return framework in _RS_FRAMEWORKS


def _is_go(framework: FrameworkChoice) -> bool:
    """Return True if the framework targets Go."""
    return framework in _GO_FRAMEWORKS


def _generate_agent_code(
    template: AgentTemplate,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate the main agent source file (Python, TypeScript, Rust, or Go)."""
    fw = template.framework
    if _is_typescript(fw):
        tmpl_name = f"{fw.value.replace('-', '_')}_agent.ts.j2"
        out_path, lang = "agent.ts", "typescript"
    elif _is_rust(fw):
        tmpl_name = f"{fw.value.replace('-', '_')}_agent.rs.j2"
        out_path, lang = "src/main.rs", "rust"
    elif _is_go(fw):
        tmpl_name = f"{fw.value.replace('-', '_')}_agent.go.j2"
        out_path, lang = "main.go", "go"
    else:
        tmpl_name = f"{fw.value.replace('-', '_')}_agent.py.j2"
        out_path, lang = "agent.py", "python"
    try:
        code = _render(tmpl_name, ctx)
        files.append(GeneratedFile(path=out_path, content=code, language=lang))
    except Exception as exc:
        logger.warning("No agent template for %s: %s", tmpl_name, exc)


def _generate_deps(
    template: AgentTemplate,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate dependency manifest (requirements.txt / package.json / Cargo.toml / go.mod)."""
    fw = template.framework
    if _is_typescript(fw):
        files.append(GeneratedFile(
            path="package.json",
            content=_render("package_json.j2", ctx),
            language="json",
        ))
        files.append(GeneratedFile(
            path="tsconfig.json",
            content=_render("tsconfig_json.j2", ctx),
            language="json",
        ))
    elif _is_rust(fw):
        files.append(GeneratedFile(
            path="Cargo.toml",
            content=_render("cargo_toml.j2", ctx),
            language="toml",
        ))
    elif _is_go(fw):
        files.append(GeneratedFile(
            path="go.mod",
            content=_render("go_mod.j2", ctx),
            language="text",
        ))
    else:
        files.append(GeneratedFile(
            path="requirements.txt",
            content=_render("requirements.txt.j2", ctx),
            language="text",
        ))


def _generate_docker(
    template: AgentTemplate,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate Dockerfile + docker-compose.yml (Python / Node / Rust / Go variant)."""
    fw = template.framework
    if _is_typescript(fw):
        dockerfile_tmpl = "Dockerfile_node.j2"
    elif _is_rust(fw):
        dockerfile_tmpl = "Dockerfile_rust.j2"
    elif _is_go(fw):
        dockerfile_tmpl = "Dockerfile_go.j2"
    else:
        dockerfile_tmpl = "Dockerfile.j2"
    files.append(GeneratedFile(
        path="Dockerfile",
        content=_render(dockerfile_tmpl, ctx),
        language="dockerfile",
    ))
    files.append(GeneratedFile(
        path="docker-compose.yml",
        content=_render("docker_compose.yml.j2", ctx),
        language="yaml",
    ))


def _generate_deploy_configs(
    deployment: DeploymentTarget,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate cloud deployment configs when deployment != LOCAL."""
    if deployment in (DeploymentTarget.CLOUD, DeploymentTarget.EXPORT):
        try:
            files.append(GeneratedFile(
                path="railway.toml",
                content=_render("railway_toml.j2", ctx),
                language="toml",
            ))
        except Exception as exc:
            logger.warning("Could not render railway.toml: %s", exc)
        try:
            files.append(GeneratedFile(
                path="render.yaml",
                content=_render("render_yaml.j2", ctx),
                language="yaml",
            ))
        except Exception as exc:
            logger.warning("Could not render render.yaml: %s", exc)
        try:
            files.append(GeneratedFile(
                path="vercel.json",
                content=_render("vercel_json.j2", ctx),
                language="json",
            ))
        except Exception as exc:
            logger.warning("Could not render vercel.json: %s", exc)


def _generate_k8s_manifests(
    deployment: DeploymentTarget,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate Kubernetes manifests when deployment is CLOUD or EXPORT."""
    if deployment in (DeploymentTarget.CLOUD, DeploymentTarget.EXPORT):
        try:
            files.append(GeneratedFile(
                path="k8s/deployment.yaml",
                content=_render("k8s_deployment.yaml.j2", ctx),
                language="yaml",
            ))
            files.append(GeneratedFile(
                path="k8s/service.yaml",
                content=_render("k8s_service.yaml.j2", ctx),
                language="yaml",
            ))
        except Exception as exc:
            logger.warning("Could not render K8s manifests: %s", exc)


def _generate_sam_template(
    deployment: DeploymentTarget,
    ctx: Dict[str, Any],
    files: List[GeneratedFile],
) -> None:
    """Generate AWS SAM template when deployment is CLOUD or EXPORT."""
    if deployment in (DeploymentTarget.CLOUD, DeploymentTarget.EXPORT):
        try:
            files.append(GeneratedFile(
                path="sam/template.yaml",
                content=_render("sam_template.yaml.j2", ctx),
                language="yaml",
            ))
        except Exception as exc:
            logger.warning("Could not render SAM template: %s", exc)


# ---------------------------------------------------------------------------
# Language label helpers
# ---------------------------------------------------------------------------
_LANG_LABELS = {
    FrameworkChoice.VERCEL_AI: "TypeScript (Vercel AI SDK)",
    FrameworkChoice.RIG: "Rust (Rig)",
    FrameworkChoice.ADK_GO: "Go (ADK-Go)",
}


def generate_package(req: GenerateRequest) -> GeneratedPackage:
    """Generate a full agent package from a template + configuration.

    Returns a GeneratedPackage with all files ready to download or deploy.
    Supports Python, TypeScript, Rust, and Go frameworks.  Cloud/Export
    deployments include Railway, Render, Vercel, Kubernetes, and AWS SAM configs.
    """
    template = get_template(req.template_id)
    if not template:
        raise ValueError(f"Template '{req.template_id}' not found")

    ctx = _build_context(template, req)
    files: List[GeneratedFile] = []
    fw = template.framework

    # 1. Main agent code — framework-specific (Python / TypeScript / Rust / Go)
    _generate_agent_code(template, ctx, files)

    # 2. Dependencies (requirements.txt / package.json / Cargo.toml / go.mod)
    _generate_deps(template, ctx, files)

    # 3. Dockerfile + docker-compose.yml
    _generate_docker(template, ctx, files)

    # 4. .env.example
    files.append(GeneratedFile(
        path=".env.example",
        content=_render("env_example.j2", ctx),
        language="text",
    ))

    # 5. MCP config
    files.append(GeneratedFile(
        path="mcp-config.json",
        content=_render("mcp_config.json.j2", ctx),
        language="json",
    ))

    # 6. Cloud deployment configs (Railway, Render, Vercel) — when not LOCAL
    _generate_deploy_configs(req.deployment, ctx, files)

    # 7. Kubernetes manifests — when CLOUD or EXPORT
    _generate_k8s_manifests(req.deployment, ctx, files)

    # 8. AWS SAM template — when CLOUD or EXPORT
    _generate_sam_template(req.deployment, ctx, files)

    # 9. README
    files.append(GeneratedFile(
        path="README.md",
        content=_render("readme.md.j2", ctx),
        language="markdown",
    ))

    # Build setup instructions — language-aware
    if _is_typescript(fw):
        setup = [
            "cp .env.example .env",
            "Fill in the required environment variables in .env",
            "npm install",
            "npx tsx agent.ts",
        ]
    elif _is_rust(fw):
        setup = [
            "cp .env.example .env",
            "Fill in the required environment variables in .env",
            "cargo build --release",
            "./target/release/$(basename $PWD)",
        ]
    elif _is_go(fw):
        setup = [
            "cp .env.example .env",
            "Fill in the required environment variables in .env",
            "go build -o agent .",
            "./agent",
        ]
    else:
        setup = [
            "cp .env.example .env",
            "Fill in the required environment variables in .env",
            "pip install -r requirements.txt",
            "python agent.py",
        ]
    if req.deployment == DeploymentTarget.LOCAL:
        setup = ["docker compose up --build"] + setup

    lang_label = _LANG_LABELS.get(fw, template.framework.value)
    return GeneratedPackage(
        project_name=req.project_name,
        template_id=req.template_id,
        framework=template.framework,
        deployment=req.deployment,
        files=files,
        summary=f"Generated {template.name} using {lang_label} with {len(ctx['mcp_servers'])} MCP integration(s).",
        setup_instructions=setup,
        env_vars=ctx["env_vars"],
    )


# ---------------------------------------------------------------------------
# Repo-to-MCP wrapper generation
# ---------------------------------------------------------------------------

def _safe_name(name: str) -> str:
    """Convert a repo name to a Python-safe identifier."""
    return re.sub(r"[^a-zA-Z0-9]", "_", name).strip("_").lower()


def generate_mcp_wrapper(
    repo_analysis: Dict[str, Any],
    project_name: Optional[str] = None,
    deployment: DeploymentTarget = DeploymentTarget.LOCAL,
) -> GeneratedPackage:
    """Generate an MCP server package that wraps an external repository.

    Uses repo_analysis (from repo_analyzer) to produce a complete MCP server
    that clones the target repo and exposes its functionality as MCP tools.
    """
    repo_name = repo_analysis.get("name", "repo")
    repo_url = repo_analysis.get("url", "")
    owner = repo_analysis.get("owner", "unknown")
    repo_name_safe = _safe_name(repo_name)
    pname = project_name or f"{repo_name}-mcp"

    ctx = {
        "project_name": pname,
        "repo_name": repo_name,
        "repo_name_safe": repo_name_safe,
        "repo_url": repo_url,
        "repo_description": repo_analysis.get("description", f"MCP wrapper for {owner}/{repo_name}"),
        "primary_language": repo_analysis.get("primary_language", "python"),
        "detected_framework": repo_analysis.get("detected_framework", ""),
        "entry_points": repo_analysis.get("entry_points", []),
        "tree_summary": repo_analysis.get("tree_summary", []),
        "languages": repo_analysis.get("languages", []),
    }

    files: List[GeneratedFile] = []

    # 1. MCP server wrapper
    try:
        files.append(GeneratedFile(
            path="mcp_server.py",
            content=_render("mcp_wrapper.py.j2", ctx),
            language="python",
        ))
    except Exception as exc:
        logger.error("Failed to render MCP wrapper: %s", exc)

    # 2. Requirements
    try:
        files.append(GeneratedFile(
            path="requirements.txt",
            content=_render("mcp_wrapper_requirements.txt.j2", ctx),
            language="text",
        ))
    except Exception as exc:
        logger.warning("Failed to render wrapper requirements: %s", exc)

    # 3. .env.example
    env_content = f"""# +12 Monkeys MCP Wrapper — {owner}/{repo_name}
# Add any API keys the wrapped repo needs below

# Where to clone the repo (defaults to ./{repo_name})
# REPO_DIR=./{repo_name}

# ANTHROPIC_API_KEY=sk-...
"""
    files.append(GeneratedFile(path=".env.example", content=env_content, language="text"))

    # 4. MCP client config
    mcp_config = {
        "mcpServers": {
            pname: {
                "command": "python",
                "args": ["mcp_server.py"],
            }
        }
    }
    files.append(GeneratedFile(
        path="mcp-config.json",
        content=json.dumps(mcp_config, indent=2),
        language="json",
    ))

    # 5. Dockerfile
    dockerfile = f"""FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "mcp_server.py"]
"""
    files.append(GeneratedFile(path="Dockerfile", content=dockerfile, language="dockerfile"))

    # 6. README
    try:
        files.append(GeneratedFile(
            path="README.md",
            content=_render("mcp_wrapper_readme.md.j2", ctx),
            language="markdown",
        ))
    except Exception as exc:
        logger.warning("Failed to render wrapper README: %s", exc)

    setup = [
        "cp .env.example .env",
        "Fill in any API keys the wrapped repo needs",
        "pip install -r requirements.txt",
        "python mcp_server.py",
    ]

    return GeneratedPackage(
        project_name=pname,
        template_id="repo-mcp-wrapper",
        framework=FrameworkChoice.LANGGRAPH,  # default; wrapper is framework-agnostic
        deployment=deployment,
        files=files,
        summary=f"MCP server wrapper for {owner}/{repo_name} — exposes repo functionality as MCP tools.",
        setup_instructions=setup,
        env_vars=["ANTHROPIC_API_KEY"],
    )
