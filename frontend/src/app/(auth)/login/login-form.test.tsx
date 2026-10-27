import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "./login-form";

/*
 * An integration test over the sign-in screen: the schema, react-hook-form, the
 * API client and the error mapping, together. Only `fetch` and the Next
 * navigation hooks are replaced — everything between the click and the request
 * is the real code.
 */

const replace = vi.fn();
const refresh = vi.fn();
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh, push: vi.fn() }),
  useSearchParams: () => searchParams,
}));

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => "application/json" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  searchParams = new URLSearchParams();
  replace.mockClear();
  refresh.mockClear();
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("validation before anything is sent", () => {
  it("reports both fields on an empty submission and makes no request", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
    // A request that cannot succeed should not be sent.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects a malformed email without a round trip", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.type(screen.getByLabelText(/password/i), "whatever");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("a rejected sign-in", () => {
  it("explains the failure in the farmer's terms, not the backend's code", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ error: "INVALID_CREDENTIALS", message: "raw backend text" }, 401),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByText("That email and password combination was not recognised."),
    ).toBeInTheDocument();
    expect(screen.queryByText("raw backend text")).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("says the server is unreachable rather than failing silently", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    // humanMessage() rewrites the transport-level text into something a
    // farmer can act on, naming the service rather than saying "fetch failed".
    expect(
      await screen.findByText(/Cannot reach the Jalachakra server/i),
    ).toBeInTheDocument();
  });

  it("attaches a field-level complaint to the field it names", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          error: "VALIDATION_ERROR",
          message: "1 field(s) failed validation.",
          details: { fields: [{ field: "email", problem: "This address is blocked." }] },
        },
        422,
      ),
    );
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "blocked@example.com");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("This address is blocked.")).toBeInTheDocument();
  });
});

describe("a successful sign-in", () => {
  it("sends the credentials to this app's own route and navigates on", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ user: { id: 1, full_name: "Demo" } }));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "demo-password-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/dashboard"));

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/auth/login");
    expect(JSON.parse(init.body)).toEqual({
      email: "demo@example.com",
      password: "demo-password-123",
    });
    // The server components have to re-read the new cookie.
    expect(refresh).toHaveBeenCalled();
  });

  it("returns the farmer to the page they were sent away from", async () => {
    searchParams = new URLSearchParams("next=/predict");
    fetchMock.mockResolvedValue(jsonResponse({ user: { id: 1 } }));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "demo-password-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/predict"));
  });

  it("refuses to follow an off-site redirect supplied in the URL", async () => {
    // Without this check the login page would be an open redirect: a link to
    // /login?next=https://evil.example would bounce the farmer off-site
    // immediately after they authenticate.
    searchParams = new URLSearchParams("next=https://evil.example/steal");
    fetchMock.mockResolvedValue(jsonResponse({ user: { id: 1 } }));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "demo-password-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/dashboard"));
  });

  it("refuses a protocol-relative redirect too", async () => {
    searchParams = new URLSearchParams("next=//evil.example/steal");
    fetchMock.mockResolvedValue(jsonResponse({ user: { id: 1 } }));
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "demo@example.com");
    await user.type(screen.getByLabelText(/password/i), "demo-password-123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/dashboard"));
  });
});

describe("an expired session", () => {
  it("explains why the farmer is back at the login screen", async () => {
    searchParams = new URLSearchParams("reason=expired");
    render(<LoginForm />);
    expect(screen.getByText("Your session ended")).toBeInTheDocument();
  });

  it("says nothing about expiry on an ordinary visit", () => {
    render(<LoginForm />);
    expect(screen.queryByText("Your session ended")).not.toBeInTheDocument();
  });
});
