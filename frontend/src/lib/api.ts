/** API client for the +12 Monkeys backend wizard endpoints. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ExtractedRequirements {
  use_case: string | null;
  description: string | null;
  integrations: string[];
  capabilities: string[];
  scale: string | null;
  compliance: string[];
  framework_preference: string | null;
  deployment_preference: string | null;
  additional_notes: string | null;
}

export interface MCPServerSummary {
  name: string;
  command: string;
  args: string[];
  required_env: string[];
  category: string;
}

export interface Recommendation {
  framework: string;
  framework_reason: string;
  agents: { role: string; goal: string }[];
  mcp_servers: MCPServerSummary[];
  deployment: string;
  estimated_monthly_cost: string | null;
  summary: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  status: string;
  requirements: ExtractedRequirements | null;
  recommendation: Recommendation | null;
}

// ---------- Generated package types ----------

export interface GeneratedFile {
  path: string;
  content: string;
  language: string;
}

export interface GeneratedPackage {
  project_name: string;
  template_id: string;
  framework: string;
  deployment: string;
  files: GeneratedFile[];
  summary: string;
  setup_instructions: string[];
  env_vars: string[];
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  framework: string;
  agents: { role: string; goal: string }[];
  mcp_servers: MCPServerSummary[];
  tags: string[];
  estimated_cost: string | null;
}

// ---------- API calls ----------

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v1/wizard/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
    }),
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

/** SSE event from the streaming chat endpoint. */
export interface StreamEvent {
  event: "status" | "delta" | "done";
  data: string;
}

/**
 * Send a message via the streaming endpoint.
 * Calls `onEvent` for each SSE event received.
 * Returns the final ChatResponse from the `done` event.
 */
export async function sendMessageStream(
  message: string,
  sessionId: string | undefined,
  onEvent: (evt: StreamEvent) => void
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v1/wizard/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let finalResponse: ChatResponse | null = null;

  // SSE parse state (per-event accumulator)
  let currentEvent = "delta";
  let dataChunks: string[] = [];

  function dispatchEvent() {
    if (dataChunks.length === 0) return;
    const rawData = dataChunks.join("\n");
    dataChunks = [];
    try {
      const parsed = JSON.parse(rawData);
      if (currentEvent === "done") {
        finalResponse = typeof parsed === "string" ? JSON.parse(parsed) : parsed;
        onEvent({ event: "done", data: typeof parsed === "string" ? parsed : rawData });
      } else {
        onEvent({ event: currentEvent as StreamEvent["event"], data: parsed });
      }
    } catch {
      onEvent({ event: currentEvent as StreamEvent["event"], data: rawData });
    }
    currentEvent = "delta";
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line === "") {
        // Blank line = end of event — dispatch accumulated data
        dispatchEvent();
      } else if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        dataChunks.push(line.slice(6));
      } else if (line.startsWith("data:")) {
        // "data:" with no space — value is everything after the colon
        dataChunks.push(line.slice(5));
      } else if (line.startsWith("id: ") || line.startsWith("id:")) {
        // Acknowledge but we don't track lastEventId for now
      } else if (line.startsWith("retry: ") || line.startsWith("retry:")) {
        // Server-suggested reconnect interval — ignored for now
      } else if (line.startsWith(":")) {
        // SSE comment — ignore
      }
    }
  }
  // Flush any trailing event without a final blank line
  dispatchEvent();

  if (!finalResponse) {
    throw new Error("Stream ended without a done event");
  }
  return finalResponse;
}

export async function confirmAndGenerate(
  sessionId: string,
  projectName: string = "my-agent"
): Promise<GeneratedPackage> {
  const res = await fetch(
    `${API_BASE}/api/v1/wizard/sessions/${sessionId}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_name: projectName }),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ---------- MCP Server types ----------

export interface MCPToolSchema {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

export interface MCPServerEntry {
  id: string;
  name: string;
  description: string;
  category: string;
  command: string;
  args: string[];
  endpoint_url: string | null;
  required_env: string[];
  optional_env: string[];
  npm_package: string | null;
  documentation_url: string | null;
  icon: string | null;
  tags: string[];
  status: "unknown" | "healthy" | "unhealthy" | "checking";
  tools: MCPToolSchema[];
  last_health_check: string | null;
  is_official: boolean;
}

export interface MCPServerListResponse {
  servers: MCPServerEntry[];
  total: number;
  categories: string[];
}

export interface MCPHealthResult {
  server_id: string;
  status: "unknown" | "healthy" | "unhealthy" | "checking";
  tools_count: number;
  tools: MCPToolSchema[];
  response_time_ms: number;
  error: string | null;
  checked_at: string;
}

// ---------- MCP API calls ----------

export async function fetchMCPServers(
  category?: string,
  search?: string,
): Promise<MCPServerListResponse> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (search) params.set("search", search);
  const qs = params.toString();
  const res = await fetch(`${API_BASE}/api/v1/mcp/servers${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function runMCPHealthCheck(
  serverId: string,
  projectId?: string,
): Promise<MCPHealthResult> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  const qs = params.toString();
  const res = await fetch(
    `${API_BASE}/api/v1/mcp/servers/${serverId}/healthcheck${qs ? `?${qs}` : ""}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function storeMCPCredentials(
  projectId: string,
  serverId: string,
  credentials: Record<string, string>,
): Promise<{ project_id: string; server_id: string; keys_stored: string[] }> {
  const res = await fetch(`${API_BASE}/api/v1/mcp/credentials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, server_id: serverId, credentials }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}



