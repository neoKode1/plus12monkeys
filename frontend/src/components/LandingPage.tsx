"use client";

import Image from "next/image";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="relative text-zinc-400 antialiased">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 w-full z-40 px-6 py-6 flex justify-between items-start mix-blend-exclusion pointer-events-none">
        <div className="pointer-events-auto">
          <Link href="/" className="flex items-center gap-2.5">
            <Image
              src="/favicon-monkey.png"
              alt="+12 Monkeys"
              width={24}
              height={24}
              className="brightness-0 invert opacity-80"
            />
            <div>
              <span className="tracking-[0.3em] text-[10px] font-bold text-zinc-300 uppercase font-mono block mb-1">
                +12 Monkeys
              </span>
              <div className="h-px w-8 bg-zinc-600" />
            </div>
          </Link>
        </div>

        <div className="flex flex-col items-end gap-1 pointer-events-auto">
          <div className="flex gap-8 text-[10px] font-mono tracking-widest uppercase text-zinc-500">
            <a href="#platform" className="hover:text-zinc-200 transition-colors">Platform</a>
            <a href="#capabilities" className="hover:text-zinc-200 transition-colors">Capabilities</a>
            <Link href="/mcp" className="hover:text-zinc-200 transition-colors">MCP</Link>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="w-2 h-2 rounded-full bg-emerald-900 animate-pulse border border-emerald-500/30" />
            <span className="text-[9px] uppercase tracking-widest text-zinc-600">System Active</span>
          </div>
        </div>
      </nav>

      <main className="relative z-10 w-full">
        {/* SECTION 1: THE GATE */}
        <section className="h-screen flex flex-col justify-center items-center px-6 relative overflow-hidden border-b border-zinc-900">
          {/* Background */}
          <div className="absolute inset-0 z-0">
            <div className="absolute inset-0 bg-black" />
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#111_1px,transparent_1px),linear-gradient(to_bottom,#111_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
            <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-[#050505] to-transparent" />
          </div>

          <div className="relative z-10 text-center space-y-12 max-w-4xl">
            <div className="reveal-text flex justify-center pb-4">
              <div className="px-3 py-1 border border-zinc-800 bg-black/50 backdrop-blur-sm text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-500">
                Agent-as-a-Service Platform
              </div>
            </div>

            <h1
              className="text-5xl md:text-8xl lg:text-9xl font-semibold tracking-tighter text-zinc-100 leading-[0.85] reveal-text"
              style={{ animationDelay: "0.2s" }}
            >
              +12<br />MONKEYS
            </h1>

            <p
              className="text-xs md:text-sm font-light tracking-[0.2em] text-zinc-500 uppercase reveal-text max-w-lg mx-auto leading-relaxed"
              style={{ animationDelay: "0.5s" }}
            >
              Build and deploy production-ready AI agents<br />
              in under 10 minutes. No code required.
            </p>

            <div className="pt-12 reveal-text" style={{ animationDelay: "0.8s" }}>
              <Link
                href="/wizard"
                className="group relative inline-flex flex-col items-center justify-center overflow-hidden px-8 py-4 transition-all hover:bg-zinc-900 border border-zinc-800"
              >
                <span className="absolute inset-0 w-full h-full -mt-10 transition-all duration-700 transform opacity-0 group-hover:translate-y-0 group-hover:opacity-100 bg-zinc-900" />
                <span className="relative text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-300 group-hover:text-white">
                  Launch Agent Wizard
                </span>
              </Link>
              <p className="mt-4 text-[9px] uppercase tracking-widest text-zinc-800">
                Scroll to learn more
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 2: PLATFORM (Philosophy) */}
        <section id="platform" className="min-h-[70vh] flex items-center py-24 px-6 md:px-12 bg-[#050505] relative border-b border-zinc-900/50">
          <div className="absolute left-6 top-6 text-[10px] font-mono text-zinc-700">01 / PLATFORM</div>

          <div className="max-w-3xl mx-auto space-y-12">
            <div className="space-y-2">
              <h2 className="text-3xl md:text-5xl font-light tracking-tight text-zinc-200 leading-tight">
                From conversation to deployment.<br />
                <span className="text-zinc-600">In minutes, not months.</span>
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-8 border-t border-zinc-900">
              <div className="space-y-6">
                <p className="text-sm text-zinc-500 font-light leading-relaxed">
                  +12 Monkeys is the open-source platform that turns natural language
                  into production-ready AI agent systems. Describe what you need,
                  and receive a complete deployable package — Python, TypeScript, Rust, or Go.
                </p>
              </div>
              <div className="space-y-6">
                <p className="text-sm text-zinc-500 font-light leading-relaxed">
                  Built on the Model Context Protocol (MCP) standard.
                  <span className="text-zinc-300"> 20 agent templates. 8 frameworks. 4 languages. Zero boilerplate.</span>
                </p>
                <div className="h-px w-12 bg-zinc-800 my-auto" />
              </div>
            </div>
          </div>
        </section>
        {/* SECTION 3: CAPABILITIES (Three Pillars) */}
        <section id="capabilities" className="py-0 border-b border-zinc-900/50">

          {/* Pillar 1: CONFIGURE */}
          <div className="group relative grid grid-cols-1 lg:grid-cols-2 min-h-[80vh] border-b border-zinc-900/50">
            <div className="p-8 md:p-16 flex flex-col justify-between order-2 lg:order-1 bg-[#080808]">
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-emerald-900/80 tracking-widest uppercase">Pillar 01</span>
                <h3 className="text-4xl md:text-6xl font-medium tracking-tighter text-zinc-300 group-hover:text-white transition-colors">CONFIGURE</h3>
                <p className="text-xs font-mono text-zinc-600 pt-2 uppercase tracking-wide">[ Chat . Define . Architect ]</p>
              </div>
              <div className="max-w-md space-y-8 mt-12">
                <p className="text-sm text-zinc-500 font-light leading-relaxed">
                  Describe your agent in natural language. The wizard extracts requirements,
                  recommends frameworks, selects MCP servers, and architects your system —
                  all through conversation.
                </p>
                <Link href="/wizard" className="inline-flex items-center gap-4 text-xs font-mono text-zinc-400 hover:text-white transition-colors uppercase tracking-widest">
                  <span>Start Building</span>
                  <span className="opacity-50">→</span>
                </Link>
              </div>
            </div>
            <div className="relative overflow-hidden order-1 lg:order-2 bg-zinc-900 border-l border-zinc-900/50 min-h-[40vh] lg:min-h-0">
              <div className="scan-line" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center space-y-4 p-8">
                  <div className="text-[100px] md:text-[160px] font-mono text-zinc-900/50 leading-none select-none">01</div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-700">Conversational Configuration</p>
                </div>
              </div>
            </div>
          </div>

          {/* Pillar 2: GENERATE */}
          <div className="group relative grid grid-cols-1 lg:grid-cols-2 min-h-[80vh] border-b border-zinc-900/50">
            <div className="relative overflow-hidden bg-zinc-900 border-r border-zinc-900/50 min-h-[40vh] lg:min-h-0">
              <div className="scan-line" style={{ animationDuration: "3s" }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center space-y-4 p-8">
                  <div className="text-[100px] md:text-[160px] font-mono text-zinc-900/50 leading-none select-none">02</div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-700">Multi-Language Packages</p>
                </div>
              </div>
            </div>
            <div className="p-8 md:p-16 flex flex-col justify-between bg-[#080808]">
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-zinc-700 tracking-widest uppercase">Pillar 02</span>
                <h3 className="text-4xl md:text-6xl font-medium tracking-tighter text-zinc-300 group-hover:text-white transition-colors">GENERATE</h3>
                <p className="text-xs font-mono text-zinc-600 pt-2 uppercase tracking-wide">[ Python . TypeScript . Rust . Go ]</p>
              </div>
              <div className="max-w-md space-y-8 mt-12">
                <p className="text-sm text-zinc-500 font-light leading-relaxed">
                  Complete deployable packages in seconds. Agent code, Dockerfile,
                  docker-compose, environment configs, MCP server setup,
                  Kubernetes manifests, and AWS SAM templates — all generated.
                </p>
                <Link href="/wizard" className="inline-flex items-center gap-4 text-xs font-mono text-zinc-400 hover:text-white transition-colors uppercase tracking-widest">
                  <span>Generate Package</span>
                  <span className="opacity-50">→</span>
                </Link>
              </div>
            </div>
          </div>

          {/* Pillar 3: DEPLOY */}
          <div className="group relative grid grid-cols-1 lg:grid-cols-2 min-h-[80vh]">
            <div className="p-8 md:p-16 flex flex-col justify-between order-2 lg:order-1 bg-[#080808]">
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-zinc-700 tracking-widest uppercase">Pillar 03</span>
                <h3 className="text-4xl md:text-6xl font-medium tracking-tighter text-zinc-300 group-hover:text-white transition-colors">DEPLOY</h3>
                <p className="text-xs font-mono text-zinc-600 pt-2 uppercase tracking-wide">[ Local . Cloud . Export ]</p>
              </div>
              <div className="max-w-md space-y-8 mt-12">
                <p className="text-sm text-zinc-500 font-light leading-relaxed">
                  One command to production. Docker Compose locally,
                  Railway / Render / Vercel in the cloud, or export and
                  self-host on your own infrastructure. 30 seconds to running.
                </p>
                <Link href="/wizard" className="inline-flex items-center gap-4 text-xs font-mono text-zinc-400 hover:text-white transition-colors uppercase tracking-widest">
                  <span>Deploy Now</span>
                  <span className="opacity-50">→</span>
                </Link>
              </div>
            </div>
            <div className="relative overflow-hidden order-1 lg:order-2 bg-zinc-900 border-l border-zinc-900/50 min-h-[40vh] lg:min-h-0">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center space-y-4 p-8">
                  <div className="text-[100px] md:text-[160px] font-mono text-zinc-900/50 leading-none select-none">03</div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-700">Production in 30 Seconds</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 4: TEMPLATES (The Path) */}
        <section className="py-32 px-6 md:px-12 bg-[#030303] border-t border-zinc-800 relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-zinc-900/10 blur-[100px]" />
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-end gap-12 mb-20 border-b border-zinc-900 pb-12">
              <div className="space-y-4">
                <h2 className="text-3xl md:text-5xl font-light tracking-tighter text-zinc-200">20 TEMPLATES</h2>
                <p className="text-sm text-zinc-500 font-light max-w-sm">
                  Production-ready agent architectures for every domain.
                  Customer service, research, healthcare, finance, defense, and more.
                </p>
              </div>
              <div className="text-right hidden md:block">
                <div className="text-[10px] font-mono uppercase text-zinc-600 tracking-widest mb-1">Frameworks</div>
                <div className="text-zinc-400 text-sm">LangGraph · CrewAI · AutoGen · Vercel AI · Rig · ADK-Go</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Template Card 1 */}
              <div className="border border-zinc-800 bg-[#050505] p-6 flex flex-col justify-between min-h-[400px] hover:border-zinc-600 transition-colors group cursor-pointer relative overflow-hidden">
                <div className="space-y-4 z-10">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Research</span>
                  <h4 className="text-xl text-zinc-300 font-medium">Research Agent</h4>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    Web search, data extraction,<br />
                    academic papers, summarization.<br />
                    LangGraph workflow engine.
                  </p>
                </div>
                <div className="z-10">
                  <Link href="/wizard" className="block w-full py-3 border border-zinc-800 text-[10px] font-mono uppercase text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all text-center">
                    Configure Agent
                  </Link>
                </div>
              </div>

              {/* Template Card 2 */}
              <div className="border border-zinc-800 bg-[#050505] p-6 flex flex-col justify-between min-h-[400px] hover:border-zinc-600 transition-colors group cursor-pointer relative overflow-hidden">
                <div className="space-y-4 z-10">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Enterprise</span>
                  <h4 className="text-xl text-zinc-300 font-medium">Multi-Agent Team</h4>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    Manager, Executor, Critic, Planner.<br />
                    Collaborative problem-solving.<br />
                    AutoGen coordination.
                  </p>
                </div>
                <div className="z-10">
                  <Link href="/wizard" className="block w-full py-3 border border-zinc-800 text-[10px] font-mono uppercase text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all text-center">
                    Configure Agent
                  </Link>
                </div>
              </div>

              {/* Template Card 3 */}
              <div className="border border-zinc-800 bg-[#050505] p-6 flex flex-col justify-between min-h-[400px] hover:border-zinc-600 transition-colors group cursor-pointer relative overflow-hidden">
                <div className="space-y-4 z-10">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Operations</span>
                  <h4 className="text-xl text-zinc-300 font-medium">Customer Service</h4>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    FAQ, ticket routing, sentiment.<br />
                    Slack + Email + CRM integration.<br />
                    CrewAI multi-agent system.
                  </p>
                </div>
                <div className="z-10">
                  <Link href="/wizard" className="block w-full py-3 border border-zinc-800 text-[10px] font-mono uppercase text-zinc-400 hover:bg-zinc-900 hover:text-white transition-all text-center">
                    Configure Agent
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 5: FINAL CTA */}
        <section className="py-24 px-6 bg-black border-t border-zinc-900">
          <div className="max-w-xl mx-auto text-center space-y-8">
            <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest">Open Source · MCP Native</p>
            <h3 className="text-2xl md:text-3xl font-light text-zinc-300">
              Deploy your first agent.<br />
              <span className="text-zinc-600">Production-ready in under 10 minutes.</span>
            </h3>
            <div className="pt-4">
              <Link
                href="/wizard"
                className="group relative inline-flex items-center justify-center overflow-hidden px-10 py-4 transition-all hover:bg-zinc-900 border border-zinc-800"
              >
                <span className="relative text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-300 group-hover:text-white">
                  Launch Wizard →
                </span>
              </Link>
            </div>
            <p className="text-[9px] text-zinc-800 pt-12 uppercase tracking-widest">
              +12 Monkeys © 2025. MIT License. All Rights Reserved.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

