/**
 * The browser's API client.
 *
 * Every call goes to this application's own `/api/proxy/...` route, never to
 * the backend directly, so no token and no backend address is present in the
 * client bundle. Failures arrive as `ApiError`, carrying the backend's error
 * code and per-field problems, which is what lets a form highlight the input
 * that was actually wrong.
 *
 * This module is imported by client components. It must not import anything
 * marked `server-only`.
 */

import { ApiError, parseErrorBody, transportError } from "./errors";

export type QueryValue = string | number | boolean | null | undefined;

export interface RequestOptions {
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

function buildPath(path: string, query?: Record<string, QueryValue>): string {
  const clean = path.startsWith("/") ? path.slice(1) : path;
  const search = new URLSearchParams();
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      search.set(key, String(value));
    }
  }
  const suffix = search.toString();
  return `/api/proxy/${clean}${suffix ? `?${suffix}` : ""}`;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildPath(path, options.query), {
      method,
      headers: body === undefined ? {} : { "content-type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: options.signal,
      // Cookies are the session. Without this the proxy sees an anonymous call.
      credentials: "same-origin",
    });
  } catch {
    if (options.signal?.aborted) {
      throw transportError("REQUEST_CANCELLED", "The request was cancelled.");
    }
    throw transportError(
      "BACKEND_UNREACHABLE",
      "Cannot reach the server. Check your connection and try again.",
    );
  }

  if (response.status === 204) return undefined as T;

  let parsed: unknown = null;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      parsed = await response.json();
    } catch {
      parsed = null;
    }
  } else {
    parsed = await response.text().catch(() => null);
  }

  if (!response.ok) {
    throw new ApiError(response.status, parseErrorBody(response.status, parsed));
  }
  return parsed as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>("GET", path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>("DELETE", path, undefined, options),
};

/**
 * The session endpoints sit outside the proxy, because they set cookies.
 */
export const auth = {
  async login(email: string, password: string) {
    return sessionCall("/api/auth/login", { email, password });
  },
  async register(payload: Record<string, unknown>) {
    return sessionCall("/api/auth/register", payload);
  },
  /**
   * End the session. Never rejects.
   *
   * Clearing the cookies is the server's job, and it happens whatever the
   * backend says. If the request cannot even be sent, the caller still has to
   * be able to navigate away — a rejected promise here would leave a farmer
   * staring at a failed sign-out on a shared phone. The cookie does survive an
   * unsent request, so `proxy.ts` will simply route them back into the app,
   * which is the honest outcome: they are, in fact, still signed in.
   */
  async logout(): Promise<void> {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
    } catch {
      // Intentionally swallowed; see above.
    }
  },
};

async function sessionCall(url: string, body: unknown) {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });
  } catch {
    throw transportError(
      "BACKEND_UNREACHABLE",
      "Cannot reach the server. Check your connection and try again.",
    );
  }

  const parsed = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, parseErrorBody(response.status, parsed));
  }
  return parsed as { user: import("./types").UserOut };
}
