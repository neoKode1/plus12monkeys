<p align="center">
  <img src="frontend/public/12m.png" alt="+12 Monkeys" width="600" />
</p>

# +12 Monkeys

**Agent-as-a-Service Platform with MCP Integration**

> Build and deploy custom AI agents in under 10 minutes through conversational configuration.

[![Status](https://img.shields.io/badge/status-active-green)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![MCP](https://img.shields.io/badge/MCP-compatible-purple)]()

---

## 🎯 What is +12 Monkeys?

+12 Monkeys is a **plug-and-play platform** that enables developers to create, configure, and deploy production-ready AI agent systems without writing code. Simply describe what you need in natural language, and the platform generates a **complete deployable package** — Python or TypeScript — ready to deploy with `docker compose up`, Railway, Render, or Vercel.

### Key Features

✨ **Conversational Configuration** - No code required, just chat
🔌 **MCP-Native** - Built on Model Context Protocol (Linux Foundation standard)
🎨 **20 Agent Templates** - Customer service, research, data analysis, code gen, multi-agent teams, sales & lead gen, content creation, e-commerce, operations, healthcare, real estate, education, STEM lab sim, STEM coding tutor, grant writing, literature review, portfolio risk, compliance & fraud, mission planning, clinical decision support
🚀 **Three Deployment Options** - LOCAL (docker compose), CLOUD (Railway/Render/Vercel), EXPORT (self-host)
🔧 **Multi-Framework Support** - LangGraph, CrewAI, AutoGen, Semantic Kernel (Python) + Vercel AI SDK (TypeScript) + Rig (Rust) + ADK-Go (Go)
🐍 **Python Packages** - agent.py, requirements.txt, Dockerfile (Python 3.12), docker-compose.yml
📘 **TypeScript Packages** - agent.ts, package.json, tsconfig.json, Dockerfile (Node 22), docker-compose.yml
🦀 **Rust Packages** - src/main.rs, Cargo.toml, Dockerfile (multi-stage Rust 1.84), docker-compose.yml
🐹 **Go Packages** - main.go, go.mod, Dockerfile (multi-stage Go 1.23 → distroless), docker-compose.yml
☁️ **Cloud Deploy Configs** - railway.toml, render.yaml, vercel.json (auto-generated for CLOUD/EXPORT)
☸️ **Kubernetes Manifests** - k8s/deployment.yaml, k8s/service.yaml (auto-generated for CLOUD/EXPORT)
⚡ **AWS SAM Templates** - sam/template.yaml with Lambda + API Gateway (auto-generated for CLOUD/EXPORT)
📋 **Copy-to-Clipboard UI** - Easy code extraction with visual feedback
⚡ **30-Second Deployment** - From generation to running agent in half a minute

---

## 🚀 Quick Start

### 1. Start the Platform

```bash
# Clone and start all services
git clone https://github.com/neoKode1/plus12monkeys.git
cd plus12monkeys
docker compose up --build

# Platform available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - NANDA Index: http://localhost:6900
```

### 2. Chat with the Wizard

```
You: "I need a research agent that can search the web and summarize findings"

+12 Monkeys: "Great! Let me ask a few questions:
  1. What data sources? (web search, academic papers, news)
  2. Output format? (markdown, JSON, PDF)
  3. Deployment preference? (local, cloud, export)"

You: "Web search and academic papers, markdown output, local deployment"

+12 Monkeys: "Perfect! I recommend:
  - Framework: LangGraph (complex workflows)
  - MCP Servers: web-search, arxiv
  - Deployment: LOCAL (docker compose)
  - Estimated cost: Free (local)

  Shall I generate this package?"

You: "Yes!"

+12 Monkeys: "✅ Package generated! 7 files ready:
  - agent.py (LangGraph workflow)
  - requirements.txt (all dependencies)
  - Dockerfile (container build)
  - docker-compose.yml (one-command deploy)
  - .env.example (environment variables)
  - mcp-config.json (MCP server config)
  - README.md (setup instructions)

  Choose delivery method:
  📋 Copy individual files
  ⬇️ Download bundle
  👁️ Preview in browser"
```

### 3. Deploy Your Agent

```bash
# Copy the generated files to a new directory
mkdir my-research-agent
cd my-research-agent

# Paste the files (or download bundle)
# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Deploy in 30 seconds
docker compose up --build

# Agent running at http://localhost:8080
```

**Result:** Production-ready agent in < 10 minutes

---

## 📦 What You Receive

Every generated agent package includes **production-ready files** tailored to the selected language and deployment target:

### Python Packages (LangGraph / CrewAI / AutoGen / Semantic Kernel)

| File | Description |
|------|-------------|
| `agent.py` | Framework-specific agent code with multi-agent workflows |
| `requirements.txt` | Python dependencies (framework SDK, anthropic, mcp, dotenv) |
| `Dockerfile` | Python 3.12-slim container (+ Node.js if MCP servers need npx) |
| `docker-compose.yml` | One-command deployment with env loading + port mapping |
| `.env.example` | Environment variable template with all required keys |
| `mcp-config.json` | MCP server configuration |
| `README.md` | Setup instructions for Docker and local development |

### TypeScript Packages (Vercel AI SDK)

| File | Description |
|------|-------------|
| `agent.ts` | TypeScript agent using Vercel AI SDK with multi-agent pipeline |
| `package.json` | Node.js dependencies (ai, @ai-sdk/anthropic, zod, tsx) |
| `tsconfig.json` | TypeScript compiler config (ES2022, ESM) |
| `Dockerfile` | Node.js 22-slim container |
| `docker-compose.yml` | One-command deployment with env loading + port mapping |
| `.env.example` | Environment variable template with all required keys |
| `mcp-config.json` | MCP server configuration |
| `README.md` | Setup instructions for Docker and local development |

### Rust Packages (Rig)

| File | Description |
|------|-------------|
| `src/main.rs` | Async Rust agent using Rig crate with tokio runtime |
| `Cargo.toml` | Rust dependencies (rig-core, tokio, serde, dotenv) |
| `Dockerfile` | Multi-stage build: rust:1.84 builder → debian:bookworm-slim runtime |
| `docker-compose.yml` | One-command deployment with env loading + port mapping |
| `.env.example` | Environment variable template with all required keys |
| `mcp-config.json` | MCP server configuration |
| `README.md` | Setup instructions for Docker and local Rust development |

### Go Packages (ADK-Go)

| File | Description |
|------|-------------|
| `main.go` | Go agent using Google ADK-Go with goroutine pipeline |
| `go.mod` | Go dependencies (google/adk-go, godotenv) |
| `Dockerfile` | Multi-stage build: golang:1.23-alpine → distroless runtime |
| `docker-compose.yml` | One-command deployment with env loading + port mapping |
| `.env.example` | Environment variable template with all required keys |
| `mcp-config.json` | MCP server configuration |
| `README.md` | Setup instructions for Docker and local Go development |

### Cloud Deployment Configs (CLOUD / EXPORT targets)

| File | Description |
|------|-------------|
| `railway.toml` | Railway deployment config (auto-detects Python/Node/Rust/Go runtime) |
| `render.yaml` | Render Blueprint spec with health checks and env vars |
| `vercel.json` | Vercel serverless config with function routes |
| `k8s/deployment.yaml` | Kubernetes Deployment with replicas, resource limits, probes |
| `k8s/service.yaml` | Kubernetes Service (ClusterIP) exposing port 80 → 8080 |
| `sam/template.yaml` | AWS SAM template with Lambda function + API Gateway |

### 5. **.env.example** - Environment Variables Template
- ✅ LLM API keys (ANTHROPIC_API_KEY)
- ✅ MCP server credentials (per server)
- ✅ Custom configuration variables
- ✅ Clear comments and organization

### 6. **mcp-config.json** - MCP Server Configuration
- ✅ MCP server definitions
- ✅ Command + args for each server
- ✅ Environment variable mapping
- ✅ Ready for MCP SDK consumption

### 7. **README.md** - Complete Documentation
- ✅ Project description
- ✅ Agent roles table
- ✅ MCP integrations list
- ✅ Quick start (Docker + local Python)
- ✅ File structure overview
- ✅ Troubleshooting tips

---

## 📤 Delivery Methods

### 📋 Copy-to-Clipboard (Individual Files)
- Click copy button on any file
- Visual feedback ("Copied ✓" for 2 seconds)
- Uses native browser `navigator.clipboard` API
- Perfect for integrating into existing projects

### ⬇️ Download Bundle (All Files)
- Single `.txt` file with all 7 files
- Clearly separated with headers
- Easy to extract locally
- Great for offline work

### 👁️ In-Browser Preview (Interactive)
- File tabs sidebar
- Syntax-highlighted code preview
- Copy button per file
- Explore before downloading

---

## 🏗️ Architecture

### Template Rendering Pipeline

```
User Input → Conversational Wizard → Template Registry → Code Generator
                                                              ↓
                                                    Jinja2 Rendering Engine
                                              ↓          ↓          ↓          ↓
                                          Python    TypeScript    Rust        Go
                                        (pip)      (npm)       (cargo)    (go mod)
                                                         ↓
                                       Docker + Cloud Deploy Configs + K8s + SAM
                                                         ↓
                                        Frontend UI (Copy/Download/Preview)
                                                         ↓
                                        User Deployment (LOCAL/CLOUD/EXPORT)
```

### Core Components

1. **Conversational Wizard** (`frontend/src/components/ChatWizard.tsx`)
   - Chat-based configuration interface
   - Real-time requirement extraction
   - Architecture recommendation display
   - Copy-to-clipboard functionality

2. **Agent Orchestrator** (`backend/app/services/orchestrator.py`)
   - AI-powered requirement analysis
   - Framework selection logic
   - MCP server recommendation
   - Deployment target selection

3. **Template Registry** (`backend/app/services/template_registry.py`)
   - 20 built-in templates (customer-service, research, data-analysis, code-generation, multi-agent-team, sales-lead-gen, content-repurposer, ecommerce-analyzer, operations-sop, healthcare-practice, real-estate-marketing, education-builder, stem-lab-simulator, stem-coding-tutor, grant-writing-assistant, systematic-lit-review, portfolio-risk-analyzer, compliance-fraud-detection, mission-planning-intel, clinical-decision-support)
   - In-memory storage
   - Template metadata and configuration

4. **Code Generator** (`backend/app/services/code_generator.py`)
   - Jinja2 templating engine
   - Context building from user config
   - 7-file package generation
   - Environment variable aggregation

5. **NANDA Index** (`nanda-index/registry.py`)
   - Unified agent registry
   - Cross-ecosystem discovery
   - MongoDB-backed storage
   - REST API for agent management

### Tech Stack

**Frontend:**
- Next.js 16 + React 19
- TypeScript 5
- Tailwind CSS 4
- Native browser APIs (clipboard)

**Backend:**
- Python 3.12 + FastAPI
- Jinja2 3.1+ (templating)
- Pydantic (validation)
- Anthropic SDK (LLM)

**Agent Layer:**
- MCP SDK (TypeScript/Python)
- LangGraph (workflows)
- CrewAI (teams)
- AutoGen (collaboration)
- Semantic Kernel (enterprise)
- Vercel AI SDK (TypeScript)
- Rig (Rust async agents)
- ADK-Go (Go concurrent agents)

**Infrastructure:**
- Docker + Docker Compose
- Kubernetes (Deployment + Service manifests)
- AWS SAM / Lambda (serverless)
- MongoDB (NANDA Index)
- Railway/Render/Vercel (cloud deployment)

---

## 🚀 Deployment Options

### LOCAL (Default)
```bash
docker compose up --build
# Agent starts on http://localhost:8080
# MCP servers auto-connect
# Ready for testing in 30 seconds
```

**What happens:**
1. Docker builds container from Dockerfile
2. Installs Python dependencies
3. Installs Node.js (if MCP servers need it)
4. Loads environment variables from `.env`
5. Starts agent on port 8080
6. MCP servers spawn as child processes
7. Agent ready to handle requests

### CLOUD (Railway/Render/Fly.io)
```bash
# Push to GitHub
git init && git add . && git commit -m "Initial agent"
git push origin main

# Deploy to Railway
railway init
railway up

# Agent deployed to: https://my-agent-abc123.railway.app
```

**What happens:**
1. Platform detects Dockerfile
2. Builds container in cloud
3. Injects environment variables from dashboard
4. Deploys to public URL
5. Auto-scales based on traffic
6. Health checks + auto-restart

### EXPORT (Self-Host)
```bash
# Download files and deploy to your infrastructure:
# - AWS EC2
# - Google Cloud Run
# - Azure Container Instances
# - On-premise Kubernetes
```

**What happens:**
1. Full control over deployment
2. Modify code as needed
3. Deploy to any Docker-compatible platform
4. Integrate with existing CI/CD
5. Custom monitoring/logging

---

## 🎨 Agent Templates

### 1. Customer Service Agent (CrewAI)
- **Use Case:** FAQ, ticket routing, sentiment analysis
- **MCP Servers:** Salesforce, Slack, Email
- **Agents:** Support Agent, Escalation Agent, Analytics Agent
- **Deployment:** CLOUD (high availability)

### 2. Research Agent (LangGraph)
- **Use Case:** Web search, data extraction, summarization
- **MCP Servers:** web-search, arxiv, wikipedia
- **Agents:** Search Agent, Analysis Agent, Summary Agent
- **Deployment:** LOCAL or CLOUD

### 3. Data Analysis Agent (LangGraph)
- **Use Case:** SQL queries, data visualization, insights
- **MCP Servers:** postgres, sqlite, bigquery
- **Agents:** Query Agent, Visualization Agent
- **Deployment:** LOCAL (data security)

### 4. Code Generation Agent (LangGraph)
- **Use Case:** Code writing, debugging, documentation
- **MCP Servers:** github, gitlab, filesystem
- **Agents:** Code Writer, Reviewer, Tester
- **Deployment:** LOCAL or EXPORT

### 5. Multi-Agent Team (AutoGen)
- **Use Case:** Collaborative problem-solving
- **MCP Servers:** Custom (based on use case)
- **Agents:** Manager, Executor, Critic, Planner
- **Deployment:** CLOUD (coordination overhead)

### 6. Sales & Lead Generation Agent (LangGraph)
- **Use Case:** Lead prospecting, personalized outreach, CRM pipeline tracking
- **MCP Servers:** web-search
- **Agents:** Prospector, Outreach Writer, Pipeline Tracker
- **Deployment:** CLOUD or LOCAL

### 7. Content Repurposer Agent (CrewAI)
- **Use Case:** Transform podcasts/blogs/videos into multi-platform social content
- **MCP Servers:** web-search
- **Agents:** Ingester, Adapter, Scheduler
- **Deployment:** CLOUD or LOCAL

### 8. E-commerce Review Analyzer (LangGraph)
- **Use Case:** Sentiment analysis, review scraping, competitive SWOT reports
- **MCP Servers:** web-search
- **Agents:** Scraper, Analyst, Reporter
- **Deployment:** LOCAL or CLOUD

### 9. Operations & SOP Generator (LangGraph)
- **Use Case:** Auto-generate SOPs, track expenses, optimize subscriptions
- **MCP Servers:** filesystem
- **Agents:** Observer, Optimizer, Documenter
- **Deployment:** LOCAL

### 10. Healthcare Practice Manager (CrewAI)
- **Use Case:** HIPAA-compliant scheduling, session notes, billing
- **MCP Servers:** Custom
- **Agents:** Scheduler, Note Taker, Billing Assistant
- **Deployment:** LOCAL (HIPAA compliance)

### 11. Real Estate Marketing Agent (CrewAI)
- **Use Case:** Listing marketing kits, social posts, virtual tour scripts
- **MCP Servers:** web-search
- **Agents:** Listing Analyst, Content Creator, Campaign Builder
- **Deployment:** CLOUD or LOCAL

### 12. Education Content Builder (LangGraph)
- **Use Case:** Interactive lessons, quizzes, curriculum design, progress tracking
- **MCP Servers:** filesystem
- **Agents:** Curriculum Designer, Content Generator, Assessment Builder
- **Deployment:** LOCAL or CLOUD

### 13. STEM Lab Simulator (LangGraph)
- **Use Case:** Virtual physics/chemistry/biology experiments with adaptive difficulty
- **MCP Servers:** filesystem
- **Agents:** Experiment Designer, Simulation Engine, Tutor
- **Deployment:** LOCAL or CLOUD

### 14. STEM Coding Tutor (CrewAI)
- **Use Case:** Interactive coding lessons, auto-grading, project scaffolding for CS/robotics/data science
- **MCP Servers:** github
- **Agents:** Instructor, Code Reviewer, Project Coach
- **Deployment:** LOCAL or CLOUD

### 15. Grant Writing Assistant (LangGraph)
- **Use Case:** NSF/NIH/DOD grant proposals, budget building, compliance checking
- **MCP Servers:** web-search, filesystem
- **Agents:** Narrative Writer, Budget Builder, Compliance Checker
- **Deployment:** LOCAL

### 16. Systematic Literature Review (LangGraph)
- **Use Case:** Paper discovery, abstract screening, PRISMA flow generation, bias assessment
- **MCP Servers:** web-search
- **Agents:** Searcher, Screener, Synthesizer
- **Deployment:** LOCAL or CLOUD

### 17. Portfolio Risk Analyzer (LangGraph)
- **Use Case:** VaR calculations, stress testing, sector exposure, rebalancing recommendations
- **MCP Servers:** web-search
- **Agents:** Market Monitor, Risk Analyst, Advisor
- **Deployment:** CLOUD or LOCAL

### 18. Compliance & Fraud Detection (CrewAI)
- **Use Case:** AML/KYC screening, transaction monitoring, SAR generation, anomaly detection
- **MCP Servers:** postgres
- **Agents:** Transaction Monitor, KYC Screener, Report Generator
- **Deployment:** LOCAL (data security)

### 19. Mission Planning & Threat Intel (LangGraph)
- **Use Case:** OSINT collection, threat assessment, COA analysis, after-action reports
- **MCP Servers:** web-search, filesystem
- **Agents:** OSINT Collector, Threat Assessor, Mission Planner
- **Deployment:** LOCAL (security)

### 20. Clinical Decision Support (CrewAI)
- **Use Case:** Differential diagnosis, drug interactions, lab interpretation, clinical notes
- **MCP Servers:** web-search
- **Agents:** Diagnostician, Pharmacist, Note Summarizer
- **Deployment:** LOCAL (HIPAA compliance)

---

## 🌍 Real-World Example

### Customer Service Agent in Production

**What you generate:**
```
my-customer-service-agent/
├── agent.py              # CrewAI multi-agent system
├── requirements.txt      # crewai, crewai-tools, mcp
├── Dockerfile            # Production container
├── docker-compose.yml    # One-command deploy
├── .env.example          # SLACK_TOKEN, EMAIL_PASSWORD, etc.
├── mcp-config.json       # Slack + Email MCP servers
└── README.md             # Setup instructions
```

**What you deploy:**
```bash
docker compose up --build
# Agent running on port 8080
```

**What it does in production:**
1. **Receives customer inquiry** (via Slack/Email)
2. **Analyzes sentiment** (using LLM)
3. **Searches knowledge base** (via MCP server)
4. **Routes to human** (if needed, via Slack MCP)
5. **Logs interaction** (to database)
6. **Sends response** (via Email MCP)

**Integration points:**
- ✅ Slack (incoming webhooks + MCP server)
- ✅ Email (SMTP via MCP server)
- ✅ Database (PostgreSQL MCP server)
- ✅ CRM (Salesforce MCP server)
- ✅ Analytics (custom logging)

---

## 🔬 Why +12 Monkeys?

### MCP (Model Context Protocol)
- Released by Anthropic (Nov 2024)
- Donated to Linux Foundation (Dec 2025)
- **75+ connectors available**
- Industry standard for agent-to-service communication
- **+12 Monkeys auto-configures MCP servers** for you

### NANDA Index Integration
- Unified agent registry for cross-ecosystem discovery
- Integrates with AGNTCY ADS (Agent Discovery Service)
- **No competitor offers cross-registry agent discovery**
- Publish your generated agents to the registry

### Production-Ready from Day One
- **No boilerplate:** Complete 7-file package
- **No configuration hell:** .env.example with all variables
- **No deployment complexity:** `docker compose up` in 30 seconds
- **No vendor lock-in:** Export and self-host anywhere

### Open-Source Alternative
- **SaaS → AaaS** paradigm shift happening now
- Salesforce Agentforce, Microsoft Copilot Studio, AWS Agent Service
- **+12 Monkeys:** Open-source, developer-friendly, self-hostable

---

## ✅ Current Status

**Phase:** ✅ Foundation + Tier 1 + Tier 2 Multi-Language Expansion
**Implemented:**
- ✅ Conversational wizard with chat UI
- ✅ Template registry with 20 built-in templates
- ✅ Jinja2-based code generation pipeline
- ✅ Python package generation (agent.py, requirements.txt, Dockerfile)
- ✅ TypeScript package generation (agent.ts, package.json, tsconfig.json, Dockerfile)
- ✅ Rust package generation (src/main.rs, Cargo.toml, multi-stage Dockerfile)
- ✅ Go package generation (main.go, go.mod, multi-stage Dockerfile → distroless)
- ✅ Multi-framework support: LangGraph, CrewAI, AutoGen, Semantic Kernel (Python) + Vercel AI SDK (TypeScript) + Rig (Rust) + ADK-Go (Go)
- ✅ Cloud deployment configs: railway.toml, render.yaml, vercel.json
- ✅ Kubernetes manifests: k8s/deployment.yaml, k8s/service.yaml
- ✅ AWS SAM template: sam/template.yaml (Lambda + API Gateway)
- ✅ Copy-to-clipboard UI with visual feedback
- ✅ Download bundle functionality
- ✅ In-browser code preview with syntax highlighting
- ✅ LOCAL deployment support (docker compose)
- ✅ CLOUD deployment support (Railway/Render/Vercel/K8s/SAM)
- ✅ EXPORT deployment support (self-host)
- ✅ NANDA Index integration
- ✅ MCP server auto-configuration

**Next Steps:**
1. Frontend chat UI scaffold (React/Next.js component)
2. Monorepo structure (Turborepo/Nx layout)
3. CI/CD pipelines (GitHub Actions)
4. Implement one-click cloud deployment
5. Add agent monitoring and analytics
6. Build agent marketplace

---

## 📚 Documentation

- **[SPRINT_PLAN.md](./SPRINT_PLAN.md)** - Complete development plan (14 weeks, 6 phases)
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick reference guide
- **[nanda-index/README.md](./nanda-index/README.md)** - NANDA Index documentation

### External Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [CrewAI Docs](https://docs.crewai.com/)
- [AutoGen Docs](https://microsoft.github.io/autogen/)
- [Semantic Kernel Docs](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Rig (Rust) Docs](https://docs.rs/rig-core/)
- [ADK-Go Docs](https://google.github.io/adk-docs/)

---

## 🛠️ Development

### Prerequisites
- Docker + Docker Compose
- Node.js 18+ (for frontend)
- Python 3.12+ (for backend)
- MongoDB (via Docker)

### Local Setup
```bash
# Clone repository
git clone https://github.com/neoKode1/plus12monkeys.git
cd plus12monkeys

# Start all services
docker compose up --build

# Services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - NANDA Index: http://localhost:6900
# - MongoDB: localhost:27017
```

### Project Structure
```
+12monkeys/
├── frontend/                 # Next.js 16 + React 19
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatWizard.tsx    # Main conversational UI
│   │   └── app/
│   └── package.json
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── services/
│   │   │   ├── code_generator.py      # Jinja2 rendering
│   │   │   ├── template_registry.py   # Template storage
│   │   │   └── orchestrator.py        # AI orchestration
│   │   ├── templates/        # Jinja2 templates (.j2 files)
│   │   └── models/           # Pydantic models
│   └── pyproject.toml
├── nanda-index/              # Agent registry
│   ├── registry.py           # FastAPI server
│   └── switchboard/          # Routing logic
└── docker-compose.yml        # Multi-service orchestration
```

---

## 🤝 Contributing

Contributions welcome! This is an open-source project.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution
- 🎨 New agent templates
- 🔌 MCP server integrations
- 🚀 Deployment platform support
- 📚 Documentation improvements
- 🐛 Bug fixes
- ✨ Feature enhancements

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- **Anthropic** - For MCP and Claude
- **Linux Foundation** - For adopting MCP as a standard
- **LangChain Team** - For LangGraph
- **CrewAI Team** - For CrewAI framework
- **Microsoft** - For AutoGen and Semantic Kernel
- **Rig Contributors** - For the Rust AI agent framework
- **Google** - For ADK-Go (Agent Development Kit)
- **NANDA Index** - For agent registry infrastructure

---

**Built with ❤️ for the AI agent community**

**Star ⭐ this repo if you find it useful!**

