/**
 * Authenticated passthrough to the backend.
 *
 * The browser calls `/api/proxy/predictions/cwr`; this handler calls
 * `BACKEND_URL/api/v1/predictions/cwr` with the access token taken from the
 * httpOnly cookie. Three things fall out of that arrangement:
 *
 *   - the token is never readable by page JavaScript, so it cannot be stolen by
 *     an injected script the way a `localStorage` value could;
 *   - the backend's address stays on the server, out of the client bundle;
 *   - an expired access token is refreshed here, once, transparently, so the
 *     farmer is not thrown back to the login screen mid-form after an hour.
 *
 * Only paths under the backend's `/api/v1` are reachable, and only the methods
 * listed at the bottom of this file. This is a proxy for this application's own
 * API, not an open relay.
 */

import { NextResponse, type NextRequest } from "next/server";

import { ApiError, parseErrorBody } from "@/lib/api/errors";
import { callBackend, refreshTokens } from "@/lib/api/server";
import {
  ACCESS_COOKIE,
  REFRESH_MAX_AGE_SECONDS,
  REFRESH_COOKIE,
  readAccessToken,
  readRefreshToken,
} from "@/lib/auth/session";
import { env } from "@/lib/env";

/** Methods a farmer's browser is allowed to send through. */
const ALLOWED_METHODS = new Set(["GET", "POST", "PUT", "DELETE"]);

/**
 * Refuse anything that tries to climb out of /api/v1.
 *
 * Next has already decoded the path segments, so a `..` would arrive as a
 * literal segment rather than being resolved away. Rejecting it explicitly is
 * cheaper than reasoning about whether `new URL` would have normalised it.
 */
function isSafeSegments(segments: string[]): boolean {
  return segments.every(
    (segment) => segment !== "" && segment !== "." && segment !== "..",
  );
}

async function handle(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const method = request.method.toUpperCase();
  if (!ALLOWED_METHODS.has(method)) {
    return NextResponse.json(
      { error: "METHOD_NOT_ALLOWED", message: `${method} is not proxied.` },
      { status: 405 },
    );
  }

  const { path: segments } = await context.params;
  if (!isSafeSegments(segments)) {
    return NextResponse.json(
      { error: "BAD_REQUEST", message: "That path is not valid." },
      { status: 400 },
    );
  }

  const backendPath = `/api/v1/${segments.join("/")}`;
  const query = Object.fromEntries(request.nextUrl.searchParams.entries());

  let body: unknown;
  if (method !== "GET" && method !== "DELETE") {
    const raw = await request.text();
    if (raw !== "") {
      try {
        body = JSON.parse(raw);
      } catch {
        return NextResponse.json(
          { error: "BAD_REQUEST", message: "The request body was not valid JSON." },
          { status: 400 },
        );
      }
    }
  }

  const accessToken = await readAccessToken();
  if (!accessToken) {
    const refreshToken = await readRefreshToken();
    if (!refreshToken) return expiredResponse();

    try {
      return await refreshAndRetry(refreshToken, (token) =>
        callBackend<unknown>({ method, path: backendPath, token, body, query }),
      );
    } catch (error) {
      return errorResponse(error);
    }
  }

  const attempt = (token: string) =>
    callBackend<unknown>({ method, path: backendPath, token, body, query });

  try {
    const { data, status } = await attempt(accessToken);
    return NextResponse.json(data, { status });
  } catch (error) {
    if (!(error instanceof ApiError) || !error.isAuthError) {
      return errorResponse(error);
    }

    // The access token was rejected. Try the refresh token exactly once; a
    // loop here would turn one dead session into a storm of requests.
    const refreshToken = await readRefreshToken();
    if (!refreshToken) return expiredResponse();

    try {
      return await refreshAndRetry(refreshToken, attempt);
    } catch (retryError) {
      return errorResponse(retryError);
    }
  }
}

async function refreshAndRetry(
  refreshToken: string,
  attempt: (token: string) => ReturnType<typeof callBackend<unknown>>,
): Promise<NextResponse> {
  const renewed = await refreshTokens(refreshToken);
  if (!renewed) return expiredResponse();

  try {
    const { data, status } = await attempt(renewed.access_token);
    const response = NextResponse.json(data, { status });
    // Persist the rotated pair on the way out, so the next request already
    // carries a valid token.
    response.cookies.set(ACCESS_COOKIE, renewed.access_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: env.cookieSecure,
      path: "/",
      maxAge: 15 * 60,
    });
    response.cookies.set(REFRESH_COOKIE, renewed.refresh_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: env.cookieSecure,
      path: "/",
      maxAge: REFRESH_MAX_AGE_SECONDS,
    });
    return response;
  } catch (error) {
    if (error instanceof ApiError && error.isAuthError) return expiredResponse();
    throw error;
  }
}

function expiredResponse(): NextResponse {
  const response = NextResponse.json(
    {
      error: "SESSION_EXPIRED",
      message: "Your session has ended. Please sign in again.",
    },
    { status: 401 },
  );
  // Clear the dead cookies so the next page load does not try again.
  const dead = {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: env.cookieSecure,
    path: "/",
    maxAge: 0,
  };
  response.cookies.set(ACCESS_COOKIE, "", dead);
  response.cookies.set(REFRESH_COOKIE, "", dead);
  return response;
}

function errorResponse(error: unknown): NextResponse {
  if (error instanceof ApiError) {
    return NextResponse.json(
      { error: error.code, message: error.message, details: error.details },
      // status 0 means we never reached the backend; report that as 502, which
      // is what it is from the browser's point of view.
      { status: error.status === 0 ? 502 : error.status },
    );
  }
  const body = parseErrorBody(500, null);
  return NextResponse.json(body, { status: 500 });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
