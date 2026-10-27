import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/session";
import { proxy } from "./proxy";

function tokenExpiringAt(expiry: number): string {
  const payload = btoa(JSON.stringify({ exp: expiry }))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  return `header.${payload}.signature`;
}

describe("protected page session handling", () => {
  it("refreshes an expired access token before rendering the page", () => {
    const request = new NextRequest("http://localhost/farms?tab=fields", {
      headers: {
        cookie: `${ACCESS_COOKIE}=${tokenExpiringAt(Math.floor(Date.now() / 1000) - 1)}; ${REFRESH_COOKIE}=refresh-token`,
      },
    });

    const response = proxy(request);

    expect(response.status).toBe(307);
    const destination = new URL(response.headers.get("location")!);
    expect(destination.pathname).toBe("/api/auth/refresh");
    expect(destination.searchParams.get("next")).toBe("/farms?tab=fields");
  });

  it("refreshes when the access cookie is gone but the refresh cookie remains", () => {
    const request = new NextRequest("http://localhost/farms", {
      headers: { cookie: `${REFRESH_COOKIE}=refresh-token` },
    });

    const response = proxy(request);

    expect(new URL(response.headers.get("location")!).pathname).toBe(
      "/api/auth/refresh",
    );
  });

  it("keeps a valid access token on the normal route path", () => {
    const request = new NextRequest("http://localhost/farms", {
      headers: {
        cookie: `${ACCESS_COOKIE}=${tokenExpiringAt(Math.floor(Date.now() / 1000) + 600)}; ${REFRESH_COOKIE}=refresh-token`,
      },
    });

    expect(proxy(request).headers.get("x-middleware-next")).toBe("1");
  });
});
