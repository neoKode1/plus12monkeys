<p align="center">
  <img src="https://raw.githubusercontent.com/neoKode1/plus12monkeys/main/frontend/public/12m.png" alt="+12 Monkeys" width="600" />
</p>

<h1 align="center">+12 Monkeys</h1>

<p align="center"><strong>Agent-as-a-Service Platform with MCP Integration</strong></p>

<p align="center">
  <em>Build and deploy custom AI agents in under 10 minutes through conversational configuration.</em>
</p>

<p align="center">
  <a href="https://plus12monkeys.com"><img src="https://img.shields.io/badge/site-plus12monkeys.com-black?style=for-the-badge" alt="Website" /></a>&nbsp;
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge" alt="Status" />&nbsp;
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License" />&nbsp;
  <img src="https://img.shields.io/badge/MCP-compatible-8B5CF6?style=for-the-badge" alt="MCP" />
</p>

---

## What is +12 Monkeys?

+12 Monkeys is a **plug-and-play platform** that enables developers to create, configure, and deploy production-ready AI agent systems without writing code. Simply describe what you need in natural language, and the platform generates a **complete deployable package** — Python, TypeScript, Rust, or Go — ready to deploy with `docker compose up`, Railway, Render, or Vercel.

---

### Key Features

| | Feature | Description |
|---|---|---|
| 💬 | **Conversational Config** | No code required — just describe what you need in plain English |
| 🔌 | **MCP-Native** | Built on Model Context Protocol (Linux Foundation standard) |
| 🎨 | **20 Agent Templates** | Customer service, research, data analysis, code gen, multi-agent teams, and 15 more |
| 🚀 | **3 Deploy Targets** | LOCAL (Docker Compose) · CLOUD (Railway / Render / Vercel) · EXPORT (self-host) |
| 🔧 | **Multi-Framework** | LangGraph · CrewAI · AutoGen · Semantic Kernel · Vercel AI SDK · Rig · ADK-Go |

### Supported Languages

| | Language | Output |
|---|---|---|
| 🐍 | **Python** | `agent.py` · `requirements.txt` · `Dockerfile` (3.12) · `docker-compose.yml` |
| 📘 | **TypeScript** | `agent.ts` · `package.json` · `tsconfig.json` · `Dockerfile` (Node 22) |
| 🦀 | **Rust** | `src/main.rs` · `Cargo.toml` · multi-stage `Dockerfile` (1.84) |
| 🐹 | **Go** | `main.go` · `go.mod` · multi-stage `Dockerfile` (1.23 → distroless) |

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