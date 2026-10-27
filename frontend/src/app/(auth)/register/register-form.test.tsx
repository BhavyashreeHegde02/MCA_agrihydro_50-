import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RegisterForm } from "./register-form";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh, push: vi.fn() }),
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
  replace.mockClear();
  refresh.mockClear();
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("registration validation", () => {
  it("blocks an incomplete form before sending a request", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText("Enter your name.")).toBeInTheDocument();
    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText(/one uppercase letter/)).toBeInTheDocument();
    expect(screen.getByText("Mobile number must contain exactly 10 digits.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("successful registration", () => {
  it("sends the validated mobile number and signs the farmer in", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ user: { id: 1, full_name: "A Farmer" } }, 201),
    );
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "A Farmer");
    await user.type(screen.getByLabelText(/email/i), "farmer@example.com");
    await user.type(screen.getByLabelText(/phone/i), "9876543210");
    await user.type(screen.getByLabelText(/^password/i), "Farmer-pass1!");
    await user.type(screen.getByLabelText(/confirm password/i), "Farmer-pass1!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/dashboard"));
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/auth/register");
    const body = JSON.parse(init.body);
    expect(body).toMatchObject({
      full_name: "A Farmer",
      email: "farmer@example.com",
      phone: "9876543210",
      password: "Farmer-pass1!",
    });
    expect(body).not.toHaveProperty("confirm_password");
    expect(refresh).toHaveBeenCalled();
  });
});
