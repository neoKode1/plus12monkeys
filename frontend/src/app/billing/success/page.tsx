"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useAuth } from "@/components/AuthProvider";

export default function BillingSuccessPage() {
  const { refresh } = useAuth();

  useEffect(() => {
    // Refresh user data to pick up the new Pro plan
    refresh();
  }, [refresh]);

  return (
    <div className="min-h-screen bg-[#030303] flex items-center justify-center font-mono text-zinc-300">
      <div className="border border-zinc-800 bg-[#050505] p-8 max-w-md w-full mx-4 space-y-6 text-center">
        <div className="text-[#00FF41] text-4xl">✓</div>
        <h1 className="text-lg font-light">You&apos;re Pro</h1>
        <p className="text-xs text-zinc-500 leading-relaxed">
          Your +12 Monkeys Pro subscription is active. You now have unlimited access for the next year.
        </p>
        <Link
          href="/wizard"
          className="block border border-[#00FF41] py-3 text-[10px] font-mono uppercase tracking-widest text-[#00FF41] hover:bg-[#00FF41] hover:text-black transition"
        >
          Continue Building →
        </Link>
      </div>
    </div>
  );
}

