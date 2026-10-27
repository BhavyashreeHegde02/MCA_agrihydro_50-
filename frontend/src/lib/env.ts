/**
 * Server-side environment, read once and validated.
 *
 * This module must never be imported from a client component. It reads
 * `process.env` values that are deliberately *not* prefixed `NEXT_PUBLIC_`, so
 * they exist only on the server and never reach the browser bundle.
 */

import "server-only";

function readString(name: string, fallback: string): string {
  const value = process.env[name];
  return value === undefined || value === "" ? fallback : value;
}

function readInt(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined || raw === "") return fallback;
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(
      `${name} must be a positive integer, received ${JSON.stringify(raw)}`,
    );
  }
  return parsed;
}

function readBool(name: string, fallback: boolean): boolean {
  const raw = process.env[name];
  if (raw === undefined || raw === "") return fallback;
  return ["1", "true", "yes", "on"].includes(raw.toLowerCase());
}

/** Trailing slashes make `${base}${path}` produce doubled separators. */
function stripTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

export const env = {
  backendUrl: stripTrailingSlash(
    readString("BACKEND_URL", "http://127.0.0.1:8000"),
  ),
  backendTimeoutMs: readInt("BACKEND_TIMEOUT_MS", 30_000),
  cookieSecure: readBool("COOKIE_SECURE", false),
  isProduction: process.env.NODE_ENV === "production",
} as const;
