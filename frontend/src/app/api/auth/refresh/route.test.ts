import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  clearSession,
  readRefreshToken,
  refreshTokens,
  writeSession,
} = vi.hoisted(() => ({
  clearSession: vi.fn(),
  readRefreshToken: vi.fn(),
  refreshTokens: vi.fn(),
  writeSession: vi.fn(),
}));

vi.mock("@/lib/auth/session", () => ({
  clearSession,
  readRefreshToken,
  writeSession,
}));
vi.mock("@/lib/api/server", () => ({ refreshTokens }));

import { GET } from "./route";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("page session refresh route", () => {
  it("renews the token pair and returns to the requested page", async () => {
    readRefreshToken.mockResolvedValue("valid-refresh-token");
    refreshTokens.mockResolvedValue({
      access_token: "new-access-token",
      refresh_token: "new-refresh-token",
    });
    const request = new NextRequest(
      "http://localhost/api/auth/refresh?next=%2Ffarms%3Ftab%3Dfields",
    );

    const response = await GET(request);

    expect(refreshTokens).toHaveBeenCalledWith("valid-refresh-token");
    expect(writeSession).toHaveBeenCalledWith({
      accessToken: "new-access-token",
      refreshToken: "new-refresh-token",
    });
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://localhost/farms?tab=fields",
    );
  });

  it("clears the session and sends the farmer to sign in if refresh fails", async () => {
    readRefreshToken.mockResolvedValue("expired-refresh-token");
    refreshTokens.mockResolvedValue(null);
    const request = new NextRequest(
      "http://localhost/api/auth/refresh?next=%2Ffarms",
    );

    const response = await GET(request);
    const destination = new URL(response.headers.get("location")!);

    expect(clearSession).toHaveBeenCalledOnce();
    expect(destination.pathname).toBe("/login");
    expect(destination.searchParams.get("reason")).toBe("expired");
    expect(destination.searchParams.get("next")).toBe("/farms");
  });

  it("does not allow a refresh redirect to leave this site", async () => {
    readRefreshToken.mockResolvedValue("valid-refresh-token");
    refreshTokens.mockResolvedValue({
      access_token: "new-access-token",
      refresh_token: "new-refresh-token",
    });
    const request = new NextRequest(
      "http://localhost/api/auth/refresh?next=%2F%5C%5Cevil.example",
    );

    const response = await GET(request);

    expect(response.headers.get("location")).toBe("http://localhost/dashboard");
  });
});
