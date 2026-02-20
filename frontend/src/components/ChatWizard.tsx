"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChatResponse,
  confirmAndGenerate,
  GeneratedFile,
  GeneratedPackage,
  Recommendation,
  sendMessage,
} from "@/lib/api";


interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
}

/* ── Icon helpers (inline SVG to avoid external deps) ── */
const IconX = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
);
const IconCopy = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
);
const IconDownload = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
);
const IconThumbUp = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>
);
const IconThumbDown = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></svg>
);
const IconSend = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
);
const IconAttach = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
);
const IconBookmark = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>
);
const IconHistory = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
);
const IconEdit = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838.838-2.872a2 2 0 0 1 .506-.855z"/></svg>
);

/* ── Markdown formatting with proper list support ── */
function formatAssistant(text: string) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const lines = escaped.split("\n");
  const result: string[] = [];
  let inUl = false;
  let inOl = false;

  for (const line of lines) {
    const trimmed = line.trim();

    // Bullet list item
    if (/^[•\-\*]\s+/.test(trimmed)) {
      if (!inUl) { result.push("<ul>"); inUl = true; }
      if (inOl) { result.push("</ol>"); inOl = false; }
      result.push(`<li>${trimmed.replace(/^[•\-\*]\s+/, "")}</li>`);
      continue;
    }
    // Numbered list item
    if (/^[0-9]+[\.\)]\s+/.test(trimmed)) {
      if (!inOl) { result.push("<ol>"); inOl = true; }
      if (inUl) { result.push("</ul>"); inUl = false; }
      result.push(`<li>${trimmed.replace(/^[0-9]+[\.\)]\s+/, "")}</li>`);
      continue;
    }
    // Close any open lists
    if (inUl) { result.push("</ul>"); inUl = false; }
    if (inOl) { result.push("</ol>"); inOl = false; }

    if (trimmed === "") {
      result.push("<br/>");
    } else {
      result.push(`<p>${trimmed}</p>`);
    }
  }
  if (inUl) result.push("</ul>");
  if (inOl) result.push("</ol>");

  return result
    .join("")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

/* ── Typewriter hook ── */
function useTypewriter(text: string, speed = 18) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    if (!text) { setDone(true); return; }

    let i = 0;
    const id = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(id);
        setDone(true);
      }
    }, speed);
    return () => clearInterval(id);
  }, [text, speed]);

  return { displayed, done };
}

/* ── Typewriter message wrapper ── */
function TypewriterMessage({
  content,
  onDone,
}: {
  content: string;
  onDone?: () => void;
}) {
  const { displayed, done } = useTypewriter(content, 14);

  useEffect(() => {
    if (done && onDone) onDone();
  }, [done, onDone]);

  return (
    <span className={done ? "" : "typewriter-cursor"}>
      <span dangerouslySetInnerHTML={{ __html: formatAssistant(displayed) }} />
    </span>
  );
}

/* ── Progress Stepper ── */
const STEPS = [
  { key: "gathering", label: "Describe", icon: "💬" },
  { key: "recommending", label: "Analyze", icon: "🔍" },
  { key: "confirmed", label: "Build", icon: "🛠️" },
  { key: "complete", label: "Ready", icon: "✅" },
];

function ProgressStepper({ status }: { status: string }) {
  const currentIdx = STEPS.findIndex((s) => s.key === status);
  const idx = currentIdx === -1 ? 0 : currentIdx;

  return (
    <div className="flex items-center justify-center gap-0 py-3 px-4">
      {STEPS.map((step, i) => {
        const isDone = i < idx;
        const isActive = i === idx;
        return (
          <div key={step.key} className="flex items-center">
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-500 ${
              isDone ? "text-[#34D399]" : isActive ? "text-[#6C63FF] bg-[#6C63FF]/10" : "text-[#555]"
            }`}>
              <span>{isDone ? "✓" : step.icon}</span>
              <span>{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className="w-8 h-[2px] mx-1 rounded step-connector"
                style={{ background: i < idx ? "#34D399" : i === idx ? "#6C63FF" : "#2A2A2A" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function ChatWizard() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [analyzingRepo, setAnalyzingRepo] = useState(false);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [status, setStatus] = useState("gathering");
  const [generatedPkg, setGeneratedPkg] = useState<GeneratedPackage | null>(null);
  const [generating, setGenerating] = useState(false);
  const [previewFile, setPreviewFile] = useState<GeneratedFile | null>(null);
  const [projectName, setProjectName] = useState("my-agent");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [typingIdx, setTypingIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content:
          "Start building your MCP server, agent, or SDK package.\n\nDescribe what you're building and I'll generate the full stack — framework, deployment config, and MCP integration included.",
      },
    ]);
  }, []);

  const handleCopy = useCallback((text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  }, []);

  /* Detect GitHub/HuggingFace URLs in text */
  const isRepoUrl = (text: string) =>
    /https?:\/\/(github\.com|huggingface\.co)\/[^\s]+/.test(text) ||
    /git@github\.com:[^\s]+/.test(text);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    if (isRepoUrl(text)) setAnalyzingRepo(true);

    try {
      const res: ChatResponse = await sendMessage(text, sessionId);
      if (!sessionId) setSessionId(res.session_id);
      setStatus(res.status);
      setMessages((prev) => {
        const next = [...prev, { role: "assistant" as const, content: res.reply }];
        setTypingIdx(next.length - 1); // trigger typewriter on new msg
        return next;
      });
      if (res.recommendation) {
        setRecommendation(res.recommendation);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Failed to reach the server. Is the backend running?" },
      ]);
    } finally {
      setLoading(false);
      setAnalyzingRepo(false);
    }
  }, [input, loading, sessionId]);

  const handleGenerate = useCallback(async () => {
    if (!sessionId || generating) return;
    setGenerating(true);
    try {
      const pkg = await confirmAndGenerate(sessionId, projectName);
      setGeneratedPkg(pkg);
      setStatus("complete");
      setPreviewFile(pkg.files[0] || null);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `🎉 Your agent **"${pkg.project_name}"** has been generated!\n\n${pkg.summary}\n\nCheck the preview below.`,
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Generation failed";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ ${msg}` },
      ]);
    } finally {
      setGenerating(false);
    }
  }, [sessionId, generating, projectName]);

  return (
    <div className="flex h-screen flex-col" style={{ background: "#0D0D0D", color: "#E8E8E8" }}>

      {/* ══════════ Top Header Bar ══════════ */}
      <header className="border-b" style={{ borderColor: "#1A1A1A" }}>
        <div className="flex items-center justify-between px-5 py-3">
          {/* Left: brand logo */}
          <div className="flex items-center gap-2.5">
            <img
              src="/favicon-monkey.png"
              alt="+12 Monkeys"
              className="h-9 w-9 brightness-0 invert"
            />
            <span
              className="text-white uppercase"
              style={{
                fontSize: "24px",
                fontFamily: "var(--font-brand), 'Barlow Condensed', sans-serif",
                fontWeight: 300,
                letterSpacing: "0.16em",
                lineHeight: 1,
              }}
            >
              +12 Monkeys
            </span>
          </div>

          {/* Center: stepper (moved here for balance) */}
          <ProgressStepper status={status} />

          {/* Right: actions */}
          <div className="flex items-center gap-1">
            <a href="/mcp" className="px-2.5 py-1 rounded-lg text-[12px] font-medium text-[#6C63FF] hover:bg-[#6C63FF]/10 transition">
              MCP Servers
            </a>
            {[IconDownload, IconBookmark, IconHistory, IconEdit].map((Icon, i) => (
              <button key={i} className="p-1.5 rounded-lg transition hover:bg-white/10 text-[#888]">
                <Icon />
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* ══════════ Messages ══════════ */}
      <div className="flex-1 overflow-y-auto flex flex-col justify-center">
        <div className="max-w-3xl mx-auto px-6 py-6 space-y-6 w-full">
          {messages.map((m, i) => (
            <div key={i} className="msg-enter">
              {m.role === "user" ? (
                /* ── User bubble ── */
                <div className="flex justify-end">
                  <div className="max-w-[80%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed"
                    style={{ background: "#1A1A1A", color: "#E8E8E8" }}>
                    {m.content}
                  </div>
                </div>
              ) : (
                /* ── Assistant flowing text (typewriter for latest) ── */
                <div className="space-y-2">
                  <div className="assistant-content text-[14px] leading-[1.75] text-[#D4D4D4]">
                    {typingIdx === i ? (
                      <TypewriterMessage
                        content={m.content}
                        onDone={() => setTypingIdx(null)}
                      />
                    ) : (
                      <span dangerouslySetInnerHTML={{ __html: formatAssistant(m.content) }} />
                    )}
                  </div>
                  {/* Action buttons row (only show when not typing) */}
                  {typingIdx !== i && (
                    <div className="flex items-center gap-1 pt-1">
                      <button
                        onClick={() => handleCopy(m.content, i)}
                        className="p-1.5 rounded-md transition hover:bg-white/10 text-[#555] hover:text-[#aaa]"
                        title="Copy"
                      >
                        {copiedIdx === i ? (
                          <span className="text-[11px] text-green-400 px-1">Copied</span>
                        ) : (
                          <IconCopy />
                        )}
                      </button>
                      <button className="p-1.5 rounded-md transition hover:bg-white/10 text-[#555] hover:text-[#aaa]" title="Good response">
                        <IconThumbUp />
                      </button>
                      <button className="p-1.5 rounded-md transition hover:bg-white/10 text-[#555] hover:text-[#aaa]" title="Bad response">
                        <IconThumbDown />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="msg-enter flex items-center gap-1 py-2">
              {analyzingRepo ? (
                <span className="text-sm text-[#6C63FF] flex items-center gap-2">
                  <span className="typing-dot w-2 h-2 rounded-full bg-[#6C63FF]" />
                  🔍 Analyzing repository…
                </span>
              ) : (
                <>
                  <span className="typing-dot w-2 h-2 rounded-full bg-[#6C63FF]" />
                  <span className="typing-dot w-2 h-2 rounded-full bg-[#6C63FF]" />
                  <span className="typing-dot w-2 h-2 rounded-full bg-[#6C63FF]" />
                </>
              )}
            </div>
          )}
          {/* ══════════ Input Box (inside message flow) ══════════ */}
          <div className="pt-4">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSend(); }}
              className="flex items-center gap-2 rounded-2xl px-4 py-2"
              style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}
            >
              <button type="button" className="p-1.5 rounded-lg text-[#555] hover:text-[#aaa] transition hover:bg-white/5">
                <IconAttach />
              </button>
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything"
                className="flex-1 bg-transparent text-[14px] text-[#E8E8E8] placeholder-[#555] outline-none py-2"
                disabled={loading || status === "complete"}
              />
              <button
                type="submit"
                disabled={loading || !input.trim() || status === "complete"}
                className="p-2 rounded-full transition disabled:opacity-30"
                style={{ background: input.trim() ? "#6C63FF" : "#333" }}
              >
                <IconSend />
              </button>
            </form>
          </div>

          <div ref={bottomRef} />
        </div>
      </div>

      {/* ══════════ Recommendation panel ══════════ */}
      {recommendation && !generatedPkg && (
        <RecommendationPanel
          rec={recommendation}
          projectName={projectName}
          setProjectName={setProjectName}
          onGenerate={handleGenerate}
          generating={generating}
          messages={messages}
        />
      )}

      {/* ══════════ Generated package preview ══════════ */}
      {generatedPkg && (
        <PackagePreview
          pkg={generatedPkg}
          previewFile={previewFile}
          onSelectFile={setPreviewFile}
        />
      )}
    </div>
  );
}


/* ══════════ Sub-components ══════════ */

function RecommendationPanel({
  rec,
  projectName,
  setProjectName,
  onGenerate,
  generating,
  messages,
}: {
  rec: Recommendation;
  projectName: string;
  setProjectName: (v: string) => void;
  onGenerate: () => void;
  generating: boolean;
  messages: DisplayMessage[];
}) {
  /* Detect if the user is a developer based on their messages */
  const devTerms = /\b(api|mcp|framework|rag|deploy|webhook|sdk|repo|github|langchain|crewai|langgraph|autogen|semantic.kernel|vercel|nextjs|next\.js|typescript|docker|kubernetes|k8s|endpoint|microservice|llm|vector|embedding|rust|rig|cargo|go|golang|adk|tokio|goroutine|lambda|sam|serverless)\b/i;
  const isDeveloper = messages
    .filter((m) => m.role === "user")
    .some((m) => devTerms.test(m.content));

  /* Adaptive deployment label */
  const friendlyDeployment = isDeveloper
    ? rec.deployment === "cloud" ? "Cloud (hosted)" : rec.deployment === "local" ? "Local" : rec.deployment
    : rec.deployment === "cloud"
      ? "We'll host it for you in the cloud"
      : rec.deployment === "local"
        ? "Runs on your own computer"
        : rec.deployment;

  const capabilities = rec.agents.map((a) => a.goal || a.role);
  const connectedServices =
    rec.mcp_servers.length > 0
      ? rec.mcp_servers.map((s) => {
          if (isDeveloper) return s.name;
          /* Pretty-print known server names for consumers */
          const friendly: Record<string, string> = {
            twilio: "📞 Phone & SMS",
            "google-calendar": "📅 Google Calendar",
            slack: "💬 Slack",
            gmail: "✉️ Email",
            salesforce: "📊 Salesforce",
            stripe: "💳 Payments",
            shopify: "🛒 Online Store",
            notion: "📝 Notion",
            github: "🐙 GitHub",
          };
          return friendly[s.name] || s.name;
        })
      : [isDeveloper ? "None" : "No extra services needed"];

  return (
    <div className="border-t px-4 py-4" style={{ borderColor: "#1A1A1A", background: "#111111" }}>
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">✨</span>
          <h2 className="text-sm font-semibold text-[#34D399]">
            {isDeveloper ? "Agent Configuration" : "Your AI Assistant Plan"}
          </h2>
        </div>
        <p className="text-[13px] text-[#B0B0B0] leading-relaxed">{rec.summary}</p>

        <div className="grid grid-cols-2 gap-3 text-xs">
          {/* Framework card — developers only */}
          {isDeveloper && (
            <div className="rounded-xl p-3" style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}>
              <span className="text-[#666] text-[11px] uppercase tracking-wide">Framework</span>
              <p className="mt-1 font-medium text-[#E8E8E8] text-[13px]">{rec.framework}</p>
              <p className="mt-0.5 text-[11px] text-[#888]">{rec.framework_reason}</p>
            </div>
          )}
          <div className="rounded-xl p-3" style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}>
            <span className="text-[#666] text-[11px] uppercase tracking-wide">
              {isDeveloper ? "Agent roles" : "What it can do"}
            </span>
            <ul className="mt-1 space-y-0.5">
              {capabilities.map((c, i) => (
                <li key={i} className="font-medium text-[#E8E8E8] text-[13px]">• {c}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl p-3" style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}>
            <span className="text-[#666] text-[11px] uppercase tracking-wide">
              {isDeveloper ? "MCP servers" : "Connected services"}
            </span>
            <ul className="mt-1 space-y-0.5">
              {connectedServices.map((s, i) => (
                <li key={i} className="font-medium text-[#E8E8E8] text-[13px]">{isDeveloper ? s : s}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl p-3" style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}>
            <span className="text-[#666] text-[11px] uppercase tracking-wide">
              {isDeveloper ? "Deployment" : "Hosting"}
            </span>
            <p className="mt-1 font-medium text-[#E8E8E8] text-[13px]">{friendlyDeployment}</p>
          </div>
          {rec.estimated_monthly_cost && (
            <div className="rounded-xl p-3" style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}>
              <span className="text-[#666] text-[11px] uppercase tracking-wide">Estimated cost</span>
              <p className="mt-1 font-medium text-[#E8E8E8] text-[13px]">About {rec.estimated_monthly_cost}/month</p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 pt-1">
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder={isDeveloper ? "Project name" : "Name your assistant"}
            className="rounded-xl px-3 py-2 text-sm text-[#E8E8E8] outline-none transition"
            style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}
            onFocus={(e) => (e.target.style.borderColor = "#6C63FF")}
            onBlur={(e) => (e.target.style.borderColor = "#2A2A2A")}
          />
          <button
            onClick={onGenerate}
            disabled={generating}
            className="rounded-xl px-5 py-2 text-sm font-medium text-white transition disabled:opacity-40"
            style={{ background: "#6C63FF" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#7B73FF")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "#6C63FF")}
          >
            {generating ? "Generating…" : isDeveloper ? "🚀 Generate Agent" : "✨ Build My Assistant"}
          </button>
        </div>
      </div>
    </div>
  );
}

function PackagePreview({
  pkg,
  previewFile,
  onSelectFile,
}: {
  pkg: GeneratedPackage;
  previewFile: GeneratedFile | null;
  onSelectFile: (f: GeneratedFile) => void;
}) {
  return (
    <div className="border-t flex flex-col" style={{ maxHeight: "45vh", borderColor: "#1A1A1A", background: "#111111" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b" style={{ borderColor: "#1A1A1A" }}>
        <div>
          <h2 className="text-sm font-semibold text-[#6C63FF]">
            📦 {pkg.project_name}
          </h2>
          <p className="text-[11px] text-[#666] mt-0.5">{pkg.summary}</p>
        </div>
        <button
          onClick={() => {
            const blob = new Blob(
              [pkg.files.map((f) => `// === ${f.path} ===\n${f.content}`).join("\n\n")],
              { type: "text/plain" }
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${pkg.project_name}-bundle.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="rounded-lg px-3 py-1.5 text-xs text-[#ccc] transition"
          style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#242424")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#1A1A1A")}
        >
          ⬇ Download All
        </button>
      </div>

      {/* File tabs + preview */}
      <div className="flex flex-1 min-h-0">
        {/* File list sidebar */}
        <div className="w-48 border-r overflow-y-auto py-2" style={{ borderColor: "#1A1A1A" }}>
          {pkg.files.map((f) => (
            <button
              key={f.path}
              onClick={() => onSelectFile(f)}
              className={`w-full text-left px-4 py-1.5 text-xs transition ${
                previewFile?.path === f.path
                  ? "text-[#6C63FF]"
                  : "text-[#666] hover:text-[#aaa]"
              }`}
              style={previewFile?.path === f.path ? { background: "#1A1A1A" } : {}}
            >
              {f.path}
            </button>
          ))}
        </div>

        {/* Code preview */}
        <div className="flex-1 overflow-auto" style={{ background: "#0D0D0D" }}>
          {previewFile ? (
            <pre className="p-4 text-xs leading-relaxed font-mono whitespace-pre" style={{ color: "#B0B0B0" }}>
              {previewFile.content}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-[#444] text-sm">
              Select a file to preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
}