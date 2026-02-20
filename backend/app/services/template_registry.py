"""In-memory registry of built-in agent templates.

Provides the 12 built-in templates and lookup helpers used by the code generator.
"""

from typing import Dict, List, Optional

from app.models.conversation import DeploymentTarget, FrameworkChoice
from app.models.template import (
    AgentRole,
    AgentTemplate,
    MCPServerConfig,
    TemplateCategory,
    TemplateField,
)

# ---------------------------------------------------------------------------
# Core templates
# ---------------------------------------------------------------------------

_TEMPLATES: Dict[str, AgentTemplate] = {}


def _register(t: AgentTemplate) -> None:
    _TEMPLATES[t.id] = t


# 1. Customer Service Agent (CrewAI)
_register(AgentTemplate(
    id="customer-service",
    name="Customer Service Agent",
    description="Multi-role agent team for customer support — triage, specialist handling, and escalation.",
    category=TemplateCategory.CUSTOMER_SERVICE,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="triage", goal="Classify and route incoming requests", backstory="Expert at understanding customer intent", tools=["search_kb"]),
        AgentRole(role="specialist", goal="Handle domain-specific queries with detailed answers", backstory="Deep product knowledge specialist", tools=["search_kb", "lookup_order"]),
        AgentRole(role="escalation", goal="Escalate complex issues to human agents", backstory="Knows when AI can't solve it", tools=["create_ticket"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="salesforce", command="npx", args=["-y", "@salesforce/mcp-server"], required_env=["SALESFORCE_INSTANCE_URL", "SALESFORCE_ACCESS_TOKEN"], category="crm"),
        MCPServerConfig(name="slack", command="npx", args=["-y", "@slack/mcp-server"], required_env=["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"], category="communication"),
    ],
    required_fields=[
        TemplateField(name="company_name", label="Company Name", required=True, description="Your company name for the agent persona"),
        TemplateField(name="support_channels", label="Support Channels", field_type="multiselect", options=["chat", "email", "slack"], required=True),
    ],
    optional_fields=[
        TemplateField(name="knowledge_base_url", label="Knowledge Base URL", description="URL to your FAQ / help center"),
        TemplateField(name="escalation_email", label="Escalation Email", description="Where to send escalated tickets"),
    ],
    estimated_cost="$50-100/month",
    tags=["customer-service", "crewai", "multi-agent", "support"],
))

# 2. Research Agent (LangGraph)
_register(AgentTemplate(
    id="research",
    name="Research Agent",
    description="Iterative research pipeline — searches the web, extracts data, synthesizes findings into reports.",
    category=TemplateCategory.RESEARCH,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="planner", goal="Break research question into sub-queries", tools=["web_search"]),
        AgentRole(role="researcher", goal="Execute searches and extract key findings", tools=["web_search", "scrape"]),
        AgentRole(role="synthesizer", goal="Combine findings into a coherent report", tools=[]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="research_domain", label="Research Domain", description="Primary area of research (e.g. technology, finance, science)"),
    ],
    optional_fields=[
        TemplateField(name="output_format", label="Output Format", field_type="select", options=["markdown", "pdf", "json"], default="markdown"),
        TemplateField(name="max_sources", label="Max Sources", field_type="number", default=10),
    ],
    estimated_cost="$30-80/month",
    tags=["research", "langgraph", "web-search", "analysis"],
))

# 3. Data Analysis Agent (LangGraph)
_register(AgentTemplate(
    id="data-analysis",
    name="Data Analysis Agent",
    description="Connects to databases, runs queries, and produces insights with visualisation suggestions.",
    category=TemplateCategory.DATA_ANALYSIS,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="planner", goal="Translate natural language to a query plan", tools=[]),
        AgentRole(role="executor", goal="Execute SQL/NoSQL queries safely", tools=["run_query"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="postgres", command="npx", args=["-y", "@postgres/mcp-server"], required_env=["DATABASE_URL"], category="data"),
    ],
    required_fields=[
        TemplateField(name="db_type", label="Database Type", field_type="select", options=["postgres", "mongodb", "mysql", "sqlite"], required=True),
    ],
    optional_fields=[
        TemplateField(name="read_only", label="Read-only Mode", field_type="boolean", default=True, description="Restrict to SELECT queries only"),
    ],
    estimated_cost="$20-60/month",
    tags=["data", "langgraph", "sql", "analytics"],
))

# 4. Code Generation Agent (LangGraph)
_register(AgentTemplate(
    id="code-generation",
    name="Code Generation Agent",
    description="Iterative code-writing agent — generates, reviews, and tests code based on specifications.",
    category=TemplateCategory.CODE_GENERATION,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="planner", goal="Break specification into implementation tasks", tools=[]),
        AgentRole(role="coder", goal="Write clean, tested code", tools=["file_write", "run_tests"]),
        AgentRole(role="reviewer", goal="Review code for quality, security, and correctness", tools=["file_read"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="github", command="npx", args=["-y", "@github/mcp-server"], required_env=["GITHUB_TOKEN"], category="dev-tools"),
    ],
    required_fields=[
        TemplateField(name="language", label="Programming Language", field_type="select", options=["python", "typescript", "javascript", "go", "rust"], required=True),
    ],
    optional_fields=[
        TemplateField(name="test_framework", label="Test Framework", description="e.g. pytest, jest, go test"),
        TemplateField(name="style_guide", label="Style Guide URL", description="Link to your code style guide"),
    ],
    estimated_cost="$40-120/month",
    tags=["code", "langgraph", "github", "development"],
))

# 5. Multi-Agent Team (AutoGen)
_register(AgentTemplate(
    id="multi-agent-team",
    name="Multi-Agent Team",
    description="Collaborative agent group chat — coordinator, workers, and critic iterate together.",
    category=TemplateCategory.MULTI_AGENT,
    framework=FrameworkChoice.AUTOGEN,
    agents=[
        AgentRole(role="coordinator", goal="Manage group conversation and task delegation", tools=[]),
        AgentRole(role="worker", goal="Execute primary tasks assigned by coordinator", tools=[]),
        AgentRole(role="critic", goal="Review outputs and suggest improvements", tools=[]),
    ],
    mcp_servers=[],
    required_fields=[
        TemplateField(name="team_goal", label="Team Goal", required=True, description="What should this agent team accomplish?"),
    ],
    optional_fields=[
        TemplateField(name="max_rounds", label="Max Conversation Rounds", field_type="number", default=10),
        TemplateField(name="human_in_loop", label="Human-in-the-loop", field_type="boolean", default=False),
    ],
    estimated_cost="$30-100/month",
    tags=["multi-agent", "autogen", "collaboration", "team"],
))

# 6. Sales & Lead Generation Agent (LangGraph)
_register(AgentTemplate(
    id="sales-lead-gen",
    name="Sales & Lead Generation Agent",
    description="AI-powered lead prospecting — monitors domains, generates personalized outreach, and tracks pipeline.",
    category=TemplateCategory.SALES_MARKETING,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="prospector", goal="Discover and qualify new leads from web sources", backstory="Expert at finding high-intent prospects", tools=["web_search", "domain_lookup"]),
        AgentRole(role="outreach_writer", goal="Generate personalized email and proposal copy", backstory="Skilled copywriter who personalizes at scale", tools=["email_draft"]),
        AgentRole(role="pipeline_tracker", goal="Track lead status and follow-up schedules", backstory="CRM specialist who never lets a lead slip", tools=["crm_update"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="target_industry", label="Target Industry", required=True, description="Industry vertical to prospect (e.g. SaaS, e-commerce, agencies)"),
        TemplateField(name="outreach_channel", label="Outreach Channel", field_type="select", options=["email", "linkedin", "both"], required=True),
    ],
    optional_fields=[
        TemplateField(name="crm_integration", label="CRM Integration", field_type="select", options=["hubspot", "pipedrive", "salesforce", "none"], default="none"),
        TemplateField(name="daily_lead_target", label="Daily Lead Target", field_type="number", default=20),
    ],
    estimated_cost="$40-100/month",
    tags=["sales", "lead-gen", "outreach", "prospecting", "marketing", "crm"],
))

# 7. Content Repurposer Agent (CrewAI)
_register(AgentTemplate(
    id="content-repurposer",
    name="Content Repurposer Agent",
    description="Transforms long-form content into multi-platform assets — podcasts to TikToks, blogs to newsletters.",
    category=TemplateCategory.CONTENT_CREATION,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="ingester", goal="Transcribe and parse source content into structured segments", backstory="Expert at identifying key themes and quotable moments", tools=["transcribe", "summarize"]),
        AgentRole(role="adapter", goal="Reformat content for each target platform", backstory="Multi-platform content strategist", tools=["format_post", "generate_image_prompt"]),
        AgentRole(role="scheduler", goal="Create a publishing calendar and queue assets", backstory="Social media scheduling expert", tools=["schedule_post"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="source_type", label="Source Content Type", field_type="select", options=["podcast", "blog", "video", "webinar", "newsletter"], required=True),
        TemplateField(name="target_platforms", label="Target Platforms", field_type="multiselect", options=["tiktok", "instagram", "linkedin", "twitter", "newsletter", "youtube-shorts"], required=True),
    ],
    optional_fields=[
        TemplateField(name="brand_voice", label="Brand Voice Guide", description="Describe your brand tone (e.g. professional, casual, witty)"),
        TemplateField(name="posting_frequency", label="Posts Per Week", field_type="number", default=5),
    ],
    estimated_cost="$30-80/month",
    tags=["content", "repurpose", "creator", "social-media", "podcast", "video"],
))

# 8. E-commerce Review Analyzer Agent (LangGraph)
_register(AgentTemplate(
    id="ecommerce-analyzer",
    name="E-commerce Review Analyzer",
    description="Scrapes and analyzes product reviews across platforms — sentiment, trends, SWOT, and competitive insights.",
    category=TemplateCategory.E_COMMERCE,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="scraper", goal="Collect reviews from target platforms", backstory="Data collection specialist", tools=["web_search", "scrape"]),
        AgentRole(role="analyst", goal="Run sentiment analysis and identify recurring themes", backstory="Consumer insights analyst", tools=["analyze_sentiment"]),
        AgentRole(role="reporter", goal="Generate actionable reports with SWOT and recommendations", backstory="E-commerce strategist", tools=[]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="product_url", label="Product URL or ASIN", required=True, description="URL or identifier of the product to analyze"),
        TemplateField(name="platforms", label="Review Platforms", field_type="multiselect", options=["amazon", "shopify", "trustpilot", "google", "yelp"], required=True),
    ],
    optional_fields=[
        TemplateField(name="competitor_urls", label="Competitor URLs", description="Comma-separated competitor product URLs for comparison"),
        TemplateField(name="report_frequency", label="Report Frequency", field_type="select", options=["daily", "weekly", "monthly"], default="weekly"),
    ],
    estimated_cost="$25-70/month",
    tags=["e-commerce", "reviews", "sentiment", "analytics", "amazon", "shopify"],
))

# 9. Operations SOP Generator Agent (LangGraph)
_register(AgentTemplate(
    id="operations-sop",
    name="Operations & SOP Generator",
    description="Auto-generates and maintains SOPs from workflows — tracks expenses, optimizes subscriptions, documents processes.",
    category=TemplateCategory.OPERATIONS,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="observer", goal="Capture and document workflow steps from screen recordings or API logs", backstory="Process documentation specialist", tools=["capture_workflow"]),
        AgentRole(role="optimizer", goal="Analyze expenses, subscriptions, and identify cost-saving opportunities", backstory="Operations efficiency expert", tools=["analyze_expenses"]),
        AgentRole(role="documenter", goal="Generate formatted SOPs with step-by-step instructions", backstory="Technical writer who creates clear documentation", tools=["generate_doc"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/sop-workspace"], required_env=[], category="tools"),
    ],
    required_fields=[
        TemplateField(name="department", label="Department", field_type="select", options=["engineering", "marketing", "sales", "support", "operations", "finance"], required=True),
        TemplateField(name="process_name", label="Process Name", required=True, description="Name of the workflow or process to document"),
    ],
    optional_fields=[
        TemplateField(name="accounting_integration", label="Accounting Integration", field_type="select", options=["quickbooks", "xero", "freshbooks", "none"], default="none"),
        TemplateField(name="output_format", label="Output Format", field_type="select", options=["markdown", "pdf", "notion", "confluence"], default="markdown"),
    ],
    estimated_cost="$20-60/month",
    tags=["operations", "sop", "process", "documentation", "expense", "optimization"],
))

# 10. Healthcare Practice Manager Agent (CrewAI)
_register(AgentTemplate(
    id="healthcare-practice",
    name="Healthcare Practice Manager",
    description="HIPAA-aware practice assistant — scheduling, session notes, billing integration for solo practitioners.",
    category=TemplateCategory.HEALTHCARE,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="scheduler", goal="Manage appointments, reminders, and availability", backstory="Healthcare scheduling coordinator", tools=["calendar_manage"]),
        AgentRole(role="note_taker", goal="Generate structured session notes from practitioner input", backstory="Clinical documentation specialist", tools=["generate_notes"]),
        AgentRole(role="billing_assistant", goal="Track billing, generate invoices, and manage insurance claims", backstory="Medical billing expert", tools=["billing_process"]),
    ],
    mcp_servers=[],
    required_fields=[
        TemplateField(name="practice_type", label="Practice Type", field_type="select", options=["therapy", "counseling", "psychiatry", "physical-therapy", "general-practice", "dental"], required=True),
        TemplateField(name="billing_method", label="Billing Method", field_type="select", options=["stripe", "square", "insurance", "manual"], required=True),
    ],
    optional_fields=[
        TemplateField(name="ehr_integration", label="EHR Integration", field_type="select", options=["simple-practice", "theranest", "jane-app", "none"], default="none"),
        TemplateField(name="hipaa_mode", label="HIPAA Strict Mode", field_type="boolean", default=True, description="Enable strict data handling and encryption"),
    ],
    estimated_cost="$40-100/month",
    tags=["healthcare", "hipaa", "therapy", "practice-management", "billing", "scheduling"],
))

# 11. Real Estate Marketing Agent (CrewAI)
_register(AgentTemplate(
    id="real-estate-marketing",
    name="Real Estate Marketing Agent",
    description="Generates complete listing marketing kits — social posts, property websites, virtual tour scripts, and QR materials.",
    category=TemplateCategory.REAL_ESTATE,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="listing_analyst", goal="Parse property details and identify key selling points", backstory="Real estate market analyst", tools=["analyze_listing"]),
        AgentRole(role="content_creator", goal="Generate marketing copy, social posts, and video scripts", backstory="Real estate marketing copywriter", tools=["generate_copy", "generate_image_prompt"]),
        AgentRole(role="campaign_builder", goal="Assemble multi-channel marketing campaigns", backstory="Digital marketing strategist for real estate", tools=["build_campaign"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="listing_address", label="Property Address", required=True, description="Full address of the listing"),
        TemplateField(name="listing_price", label="Listing Price", required=True, description="Asking price for the property"),
        TemplateField(name="property_type", label="Property Type", field_type="select", options=["single-family", "condo", "townhouse", "multi-family", "commercial", "land"], required=True),
    ],
    optional_fields=[
        TemplateField(name="mls_id", label="MLS ID", description="MLS listing identifier for data enrichment"),
        TemplateField(name="target_platforms", label="Marketing Platforms", field_type="multiselect", options=["instagram", "facebook", "zillow", "realtor.com", "tiktok"], default=["instagram", "facebook"]),
    ],
    estimated_cost="$30-80/month",
    tags=["real-estate", "marketing", "listings", "social-media", "property"],
))

# 12. Education Content Builder Agent (LangGraph)
_register(AgentTemplate(
    id="education-builder",
    name="Education Content Builder",
    description="Creates interactive learning experiences — quizzes, lesson plans, video walkthroughs, and progress tracking.",
    category=TemplateCategory.EDUCATION,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="curriculum_designer", goal="Structure learning objectives and lesson sequences", backstory="Instructional design specialist", tools=["design_curriculum"]),
        AgentRole(role="content_generator", goal="Create lessons, quizzes, and interactive exercises", backstory="Educational content creator", tools=["generate_lesson", "generate_quiz"]),
        AgentRole(role="assessment_builder", goal="Design assessments and track learner progress", backstory="Education assessment expert", tools=["build_assessment"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/edu-workspace"], required_env=[], category="tools"),
    ],
    required_fields=[
        TemplateField(name="subject", label="Subject Area", required=True, description="Subject to create content for (e.g. Mathematics, History, Programming)"),
        TemplateField(name="grade_level", label="Grade / Skill Level", field_type="select", options=["elementary", "middle-school", "high-school", "college", "professional", "self-paced"], required=True),
    ],
    optional_fields=[
        TemplateField(name="lesson_count", label="Number of Lessons", field_type="number", default=10),
        TemplateField(name="include_video", label="Include Video Scripts", field_type="boolean", default=False, description="Generate video walkthrough scripts for each lesson"),
        TemplateField(name="lms_integration", label="LMS Integration", field_type="select", options=["canvas", "moodle", "google-classroom", "none"], default="none"),
    ],
    estimated_cost="$25-70/month",
    tags=["education", "learning", "curriculum", "quizzes", "interactive", "edtech"],
))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_templates() -> List[AgentTemplate]:
    """Return all available templates."""
    return list(_TEMPLATES.values())


def get_template(template_id: str) -> Optional[AgentTemplate]:
    """Get a template by ID."""
    return _TEMPLATES.get(template_id)


def get_template_for_framework(framework: FrameworkChoice) -> Optional[AgentTemplate]:
    """Get the first template that uses the given framework."""
    for t in _TEMPLATES.values():
        if t.framework == framework:
            return t
    return None

