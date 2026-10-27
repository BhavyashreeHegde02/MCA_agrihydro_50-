/**
 * End a session the backend has already rejected.
 *
 * A server component can read cookies but cannot set them, so when `rscGet`
 * discovers the access token is no longer accepted it cannot clear the dead
 * cookie itself. Redirecting straight to /login does not help either: the
 * cookie is still there, `proxy.ts` sees a signed-in visitor on a public page
 * and sends them back to /dashboard, which fails the same way — a redirect
 * loop that ends only when the browser gives up.
 *
 * This route is the way out. It is a route handler, so it *can* clear the
 * cookies, and it then sends the farmer to the login page with the reason.
 */

import { NextResponse, type NextRequest } from "next/server";

import { clearSession } from "@/lib/auth/session";

export async function GET(request: NextRequest): Promise<NextResponse> {
  await clearSession();

  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  url.searchParams.set("reason", "expired");

  // Preserve where they were headed, but only if it is a path on this site;
  // an absolute URL here would make this an open redirect.
  const next = request.nextUrl.searchParams.get("next");
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    url.searchParams.set("next", next);
  }

  return NextResponse.redirect(url);
}
