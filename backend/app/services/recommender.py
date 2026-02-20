"""Rule-based recommendation engine.

Given extracted requirements, selects framework, MCP servers, and deployment target.
Now pulls MCP server metadata from the comprehensive registry service.
"""

from typing import Any, Dict, List

from app.models.conversation import (
    DeploymentTarget,
    ExtractedRequirements,
    FrameworkChoice,
    Recommendation,
)
from app.services.mcp_registry import get_server, list_servers


# Keyword → server_id mapping (fuzzy match helper)
_KEYWORD_TO_SERVER_ID: Dict[str, str] = {
    # --- original 17 ---
    "salesforce": "salesforce", "sfdc": "salesforce", "crm": "salesforce",
    "slack": "slack",
    "github": "github",
    "postgres": "postgres", "postgresql": "postgres", "sql": "postgres",
    "sqlite": "sqlite",
    "email": "email", "smtp": "email", "mail": "email",
    "search": "web-search", "brave search": "web-search", "google search": "web-search",
    "mongo": "mongodb", "mongodb": "mongodb",
    "notion": "notion",
    "drive": "google-drive", "google drive": "google-drive", "gdrive": "google-drive",
    "discord": "discord",
    "linear": "linear",
    "jira": "jira", "atlassian jira": "jira",
    "filesystem": "filesystem", "files": "filesystem", "file system": "filesystem",
    "arxiv": "arxiv", "papers": "arxiv", "academic papers": "arxiv",
    "huggingface": "huggingface", "hugging face": "huggingface", "hf": "huggingface",
    "breach": "breach", "intelligence": "breach", "facilities": "breach",
    "defense": "breach", "military": "breach", "clawbot": "breach",
    "research facilities": "breach", "knowledge graph": "breach",
    "satellite": "breach", "palantir": "breach",
    # --- official reference servers ---
    "fetch": "fetch", "web fetch": "fetch", "scrape": "fetch", "scraping": "fetch",
    "git": "git", "version control": "git", "git log": "git", "git diff": "git",
    "memory": "memory", "remember": "memory", "persistent memory": "memory",
    "sequential thinking": "sequential-thinking", "reasoning": "sequential-thinking",
    "chain of thought": "sequential-thinking", "thinking": "sequential-thinking",
    "time": "time", "timezone": "time", "clock": "time", "datetime": "time",
    # --- data / database ---
    "mysql": "mysql", "mariadb": "mysql",
    "redis": "redis", "cache": "redis", "key-value": "redis",
    "supabase": "supabase", "supabase db": "supabase",
    "snowflake": "snowflake", "data warehouse": "snowflake",
    "pinecone": "pinecone", "vector database": "pinecone", "vector db": "pinecone",
    "embeddings": "pinecone", "rag": "pinecone",
    "neo4j": "neo4j", "graph database": "neo4j", "cypher": "neo4j",
    # --- communication ---
    "twilio": "twilio", "sms": "twilio", "phone": "twilio", "voice": "twilio",
    "telegram": "telegram", "telegram bot": "telegram",
    "twitter": "twitter", "x": "twitter", "tweets": "twitter", "social media": "twitter",
    # --- dev tools ---
    "gitlab": "gitlab", "merge request": "gitlab",
    "sentry": "sentry", "error tracking": "sentry", "error monitoring": "sentry",
    "docker": "docker", "containers": "docker", "dockerfile": "docker",
    "kubernetes": "kubernetes", "k8s": "kubernetes", "pods": "kubernetes",
    "puppeteer": "puppeteer", "browser automation": "puppeteer", "screenshot": "puppeteer",
    "playwright": "playwright", "cross-browser": "playwright", "e2e testing": "playwright",
    "cloudflare": "cloudflare", "workers": "cloudflare", "cdn": "cloudflare",
    # --- productivity ---
    "google calendar": "google-calendar", "calendar": "google-calendar",
    "gcal": "google-calendar", "scheduling": "google-calendar",
    "trello": "trello", "kanban": "trello", "boards": "trello",
    "todoist": "todoist", "todo": "todoist", "tasks": "todoist",
    "confluence": "confluence", "wiki": "confluence", "atlassian confluence": "confluence",
    # --- search ---
    "tavily": "tavily", "ai search": "tavily",
    "exa": "exa", "neural search": "exa", "semantic search": "exa",
    # --- finance / commerce ---
    "stripe": "stripe", "payments": "stripe", "billing": "stripe",
    "subscriptions": "stripe", "invoices": "stripe",
    "shopify": "shopify", "ecommerce": "shopify", "e-commerce": "shopify",
    "online store": "shopify", "products": "shopify",
    # --- ai / ml ---
    "replicate": "replicate", "image generation": "replicate",
    "ml models": "replicate", "stable diffusion": "replicate",
    # --- cloud / infrastructure (critical) ---
    "aws": "aws", "amazon web services": "aws", "s3": "aws", "lambda": "aws",
    "ec2": "aws", "cloudformation": "aws", "cdk": "aws", "bedrock": "aws",
    "azure devops": "azure-devops", "azure pipelines": "azure-devops",
    "azure boards": "azure-devops", "azure repos": "azure-devops",
    "microsoft 365": "microsoft-365", "office 365": "microsoft-365",
    "outlook": "microsoft-365", "teams": "microsoft-365", "excel": "microsoft-365",
    "onedrive": "microsoft-365", "sharepoint": "microsoft-365",
    "bigquery": "bigquery", "big query": "bigquery", "google bigquery": "bigquery",
    # --- data (important gaps) ---
    "youtube": "youtube", "video transcripts": "youtube", "subtitles": "youtube",
    "airtable": "airtable", "air table": "airtable",
    "contentful": "contentful", "headless cms": "contentful", "cms": "contentful",
    "dynamodb": "dynamodb", "dynamo": "dynamodb", "dynamo db": "dynamodb",
    # --- productivity (important gaps) ---
    "obsidian": "obsidian", "obsidian notes": "obsidian", "pkm": "obsidian",
    "make": "make", "integromat": "make", "make.com": "make",
    # --- dev tools (important gaps) ---
    "postman": "postman", "api testing": "postman", "api collections": "postman",
    "sonarqube": "sonarqube", "sonar": "sonarqube", "code quality": "sonarqube",
    "static analysis": "sonarqube",
    # --- iot / media (important gaps) ---
    "home assistant": "home-assistant", "smart home": "home-assistant",
    "iot": "home-assistant", "hass": "home-assistant",
    "spotify": "spotify", "music": "spotify", "playlist": "spotify",
}

# Use-case → default framework
_USECASE_FRAMEWORK: Dict[str, FrameworkChoice] = {
    "customer_service": FrameworkChoice.CREWAI,
    "customer service": FrameworkChoice.CREWAI,
    "support": FrameworkChoice.CREWAI,
    "research": FrameworkChoice.LANGGRAPH,
    "data_analysis": FrameworkChoice.LANGGRAPH,
    "data analysis": FrameworkChoice.LANGGRAPH,
    "code_generation": FrameworkChoice.LANGGRAPH,
    "code generation": FrameworkChoice.LANGGRAPH,
    "coding": FrameworkChoice.LANGGRAPH,
    "multi_agent": FrameworkChoice.AUTOGEN,
    "multi-agent": FrameworkChoice.AUTOGEN,
    "collaboration": FrameworkChoice.AUTOGEN,
    "automation": FrameworkChoice.LANGGRAPH,
    # Content creation / media / video production
    "content_creation": FrameworkChoice.CREWAI,
    "content creation": FrameworkChoice.CREWAI,
    "content": FrameworkChoice.CREWAI,
    "video production": FrameworkChoice.CREWAI,
    "video": FrameworkChoice.CREWAI,
    "film": FrameworkChoice.CREWAI,
    "media": FrameworkChoice.CREWAI,
    "production pipeline": FrameworkChoice.CREWAI,
    "creative": FrameworkChoice.CREWAI,
    "storyboard": FrameworkChoice.CREWAI,
    # TypeScript / Vercel AI SDK targets
    "typescript": FrameworkChoice.VERCEL_AI,
    "nextjs": FrameworkChoice.VERCEL_AI,
    "next.js": FrameworkChoice.VERCEL_AI,
    "vercel": FrameworkChoice.VERCEL_AI,
    "node": FrameworkChoice.VERCEL_AI,
    "javascript": FrameworkChoice.VERCEL_AI,
    "frontend": FrameworkChoice.VERCEL_AI,
    "react": FrameworkChoice.VERCEL_AI,
    # Rust / Rig targets
    "rust": FrameworkChoice.RIG,
    "rig": FrameworkChoice.RIG,
    "cargo": FrameworkChoice.RIG,
    "tokio": FrameworkChoice.RIG,
    "systems programming": FrameworkChoice.RIG,
    "low-latency": FrameworkChoice.RIG,
    # Go / ADK-Go targets
    "go": FrameworkChoice.ADK_GO,
    "golang": FrameworkChoice.ADK_GO,
    "adk": FrameworkChoice.ADK_GO,
    "google adk": FrameworkChoice.ADK_GO,
    "concurrency": FrameworkChoice.ADK_GO,
    "goroutine": FrameworkChoice.ADK_GO,
}

_FRAMEWORK_REASONS: Dict[FrameworkChoice, str] = {
    FrameworkChoice.CREWAI: "CrewAI excels at role-based agent teams — ideal for workflows with distinct responsibilities like triage, specialist handling, and escalation.",
    FrameworkChoice.LANGGRAPH: "LangGraph provides fine-grained control over complex state machines and iterative workflows — great for research, analysis, and code generation.",
    FrameworkChoice.AUTOGEN: "AutoGen's group-chat paradigm is purpose-built for multi-agent collaboration where agents need to negotiate and iterate together.",
    FrameworkChoice.SEMANTIC_KERNEL: "Semantic Kernel offers enterprise-grade plugin architecture with strong .NET/Java interop — suited for large-scale enterprise integration.",
    FrameworkChoice.VERCEL_AI: "Vercel AI SDK provides a TypeScript-native agent framework with streaming, tool calling, and seamless Vercel/Next.js deployment — ideal for JavaScript/TypeScript developers.",
    FrameworkChoice.RIG: "Rig is Rust's leading async AI agent framework — perfect for high-performance, low-latency workloads where memory safety and zero-cost abstractions matter.",
    FrameworkChoice.ADK_GO: "Google ADK-Go brings Go's concurrency model (goroutines) to AI agents — ideal for scalable, cloud-native services that need strong typing and fast compilation.",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_integrations(raw: List[str]) -> List[Dict[str, Any]]:
    """Map user-mentioned integration names to real MCP registry entries."""
    resolved: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for term in raw:
        server_id = _KEYWORD_TO_SERVER_ID.get(term.lower().strip())
        if server_id and server_id not in seen:
            seen.add(server_id)
            entry = get_server(server_id)
            if entry:
                resolved.append({
                    "name": entry.name,
                    "command": entry.command,
                    "args": entry.args,
                    "required_env": entry.required_env,
                    "category": entry.category.value,
                    "tools_count": len(entry.tools),
                    "icon": entry.icon,
                    "npm_package": entry.npm_package,
                })
    return resolved


def pick_framework(reqs: ExtractedRequirements) -> FrameworkChoice:
    """Choose the best framework given the extracted requirements."""
    if reqs.framework_preference:
        return reqs.framework_preference
    if reqs.use_case:
        uc = reqs.use_case.lower().strip()
        for keyword, fw in _USECASE_FRAMEWORK.items():
            if keyword in uc:
                return fw
    return FrameworkChoice.LANGGRAPH  # sensible default


def pick_deployment(reqs: ExtractedRequirements) -> DeploymentTarget:
    """Choose deployment target."""
    if reqs.deployment_preference:
        return reqs.deployment_preference
    scale = (reqs.scale or "").lower()
    if scale in ("high", "enterprise"):
        return DeploymentTarget.CLOUD
    return DeploymentTarget.CLOUD  # cloud-first default


def _default_agents(framework: FrameworkChoice) -> List[Dict[str, Any]]:
    """Return sensible default agent roles for a given framework."""
    if framework == FrameworkChoice.CREWAI:
        return [
            {"role": "triage", "goal": "Classify and route incoming requests"},
            {"role": "specialist", "goal": "Handle domain-specific queries"},
            {"role": "escalation", "goal": "Escalate complex issues to humans"},
        ]
    elif framework == FrameworkChoice.AUTOGEN:
        return [
            {"role": "coordinator", "goal": "Manage group conversation flow"},
            {"role": "worker_1", "goal": "Execute primary tasks"},
            {"role": "critic", "goal": "Review and validate outputs"},
        ]
    elif framework == FrameworkChoice.VERCEL_AI:
        return [
            {"role": "planner", "goal": "Break down tasks into actionable steps"},
            {"role": "executor", "goal": "Execute each step and return results"},
        ]
    elif framework == FrameworkChoice.RIG:
        return [
            {"role": "planner", "goal": "Decompose tasks into async pipeline stages"},
            {"role": "executor", "goal": "Execute each stage with zero-copy efficiency"},
        ]
    elif framework == FrameworkChoice.ADK_GO:
        return [
            {"role": "planner", "goal": "Divide work into concurrent goroutine tasks"},
            {"role": "executor", "goal": "Execute tasks in parallel and merge results"},
        ]
    else:  # langgraph / semantic-kernel
        return [
            {"role": "planner", "goal": "Break down tasks into steps"},
            {"role": "executor", "goal": "Execute each step"},
        ]


def build_recommendation(reqs: ExtractedRequirements) -> Recommendation:
    """Produce a full Recommendation from extracted requirements."""
    framework = pick_framework(reqs)
    deployment = pick_deployment(reqs)
    mcp_servers = resolve_integrations(reqs.integrations)

    # Use custom agents from the user's request when provided;
    # fall back to framework-specific defaults otherwise.
    if reqs.custom_agents:
        agents = [
            {
                "role": a.get("role", "agent"),
                "goal": a.get("goal", ""),
                **({"backstory": a["backstory"]} if a.get("backstory") else {}),
            }
            for a in reqs.custom_agents
        ]
    else:
        agents = _default_agents(framework)

    return Recommendation(
        framework=framework,
        framework_reason=_FRAMEWORK_REASONS[framework],
        agents=agents,
        mcp_servers=mcp_servers,
        deployment=deployment,
        estimated_monthly_cost="$50-150/month" if deployment == DeploymentTarget.CLOUD else "Free (local)",
        summary=(
            f"A {framework.value}-based agent with {len(agents)} roles, "
            f"{len(mcp_servers)} MCP integration(s), deployed to {deployment.value}."
        ),
    )
