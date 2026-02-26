"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { verifyToken } from "@/lib/auth";
import { useAuth } from "@/components/AuthProvider";

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#030303]">
        <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest animate-pulse">Loading...</p>
      </div>
    }>
      <VerifyContent />
    </Suspense>
  );
}

function VerifyContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refresh } = useAuth();
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setErrorMsg("No key found in URL.");
      return;
    }

    verifyToken(token)
      .then(async () => {
        setStatus("success");
        await refresh();
        // Redirect to homepage after short delay
        setTimeout(() => router.replace("/"), 1500);
      })
      .catch(() => {
        setStatus("error");
        setErrorMsg("Invalid or expired key.");
      });
  }, [searchParams, router, refresh]);

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
        {status === "verifying" && (
          <>
            <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest animate-pulse">
              Verifying key...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <p className="text-[10px] font-mono text-emerald-800 uppercase tracking-widest">
              ✓ Authenticated
            </p>
            <p className="text-sm text-zinc-400 font-light">
              Redirecting...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <p className="text-[10px] font-mono text-red-800 uppercase tracking-widest">
              Key Invalid
            </p>
            <p className="text-sm text-zinc-500 font-light">{errorMsg}</p>
            <Link
              href="/sign-in"
              className="inline-block mt-4 border border-zinc-800 px-6 py-2 text-[10px] font-mono uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-zinc-900 transition-all"
            >
              Request New Key →
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

