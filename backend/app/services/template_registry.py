"""In-memory registry of built-in agent templates.

Provides the 20 built-in templates and lookup helpers used by the code generator.
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
        AgentRole(role="triage", goal="Classify and route incoming requests", backstory="Expert at understanding customer intent", tools=["search_kb"], prompt_pattern_ids=["scope-strict", "comm-user-feedback"]),
        AgentRole(role="specialist", goal="Handle domain-specific queries with detailed answers", backstory="Deep product knowledge specialist", tools=["search_kb", "lookup_order"], prompt_pattern_ids=["error-gather-first", "tool-summary"]),
        AgentRole(role="escalation", goal="Escalate complex issues to human agents", backstory="Knows when AI can't solve it", tools=["create_ticket"], prompt_pattern_ids=["comm-browser-handoff", "safety-secrets"]),
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
        AgentRole(role="planner", goal="Break research question into sub-queries", tools=["web_search"], prompt_pattern_ids=["planning-agent-loop", "scope-conservative"]),
        AgentRole(role="researcher", goal="Execute searches and extract key findings", tools=["web_search", "scrape"], prompt_pattern_ids=["planning-dual-mode", "error-gather-first"]),
        AgentRole(role="synthesizer", goal="Combine findings into a coherent report", tools=[], prompt_pattern_ids=["scope-strict", "comm-user-feedback"]),
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
        AgentRole(role="planner", goal="Translate natural language to a query plan", tools=[], prompt_pattern_ids=["planning-dual-mode", "scope-strict"]),
        AgentRole(role="executor", goal="Execute SQL/NoSQL queries safely", tools=["run_query"], prompt_pattern_ids=["safety-classification", "error-gather-first", "tool-summary"]),
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
        AgentRole(role="planner", goal="Break specification into implementation tasks", tools=[], prompt_pattern_ids=["planning-agent-loop", "scope-strict"]),
        AgentRole(role="coder", goal="Write clean, tested code", tools=["file_write", "run_tests"], prompt_pattern_ids=["coding-conventions", "coding-testing", "safety-secrets"]),
        AgentRole(role="reviewer", goal="Review code for quality, security, and correctness", tools=["file_read"], prompt_pattern_ids=["coding-conventions", "error-gather-first"]),
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
        AgentRole(role="coordinator", goal="Manage group conversation and task delegation", tools=[], prompt_pattern_ids=["planning-agent-loop", "scope-conservative", "comm-user-feedback"]),
        AgentRole(role="worker", goal="Execute primary tasks assigned by coordinator", tools=[], prompt_pattern_ids=["coding-conventions", "error-gather-first"]),
        AgentRole(role="critic", goal="Review outputs and suggest improvements", tools=[], prompt_pattern_ids=["error-gather-first", "scope-strict"]),
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
        AgentRole(role="prospector", goal="Discover and qualify new leads from web sources", backstory="Expert at finding high-intent prospects", tools=["web_search", "domain_lookup"], prompt_pattern_ids=["planning-dual-mode", "safety-secrets"]),
        AgentRole(role="outreach_writer", goal="Generate personalized email and proposal copy", backstory="Skilled copywriter who personalizes at scale", tools=["email_draft"], prompt_pattern_ids=["scope-conservative", "comm-user-feedback"]),
        AgentRole(role="pipeline_tracker", goal="Track lead status and follow-up schedules", backstory="CRM specialist who never lets a lead slip", tools=["crm_update"], prompt_pattern_ids=["tool-summary", "error-gather-first"]),
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

# 13. STEM Lab Simulator Agent (LangGraph)
_register(AgentTemplate(
    id="stem-lab-simulator",
    name="STEM Lab Simulator",
    description="Virtual lab environment — physics, chemistry, and biology experiment simulations with adaptive problem-solving walkthroughs.",
    category=TemplateCategory.STEM_EDUCATION,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="experiment_designer", goal="Design virtual experiments with realistic parameters and safety constraints", backstory="PhD-level science educator who builds engaging lab experiences", tools=["design_experiment"]),
        AgentRole(role="simulation_engine", goal="Run step-by-step simulations and calculate outcomes", backstory="Computational scientist specializing in physics and chemistry models", tools=["run_simulation", "calculate"]),
        AgentRole(role="tutor", goal="Provide hints, explain results, and adapt difficulty based on student performance", backstory="Adaptive learning specialist who meets students at their level", tools=["assess_understanding", "generate_hint"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/stem-lab"], required_env=[], category="tools"),
    ],
    required_fields=[
        TemplateField(name="subject", label="STEM Subject", field_type="select", options=["physics", "chemistry", "biology", "earth-science", "environmental-science"], required=True),
        TemplateField(name="level", label="Education Level", field_type="select", options=["middle-school", "high-school", "ap-level", "college-intro", "college-advanced"], required=True),
    ],
    optional_fields=[
        TemplateField(name="lab_safety_mode", label="Lab Safety Prompts", field_type="boolean", default=True, description="Include safety reminders and proper procedure guidance"),
        TemplateField(name="difficulty_adaptation", label="Adaptive Difficulty", field_type="boolean", default=True, description="Automatically adjust problem difficulty based on student responses"),
        TemplateField(name="max_experiments", label="Max Experiments Per Session", field_type="number", default=5),
    ],
    estimated_cost="$20-50/month",
    tags=["stem", "education", "lab", "simulation", "physics", "chemistry", "biology", "adaptive-learning"],
))

# 14. STEM Coding Tutor Agent (CrewAI)
_register(AgentTemplate(
    id="stem-coding-tutor",
    name="STEM Coding Tutor",
    description="Interactive coding instructor — real-time feedback, auto-grading, project scaffolding for CS, robotics, and data science.",
    category=TemplateCategory.STEM_EDUCATION,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="instructor", goal="Deliver structured coding lessons with clear explanations and examples", backstory="Senior CS educator with 15 years teaching experience", tools=["generate_lesson", "create_example"]),
        AgentRole(role="code_reviewer", goal="Review student code in real-time, provide hints without giving answers", backstory="Code review expert who teaches through guided discovery", tools=["analyze_code", "run_tests"]),
        AgentRole(role="project_coach", goal="Scaffold hands-on projects and track milestone completion", backstory="Project-based learning specialist", tools=["scaffold_project", "track_progress"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="github", command="npx", args=["-y", "@github/mcp-server"], required_env=["GITHUB_TOKEN"], category="dev-tools"),
    ],
    required_fields=[
        TemplateField(name="language", label="Programming Language", field_type="select", options=["python", "javascript", "scratch", "java", "c++", "r", "matlab"], required=True),
        TemplateField(name="track", label="Learning Track", field_type="select", options=["intro-cs", "data-science", "web-dev", "robotics", "machine-learning", "algorithms", "cybersecurity"], required=True),
    ],
    optional_fields=[
        TemplateField(name="skill_level", label="Starting Skill Level", field_type="select", options=["beginner", "intermediate", "advanced"], default="beginner"),
        TemplateField(name="auto_grade", label="Auto-Grading", field_type="boolean", default=True, description="Automatically grade exercises with test cases"),
        TemplateField(name="project_count", label="Number of Projects", field_type="number", default=3),
    ],
    estimated_cost="$25-60/month",
    tags=["stem", "coding", "tutor", "cs-education", "auto-grading", "robotics", "data-science"],
))

# 15. Grant Writing Assistant Agent (LangGraph)
_register(AgentTemplate(
    id="grant-writing-assistant",
    name="Grant Writing Assistant",
    description="Multi-agent grant proposal pipeline — drafts narratives, builds budgets, checks compliance for NSF/NIH/DOD/EU formats.",
    category=TemplateCategory.RESEARCH,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="narrative_writer", goal="Draft compelling research narratives, specific aims, and impact statements", backstory="Former program officer who has reviewed 1000+ proposals", tools=["web_search", "draft_section"]),
        AgentRole(role="budget_builder", goal="Build detailed budgets with justifications matching funder requirements", backstory="Research administrator and budget specialist", tools=["calculate_budget", "generate_justification"]),
        AgentRole(role="compliance_checker", goal="Verify proposal meets all funder guidelines, page limits, and formatting rules", backstory="Grants compliance officer with deep knowledge of federal requirements", tools=["check_compliance", "validate_format"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
        MCPServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/grant-workspace"], required_env=[], category="tools"),
    ],
    required_fields=[
        TemplateField(name="funding_agency", label="Funding Agency", field_type="select", options=["nsf", "nih", "dod", "doe", "darpa", "eu-horizon", "private-foundation", "other"], required=True),
        TemplateField(name="research_area", label="Research Area", required=True, description="Primary research domain (e.g. computational biology, materials science)"),
    ],
    optional_fields=[
        TemplateField(name="budget_ceiling", label="Budget Ceiling ($)", field_type="number", description="Maximum total budget for the proposal"),
        TemplateField(name="duration_years", label="Project Duration (years)", field_type="number", default=3),
        TemplateField(name="include_biosketch", label="Generate Biosketch Template", field_type="boolean", default=True),
    ],
    estimated_cost="$30-80/month",
    tags=["research", "grant-writing", "nsf", "nih", "proposals", "academic", "funding"],
))

# 16. Systematic Literature Review Agent (LangGraph)
_register(AgentTemplate(
    id="systematic-lit-review",
    name="Systematic Literature Review",
    description="Automated systematic review pipeline — paper discovery, screening, data extraction, PRISMA flow, and bias assessment.",
    category=TemplateCategory.RESEARCH,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="searcher", goal="Execute comprehensive searches across academic databases and generate keyword strategies", backstory="Information scientist and systematic review methodologist", tools=["web_search", "search_pubmed", "search_arxiv"]),
        AgentRole(role="screener", goal="Apply inclusion/exclusion criteria and screen abstracts and full texts", backstory="Research assistant trained in systematic review protocols", tools=["screen_paper", "extract_metadata"]),
        AgentRole(role="synthesizer", goal="Extract data, assess bias, generate PRISMA diagrams and summary tables", backstory="Meta-analysis expert who synthesizes evidence across studies", tools=["extract_data", "assess_bias", "generate_prisma"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="research_question", label="Research Question", required=True, description="The primary research question using PICO/PECO format"),
        TemplateField(name="databases", label="Databases to Search", field_type="multiselect", options=["pubmed", "arxiv", "scopus", "web-of-science", "cochrane", "ieee", "google-scholar"], required=True),
    ],
    optional_fields=[
        TemplateField(name="date_range", label="Publication Date Range", description="e.g. 2020-2026"),
        TemplateField(name="max_papers", label="Max Papers to Screen", field_type="number", default=500),
        TemplateField(name="review_type", label="Review Type", field_type="select", options=["systematic-review", "scoping-review", "meta-analysis", "rapid-review"], default="systematic-review"),
    ],
    estimated_cost="$30-90/month",
    tags=["research", "literature-review", "systematic-review", "prisma", "meta-analysis", "academic"],
))

# 17. Portfolio Risk Analyzer Agent (LangGraph)
_register(AgentTemplate(
    id="portfolio-risk-analyzer",
    name="Portfolio Risk Analyzer",
    description="Real-time portfolio monitoring — VaR calculations, sector exposure analysis, stress testing, and rebalancing recommendations.",
    category=TemplateCategory.FINANCE,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="market_monitor", goal="Track real-time market data, news, and macro indicators", backstory="Quantitative analyst with expertise in market microstructure", tools=["fetch_market_data", "web_search"]),
        AgentRole(role="risk_analyst", goal="Calculate VaR, stress tests, correlation matrices, and drawdown scenarios", backstory="Risk management specialist with CFA expertise", tools=["calculate_var", "stress_test", "correlation_analysis"]),
        AgentRole(role="advisor", goal="Generate rebalancing recommendations and portfolio health reports", backstory="Senior portfolio strategist who communicates complex risk in plain language", tools=["generate_report", "recommend_rebalance"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="portfolio_type", label="Portfolio Type", field_type="select", options=["equity", "fixed-income", "crypto", "mixed", "etf-only", "options"], required=True),
        TemplateField(name="risk_tolerance", label="Risk Tolerance", field_type="select", options=["conservative", "moderate", "aggressive"], required=True),
    ],
    optional_fields=[
        TemplateField(name="benchmark", label="Benchmark Index", field_type="select", options=["sp500", "nasdaq", "dow", "russell2000", "msci-world", "custom"], default="sp500"),
        TemplateField(name="market_data_source", label="Market Data API", field_type="select", options=["yahoo-finance", "alpha-vantage", "polygon", "twelve-data"], default="yahoo-finance"),
        TemplateField(name="report_frequency", label="Report Frequency", field_type="select", options=["real-time", "daily", "weekly", "monthly"], default="daily"),
    ],
    estimated_cost="$50-150/month",
    tags=["finance", "portfolio", "risk", "var", "trading", "investing", "quantitative"],
))

# 18. Compliance & Fraud Detection Agent (CrewAI)
_register(AgentTemplate(
    id="compliance-fraud-detection",
    name="Compliance & Fraud Detection",
    description="Financial compliance automation — transaction monitoring, AML/KYC screening, anomaly detection, and regulatory report generation.",
    category=TemplateCategory.FINANCE,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="transaction_monitor", goal="Screen transactions for suspicious patterns and threshold violations", backstory="Anti-money laundering analyst with banking compliance expertise", tools=["scan_transactions", "flag_anomaly"]),
        AgentRole(role="kyc_screener", goal="Verify customer identities against watchlists and sanctions databases", backstory="KYC/AML compliance officer", tools=["screen_entity", "check_sanctions"]),
        AgentRole(role="report_generator", goal="Generate SARs, CTRs, and regulatory compliance reports", backstory="Regulatory reporting specialist for FinCEN and SEC", tools=["generate_sar", "generate_report"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="postgres", command="npx", args=["-y", "@postgres/mcp-server"], required_env=["DATABASE_URL"], category="data"),
    ],
    required_fields=[
        TemplateField(name="regulation_framework", label="Regulatory Framework", field_type="multiselect", options=["aml-bsa", "kyc", "sox", "gdpr", "pci-dss", "dodd-frank", "mifid-ii"], required=True),
        TemplateField(name="institution_type", label="Institution Type", field_type="select", options=["bank", "credit-union", "fintech", "broker-dealer", "insurance", "crypto-exchange"], required=True),
    ],
    optional_fields=[
        TemplateField(name="alert_threshold", label="Alert Threshold ($)", field_type="number", default=10000, description="Transaction amount threshold for automatic flagging"),
        TemplateField(name="sanctions_lists", label="Sanctions Lists", field_type="multiselect", options=["ofac-sdn", "un-sanctions", "eu-sanctions", "pep-lists"], default=["ofac-sdn"]),
    ],
    estimated_cost="$60-200/month",
    tags=["finance", "compliance", "fraud", "aml", "kyc", "regulatory", "fintech"],
))

# 19. Mission Planning & Threat Intel Agent (LangGraph)
_register(AgentTemplate(
    id="mission-planning-intel",
    name="Mission Planning & Threat Intel",
    description="OSINT-driven intelligence agent — threat assessment briefs, logistics planning, COA analysis, and after-action report generation.",
    category=TemplateCategory.MILITARY,
    framework=FrameworkChoice.LANGGRAPH,
    agents=[
        AgentRole(role="osint_collector", goal="Gather and correlate open-source intelligence from multiple feeds", backstory="Intelligence analyst specializing in OSINT collection and fusion", tools=["web_search", "scrape", "monitor_feeds"]),
        AgentRole(role="threat_assessor", goal="Analyze threats, generate risk matrices, and produce threat assessment briefs", backstory="Threat intelligence expert with DoD analytical framework experience", tools=["assess_threat", "generate_risk_matrix"]),
        AgentRole(role="mission_planner", goal="Develop courses of action, logistics plans, and after-action reports", backstory="Military operations planner experienced in MDMP and JOPG processes", tools=["plan_coa", "logistics_calc", "generate_aar"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
        MCPServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/mission-workspace"], required_env=[], category="tools"),
    ],
    required_fields=[
        TemplateField(name="domain", label="Operations Domain", field_type="select", options=["land", "maritime", "air", "cyber", "space", "multi-domain"], required=True),
        TemplateField(name="classification_level", label="Classification Level", field_type="select", options=["unclassified", "cui", "fouo"], required=True, description="Only unclassified data processing — no classified material"),
    ],
    optional_fields=[
        TemplateField(name="osint_sources", label="OSINT Sources", field_type="multiselect", options=["news-feeds", "social-media", "satellite-imagery", "maritime-ais", "flight-tracking", "government-reports"], default=["news-feeds", "government-reports"]),
        TemplateField(name="output_format", label="Output Format", field_type="select", options=["nato-stanag", "joint-pub", "custom-brief", "markdown"], default="markdown"),
        TemplateField(name="aor", label="Area of Responsibility", description="Geographic region or area of interest"),
    ],
    estimated_cost="$40-120/month",
    tags=["military", "defense", "osint", "threat-intel", "mission-planning", "logistics", "c2"],
))

# 20. Clinical Decision Support Agent (CrewAI)
_register(AgentTemplate(
    id="clinical-decision-support",
    name="Clinical Decision Support",
    description="Evidence-based clinical assistant — differential diagnosis, lab interpretation, drug interaction checks, and clinical note summarization.",
    category=TemplateCategory.MEDICAL,
    framework=FrameworkChoice.CREWAI,
    agents=[
        AgentRole(role="diagnostician", goal="Generate differential diagnoses ranked by probability based on symptoms and history", backstory="Board-certified internist with diagnostic reasoning expertise", tools=["differential_dx", "web_search"]),
        AgentRole(role="pharmacist", goal="Check drug interactions, contraindications, and dosing recommendations", backstory="Clinical pharmacist specializing in polypharmacy and drug safety", tools=["check_interactions", "lookup_drug"]),
        AgentRole(role="note_summarizer", goal="Summarize clinical notes, lab results, and generate structured reports", backstory="Medical scribe and clinical documentation improvement specialist", tools=["summarize_note", "interpret_labs"]),
    ],
    mcp_servers=[
        MCPServerConfig(name="web-search", command="npx", args=["-y", "@web-search/mcp-server"], required_env=["SEARCH_API_KEY"], category="tools"),
    ],
    required_fields=[
        TemplateField(name="specialty", label="Medical Specialty", field_type="select", options=["internal-medicine", "emergency", "pediatrics", "cardiology", "oncology", "neurology", "psychiatry", "radiology", "general-surgery"], required=True),
        TemplateField(name="ehr_system", label="EHR System", field_type="select", options=["epic", "cerner", "allscripts", "meditech", "athenahealth", "standalone"], required=True),
    ],
    optional_fields=[
        TemplateField(name="formulary", label="Drug Formulary", field_type="select", options=["cms-medicare", "va-national", "tricare", "custom", "none"], default="none"),
        TemplateField(name="evidence_sources", label="Evidence Sources", field_type="multiselect", options=["uptodate", "pubmed", "cochrane", "dynamed", "epocrates"], default=["pubmed"]),
        TemplateField(name="hipaa_strict", label="HIPAA Strict Mode", field_type="boolean", default=True, description="Enable strict PHI handling and audit logging"),
    ],
    estimated_cost="$50-150/month",
    tags=["medical", "clinical", "diagnosis", "drug-interactions", "ehr", "hipaa", "decision-support"],
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

