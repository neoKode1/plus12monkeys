/** Auth API client for +12 Monkeys magic-link auth. */

// Use relative URLs so requests go through Next.js rewrites (same-origin cookies)
const API_BASE = "";

export interface AuthUser {
  email: string;
  created_at: string;
  usage_count: number;
  plan: "free" | "pro";
  subscription_expires_at: string | null;
}

/** Request a magic-link email. */
export async function sendKey(email: string): Promise<{ ok: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/send-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  });
  return res.json();
}

/** Verify a magic-link token and set session cookie. */
export async function verifyToken(token: string): Promise<{ ok: boolean; email: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ token }),
  });
  if (!res.ok) throw new Error("Invalid or expired key.");
  return res.json();
}

/** Get the current authenticated user (via session cookie). */
export async function getMe(): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/** Log out (clear session cookie). */
export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

// ── Billing ──

export interface BillingStatus {
  usage_count: number;
  plan: "free" | "pro";
  free_limit: number;
  needs_upgrade: boolean;
  subscription_expires_at: string | null;
}

export interface UsageResult {
  allowed: boolean;
  usage_count: number;
  plan: string;
  remaining?: number;
  message?: string;
}

/** Get current billing status. */
export async function getBillingStatus(): Promise<BillingStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/billing/status`, {
      credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/** Increment usage and check if allowed. */
export async function recordUsage(): Promise<UsageResult | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/billing/use`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/** Create a Stripe Checkout session and return the URL. */
export async function createCheckout(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/billing/checkout`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.url;
  } catch {
    return null;
  }
}

