import { describe, expect, it } from "vitest";

import {
  ApiError,
  humanMessage,
  parseErrorBody,
  transportError,
} from "./errors";

describe("ApiError", () => {
  it("classifies each status the backend actually returns", () => {
    const cases: [number, keyof ApiError][] = [
      [401, "isAuthError"],
      [403, "isForbidden"],
      [404, "isNotFound"],
      [409, "isConflict"],
      [422, "isValidation"],
      [0, "isUnreachable"],
    ];
    for (const [status, flag] of cases) {
      const error = new ApiError(status, { error: "X", message: "m" });
      expect(error[flag], `status ${status} -> ${String(flag)}`).toBe(true);
    }
  });

  it("treats a response carrying field problems as a validation failure even at 400", () => {
    const error = new ApiError(400, {
      error: "AREA_EXCEEDS_FARM",
      message: "bad",
      details: { fields: [{ field: "area_ha", problem: "too large" }] },
    });
    expect(error.isValidation).toBe(true);
  });

  it("keeps the backend error code rather than inventing one", () => {
    const error = new ApiError(409, {
      error: "EMAIL_ALREADY_REGISTERED",
      message: "taken",
    });
    expect(error.code).toBe("EMAIL_ALREADY_REGISTERED");
    expect(error.message).toBe("taken");
  });

  it("maps field problems for a form, keeping the first problem per field", () => {
    const error = new ApiError(422, {
      error: "VALIDATION_ERROR",
      message: "2 field(s) failed validation.",
      details: {
        fields: [
          { field: "email", problem: "not an email" },
          { field: "password", problem: "too short" },
          { field: "email", problem: "second complaint" },
        ],
      },
    });
    expect(error.fieldMap()).toEqual({
      email: "not an email",
      password: "too short",
    });
  });

  it("reports an empty field map when the failure was not field-level", () => {
    const error = new ApiError(500, { error: "INTERNAL_ERROR", message: "boom" });
    expect(error.fieldMap()).toEqual({});
    expect(error.fields).toEqual([]);
  });
});

describe("parseErrorBody", () => {
  it("passes through the backend's own shape untouched", () => {
    const body = { error: "NOT_FOUND", message: "No farm with id 9 was found." };
    expect(parseErrorBody(404, body)).toEqual(body);
  });

  it("accepts FastAPI's bare `detail` shape", () => {
    expect(parseErrorBody(404, { detail: "Not Found" })).toEqual({
      error: "NOT_FOUND",
      message: "Not Found",
    });
  });

  it("does not throw when a gateway returns HTML instead of JSON", () => {
    const parsed = parseErrorBody(502, "<html><body>Bad Gateway</body></html>");
    expect(parsed.error).toBe("BAD_GATEWAY");
    expect(parsed.message).toContain("Bad Gateway");
  });

  it("explains an empty body rather than producing an empty message", () => {
    const parsed = parseErrorBody(503, null);
    expect(parsed.error).toBe("SERVICE_UNAVAILABLE");
    expect(parsed.message).toMatch(/503/);
  });

  it("truncates an unreasonably long text body", () => {
    const parsed = parseErrorBody(500, "x".repeat(5000));
    expect(parsed.message.length).toBeLessThanOrEqual(500);
  });
});

describe("humanMessage", () => {
  it("rewrites codes a farmer should not have to interpret", () => {
    expect(humanMessage(transportError("BACKEND_UNREACHABLE", "raw"))).toMatch(
      /Cannot reach/i,
    );
    expect(
      humanMessage(new ApiError(401, { error: "INVALID_TOKEN", message: "raw" })),
    ).toMatch(/sign in again/i);
    expect(
      humanMessage(
        new ApiError(401, { error: "INVALID_CREDENTIALS", message: "raw" }),
      ),
    ).toMatch(/not recognised/i);
  });

  it("prefers the backend's own message when it is already specific", () => {
    const error = new ApiError(400, {
      error: "AREA_EXCEEDS_FARM",
      message: "The field is larger than the farm it belongs to.",
    });
    expect(humanMessage(error)).toBe(
      "The field is larger than the farm it belongs to.",
    );
  });

  it("handles a non-ApiError without exposing an empty string", () => {
    expect(humanMessage(new Error(""))).toMatch(/went wrong/i);
    expect(humanMessage("not an error at all")).toMatch(/went wrong/i);
  });
});
