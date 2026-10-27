/**
 * Route protection.
 *
 * Named `proxy.ts` rather than `middleware.ts`: Next.js 16 renamed the
 * convention, and the old filename is deprecated.
 *
 * It reads the token expiry without verifying the signature, so it can refresh
 * a stale token before a server-rendered page tries to use it. The backend
 * remains the authority that verifies every token. This avoids both shipping
 * the signing secret to the proxy and logging a farmer out on page navigation.
 */

import { NextResponse, type NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/session";

const REFRESH_BUFFER_SECONDS = 60;

/** Reachable without a session. */
const PUBLIC_PATHS = ["/login", "/register"];

export function proxy(request: NextRequest): NextResponse {
  const { pathname, search } = request.nextUrl;
  const hasSession = request.cookies.has(ACCESS_COOKIE);
  const hasRefreshToken = request.cookies.has(REFRESH_COOKIE);
  const isPublic =
    pathname === "/" ||
    PUBLIC_PATHS.some(
      (path) => pathname === path || pathname.startsWith(`${path}/`),
    );

  if (!hasSession && !hasRefreshToken && !isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = "";
    // Remember where they were headed so sign-in can return them there.
    if (pathname !== "/") {
      url.searchParams.set("next", `${pathname}${search}`);
    }
    return NextResponse.redirect(url);
  }

  if (!isPublic && hasRefreshToken && shouldRefresh(request.cookies.get(ACCESS_COOKIE)?.value)) {
    const url = request.nextUrl.clone();
    url.pathname = "/api/auth/refresh";
    url.search = "";
    url.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(url);
  }

  /*
   * Someone already signed in has no use for the login form — unless they
   * arrived because their session was rejected. In that case the cookie is
   * present but dead, and bouncing them to /dashboard would loop: the page
   * fails, redirects back here, and round it goes. The expiry route clears
   * the cookie, so this only has to avoid fighting it.
   */
  const reportingExpiry = request.nextUrl.searchParams.get("reason") === "expired";
  if (hasSession && isPublic && !reportingExpiry) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

/**
 * The payload is only inspected to decide when to refresh; the backend still
 * verifies every access and refresh token before accepting it.
 */
function shouldRefresh(token: string | undefined): boolean {
  if (!token) return true;

  try {
    const payload = token.split(".")[1];
    if (!payload) return true;
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const claims: unknown = JSON.parse(atob(base64));
    if (!claims || typeof claims !== "object" || !("exp" in claims)) return true;
    const expiry = claims.exp;
    return typeof expiry !== "number" ||
      expiry <= Math.floor(Date.now() / 1000) + REFRESH_BUFFER_SECONDS;
  } catch {
    return true;
  }
}

export const config = {
  /*
   * Everything except Next's own assets and the API routes. The API routes are
   * excluded deliberately: /api/auth/login must be reachable without a session,
   * and /api/proxy returns a JSON 401 rather than a redirect, which is what a
   * fetch caller can actually handle.
   */
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};
