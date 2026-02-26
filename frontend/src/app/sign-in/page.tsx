"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { sendKey } from "@/lib/auth";
import { useAuth } from "@/components/AuthProvider";

/* ── Waveform Visualizer ── */
function Waveform() {
  const barsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let raf: number;
    const animate = () => {
      const t = Date.now() * 0.005;
      const el = barsRef.current;
      if (el) {
        Array.from(el.children).forEach((bar, i) => {
          const h = Math.sin(t + i * 0.2) * 100 + 20;
          const clamped = Math.max(2, h);
          (bar as HTMLElement).style.height = `${clamped}%`;
          (bar as HTMLElement).style.opacity = `${0.1 + (h / 100) * 0.5}`;
        });
      }
      raf = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div ref={barsRef} className="flex items-center justify-between gap-[2px] w-[300px] h-[40px]">
      {Array.from({ length: 40 }).map((_, i) => (
        <div key={i} className="flex-1 bg-[#EAEAEA] min-h-[2px] opacity-30" />
      ))}
    </div>
  );
}

/* ── Live Clock ── */
function useClock() {
  const [time, setTime] = useState("00:00:00 [GMT]");
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(now.toISOString().split("T")[1].split(".")[0] + " [GMT]");
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return time;
}

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scanTop, setScanTop] = useState(0);
  const time = useClock();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  /* If already authenticated, redirect to home */
  useEffect(() => {
    if (!authLoading && user) {
      router.replace("/");
    }
  }, [user, authLoading, router]);

  /* Scanner animation */
  useEffect(() => {
    let raf: number;
    const animate = () => {
      setScanTop((prev) => (prev >= 100 ? 0 : prev + 0.35));
      raf = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!email.trim()) return;
      setLoading(true);
      await sendKey(email.trim());
      setSent(true);
      setLoading(false);
    },
    [email],
  );

  return (
    <div className="relative w-full min-h-screen bg-[#050505] text-[#EAEAEA] font-mono overflow-hidden select-none">
      {/* ── Scanline Overlay ── */}
      <div
        className="pointer-events-none fixed inset-0 z-50 w-full h-full"
        style={{
          background:
            "linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.1) 50%)",
          backgroundSize: "100% 4px",
        }}
      />

      {/* ── UI Frame Layer ── */}
      <div className="absolute inset-0 z-10 pointer-events-none"
        style={{ display: "grid", gridTemplateColumns: "60px 1fr 60px", gridTemplateRows: "60px 1fr 60px" }}>
        {/* Grid lines */}
        <div className="absolute top-[60px] left-0 w-full h-px bg-white/[0.08]" />
        <div className="absolute bottom-[60px] left-0 w-full h-px bg-white/[0.08]" />
        <div className="absolute left-[60px] top-0 h-full w-px bg-white/[0.08]" />
        <div className="absolute right-[60px] top-0 h-full w-px bg-white/[0.08]" />

        {/* Crosshairs */}
        {[
          "top-[55px] left-[55px]",
          "top-[55px] right-[55px]",
          "bottom-[55px] left-[55px]",
          "bottom-[55px] right-[55px]",
        ].map((pos, i) => (
          <div key={i} className={`absolute ${pos} w-2.5 h-2.5`}>
            <span className="absolute top-1/2 left-0 w-full h-px bg-[#EAEAEA]" />
            <span className="absolute left-1/2 top-0 h-full w-px bg-[#EAEAEA]" />
          </div>
        ))}

        {/* Meta Header */}
        <div className="flex justify-between items-center px-5 text-[10px] uppercase tracking-[0.15em]"
          style={{ gridColumn: 2, gridRow: 1 }}>
          <div className="flex items-center gap-4">
            <span className="font-bold">AUTH_GATEWAY</span>
            <span className="text-[#555]">PROT.SEQ.99</span>
          </div>
          <div className="hidden sm:block">STATION / SECURE_ACCESS / NOD_01</div>
          <div className="text-[#555] tabular-nums">{time}</div>
        </div>

        {/* Meta Sides */}
        <div className="flex items-center justify-center text-[10px] text-[#555] uppercase tracking-[0.15em] rotate-180"
          style={{ gridColumn: 1, gridRow: 2, writingMode: "vertical-rl" }}>
          ENCRYPTION_LAYER: ACTIVE [AES-256]
        </div>
        <div className="hidden sm:flex items-center justify-center text-[10px] text-[#555] uppercase tracking-[0.15em]"
          style={{ gridColumn: 3, gridRow: 2, writingMode: "vertical-rl" }}>
          TERMINAL_ID: +12_MONKEYS_04
        </div>

        {/* Meta Footer */}
        <div className="flex justify-between items-center px-5 text-[10px] uppercase tracking-[0.15em]"
          style={{ gridColumn: 2, gridRow: 3 }}>
          <div className="flex items-center">
            <div className="w-1.5 h-1.5 bg-[#00FF41] rounded-full mr-3 animate-pulse"
              style={{ boxShadow: "0 0 12px #00FF41" }} />
            <span>SYSTEM_READY</span>
          </div>
          <div className="text-[#555]">99% / SYNCED</div>
          <div className="w-[100px]" />
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="absolute inset-0 flex flex-col items-center justify-center z-20 gap-8 px-6">
        {/* Waveform */}
        <Waveform />

        {/* Form Card */}
        <div className="w-full max-w-[400px] p-8 border border-white/10 bg-black/40 backdrop-blur-sm relative overflow-hidden rounded-sm">
          {/* Scan line inside form */}
          <div
            className="absolute left-0 w-full h-px opacity-20 pointer-events-none"
            style={{
              top: `${scanTop}%`,
              background: "linear-gradient(to right, transparent, #EAEAEA, transparent)",
            }}
          />

          {/* Monkey Head + Title */}
          <div className="flex flex-col items-center gap-4 mb-8 border-b border-white/10 pb-4">
            <Link href="/" className="hover:opacity-80 transition">
              <Image
                src="/favicon-monkey.png"
                alt="+12 Monkeys"
                width={48}
                height={48}
                className="brightness-0 invert opacity-80"
              />
            </Link>
            <h1 className="text-[12px] tracking-[0.4em] text-center uppercase">
              Identity_Verification
            </h1>
          </div>

          {!sent ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-[9px] text-[#555] uppercase tracking-widest block">
                  / Identity_Key
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="USER@DOMAIN.COM"
                  required
                  autoFocus
                  className="w-full bg-transparent border border-[#555] p-3 text-[11px] focus:outline-none focus:border-[#00FF41] text-[#EAEAEA] transition-colors tracking-widest uppercase placeholder:normal-case placeholder:text-[#333] rounded-sm"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !email.trim()}
                className="group relative w-full border border-[#00FF41] py-4 mt-4 overflow-hidden transition-all hover:bg-[#00FF41]/10 disabled:opacity-30 disabled:cursor-not-allowed disabled:border-[#333] rounded-sm"
              >
                <span className="relative z-10 text-[10px] tracking-[0.3em] text-[#00FF41] group-hover:text-white transition-colors">
                  {loading ? "TRANSMITTING..." : "TRANSMIT_KEY →"}
                </span>
                <div className="absolute inset-0 translate-y-full group-hover:translate-y-0 bg-[#00FF41]/20 transition-transform duration-300" />
              </button>

              <div className="pt-4 flex justify-between text-[8px] text-[#555] uppercase tracking-wider">
                <span>No password required</span>
                <Link href="/" className="hover:text-[#00FF41] transition-colors">
                  Return_Home
                </Link>
              </div>
            </form>
          ) : (
            <div className="space-y-6 text-center">
              <div className="flex justify-center mb-2">
                <div className="w-3 h-3 bg-[#00FF41] rounded-full animate-pulse"
                  style={{ boxShadow: "0 0 20px #00FF41" }} />
              </div>
              <p className="text-[10px] tracking-[0.3em] text-[#00FF41] uppercase">
                Key_Transmitted
              </p>
              <p className="text-[11px] text-[#888] tracking-widest">
                Check <span className="text-[#EAEAEA]">{email}</span>
              </p>
              <p className="text-[9px] text-[#555] tracking-widest uppercase">
                Expires in 15 minutes
              </p>

              <button
                onClick={() => { setSent(false); setEmail(""); }}
                className="mt-4 border border-[#555] px-6 py-2 text-[9px] uppercase tracking-[0.2em] text-[#555] hover:text-[#00FF41] hover:border-[#00FF41] transition-colors rounded-sm"
              >
                Retry_Transmission
              </button>
            </div>
          )}
        </div>

        {/* Status text */}
        <div className="text-[9px] text-[#555] tracking-[0.2em] animate-pulse uppercase">
          {sent ? "Awaiting key activation..." : "Waiting for spatial handshake..."}
        </div>
      </div>
    </div>
  );
}
