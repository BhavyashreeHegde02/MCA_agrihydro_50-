import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, auth } from "./client";
import { ApiError } from "./errors";

/** Build a Response-like object without pulling in a real fetch. */
function jsonResponse(
  body: unknown,
  status = 200,
  contentType = "application/json",
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name: string) => (name === "content-type" ? contentType : null) },
    json: async () => body,
    text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
  } as unknown as Response;
}

/**
 * Await a call that is expected to fail, and hand back the ApiError.
 *
 * `promise.catch(e => e)` types the result as `unknown`, so every assertion
 * after it fails to compile. This narrows once, here, and fails the test
 * loudly if the call unexpectedly succeeds rather than silently asserting
 * against undefined.
 */
async function captureError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
  throw new Error("expected the request to fail, but it succeeded");
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("request routing", () => {
  it("sends every call to this app's proxy, never to the backend", async () => {
    fetchMock.mockResolvedValue(jsonResponse([{ id: 1 }]));
    await api.get("farms");

    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/proxy/farms");
    // If this ever became an absolute backend URL, the access token would have
    // to live in the browser, which is the thing the whole design avoids.
    expect(String(url)).not.toMatch(/^https?:/);
  });

  it("tolerates a leading slash without doubling it", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("/farms");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/proxy/farms");
  });

  it("sends cookies, which are the whole session", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("farms");
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      credentials: "same-origin",
    });
  });
});

describe("query parameters", () => {
  it("appends the parameters it was given", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("predictions/history", { query: { limit: 5, field_crop_id: 4 } });
    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/proxy/predictions/history?limit=5&field_crop_id=4",
    );
  });

  it("drops undefined, null and empty values instead of sending them", async () => {
    // Sending `field_crop_id=` would make the backend reject the request as a
    // validation failure rather than treating the filter as absent.
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("predictions/history", {
      query: { limit: 5, field_crop_id: undefined, start_date: "", end_date: null },
    });
    expect(fetchMock.mock.calls[0][0]).toBe("/api/proxy/predictions/history?limit=5");
  });

  it("keeps a boolean false, which is a real value", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("field-crops", { query: { active_only: false } });
    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/proxy/field-crops?active_only=false",
    );
  });
});

describe("request bodies", () => {
  it("serialises a POST body and sets the content type", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: 1 }, 201));
    await api.post("farms", { name: "Test", total_area_ha: 2 });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ "content-type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ name: "Test", total_area_ha: 2 });
  });

  it("sends no body or content type on a GET", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await api.get("farms");
    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBeUndefined();
    expect(init.headers).toEqual({});
  });
});

describe("failures", () => {
  it("raises an ApiError carrying the backend's code and field problems", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          error: "VALIDATION_ERROR",
          message: "1 field(s) failed validation.",
          details: { fields: [{ field: "area_ha", problem: "must be > 0" }] },
        },
        422,
      ),
    );

    const error = await captureError(api.post("farms", {}));
    expect(error.status).toBe(422);
    expect(error.code).toBe("VALIDATION_ERROR");
    expect(error.fieldMap()).toEqual({ area_ha: "must be > 0" });
  });

  it("marks a 401 as an auth error so the session handler can act", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ error: "SESSION_EXPIRED", message: "gone" }, 401),
    );
    const error = await captureError(api.get("farms"));
    expect(error.isAuthError).toBe(true);
  });

  it("reports an unreachable server rather than throwing a raw TypeError", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const error = await captureError(api.get("farms"));
    expect(error).toBeInstanceOf(ApiError);
    expect(error.isUnreachable).toBe(true);
    expect(error.code).toBe("BACKEND_UNREACHABLE");
  });

  it("survives an HTML error page where JSON was expected", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse("<html>502 Bad Gateway</html>", 502, "text/html"),
    );
    const error = await captureError(api.get("farms"));
    expect(error.status).toBe(502);
    expect(error.message).toContain("Bad Gateway");
  });

  it("does not choke on a 204 with no body", async () => {
    fetchMock.mockResolvedValue(jsonResponse(null, 204));
    await expect(api.delete("farms/1")).resolves.toBeUndefined();
  });

  it("distinguishes a cancelled request from a dead server", async () => {
    const controller = new AbortController();
    controller.abort();
    fetchMock.mockRejectedValue(new DOMException("Aborted", "AbortError"));

    const error = await captureError(
      api.get("farms", { signal: controller.signal }),
    );
    expect(error.code).toBe("REQUEST_CANCELLED");
  });
});

describe("session endpoints", () => {
  it("posts credentials to this app's own login route, not the proxy", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ user: { id: 1 } }));
    await auth.login("a@b.co", "secret");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/auth/login");
    expect(JSON.parse(init.body)).toEqual({ email: "a@b.co", password: "secret" });
  });

  it("surfaces a rejected sign-in as an ApiError with the backend's code", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ error: "INVALID_CREDENTIALS", message: "no" }, 401),
    );
    const error = await captureError(auth.login("a@b.co", "wrong"));
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("INVALID_CREDENTIALS");
  });

  it("signs out without throwing even if the request fails", async () => {
    fetchMock.mockRejectedValue(new TypeError("offline"));
    // The local session must end regardless; a thrown error here would leave
    // a farmer apparently signed in on a shared phone.
    await expect(auth.logout()).resolves.toBeUndefined();
  });
});
