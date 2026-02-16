# 🔗 NANDA Index Integration Plan

**How My-Agent-Too will integrate with NANDA Index for agent discovery and management**

---

## 🎯 Executive Summary

**NANDA Index** is a unified agent registry that provides exactly what My-Agent-Too needs for its backend:
- Agent registration and discovery
- MongoDB persistence
- MCP server registry
- Cross-index federation (AGNTCY ADS integration)
- Skill taxonomy mapping

**Integration Strategy:** Use NANDA Index as the **core registry backend** for My-Agent-Too, eliminating the need to build a custom agent storage system.

---

## 📊 What NANDA Index Provides

### Core Features
1. **Agent Registry** - Store and retrieve agent metadata
2. **Capabilities-based Search** - Query agents by skills and tags
3. **MongoDB Persistence** - Durable storage with flexible schema
4. **MCP Registry** - Already has MCP server tracking (perfect for our use case!)
5. **Client-Agent Allocation** - Automatic assignment and tracking
6. **SSL Support** - Production-ready deployment

### Advanced Features
1. **Switchboard** - Cross-index discovery (AGNTCY ADS integration via gRPC)
2. **Batch Operations** - Export/import OASF records
3. **Skill Taxonomy Mapping** - Intelligent capability translation
4. **Schema Translation** - OASF ↔ NANDA AgentFacts conversion

---

## 🏗️ Integration Architecture

### Before (Original My-Agent-Too Plan)
```
User Chat → Agent Orchestrator → Template Selection → 
Code Generation → PostgreSQL (custom schema) → Deployment
```

### After (With NANDA Integration)
```
User Chat → Agent Orchestrator → Template Selection → 
Code Generation → NANDA Index (agent registry) → Deployment
                                ↓
                         MongoDB (persistence)
                                ↓
                    Switchboard (cross-index discovery)
```

### System Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                   My-Agent-Too Platform                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Frontend (Next.js)                                    │ │
│  │  - Chat Interface                                      │ │
│  │  - Dashboard                                           │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  API Layer (Express/FastAPI)                          │ │
│  │  - Authentication                                      │ │
│  │  - WebSocket                                           │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Agent Orchestrator (Claude + LangChain)              │ │
│  │  - Requirement analysis                                │ │
│  │  - Architecture recommendation                         │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Code Generator (Jinja2)                              │ │
│  │  - Template rendering                                  │ │
│  │  - Package creation                                    │ │
│  └────────────────────┬───────────────────────────────────┘ │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 NANDA Index (Port 6900)                      │
│  ┌────────────────┐  ┌──────────────────────────────────┐  │
│  │  Core Index    │  │  Switchboard                     │  │
│  │  - /register   │  │  - Cross-index discovery         │  │
│  │  - /search     │  │  - AGNTCY ADS integration        │  │
│  │  - /mcp_servers│  │  - Schema translation            │  │
│  └────────┬───────┘  └──────────────────────────────────┘  │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
     MongoDB (Persistence)
     - agent_registry
     - mcp_registry
     - client_registry
```

---

## 🔌 Integration Points

### 1. Agent Template Storage
**Original Plan:** Custom PostgreSQL schema  
**With NANDA:** Use NANDA's agent registry

**How:**
- When user creates an agent via My-Agent-Too chat
- Agent Orchestrator recommends architecture
- Code Generator creates package
- **Register agent in NANDA Index** via `POST /register`
- Store agent metadata: name, capabilities, MCP servers, deployment info

**Example:**
```python
# my-agent-too/backend/nanda_client.py
import requests

class NANDAClient:
    def __init__(self, nanda_url="http://localhost:6900"):
        self.base_url = nanda_url
    
    def register_agent(self, agent_data):
        """Register a generated agent in NANDA Index"""
        response = requests.post(
            f"{self.base_url}/register",
            json={
                "agent_id": agent_data["agent_id"],
                "agent_name": agent_data["name"],
                "agent_url": agent_data["repo_url"],
                "api_url": agent_data["api_endpoint"],
                "capabilities": agent_data["capabilities"],
                "framework": agent_data["framework"],  # LangGraph, CrewAI, etc.
                "mcp_servers": agent_data["mcp_servers"],
                "deployment_type": agent_data["deployment"],  # local, cloud, export
                "created_by": agent_data["user_id"]
            }
        )
        return response.json()
```

### 2. MCP Server Registry
**Original Plan:** Custom MCP server tracking  
**With NANDA:** Use existing `/mcp_servers` endpoint

**How:**
- NANDA already has `mcp_registry` collection in MongoDB
- My-Agent-Too can query available MCP servers
- Agent Orchestrator uses this to recommend integrations

**Example:**
```python
def get_available_mcp_servers(self):
    """Get list of available MCP servers from NANDA"""
    response = requests.get(f"{self.base_url}/mcp_servers")
    return response.json()

def recommend_mcp_servers(self, user_requirements):
    """Recommend MCP servers based on user needs"""
    available_servers = self.get_available_mcp_servers()
    
    # Filter based on requirements
    if "salesforce" in user_requirements["integrations"]:
        return [s for s in available_servers if s["name"] == "salesforce"]
```

### 3. Agent Discovery
**Original Plan:** Custom search functionality  
**With NANDA:** Use `/search` endpoint with capabilities-based search

**How:**
- Users can browse previously created agents
- Search by framework, capabilities, MCP servers
- Reuse existing agent templates

**Example:**
```python
def search_agents(self, query=None, capabilities=None, framework=None):
    """Search for agents in NANDA Index"""
    params = {}
    if query:
        params["query"] = query
    if capabilities:
        params["capabilities"] = ",".join(capabilities)
    if framework:
        params["tags"] = framework
    
    response = requests.get(f"{self.base_url}/search", params=params)
    return response.json()
```

### 4. Cross-Framework Discovery (Switchboard)
**Original Plan:** Not planned  
**With NANDA:** Leverage Switchboard for AGNTCY ADS integration

**How:**
- Enable federation: `ENABLE_FEDERATION=true`
- My-Agent-Too can discover agents from external indices
- Users can import agents from AGNTCY ecosystem

**Example:**
```python
def lookup_external_agent(self, agent_id):
    """Lookup agent from external index via Switchboard"""
    # agent_id format: @agntcy:helper-agent
    response = requests.get(f"{self.base_url}/switchboard/lookup/{agent_id}")
    return response.json()
```

---

## 📋 Updated Database Schema

### MongoDB Collections (via NANDA)

**1. agent_registry** (NANDA native)
```javascript
{
  agent_id: "customer-service-agent-001",
  agent_name: "Customer Service Agent",
  agent_url: "https://github.com/user/cs-agent",
  api_url: "https://cs-agent.railway.app",
  capabilities: ["customer_support", "ticket_routing", "sentiment_analysis"],
  framework: "crewai",
  mcp_servers: ["salesforce", "slack", "email"],
  deployment_type: "cloud",
  created_by: "user_123",
  alive: true,
  last_update: "2026-02-16T10:00:00Z"
}
```

**2. mcp_registry** (NANDA native)
```javascript
{
  server_name: "salesforce",
  command: "npx",
  args: ["-y", "@salesforce/mcp-server"],
  required_env: ["SALESFORCE_INSTANCE_URL", "SALESFORCE_ACCESS_TOKEN"],
  description: "Salesforce CRM integration",
  category: "crm"
}
```

**3. users** (My-Agent-Too specific - extend NANDA)
```javascript
{
  user_id: "user_123",
  email: "developer@example.com",
  created_at: "2026-01-01T00:00:00Z",
  subscription_tier: "pro",
  agent_count: 5
}
```

**4. agent_projects** (My-Agent-Too specific - new collection)
```javascript
{
  project_id: "proj_456",
  user_id: "user_123",
  agent_id: "customer-service-agent-001",
  conversation_history: [...],
  generated_code: {...},
  deployment_status: "deployed",
  created_at: "2026-02-16T09:00:00Z"
}
```

---

## 🚀 Implementation Plan

### Phase 0: Foundation (Weeks 1-2) - UPDATED
- [x] Set up NANDA Index locally
- [ ] Configure MongoDB connection
- [ ] Create NANDA client library for My-Agent-Too
- [ ] Test agent registration flow
- [ ] Extend NANDA schema with My-Agent-Too specific fields

### Phase 2: Agent Template Library (Weeks 5-6) - UPDATED
- [ ] Register 5 core templates in NANDA Index
- [ ] Use NANDA's capabilities-based search for template discovery
- [ ] Implement template reuse via NANDA lookup

### Phase 3: MCP Integration (Weeks 7-8) - UPDATED
- [ ] Populate NANDA's mcp_registry with 10+ MCP servers
- [ ] Use `/mcp_servers` endpoint in Agent Orchestrator
- [ ] Implement MCP server recommendation logic

### Phase 5: Deployment Engine (Weeks 11-12) - UPDATED
- [ ] Update agent status in NANDA after deployment
- [ ] Track deployment URLs in NANDA's `api_url` field
- [ ] Enable Switchboard for cross-index discovery

---

## ✅ Benefits of Integration

1. **Reduced Development Time** - Don't build custom registry (save 2-3 weeks)
2. **MongoDB Persistence** - Production-ready storage out of the box
3. **MCP Registry** - Already has MCP server tracking
4. **Cross-Index Discovery** - Switchboard enables AGNTCY integration
5. **Skill Taxonomy** - Intelligent capability mapping
6. **Proven Architecture** - NANDA is battle-tested
7. **Future-Proof** - OASF/AgentFacts schema compatibility

---

## 🔄 Next Steps

1. ✅ Clone NANDA Index repository
2. [ ] Set up local NANDA Index instance
3. [ ] Test NANDA API endpoints
4. [ ] Create NANDA client library for My-Agent-Too
5. [ ] Update SPRINT_PLAN.md with NANDA integration
6. [ ] Begin Phase 0 implementation

---

**Ready to integrate!** 🚀

