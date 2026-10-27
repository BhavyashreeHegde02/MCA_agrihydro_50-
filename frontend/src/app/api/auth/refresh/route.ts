/**
 * Refresh an access token before a protected page is server-rendered.
 *
 * Server components cannot write cookies. The page proxy sends tokens that
 * are missing or near expiry through this route first, then returns to the
 * requested local path with the renewed cookie pair.
 */

import { NextResponse, type NextRequest } from "next/server";

import { ApiError } from "@/lib/api/errors";
import { refreshTokens } from "@/lib/api/server";
import {
  clearSession,
  readRefreshToken,
  writeSession,
} from "@/lib/auth/session";

function safeNextPath(value: string | null, request: NextRequest): URL {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return new URL("/dashboard", request.url);
  }
  const next = new URL(value, request.url);
  return next.origin === new URL(request.url).origin
    ? next
    : new URL("/dashboard", request.url);
}

function expiredRedirect(next: URL, request: NextRequest): NextResponse {
  const login = new URL("/login", request.url);
  login.searchParams.set("reason", "expired");
  login.searchParams.set("next", `${next.pathname}${next.search}`);
  return NextResponse.redirect(login);
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const next = safeNextPath(request.nextUrl.searchParams.get("next"), request);
  const refreshToken = await readRefreshToken();

  if (!refreshToken) {
    await clearSession();
    return expiredRedirect(next, request);
  }

  try {
    const renewed = await refreshTokens(refreshToken);
    if (!renewed) {
      await clearSession();
      return expiredRedirect(next, request);
    }

    await writeSession({
      accessToken: renewed.access_token,
      refreshToken: renewed.refresh_token,
    });
    return NextResponse.redirect(next);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { error: error.code, message: error.message, details: error.details },
        { status: error.status === 0 ? 502 : error.status },
      );
    }
    return NextResponse.json(
      { error: "INTERNAL_ERROR", message: "Session refresh failed unexpectedly." },
      { status: 500 },
    );
  }
}
