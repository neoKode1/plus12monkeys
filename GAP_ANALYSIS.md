# Gap Analysis: My-Agent-Too + NANDA Index Feasibility

**Date:** February 2026
**Scope:** Technical feasibility, code maturity, risk assessment, and strengthening recommendations

---

## Executive Summary

**Verdict: FEASIBLE — with significant investment needed.**

NANDA Index provides a solid *starting point* for the My-Agent-Too agent registry backend, but it is currently a **prototype-stage project**, not a production-ready platform. Using it saves ~2 weeks of building basic CRUD registry APIs from scratch, but we'll need ~4-6 weeks of hardening, refactoring, and feature extension before it can support My-Agent-Too's vision.

The Switchboard (cross-registry discovery) and AGNTCY interoperability are **unique differentiators** that no competing platform offers — this is the strongest reason to build on NANDA rather than starting from scratch.

---

## 1. Code Maturity Assessment

### What Works Well ✅

| Component | Assessment |
|-----------|-----------|
| **Basic CRUD API** | Register, lookup, search, delete agents — functional |
| **MongoDB Integration** | Write-through persistence with in-memory fallback |
| **TEST_MODE** | Clean in-memory mode for testing without MongoDB |
| **Switchboard Architecture** | Well-designed adapter pattern for cross-registry federation |
| **AGNTCY Adapter** | gRPC integration with OASF schema translation |
| **SkillMapper** | Taxonomy-based capability mapping (exact, substring, heuristic) |
| **Batch Import/Export** | NANDA ↔ OASF record conversion tools |
| **SSL Support** | Optional TLS via CERT_DIR environment variable |
| **Test Suite** | 7 test files covering unit, integration, and end-to-end |

### What's Concerning ⚠️

| Issue | Severity | Detail |
|-------|----------|--------|
| **No Authentication** | 🔴 CRITICAL | Zero auth on any endpoint. `CORS(app)` allows all origins. Anyone can register, delete, or allocate agents. |
| **No Rate Limiting** | 🔴 CRITICAL | Vulnerable to abuse and DoS |
| **Monolithic Structure** | 🟡 HIGH | 801-line single file (`registry.py`) handles all routes, models, persistence |
| **In-Memory Primary Store** | 🟡 HIGH | Python dict is the authoritative data store; MongoDB is write-through. Horizontal scaling impossible. |
| **No API Versioning** | 🟡 HIGH | Breaking changes will affect all consumers |
| **Duplicated Code** | 🟡 MEDIUM | `SkillMapper` class duplicated between `registry.py` and `export_nanda_to_agntcy.py` |
| **No Logging Framework** | 🟡 MEDIUM | Uses `print()` throughout — no structured logging |
| **Full Upsert on Every Write** | 🟡 MEDIUM | `save_registry()` writes entire registry to MongoDB on each mutation |
| **No Pagination** | 🟡 MEDIUM | `/list`, `/search`, `/clients` return unbounded results |
| **Hardcoded Agent Prefixes** | 🟠 LOW | `agentm` prefix filter in allocation logic (lines 440, 611) |
| **Flask Dev Server** | 🟠 LOW | No Gunicorn/uWSGI configuration for production |

### Specific Code Issues Found

**Bug in `/api/setup` (line 658):**
```python
if not user_selected_agent_id.split("agent")[1][0].lower() == "s":
    save_registry()
```
This silently calls `save_registry()` as a side-effect based on an unclear naming convention. If the agent ID doesn't contain "agent", this will crash with an `IndexError`.

**Allocation uses `random.choice()`:** No load balancing, health checking, or preference logic — just random assignment.

**Search is naive substring matching:**
```python
if q:
    results = [a for a in results if q.lower() in a['agent_id'].lower()]
```
No semantic search, no relevance scoring, no fuzzy matching.

---

## 2. Feature Gap Analysis: NANDA vs. My-Agent-Too Requirements

### Critical Missing Features (Must Build)

| My-Agent-Too Needs | NANDA Has | Gap |
|---------------------|-----------|-----|
| **Agent Templates** | ❌ Nothing | Need template storage, versioning, and code generation support |
| **MCP Server Configuration** | ⚠️ Stub only | `/mcp_servers` is a filter hack; `/get_mcp_registry` queries MongoDB but no write endpoint |
| **Package Generation** | ❌ Nothing | Core feature — generate deployable agent packages from templates |
| **Conversational Wizard** | ❌ Nothing | Chat-based agent configuration UI needs LLM integration |
| **Multi-Tenant Isolation** | ❌ Nothing | No tenant/org concept; all agents in one flat namespace |
| **Authentication & Authorization** | ❌ Nothing | No JWT, API keys, OAuth, or RBAC |
| **Agent Versioning** | ❌ Nothing | Only stores latest state; no version history |
| **Deployment Management** | ❌ Nothing | No concept of deployment targets, environments, or CI/CD |
| **Billing & Usage Tracking** | ❌ Nothing | No metering, quotas, or subscription management |
| **Webhook/Event System** | ❌ Nothing | No lifecycle events for agent creation, deployment, health changes |

### Important Missing Features (Should Build)

| Feature | Gap Level | Notes |
|---------|-----------|-------|
| **Semantic Search** | 🔴 Missing | Current substring search won't scale; need vector embeddings |
| **Agent Composition** | 🔴 Missing | No way to combine agents into multi-agent workflows |
| **Health Monitoring** | 🟡 Partial | `alive` field exists but no heartbeat/polling mechanism |
| **Agent Marketplace** | 🔴 Missing | No sharing, ratings, or community features |
| **Configuration Validation** | 🔴 Missing | No schema validation for agent configurations |
| **Async Processing** | 🟡 Partial | Switchboard uses async but Flask is sync |
| **Agent Testing Framework** | 🔴 Missing | No way to validate agent behavior before deployment |

### What NANDA Provides That We'd Otherwise Build

| Component | Effort Saved |
|-----------|-------------|
| Agent CRUD API | ~1 week |
| MongoDB persistence layer | ~3 days |
| Cross-registry discovery (Switchboard) | ~2 weeks |
| AGNTCY/OASF interoperability | ~1 week |
| Skill taxonomy mapping | ~3 days |
| Batch import/export tools | ~2 days |
| **Total effort saved** | **~4-5 weeks** |

---

## 3. Production Readiness Score

| Category | Score | Notes |
|----------|-------|-------|
| **Security** | 1/10 | No auth, no rate limiting, wildcard CORS |
| **Scalability** | 2/10 | In-memory dict, single process, no caching |
| **Reliability** | 3/10 | No health checks, no graceful degradation beyond in-memory fallback |
| **Observability** | 1/10 | print() logging, no metrics, no tracing |
| **Testing** | 5/10 | Decent test suite but no load testing, no security testing |
| **Documentation** | 4/10 | README is good; no API docs (OpenAPI/Swagger) |
| **DevOps** | 1/10 | No Dockerfile, no CI/CD, no deployment scripts |
| **Code Quality** | 4/10 | Functional but monolithic; some duplication and bugs |
| **Overall** | **2.6/10** | Prototype quality — not production-ready |

## 4. Risk Assessment

### 🔴 High-Risk Items

**R1: Security is Nonexistent**
- *Impact:* Any malicious actor can delete all agents, register fake services, or exfiltrate user data
- *Likelihood:* Certain (if deployed as-is)
- *Mitigation:* Must build auth layer before any public deployment. Estimate: 1-2 weeks for JWT + API keys + RBAC

**R2: NANDA Index is a Young, Solo-Maintained Project**
- *Impact:* If the maintainer stops updating, we inherit all maintenance burden
- *Likelihood:* Medium-High (common with individual open-source projects)
- *Mitigation:* Fork early, maintain our own version, contribute upstream. Don't depend on upstream releases.

**R3: In-Memory Architecture Prevents Scaling**
- *Impact:* Cannot run multiple instances; a crash loses all state until MongoDB reload
- *Likelihood:* Certain (if we grow beyond a single server)
- *Mitigation:* Refactor to make MongoDB the primary store, not a write-through cache. Estimate: 1 week.

**R4: AGNTCY SDK is an External Dependency with gRPC Complexity**
- *Impact:* SDK changes or gRPC issues could break federation
- *Likelihood:* Medium (AGNTCY was donated to Linux Foundation in July 2025, so governance is stabilizing)
- *Mitigation:* Abstract behind adapter pattern (already done); pin SDK version; build fallback REST adapter

### 🟡 Medium-Risk Items

**R5: Flask May Not Scale for Async Workloads**
- My-Agent-Too will need async for LLM calls, agent health checks, and package generation
- *Mitigation:* Plan migration to FastAPI (or add async support via Quart) in Phase 2

**R6: MongoDB Schema Needs Significant Extension**
- Current schema is flat (agent_id, agent_url, api_url, alive, assigned_to)
- My-Agent-Too needs: templates, versions, configurations, deployments, billing
- *Mitigation:* Design extended schema before building; use MongoDB's flexibility to evolve

**R7: Test Coverage is Incomplete**
- No negative/error path testing, no load testing, no security testing
- *Mitigation:* Add comprehensive test suite during Phase 0

### 🟢 Low-Risk Items

**R8: Technology Choices are Sound**
- Python, Flask, MongoDB, gRPC — all mature, well-supported technologies
- The adapter pattern for registry federation is well-designed and extensible

**R9: AGNTCY/OASF Standards are Gaining Traction**
- AGNTCY donated to Linux Foundation (July 2025), backed by Cisco, multiple contributors
- Building on open standards reduces long-term lock-in risk

---

## 5. Competitive Positioning

### The Landscape (February 2026)

| Platform | Type | Price | Strengths | Weaknesses |
|----------|------|-------|-----------|------------|
| **Salesforce Agentforce** | Enterprise SaaS | $2/conversation | Deep CRM integration, massive ecosystem | Locked to Salesforce, expensive at scale |
| **Microsoft Copilot Studio** | Enterprise SaaS | $200/mo per agent | Microsoft 365 integration, Teams | Microsoft-only ecosystem |
| **CrewAI Enterprise** | Agent Platform | Custom pricing | Multi-agent orchestration, production-ready | Closed source, crew-specific paradigm |
| **LangGraph Cloud** | Infrastructure | Pay-per-use | State management, checkpointing, human-in-loop | LangChain-specific, complex |
| **Google Vertex AI Agent Builder** | Cloud SaaS | Pay-per-use | Google Cloud integration, Gemini models | Google Cloud lock-in |
| **My-Agent-Too** | Open Platform | Freemium | Framework-agnostic, open standards, cross-registry | Not yet built |

### Our Unique Differentiators

1. **Cross-Registry Discovery (Switchboard)** — No other platform can discover agents across multiple registries (NANDA + AGNTCY). This is genuinely unique.

2. **Framework-Agnostic** — We support LangGraph, CrewAI, AutoGen, and Semantic Kernel. Competitors lock you into one framework.

3. **MCP-Native** — Built on the industry standard for agent-to-service communication. MCP is now a Linux Foundation project (donated Dec 2025).

4. **Open-Source Foundation** — Unlike Salesforce/Microsoft/Google, developers can self-host, inspect, and extend.

5. **Developer-First** — Conversational wizard + deployable packages, not enterprise dashboards.

### Where Competitors Are Stronger

| Area | Who Leads | Our Gap |
|------|-----------|---------|
| **Production Reliability** | CrewAI, LangGraph | They have battle-tested infrastructure; we're starting from prototype |
| **Enterprise Features** | Salesforce, Microsoft | SSO, compliance, audit trails, SLAs — all missing |
| **Ecosystem Size** | Salesforce, Microsoft | Massive partner/integration ecosystems |
| **Documentation** | LangGraph, CrewAI | Professional docs, tutorials, examples |
| **Managed Hosting** | All cloud vendors | We have no hosting story yet |

---

## 6. Strengthening Recommendations

### Tier 1: Do Before Building Anything (Phase 0 Prerequisites)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | **Add JWT Authentication + API Keys** | 1-2 weeks | Security from day one |
| 2 | **Refactor registry.py into modules** | 1 week | Maintainability, testability |
| 3 | **Make MongoDB the primary store** (not in-memory dict) | 1 week | Scalability, reliability |
| 4 | **Add rate limiting** (Flask-Limiter) | 2 days | Protection against abuse |
| 5 | **Add API versioning** (`/api/v1/`) | 3 days | Forward compatibility |
| 6 | **Add structured logging** (Python `logging` module) | 2 days | Observability |
| 7 | **Create Dockerfile + docker-compose** | 2 days | Reproducible deployment |
| 8 | **Add OpenAPI/Swagger documentation** | 2 days | Developer experience |
| 9 | **Fix the `/api/setup` bug** (line 658) | 1 hour | Correctness |
| 10 | **Add pagination to all list endpoints** | 1 day | Scalability |

### Tier 2: Build During Phase 1-2

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 11 | **Build Agent Template system** | 2 weeks | Core My-Agent-Too feature |
| 12 | **Build proper MCP Server Registry** (with write endpoints) | 1 week | MCP-native promise |
| 13 | **Add semantic search** (vector embeddings via MongoDB Atlas or Pinecone) | 1 week | Intelligent agent discovery |
| 14 | **Add webhook/event system** | 1 week | Agent lifecycle visibility |
| 15 | **Add multi-tenant support** (org/workspace isolation) | 1-2 weeks | Required for SaaS |
| 16 | **Add agent versioning** | 1 week | Configuration management |
| 17 | **Build conversation/session management** | 2 weeks | Wizard state tracking |
| 18 | **Migrate from Flask to FastAPI** | 1-2 weeks | Async support, auto-docs, Pydantic validation |

### Tier 3: Build During Phase 3-4

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 19 | **Add agent composition/workflow support** | 2-3 weeks | Multi-agent orchestration |
| 20 | **Build deployment management** (Docker, cloud targets) | 2-3 weeks | End-to-end story |
| 21 | **Add billing/usage tracking** (Stripe integration) | 2 weeks | Revenue |
| 22 | **Build agent marketplace** | 3-4 weeks | Community ecosystem |
| 23 | **Add Redis caching layer** | 1 week | Performance at scale |
| 24 | **Add CI/CD pipeline** (GitHub Actions) | 3 days | Quality assurance |

---

## 7. Go/No-Go Decision Framework

### ✅ GO — Build on NANDA Index, with conditions:

**Reasons to BUILD on NANDA:**
1. **Switchboard is genuinely unique** — Cross-registry discovery is a real differentiator that would take 3+ weeks to build from scratch
2. **AGNTCY alignment** — Building on AGNTCY/OASF standards (now Linux Foundation) gives us credibility and interoperability
3. **4-5 weeks of saved effort** — Basic registry, persistence, and federation already work
4. **MongoDB is the right choice** — Flexible schema supports our evolving data model
5. **Adapter pattern is extensible** — Easy to add new registry sources (Hugging Face, custom enterprise registries)

**Conditions for GO:**
1. **Fork the repository** — Don't depend on upstream; maintain our version
2. **Security first** — Auth layer must be complete before any deployment
3. **Refactor before extending** — Break up the monolith before adding features
4. **Plan for FastAPI migration** — Flask will become a bottleneck; plan the migration early

### ❌ Reasons we might STOP:
- If NANDA maintainer goes hostile (license change, etc.) — mitigated by forking
- If AGNTCY standard dies — unlikely given Linux Foundation backing
- If a competitor launches an identical open-source product — monitor CrewAI/LangGraph closely

---

## 8. Revised Effort Estimate

| Phase | Original Estimate | Revised Estimate | Delta | Reason |
|-------|-------------------|------------------|-------|--------|
| Phase 0: Foundation | 2 weeks | 3-4 weeks | +1-2 weeks | NANDA hardening (auth, refactor, containerize) |
| Phase 1: Core Platform | 3 weeks | 3 weeks | Same | Template system + wizard (NANDA saves time on registry) |
| Phase 2: Agent Generation | 3 weeks | 3 weeks | Same | Code generation is new work regardless |
| Phase 3: Deployment | 3 weeks | 3-4 weeks | +0-1 weeks | Deployment infra + FastAPI migration |
| Phase 4: Polish | 2 weeks | 2-3 weeks | +0-1 weeks | Marketplace + billing |
| Phase 5: Launch | 1 week | 1 week | Same | — |
| **Total** | **14 weeks** | **15-18 weeks** | **+1-4 weeks** | Hardening cost offset by registry savings |

---

## 9. Summary of Key Metrics

```
┌─────────────────────────────────────────────────┐
│  NANDA Index as My-Agent-Too Backend             │
├─────────────────────────────────────────────────┤
│  Feasibility:          ██████████░░  YES (8/10)  │
│  Code Maturity:        ██░░░░░░░░░░  LOW (2.6/10)│
│  Effort Saved:         ~4-5 weeks                │
│  Hardening Needed:     ~3-4 weeks                │
│  Net Savings:          ~1-2 weeks + unique features│
│  Unique Differentiator: Switchboard (cross-registry)│
│  Biggest Risk:         Security (zero auth)      │
│  Biggest Opportunity:  AGNTCY/OASF standards     │
│  Recommendation:       FORK → HARDEN → BUILD     │
└─────────────────────────────────────────────────┘
```

---

*This analysis is based on a line-by-line review of the NANDA Index codebase (registry.py, switchboard, adapters, tests, batch tools) and competitive research conducted February 2026.*

---

