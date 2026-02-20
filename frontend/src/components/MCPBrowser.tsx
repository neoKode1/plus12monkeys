"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchMCPServers,
  MCPServerEntry,
  MCPHealthResult,
  runMCPHealthCheck,
  storeMCPCredentials,
} from "@/lib/api";


/* ── Category metadata ── */
const CATEGORY_META: Record<string, { label: string; icon: string }> = {
  data: { label: "Data", icon: "🗄️" },
  communication: { label: "Communication", icon: "💬" },
  "dev-tools": { label: "Dev Tools", icon: "🛠️" },
  productivity: { label: "Productivity", icon: "📋" },
  search: { label: "Search", icon: "🔍" },
  "ai-ml": { label: "AI / ML", icon: "🤖" },
  finance: { label: "Finance", icon: "💳" },
  intelligence: { label: "Intelligence", icon: "🔓" },
  custom: { label: "Custom", icon: "⚙️" },
};

/* ── Status badge ── */
function StatusDot({ status }: { status: string }) {
  const color =
    status === "healthy" ? "#34D399" : status === "unhealthy" ? "#F87171" : "#555";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: color }}
    />
  );
}

export default function MCPBrowser() {
  const [servers, setServers] = useState<MCPServerEntry[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<MCPServerEntry | null>(null);
  const [healthResult, setHealthResult] = useState<MCPHealthResult | null>(null);
  const [checking, setChecking] = useState(false);
  const [credValues, setCredValues] = useState<Record<string, string>>({});
  const [credSaved, setCredSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  /* Load servers */
  const loadServers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMCPServers(
        activeCategory || undefined,
        search || undefined,
      );
      setServers(data.servers);
      if (data.categories.length) setCategories(data.categories);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, [activeCategory, search]);

  useEffect(() => {
    loadServers();
  }, [loadServers]);

  /* Health check */
  const doHealthCheck = useCallback(async (serverId: string) => {
    setChecking(true);
    setHealthResult(null);
    try {
      const result = await runMCPHealthCheck(serverId);
      setHealthResult(result);
    } catch {
      setHealthResult({
        server_id: serverId,
        status: "unhealthy",
        tools_count: 0,
        tools: [],
        response_time_ms: 0,
        error: "Health check failed — server may require credentials.",
        checked_at: new Date().toISOString(),
      });
    } finally {
      setChecking(false);
    }
  }, []);

  /* Save credentials */
  const handleSaveCredentials = useCallback(async () => {
    if (!selected) return;
    try {
      await storeMCPCredentials("default", selected.id, credValues);
      setCredSaved(true);
      setTimeout(() => setCredSaved(false), 3000);
    } catch {
      /* silent */
    }
  }, [selected, credValues]);

  /* Select server */
  const handleSelect = (s: MCPServerEntry) => {
    setSelected(s);
    setHealthResult(null);
    setCredSaved(false);
    const initial: Record<string, string> = {};
    s.required_env.forEach((k) => (initial[k] = ""));
    s.optional_env.forEach((k) => (initial[k] = ""));
    setCredValues(initial);
  };

  return (
    <div className="flex h-screen flex-col" style={{ background: "#0D0D0D", color: "#E8E8E8" }}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "#1A1A1A" }}>
        <div className="flex items-center gap-3">
          <a href="/" className="flex items-center gap-2.5 hover:opacity-80 transition">
            <img
              src="/favicon-monkey.png"
              alt="+12 Monkeys"
              className="h-8 w-8 brightness-0 invert"
            />
            <span
              className="text-white uppercase"
              style={{
                fontSize: "22px",
                fontFamily: "var(--font-brand), 'Barlow Condensed', sans-serif",
                fontWeight: 300,
                letterSpacing: "0.16em",
                lineHeight: 1,
              }}
            >
              +12 Monkeys
            </span>
          </a>
          <span className="text-[#333]">|</span>
          <h1 className="text-lg font-semibold">MCP Servers</h1>
          <span className="text-[12px] text-[#666] rounded-full px-2 py-0.5" style={{ background: "#1A1A1A" }}>
            {servers.length} servers
          </span>
        </div>
        {/* Search */}
        <div className="flex items-center gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search servers…"
            className="rounded-xl px-3 py-1.5 text-[13px] text-[#E8E8E8] placeholder-[#555] outline-none w-56"
            style={{ background: "#1A1A1A", border: "1px solid #2A2A2A" }}
          />
        </div>
      </header>

      {/* Category pills */}
      <div className="flex items-center gap-2 px-6 py-3 overflow-x-auto" style={{ borderBottom: "1px solid #1A1A1A" }}>
        <button
          onClick={() => setActiveCategory(null)}
          className="px-3 py-1 rounded-full text-[12px] font-medium transition whitespace-nowrap"
          style={{
            background: !activeCategory ? "#6C63FF" : "#1A1A1A",
            color: !activeCategory ? "#fff" : "#888",
          }}
        >
          All
        </button>
        {categories.map((cat) => {
          const meta = CATEGORY_META[cat] || { label: cat, icon: "📦" };
          return (
            <button key={cat} onClick={() => setActiveCategory(cat)}
              className="px-3 py-1 rounded-full text-[12px] font-medium transition whitespace-nowrap"
              style={{
                background: activeCategory === cat ? "#6C63FF" : "#1A1A1A",
                color: activeCategory === cat ? "#fff" : "#888",
              }}
            >
              {meta.icon} {meta.label}
            </button>
          );
        })}
      </div>

      {/* Main content */}
      <div className="flex flex-1 min-h-0">
        {/* ══ Server Grid ══ */}
        <div className={`${selected ? "w-1/2" : "w-full"} overflow-y-auto p-6 transition-all`}>
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[#555]">Loading servers…</div>
          ) : servers.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-[#555]">No servers found</div>
          ) : (
            <div className="grid gap-3" style={{ gridTemplateColumns: selected ? "1fr" : "repeat(auto-fill, minmax(280px, 1fr))" }}>
              {servers.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelect(s)}
                  className="text-left rounded-xl p-4 transition group"
                  style={{
                    background: selected?.id === s.id ? "#1E1E2E" : "#111",
                    border: `1px solid ${selected?.id === s.id ? "#6C63FF" : "#1A1A1A"}`,
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{s.icon || "📦"}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[14px] font-medium text-[#E8E8E8] group-hover:text-white transition">{s.name}</span>
                          <StatusDot status={s.status} />
                        </div>
                        <span className="text-[11px] text-[#555] uppercase tracking-wide">
                          {CATEGORY_META[s.category]?.label || s.category}
                        </span>
                      </div>
                    </div>
                    {s.is_official && (
                      <span className="text-[10px] text-[#6C63FF] px-1.5 py-0.5 rounded" style={{ background: "rgba(108,99,255,0.1)" }}>
                        Official
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-[#777] mt-2 leading-relaxed line-clamp-2">{s.description}</p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    {s.tags.slice(0, 3).map((t) => (
                      <span key={t} className="text-[10px] text-[#555] px-1.5 py-0.5 rounded" style={{ background: "#1A1A1A" }}>
                        {t}
                      </span>
                    ))}
                    {s.required_env.length > 0 && (
                      <span className="text-[10px] text-[#F59E0B] px-1.5 py-0.5 rounded" style={{ background: "rgba(245,158,11,0.1)" }}>
                        {s.required_env.length} env var{s.required_env.length > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ══ Detail Panel ══ */}
        {selected && (
          <div className="w-1/2 border-l overflow-y-auto" style={{ borderColor: "#1A1A1A", background: "#0A0A0A" }}>
            <div className="p-6 space-y-5">
              {/* Close + title */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{selected.icon || "📦"}</span>
                  <div>
                    <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
                    <span className="text-[12px] text-[#555]">{selected.id} · {CATEGORY_META[selected.category]?.label || selected.category}</span>
                  </div>
                </div>
                <button onClick={() => setSelected(null)} className="p-1.5 rounded-lg text-[#555] hover:text-[#aaa] hover:bg-white/5 transition">
                  ✕
                </button>
              </div>

              <p className="text-[13px] text-[#999] leading-relaxed">{selected.description}</p>

              {/* Tags */}
              <div className="flex items-center gap-2 flex-wrap">
                {selected.tags.map((t) => (
                  <span key={t} className="text-[11px] text-[#888] px-2 py-1 rounded-lg" style={{ background: "#1A1A1A" }}>{t}</span>
                ))}
                {selected.is_official && (
                  <span className="text-[11px] text-[#6C63FF] px-2 py-1 rounded-lg" style={{ background: "rgba(108,99,255,0.1)" }}>✓ Official</span>
                )}
              </div>

              {/* NPM + docs links */}
              <div className="flex items-center gap-3 text-[12px]">
                {selected.npm_package && (
                  <span className="text-[#666]">📦 {selected.npm_package}</span>
                )}
                {selected.documentation_url && (
                  <a href={selected.documentation_url} target="_blank" rel="noopener noreferrer" className="text-[#6C63FF] hover:underline">Docs ↗</a>
                )}
              </div>

              {/* Health check section */}
              <div className="rounded-xl p-4 space-y-3" style={{ background: "#111", border: "1px solid #1A1A1A" }}>
                <div className="flex items-center justify-between">
                  <h3 className="text-[13px] font-semibold text-[#ccc]">Health Check</h3>
                  <button
                    onClick={() => doHealthCheck(selected.id)}
                    disabled={checking}
                    className="px-3 py-1 rounded-lg text-[12px] font-medium transition disabled:opacity-40"
                    style={{ background: "#6C63FF", color: "#fff" }}
                  >
                    {checking ? "Checking…" : "Run Check"}
                  </button>
                </div>
                {healthResult && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <StatusDot status={healthResult.status} />
                      <span className="text-[13px] text-[#ccc] capitalize">{healthResult.status}</span>
                      {healthResult.response_time_ms > 0 && (
                        <span className="text-[11px] text-[#555]">{Math.round(healthResult.response_time_ms)}ms</span>
                      )}
                    </div>
                    {healthResult.error && (
                      <p className="text-[12px] text-[#F87171] leading-relaxed">{healthResult.error}</p>
                    )}
                    {healthResult.tools.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <span className="text-[11px] text-[#666] uppercase tracking-wide">
                          {healthResult.tools_count} tool{healthResult.tools_count !== 1 ? "s" : ""} discovered
                        </span>
                        {healthResult.tools.map((tool) => (
                          <div key={tool.name} className="rounded-lg p-2" style={{ background: "#0D0D0D" }}>
                            <span className="text-[12px] text-[#6C63FF] font-mono">{tool.name}</span>
                            {tool.description && (
                              <p className="text-[11px] text-[#666] mt-0.5">{tool.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Credentials section */}
              {selected.required_env.length > 0 && (
                <div className="rounded-xl p-4 space-y-3" style={{ background: "#111", border: "1px solid #1A1A1A" }}>
                  <h3 className="text-[13px] font-semibold text-[#ccc]">Credentials</h3>
                  <p className="text-[11px] text-[#666]">Required environment variables for this MCP server.</p>
                  <div className="space-y-2">
                    {selected.required_env.map((envKey) => (
                      <div key={envKey}>
                        <label className="text-[11px] text-[#888] font-mono block mb-1">{envKey} <span className="text-[#F59E0B]">*</span></label>
                        <input
                          type="password"
                          value={credValues[envKey] || ""}
                          onChange={(e) => setCredValues((prev) => ({ ...prev, [envKey]: e.target.value }))}
                          placeholder={`Enter ${envKey}`}
                          className="w-full rounded-lg px-3 py-2 text-[12px] text-[#E8E8E8] placeholder-[#444] outline-none font-mono"
                          style={{ background: "#0D0D0D", border: "1px solid #2A2A2A" }}
                        />
                      </div>
                    ))}
                    {selected.optional_env.map((envKey) => (
                      <div key={envKey}>
                        <label className="text-[11px] text-[#888] font-mono block mb-1">{envKey} <span className="text-[#555]">(optional)</span></label>
                        <input
                          type="password"
                          value={credValues[envKey] || ""}
                          onChange={(e) => setCredValues((prev) => ({ ...prev, [envKey]: e.target.value }))}
                          placeholder={`Enter ${envKey}`}
                          className="w-full rounded-lg px-3 py-2 text-[12px] text-[#E8E8E8] placeholder-[#444] outline-none font-mono"
                          style={{ background: "#0D0D0D", border: "1px solid #2A2A2A" }}
                        />
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={handleSaveCredentials}
                    className="px-4 py-1.5 rounded-lg text-[12px] font-medium transition"
                    style={{ background: credSaved ? "#34D399" : "#6C63FF", color: "#fff" }}
                  >
                    {credSaved ? "✓ Saved" : "Save Credentials"}
                  </button>
                </div>
              )}

              {/* Command preview */}
              <div className="rounded-xl p-4 space-y-2" style={{ background: "#111", border: "1px solid #1A1A1A" }}>
                <h3 className="text-[13px] font-semibold text-[#ccc]">Start Command</h3>
                <pre className="text-[12px] font-mono text-[#888] whitespace-pre-wrap">
                  {selected.command} {selected.args.join(" ")}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

