"use client";

import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <div className="min-h-screen bg-[#030303] flex items-center justify-center font-mono text-zinc-300">
      <div className="border border-zinc-800 bg-[#050505] p-8 max-w-md w-full mx-4 space-y-6 text-center">
        <div className="text-zinc-600 text-4xl">×</div>
        <h1 className="text-lg font-light">Checkout Cancelled</h1>
        <p className="text-xs text-zinc-500 leading-relaxed">
          No worries — you can upgrade anytime. You still have your free uses available.
        </p>
        <Link
          href="/wizard"
          className="block border border-zinc-800 py-3 text-[10px] font-mono uppercase tracking-widest text-zinc-500 hover:bg-zinc-900 hover:text-white transition"
        >
          Back to Wizard
        </Link>
      </div>
    </div>
  );
}

