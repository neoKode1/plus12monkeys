"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import DOMPurify from "isomorphic-dompurify";
import JSZip from "jszip";
import {
  confirmAndGenerate,
  GeneratedFile,
  GeneratedPackage,
  Recommendation,
  sendMessageStream,
  StreamEvent,
} from "@/lib/api";


interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
}

/* ── Icon helpers (inline SVG to avoid external deps) ── */
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

  const raw = result
    .join("")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");

  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ["p", "br", "ul", "ol", "li", "strong", "code"],
    ALLOWED_ATTR: [],
  });
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
  { key: "gathering", label: "Describe", num: "01" },
  { key: "recommending", label: "Analyze", num: "02" },
  { key: "confirmed", label: "Build", num: "03" },
  { key: "complete", label: "Ready", num: "04" },
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
            <div className={`flex items-center gap-1.5 px-2 py-1 text-[10px] font-mono uppercase tracking-widest transition-all duration-500 ${
              isDone ? "text-emerald-600" : isActive ? "text-zinc-200" : "text-zinc-700"
            }`}>
              <span className="text-[9px]">{step.num}</span>
              <span>{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className="w-6 h-px mx-1 step-connector"
                style={{ background: i < idx ? "#065f46" : i === idx ? "#52525b" : "#18181b" }}
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
  const [streamingIdx, setStreamingIdx] = useState<number | null>(null);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
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
          "Start building your MCP server, agent, or SDK package.\n\nDescribe what you're building and I'll generate the full stack — framework, deployment config, and MCP integration included.\n\n💡 Have an existing app? Paste a **GitHub** or **HuggingFace** link and I'll tailor the agent to fit your stack.",
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
    setToolStatus(null);
    if (isRepoUrl(text)) setAnalyzingRepo(true);

    // Add an empty assistant message placeholder for streaming
    setMessages((prev) => {
      const next = [...prev, { role: "assistant" as const, content: "" }];
      setStreamingIdx(next.length - 1);
      return next;
    });

    try {
      const res = await sendMessageStream(text, sessionId, (evt: StreamEvent) => {
        if (evt.event === "status") {
          setToolStatus(evt.data);
        } else if (evt.event === "delta") {
          // Append streamed text to the assistant placeholder
          setMessages((prev) => {
            const updated = [...prev];
            const idx = updated.length - 1;
            if (updated[idx] && updated[idx].role === "assistant") {
              updated[idx] = { ...updated[idx], content: updated[idx].content + evt.data };
            }
            return updated;
          });
          setToolStatus(null); // clear status once text starts flowing
        } else if (evt.event === "done") {
          setToolStatus(null);
        }
      });

      if (!sessionId) setSessionId(res.session_id);
      setStatus(res.status);
      // Update the final message content from the done event
      setMessages((prev) => {
        const updated = [...prev];
        const idx = updated.length - 1;
        if (updated[idx] && updated[idx].role === "assistant") {
          updated[idx] = { ...updated[idx], content: res.reply };
        }
        return updated;
      });
      if (res.recommendation) {
        setRecommendation(res.recommendation);
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const idx = updated.length - 1;
        if (updated[idx] && updated[idx].role === "assistant") {
          updated[idx] = { ...updated[idx], content: "⚠️ Failed to reach the server. Is the backend running?" };
        }
        return updated;
      });
    } finally {
      setLoading(false);
      setAnalyzingRepo(false);
      setStreamingIdx(null);
      setToolStatus(null);
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
    <div className="relative flex h-screen flex-col bg-[#030303] text-zinc-400">

      {/* ══════════ Top Header Bar ══════════ */}
      <header className="border-b border-zinc-900/50 shrink-0 bg-[#030303]/80 backdrop-blur-sm z-30">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
          {/* Left: brand */}
          <div className="flex items-center gap-2.5 min-w-0">
            <Image
              src="/favicon-monkey.png"
              alt="+12 Monkeys"
              width={28}
              height={28}
              className="h-6 w-6 sm:h-7 sm:w-7 brightness-0 invert shrink-0 opacity-80"
            />
            <div>
              <span className="text-[10px] font-mono tracking-[0.3em] text-zinc-300 uppercase font-bold block">
                +12 Monkeys
              </span>
              <div className="h-px w-8 bg-zinc-800 mt-1" />
            </div>
          </div>

          {/* Center: stepper — hidden on mobile */}
          <div className="hidden md:block">
            <ProgressStepper status={status} />
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-3 shrink-0">
            <a href="/mcp" className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 hover:text-zinc-200 transition-colors">
              MCP
            </a>
            <div className="hidden sm:flex items-center gap-1">
              {[IconDownload, IconBookmark, IconHistory, IconEdit].map((Icon, i) => (
                <button key={i} className="p-1.5 transition hover:bg-zinc-900 text-zinc-600 hover:text-zinc-400">
                  <Icon />
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 ml-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-900 animate-pulse border border-emerald-500/30" />
              <span className="text-[9px] uppercase tracking-widest text-zinc-700 font-mono hidden sm:inline">Active</span>
            </div>
          </div>
        </div>
        {/* Mobile-only stepper */}
        <div className="md:hidden border-t border-zinc-900/50">
          <ProgressStepper status={status} />
        </div>
      </header>

      {/* ══════════ Messages (scrollable area) ══════════ */}
      <div className="flex-1 overflow-y-auto min-h-0 relative z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-5 sm:space-y-7 w-full">
          {messages.map((m, i) => (
            <div key={i} className="msg-enter">
              {m.role === "user" ? (
                /* ── User message ── */
                <div className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[80%] border border-zinc-800 bg-[#050505] px-4 py-3 text-[13px] leading-relaxed text-zinc-300">
                    {m.content}
                  </div>
                </div>
              ) : (
                /* ── Assistant flowing text ── */
                <div className="space-y-2">
                  <div className="assistant-content text-[13px] leading-[1.8] text-zinc-400">
                    {streamingIdx === i ? (
                      <>
                        <span dangerouslySetInnerHTML={{ __html: formatAssistant(m.content) }} />
                        <span className="inline-block w-1.5 h-4 bg-zinc-600 animate-pulse ml-0.5 align-middle" />
                      </>
                    ) : typingIdx === i ? (
                      <TypewriterMessage
                        content={m.content}
                        onDone={() => setTypingIdx(null)}
                      />
                    ) : (
                      <span dangerouslySetInnerHTML={{ __html: formatAssistant(m.content) }} />
                    )}
                  </div>
                  {/* Tool status indicator */}
                  {streamingIdx === i && toolStatus && (
                    <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-zinc-600 animate-pulse">
                      <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-600" />
                      {toolStatus}
                    </div>
                  )}
                  {/* Action buttons */}
                  {typingIdx !== i && streamingIdx !== i && m.content && (
                    <div className="flex items-center gap-0.5 pt-1">
                      <button
                        onClick={() => handleCopy(m.content, i)}
                        className="p-1.5 transition hover:bg-zinc-900 text-zinc-700 hover:text-zinc-400"
                        title="Copy"
                      >
                        {copiedIdx === i ? (
                          <span className="text-[9px] font-mono uppercase tracking-widest text-emerald-700 px-1">Copied</span>
                        ) : (
                          <IconCopy />
                        )}
                      </button>
                      <button className="p-1.5 transition hover:bg-zinc-900 text-zinc-700 hover:text-zinc-400" title="Good response">
                        <IconThumbUp />
                      </button>
                      <button className="p-1.5 transition hover:bg-zinc-900 text-zinc-700 hover:text-zinc-400" title="Bad response">
                        <IconThumbDown />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {loading && streamingIdx === null && (
            <div className="msg-enter flex items-center gap-1.5 py-2">
              {analyzingRepo ? (
                <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                  <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-500" />
                  Analyzing repository…
                </span>
              ) : toolStatus ? (
                <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                  <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-500" />
                  {toolStatus}
                </span>
              ) : (
                <>
                  <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-600" />
                  <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-600" />
                  <span className="typing-dot w-1.5 h-1.5 rounded-full bg-zinc-600" />
                </>
              )}
            </div>
          )}

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

      {/* ══════════ Input Bar — pinned to bottom ══════════ */}
      <div className="shrink-0 border-t border-zinc-900/50 px-4 sm:px-6 py-3 sm:py-4 bg-[#030303] relative z-20">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="max-w-3xl mx-auto flex items-center gap-3"
        >
          <button type="button" className="p-1.5 text-zinc-700 hover:text-zinc-400 transition shrink-0">
            <IconAttach />
          </button>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="DESCRIBE YOUR AGENT"
            className="flex-1 min-w-0 bg-transparent border-b border-zinc-800 text-[11px] font-mono text-zinc-300 placeholder-zinc-800 uppercase tracking-widest outline-none py-2 focus:border-zinc-500 transition-colors"
            disabled={loading || status === "complete"}
          />
          <button
            type="submit"
            disabled={loading || !input.trim() || status === "complete"}
            className="p-2 border border-zinc-800 text-zinc-500 hover:bg-zinc-900 hover:text-white transition disabled:opacity-20 shrink-0"
          >
            <IconSend />
          </button>
        </form>
      </div>
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
    <div className="border-t border-zinc-900/50 px-4 sm:px-6 py-4 sm:py-5 shrink-0 overflow-y-auto max-h-[50vh] sm:max-h-[40vh] bg-[#050505] relative z-20">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-zinc-700 tracking-widest uppercase">Configuration</span>
            <h2 className="text-sm font-light text-zinc-200">
              {isDeveloper ? "Agent Configuration" : "Your AI Assistant Plan"}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-900 border border-emerald-500/30" />
            <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-700">Ready</span>
          </div>
        </div>
        <p className="text-xs text-zinc-500 font-light leading-relaxed">{rec.summary}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {isDeveloper && (
            <div className="border border-zinc-800 bg-[#030303] p-4">
              <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">Framework</span>
              <p className="mt-2 font-medium text-zinc-300 text-[13px]">{rec.framework}</p>
              <p className="mt-1 text-[10px] text-zinc-600 font-mono">{rec.framework_reason}</p>
            </div>
          )}
          <div className="border border-zinc-800 bg-[#030303] p-4">
            <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">
              {isDeveloper ? "Agent Roles" : "Capabilities"}
            </span>
            <ul className="mt-2 space-y-1">
              {capabilities.map((c, i) => (
                <li key={i} className="text-zinc-300 text-[12px]">— {c}</li>
              ))}
            </ul>
          </div>
          <div className="border border-zinc-800 bg-[#030303] p-4">
            <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">
              {isDeveloper ? "MCP Servers" : "Services"}
            </span>
            <ul className="mt-2 space-y-1">
              {connectedServices.map((s, i) => (
                <li key={i} className="text-zinc-300 text-[12px]">{isDeveloper ? s : s}</li>
              ))}
            </ul>
          </div>
          <div className="border border-zinc-800 bg-[#030303] p-4">
            <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">
              {isDeveloper ? "Deployment" : "Hosting"}
            </span>
            <p className="mt-2 text-zinc-300 text-[12px]">{friendlyDeployment}</p>
          </div>
          {rec.estimated_monthly_cost && (
            <div className="border border-zinc-800 bg-[#030303] p-4">
              <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">Cost</span>
              <p className="mt-2 text-zinc-300 text-[12px]">~{rec.estimated_monthly_cost}/mo</p>
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2 border-t border-zinc-900">
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder={isDeveloper ? "PROJECT NAME" : "NAME YOUR ASSISTANT"}
            className="bg-transparent border-b border-zinc-800 px-1 py-2 text-[11px] font-mono text-zinc-300 placeholder-zinc-800 uppercase tracking-widest outline-none focus:border-zinc-500 transition-colors w-full sm:w-auto"
          />
          <button
            onClick={onGenerate}
            disabled={generating}
            className="border border-zinc-800 px-6 py-2.5 text-[10px] font-mono uppercase tracking-widest text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all disabled:opacity-30 whitespace-nowrap"
          >
            {generating ? "Generating…" : isDeveloper ? "Generate Agent" : "Build Assistant"}
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
    <div className="border-t border-zinc-900/50 flex flex-col shrink-0 bg-[#050505] relative z-20" style={{ maxHeight: "50vh" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-zinc-900/50">
        <div className="min-w-0 flex-1 space-y-1">
          <span className="text-[10px] font-mono text-zinc-700 tracking-widest uppercase">Package</span>
          <h2 className="text-sm font-light text-zinc-200 truncate">
            {pkg.project_name}
          </h2>
          <p className="text-[10px] text-zinc-600 font-mono truncate">{pkg.summary}</p>
        </div>
        <button
          onClick={async () => {
            const zip = new JSZip();
            for (const f of pkg.files) {
              zip.file(f.path, f.content);
            }
            const blob = await zip.generateAsync({ type: "blob" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${pkg.project_name}.zip`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="border border-zinc-800 px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all shrink-0 ml-3"
        >
          Download
        </button>
      </div>

      {/* File tabs + preview */}
      <div className="flex flex-col sm:flex-row flex-1 min-h-0">
        <div className="sm:w-48 border-b sm:border-b-0 sm:border-r border-zinc-900/50 overflow-x-auto sm:overflow-x-visible overflow-y-hidden sm:overflow-y-auto py-1 sm:py-2 flex sm:block shrink-0">
          {pkg.files.map((f) => (
            <button
              key={f.path}
              onClick={() => onSelectFile(f)}
              className={`whitespace-nowrap sm:whitespace-normal sm:w-full text-left px-3 sm:px-4 py-1.5 text-[11px] font-mono transition shrink-0 ${
                previewFile?.path === f.path
                  ? "text-zinc-200 bg-zinc-900/50"
                  : "text-zinc-600 hover:text-zinc-400"
              }`}
            >
              {f.path}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto min-h-0 bg-[#030303]">
          {previewFile ? (
            <pre className="p-4 text-[11px] leading-relaxed font-mono whitespace-pre overflow-x-auto text-zinc-500">
              {previewFile.content}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-zinc-800 text-[10px] font-mono uppercase tracking-widest py-8">
              Select a file to preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
}