/**
 * Create an account, then sign straight in.
 *
 * The backend's register endpoint returns the user, not tokens. Making the
 * farmer type the same password again immediately afterwards would be pointless
 * friction, so this handler logs in on their behalf and sets the session in the
 * same request.
 *
 * Field-level validation problems come back from the backend unchanged, so the
 * form can attach each complaint to the input that caused it.
 */

import { NextResponse, type NextRequest } from "next/server";

import { ApiError } from "@/lib/api/errors";
import { callBackend } from "@/lib/api/server";
import { writeSession } from "@/lib/auth/session";
import type { RegisterRequest, TokenPair, UserOut } from "@/lib/api/types";

function cleanOptional(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let payload: Record<string, unknown>;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { error: "BAD_REQUEST", message: "The request body was not valid JSON." },
      { status: 400 },
    );
  }

  const email = typeof payload.email === "string" ? payload.email.trim() : "";
  const password = typeof payload.password === "string" ? payload.password : "";

  const body: RegisterRequest = {
    email,
    password,
    full_name:
      typeof payload.full_name === "string" ? payload.full_name.trim() : "",
    phone: typeof payload.phone === "string" ? payload.phone.trim() : "",
    state: cleanOptional(payload.state),
    district: cleanOptional(payload.district),
    taluk: cleanOptional(payload.taluk),
  };

  try {
    await callBackend<UserOut>({
      method: "POST",
      path: "/api/v1/auth/register",
      body,
    });

    // Registration succeeded, so these credentials are known good. A failure
    // here is a server problem, not a user error.
    const { data: tokens } = await callBackend<TokenPair>({
      method: "POST",
      path: "/api/v1/auth/login",
      body: { email, password },
    });

    await writeSession({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    });

    const { data: user } = await callBackend<UserOut>({
      path: "/api/v1/auth/me",
      token: tokens.access_token,
    });

    return NextResponse.json({ user }, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { error: error.code, message: error.message, details: error.details },
        { status: error.status === 0 ? 502 : error.status },
      );
    }
    return NextResponse.json(
      { error: "INTERNAL_ERROR", message: "Registration failed unexpectedly." },
      { status: 500 },
    );
  }
}
