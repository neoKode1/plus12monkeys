"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { sendKey } from "@/lib/auth";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    await sendKey(email.trim());
    setSent(true);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#030303] px-6">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-3 mb-16 hover:opacity-80 transition">
        <Image
          src="/favicon-monkey.png"
          alt="+12 Monkeys"
          width={40}
          height={40}
          className="brightness-0 invert opacity-80"
        />
        <span className="text-[11px] font-mono tracking-[0.3em] text-zinc-300 uppercase font-bold">
          +12 Monkeys
        </span>
      </Link>

      {!sent ? (
        <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-8">
          <div className="space-y-2 text-center">
            <p className="text-sm text-zinc-400 font-light">
              Enter your email to receive a key.
            </p>
          </div>

          <div className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
              className="w-full bg-transparent border border-zinc-800 px-4 py-3 text-sm font-mono text-zinc-300 placeholder-zinc-700 outline-none focus:border-zinc-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !email.trim()}
              className="w-full border border-zinc-700 px-4 py-3 text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-300 hover:bg-zinc-900 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {loading ? "Sending..." : "Send Key →"}
            </button>
          </div>

          <p className="text-[10px] text-zinc-700 text-center font-mono">
            No password needed. We&apos;ll email you a one-time key.
          </p>
        </form>
      ) : (
        <div className="w-full max-w-sm text-center space-y-6">
          <div className="border border-zinc-800 bg-[#050505] p-8 space-y-4">
            <p className="text-[10px] font-mono text-emerald-800 uppercase tracking-widest">
              Key Sent
            </p>
            <p className="text-sm text-zinc-400 font-light">
              Check <span className="text-zinc-200">{email}</span> for your key.
            </p>
            <p className="text-[10px] text-zinc-600 font-mono">
              Expires in 15 minutes.
            </p>
          </div>
          <button
            onClick={() => { setSent(false); setEmail(""); }}
            className="text-[10px] font-mono text-zinc-600 hover:text-zinc-300 uppercase tracking-widest transition-colors"
          >
            Try a different email
          </button>
        </div>
      )}
    </div>
  );
}

