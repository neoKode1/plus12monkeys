"use client";

import Link from "next/link";
import Image from "next/image";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#030303] px-6">
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

      <div className="w-full max-w-sm border border-zinc-800 bg-[#050505] p-8 text-center space-y-4">
        <p className="text-[10px] font-mono text-red-800 uppercase tracking-widest">
          Something went wrong
        </p>
        <p className="text-sm text-zinc-500 font-light">
          {error.message || "An unexpected error occurred."}
        </p>
        <button
          onClick={reset}
          className="inline-block mt-4 border border-zinc-800 px-6 py-2 text-[10px] font-mono uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-zinc-900 transition-all cursor-pointer"
        >
          Try Again
        </button>
        <Link
          href="/"
          className="block text-[10px] font-mono text-zinc-600 hover:text-zinc-400 transition"
        >
          ← Back to Home
        </Link>
      </div>
    </div>
  );
}

