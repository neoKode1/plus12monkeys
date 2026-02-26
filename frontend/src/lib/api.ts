/** API client for the +12 Monkeys backend wizard endpoints. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Typed error & fetch helper
// ---------------------------------------------------------------------------

/** Structured API error with HTTP status and retry hint. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly retryable: boolean = false,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1_000;
const RETRYABLE_STATUSES = new Set([429, 502, 503, 504]);

/**
 * Thin wrapper around `fetch` that adds:
 * - Timeout via AbortController
 * - Automatic retry for transient failures (429 / 5xx / network errors)
 * - Typed `ApiError` instead of generic `Error`
 */
async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit & { timeout?: number; retries?: number },
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT_MS, retries = MAX_RETRIES, ...fetchInit } =
    init ?? {};

  let lastError: ApiError | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(input, { ...fetchInit, signal: controller.signal, credentials: "include" });
      clearTimeout(timer);

      if (res.ok) return res;

      const body = await res.json().catch(() => ({ detail: res.statusText }));
      const detail: string =
        body?.detail || body?.message || `HTTP ${res.status}`;
      const canRetry = RETRYABLE_STATUSES.has(res.status);

      if (canRetry && attempt < retries) {
        lastError = new ApiError(res.status, detail, true);
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)));
        continue;
      }
      throw new ApiError(res.status, detail, canRetry);
    } catch (err) {
      clearTimeout(timer);
      if (err instanceof ApiError) throw err;

      const isAbort =
        err instanceof DOMException && err.name === "AbortError";
      const msg = isAbort
        ? `Request timed out after ${timeout}ms`
        : String(err);

      if (attempt < retries) {
        lastError = new ApiError(0, msg, true);
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)));
        continue;
      }
      throw new ApiError(0, msg, true);
    }
  }
  throw lastError ?? new ApiError(0, "Unexpected retry loop exit", false);
}

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
  const res = await apiFetch(`${API_BASE}/api/v1/wizard/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });
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
  // Streaming: no retry (can't replay a partial stream), longer timeout
  const res = await apiFetch(`${API_BASE}/api/v1/wizard/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId || null }),
    retries: 0,
    timeout: 120_000,
  });

  const reader = res.body?.getReader();
  if (!reader) throw new ApiError(0, "No response body", false);

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
    throw new ApiError(0, "Stream ended without a done event", true);
  }
  return finalResponse;
}

export async function confirmAndGenerate(
  sessionId: string,
  projectName: string = "my-agent"
): Promise<GeneratedPackage> {
  const res = await apiFetch(
    `${API_BASE}/api/v1/wizard/sessions/${sessionId}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_name: projectName }),
      timeout: 60_000,
    }
  );
  return res.json();
}

// ---------- MCP Server types ----------

export interface MCPToolSchema {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  safety_level: "safe" | "moderate" | "dangerous";
  task_name_active: string | null;
  task_name_complete: string | null;
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
  const res = await apiFetch(`${API_BASE}/api/v1/mcp/servers${qs ? `?${qs}` : ""}`);
  return res.json();
}

export async function runMCPHealthCheck(
  serverId: string,
  projectId?: string,
): Promise<MCPHealthResult> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  const qs = params.toString();
  const res = await apiFetch(
    `${API_BASE}/api/v1/mcp/servers/${serverId}/healthcheck${qs ? `?${qs}` : ""}`,
    { method: "POST" },
  );
  return res.json();
}

export async function storeMCPCredentials(
  projectId: string,
  serverId: string,
  credentials: Record<string, string>,
): Promise<{ project_id: string; server_id: string; keys_stored: string[] }> {
  const res = await apiFetch(`${API_BASE}/api/v1/mcp/credentials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, server_id: serverId, credentials }),
  });
  return res.json();
}
