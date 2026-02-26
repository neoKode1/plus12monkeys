"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
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
  const cls =
    status === "healthy"
      ? "bg-emerald-900 border-emerald-500/30"
      : status === "unhealthy"
        ? "bg-red-900 border-red-500/30"
        : "bg-zinc-800 border-zinc-700";
  return (
    <span className={`inline-block w-1.5 h-1.5 rounded-full border ${cls}`} />
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
    <div className="relative flex h-screen flex-col bg-[#030303] text-zinc-400">
      {/* Header */}
      <header className="shrink-0 border-b border-zinc-900/50 bg-[#030303]/80 backdrop-blur-sm z-30">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition shrink-0">
              <Image
                src="/favicon-monkey.png"
                alt="+12 Monkeys"
                width={28}
                height={28}
                className="h-6 w-6 sm:h-7 sm:w-7 brightness-0 invert opacity-80"
              />
              <div>
                <span className="text-[10px] font-mono tracking-[0.3em] text-zinc-300 uppercase font-bold block">
                  +12 Monkeys
                </span>
                <div className="h-px w-8 bg-zinc-800 mt-1" />
              </div>
            </Link>
            <span className="text-zinc-800 hidden sm:inline">/</span>
            <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">MCP Servers</span>
            <span className="text-[9px] font-mono text-zinc-700 hidden sm:inline">
              [{servers.length}]
            </span>
          </div>
          {/* Search */}
          <div className="flex items-center gap-3 shrink-0 ml-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="SEARCH"
              className="bg-transparent border-b border-zinc-800 px-1 py-1.5 text-[11px] font-mono text-zinc-300 placeholder-zinc-800 uppercase tracking-widest outline-none w-28 sm:w-48 focus:border-zinc-500 transition-colors"
            />
          </div>
        </div>
      </header>

      {/* Category filters */}
      <div className="flex items-center gap-4 px-4 sm:px-6 py-3 overflow-x-auto shrink-0 border-b border-zinc-900/50">
        <button
          onClick={() => setActiveCategory(null)}
          className={`text-[10px] font-mono uppercase tracking-widest transition whitespace-nowrap ${!activeCategory ? "text-zinc-200" : "text-zinc-700 hover:text-zinc-400"}`}
        >
          All
        </button>
        {categories.map((cat) => {
          const meta = CATEGORY_META[cat] || { label: cat, icon: "📦" };
          return (
            <button key={cat} onClick={() => setActiveCategory(cat)}
              className={`text-[10px] font-mono uppercase tracking-widest transition whitespace-nowrap ${activeCategory === cat ? "text-zinc-200" : "text-zinc-700 hover:text-zinc-400"}`}
            >
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* Main content */}
      <div className="flex flex-1 min-h-0 relative z-10">
        {/* ══ Server Grid ══ */}
        <div className={`${selected ? "hidden md:block md:w-1/2" : "w-full"} overflow-y-auto p-4 sm:p-6 transition-all`}>
          {loading ? (
            <div className="flex items-center justify-center h-40 text-zinc-700 text-[10px] font-mono uppercase tracking-widest">Loading…</div>
          ) : servers.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-zinc-700 text-[10px] font-mono uppercase tracking-widest">No servers found</div>
          ) : (
            <div className="grid gap-3" style={{ gridTemplateColumns: selected ? "1fr" : "repeat(auto-fill, minmax(280px, 1fr))" }}>
              {servers.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelect(s)}
                  className={`text-left p-4 transition group border ${selected?.id === s.id ? "border-zinc-600 bg-[#080808]" : "border-zinc-800 bg-[#050505] hover:border-zinc-600"}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="text-lg shrink-0 opacity-70">{s.icon || "📦"}</span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] text-zinc-300 group-hover:text-zinc-100 transition truncate">{s.name}</span>
                          <StatusDot status={s.status} />
                        </div>
                        <span className="text-[9px] font-mono text-zinc-700 uppercase tracking-widest">
                          {CATEGORY_META[s.category]?.label || s.category}
                        </span>
                      </div>
                    </div>
                    {s.is_official && (
                      <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500 border border-zinc-800 px-1.5 py-0.5 shrink-0">
                        Official
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-600 mt-2.5 leading-relaxed line-clamp-2">{s.description}</p>
                  <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                    {s.tags.slice(0, 3).map((t) => (
                      <span key={t} className="text-[9px] font-mono text-zinc-700 border border-zinc-900 px-1.5 py-0.5">
                        {t}
                      </span>
                    ))}
                    {s.required_env.length > 0 && (
                      <span className="text-[9px] font-mono text-amber-700 border border-amber-900/30 px-1.5 py-0.5">
                        {s.required_env.length} env
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
          <div className="fixed inset-0 z-50 md:relative md:inset-auto md:z-auto md:w-1/2 md:border-l border-zinc-900/50 flex flex-col">
            {/* Mobile backdrop */}
            <div className="absolute inset-0 bg-black/80 md:hidden" onClick={() => setSelected(null)} />
            {/* Panel content */}
            <div className="relative flex-1 overflow-y-auto mt-12 md:mt-0 bg-[#030303]">
            <div className="p-5 sm:p-6 space-y-5">
              {/* Close + title */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xl shrink-0 opacity-70">{selected.icon || "📦"}</span>
                  <div className="min-w-0 space-y-1">
                    <h2 className="text-sm font-light text-zinc-200 truncate">{selected.name}</h2>
                    <span className="text-[9px] font-mono text-zinc-700 uppercase tracking-widest truncate block">{selected.id} / {CATEGORY_META[selected.category]?.label || selected.category}</span>
                  </div>
                </div>
                <button onClick={() => setSelected(null)} className="p-1.5 text-zinc-700 hover:text-zinc-400 transition shrink-0">
                  ✕
                </button>
              </div>

              <p className="text-[12px] text-zinc-500 leading-relaxed font-light">{selected.description}</p>

              {/* Tags */}
              <div className="flex items-center gap-2 flex-wrap">
                {selected.tags.map((t) => (
                  <span key={t} className="text-[9px] font-mono text-zinc-600 border border-zinc-900 px-2 py-1 uppercase tracking-widest">{t}</span>
                ))}
                {selected.is_official && (
                  <span className="text-[9px] font-mono text-zinc-400 border border-zinc-700 px-2 py-1 uppercase tracking-widest">✓ Official</span>
                )}
              </div>

              {/* NPM + docs links */}
              <div className="flex items-center gap-4 text-[10px] font-mono">
                {selected.npm_package && (
                  <span className="text-zinc-600">{selected.npm_package}</span>
                )}
                {selected.documentation_url && (
                  <a href={selected.documentation_url} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-zinc-300 uppercase tracking-widest transition-colors">Docs ↗</a>
                )}
              </div>

              {/* Health check section */}
              <div className="border border-zinc-800 bg-[#050505] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">Health Check</span>
                  <button
                    onClick={() => doHealthCheck(selected.id)}
                    disabled={checking}
                    className="border border-zinc-800 px-3 py-1.5 text-[10px] font-mono uppercase tracking-widest text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all disabled:opacity-30"
                  >
                    {checking ? "Checking…" : "Run Check"}
                  </button>
                </div>
                {healthResult && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <StatusDot status={healthResult.status} />
                      <span className="text-[11px] text-zinc-400 capitalize">{healthResult.status}</span>
                      {healthResult.response_time_ms > 0 && (
                        <span className="text-[9px] font-mono text-zinc-700">{Math.round(healthResult.response_time_ms)}ms</span>
                      )}
                    </div>
                    {healthResult.error && (
                      <p className="text-[11px] text-red-700 leading-relaxed">{healthResult.error}</p>
                    )}
                    {healthResult.tools.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[9px] font-mono text-zinc-700 uppercase tracking-widest">
                          {healthResult.tools_count} tool{healthResult.tools_count !== 1 ? "s" : ""}
                        </span>
                        {healthResult.tools.map((tool) => (
                          <div key={tool.name} className="border border-zinc-900 bg-[#030303] p-2.5">
                            <span className="text-[11px] text-zinc-300 font-mono">{tool.name}</span>
                            {tool.description && (
                              <p className="text-[10px] text-zinc-600 mt-0.5">{tool.description}</p>
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
                <div className="border border-zinc-800 bg-[#050505] p-4 space-y-3">
                  <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">Credentials</span>
                  <p className="text-[10px] text-zinc-600 font-mono">Required environment variables.</p>
                  <div className="space-y-3">
                    {selected.required_env.map((envKey) => (
                      <div key={envKey}>
                        <label className="text-[10px] text-zinc-600 font-mono uppercase tracking-widest block mb-1.5">{envKey} <span className="text-amber-700">*</span></label>
                        <input
                          type="password"
                          value={credValues[envKey] || ""}
                          onChange={(e) => setCredValues((prev) => ({ ...prev, [envKey]: e.target.value }))}
                          placeholder={envKey}
                          className="w-full bg-transparent border-b border-zinc-800 px-1 py-2 text-[11px] text-zinc-300 placeholder-zinc-800 outline-none font-mono focus:border-zinc-500 transition-colors"
                        />
                      </div>
                    ))}
                    {selected.optional_env.map((envKey) => (
                      <div key={envKey}>
                        <label className="text-[10px] text-zinc-600 font-mono uppercase tracking-widest block mb-1.5">{envKey} <span className="text-zinc-800">(opt)</span></label>
                        <input
                          type="password"
                          value={credValues[envKey] || ""}
                          onChange={(e) => setCredValues((prev) => ({ ...prev, [envKey]: e.target.value }))}
                          placeholder={envKey}
                          className="w-full bg-transparent border-b border-zinc-800 px-1 py-2 text-[11px] text-zinc-300 placeholder-zinc-800 outline-none font-mono focus:border-zinc-500 transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={handleSaveCredentials}
                    className={`border px-4 py-2 text-[10px] font-mono uppercase tracking-widest transition-all ${credSaved ? "border-emerald-800 text-emerald-600" : "border-zinc-800 text-zinc-400 hover:bg-zinc-900 hover:text-white"}`}
                  >
                    {credSaved ? "✓ Saved" : "Save"}
                  </button>
                </div>
              )}

              {/* Command preview */}
              <div className="border border-zinc-800 bg-[#050505] p-4 space-y-2">
                <span className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">Start Command</span>
                <pre className="text-[11px] font-mono text-zinc-500 whitespace-pre-wrap break-all">
                  {selected.command} {selected.args.join(" ")}
                </pre>
              </div>
            </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

