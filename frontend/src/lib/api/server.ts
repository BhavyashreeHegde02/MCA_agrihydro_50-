/**
 * Server-side access to the FastAPI backend.
 *
 * Everything that talks to the backend goes through here, so timeouts, error
 * normalisation and token refresh are implemented once. The browser never calls
 * the backend directly — it calls this app's `/api/proxy/...` route, which uses
 * these functions. Two consequences worth stating: the access token stays in an
 * httpOnly cookie, and `BACKEND_URL` never appears in the client bundle.
 */

import "server-only";

import {
  ApiError,
  parseErrorBody,
  transportError,
} from "./errors";
import { env } from "@/lib/env";

export interface BackendResponse<T> {
  data: T;
  status: number;
}

interface CallOptions {
  method?: string;
  path: string;
  token?: string | null;
  body?: unknown;
  /** Appended as a query string; undefined and null entries are dropped. */
  query?: Record<string, string | number | boolean | null | undefined>;
  /** Next.js fetch caching. Defaults to no-store: this data is per-farmer. */
  cache?: RequestCache;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: CallOptions["query"]): string {
  const url = new URL(
    path.startsWith("/") ? path : `/${path}`,
    `${env.backendUrl}/`,
  );
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/**
 * Read a response body without assuming it is JSON.
 *
 * A gateway timeout or a crash upstream can return HTML. Parsing blindly would
 * replace a useful 502 with an unhelpful SyntaxError.
 */
async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (response.status === 204) return null;
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
  try {
    return await response.text();
  } catch {
    return null;
  }
}

/**
 * One call to the backend. Returns the parsed body, or throws an ApiError that
 * already carries the backend's own error code and per-field problems.
 */
export async function callBackend<T>(options: CallOptions): Promise<BackendResponse<T>> {
  const { method = "GET", path, token, body, query, cache = "no-store", signal } = options;

  const headers: Record<string, string> = { accept: "application/json" };
  if (token) headers.authorization = `Bearer ${token}`;
  if (body !== undefined) headers["content-type"] = "application/json";

  // A request that never returns would hang the page. Abort on our own timeout
  // and report it as a timeout rather than as a generic network failure.
  const timeout = AbortSignal.timeout(env.backendTimeoutMs);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache,
      signal: combined,
    });
  } catch {
    if (timeout.aborted) {
      throw transportError(
        "BACKEND_TIMEOUT",
        `The backend did not answer within ${env.backendTimeoutMs} ms.`,
      );
    }
    if (signal?.aborted) {
      throw transportError("REQUEST_CANCELLED", "The request was cancelled.");
    }
    throw transportError(
      "BACKEND_UNREACHABLE",
      `Could not reach the backend at ${env.backendUrl}. Is it running?`,
    );
  }

  const parsed = await readBody(response);
  if (!response.ok) {
    throw new ApiError(response.status, parseErrorBody(response.status, parsed));
  }
  return { data: parsed as T, status: response.status };
}

/**
 * Exchange a refresh token for a new pair.
 *
 * Returns null rather than throwing when the refresh token is itself rejected:
 * at that point the session is simply over, which is an expected outcome and
 * not an error the caller needs a stack trace for.
 */
export async function refreshTokens(
  refreshToken: string,
): Promise<{ access_token: string; refresh_token: string } | null> {
  try {
    const { data } = await callBackend<{
      access_token: string;
      refresh_token: string;
    }>({
      method: "POST",
      path: "/api/v1/auth/refresh",
      body: { refresh_token: refreshToken },
    });
    return data;
  } catch (error) {
    if (error instanceof ApiError && (error.isAuthError || error.status === 422)) {
      return null;
    }
    throw error;
  }
}
