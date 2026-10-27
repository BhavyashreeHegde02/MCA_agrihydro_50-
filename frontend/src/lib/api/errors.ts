/**
 * One error type for every way a request can fail.
 *
 * The backend returns a single error shape for every failure:
 *
 *     { "error": "VALIDATION_ERROR",
 *       "message": "2 field(s) failed validation.",
 *       "details": { "fields": [{ "field": "area_ha", "problem": "..." }] } }
 *
 * That shape is preserved end to end. A form can therefore attach a backend
 * complaint to the exact input that caused it, instead of dropping a generic
 * banner on the page and making the farmer guess which box is wrong.
 *
 * Transport failures (the backend is down, the request timed out) are given the
 * same shape with a synthetic code, so callers handle one type rather than two.
 */

export interface FieldProblem {
  field: string;
  problem: string;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  details?: { fields?: FieldProblem[] } & Record<string, unknown>;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: FieldProblem[];
  readonly details?: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error;
    this.fields = body.details?.fields ?? [];
    this.details = body.details;
  }

  /** The session is gone or was never established. */
  get isAuthError(): boolean {
    return this.status === 401;
  }

  /** The request was understood and refused. */
  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  /** A uniqueness rule was violated, such as registering a taken email. */
  get isConflict(): boolean {
    return this.status === 409;
  }

  get isValidation(): boolean {
    return this.status === 422 || this.fields.length > 0;
  }

  /**
   * The backend could not be reached at all, as opposed to answering with a
   * refusal. Worth distinguishing: one is retryable, the other is not.
   */
  get isUnreachable(): boolean {
    return this.status === 0;
  }

  /** Field problems keyed by field name, for react-hook-form's `setError`. */
  fieldMap(): Record<string, string> {
    const map: Record<string, string> = {};
    for (const { field, problem } of this.fields) {
      // First problem wins: showing one clear sentence under an input beats
      // stacking three.
      if (!(field in map)) map[field] = problem;
    }
    return map;
  }
}

/** A message a farmer can act on, for each failure we can anticipate. */
export function humanMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return error instanceof Error && error.message
      ? error.message
      : "Something went wrong. Please try again.";
  }
  switch (error.code) {
    case "BACKEND_UNREACHABLE":
      return "Cannot reach the Jalachakra server. Check that it is running, then try again.";
    case "BACKEND_TIMEOUT":
      return "The server took too long to answer. It may be busy — please try again.";
    case "INVALID_CREDENTIALS":
      return "That email and password combination was not recognised.";
    case "EMAIL_ALREADY_REGISTERED":
      return "An account already exists with that email address.";
    case "NOT_AUTHENTICATED":
    case "INVALID_TOKEN":
    case "USER_INACTIVE":
      return "Your session has ended. Please sign in again.";
    case "SERVICE_UNAVAILABLE":
      return error.message || "That service is temporarily unavailable.";
    default:
      return error.message || "Something went wrong. Please try again.";
  }
}

/** Build an ApiError for a failure that happened before the backend answered. */
export function transportError(code: string, message: string): ApiError {
  return new ApiError(0, { error: code, message });
}

/**
 * Coerce whatever a failed response carried into the standard shape.
 *
 * A proxy, a load balancer or an unhandled crash can return HTML or an empty
 * body where JSON was expected. Rather than throwing a parse error that hides
 * the real status, that case is reported as the status it actually was.
 */
export function parseErrorBody(status: number, raw: unknown): ApiErrorBody {
  if (raw && typeof raw === "object") {
    const candidate = raw as Partial<ApiErrorBody>;
    if (typeof candidate.error === "string" && typeof candidate.message === "string") {
      return candidate as ApiErrorBody;
    }
    // FastAPI's own default shape, if a handler slips past our middleware.
    const detail = (raw as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return { error: codeForStatus(status), message: detail };
    }
  }
  if (typeof raw === "string" && raw.trim() !== "") {
    return { error: codeForStatus(status), message: raw.slice(0, 500) };
  }
  return {
    error: codeForStatus(status),
    message: `The server returned ${status} with no explanation.`,
  };
}

function codeForStatus(status: number): string {
  const codes: Record<number, string> = {
    400: "BAD_REQUEST",
    401: "NOT_AUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
  };
  return codes[status] ?? "ERROR";
}
