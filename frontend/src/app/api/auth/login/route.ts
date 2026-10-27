/**
 * Sign in.
 *
 * Takes the credentials, exchanges them with the backend, and keeps the
 * resulting tokens in httpOnly cookies. The response body carries the user, not
 * the tokens: the browser has no reason to hold a credential it cannot use
 * safely, and giving it one is how tokens end up in `localStorage`.
 */

import { NextResponse, type NextRequest } from "next/server";

import { ApiError } from "@/lib/api/errors";
import { callBackend } from "@/lib/api/server";
import { writeSession } from "@/lib/auth/session";
import type { TokenPair, UserOut } from "@/lib/api/types";

export async function POST(request: NextRequest): Promise<NextResponse> {
  let payload: { email?: unknown; password?: unknown };
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

  // Catch the empty submission here rather than spending a network round trip
  // on a request that cannot succeed.
  const fields: { field: string; problem: string }[] = [];
  if (email === "") fields.push({ field: "email", problem: "Enter your email address." });
  if (password === "") fields.push({ field: "password", problem: "Enter your password." });
  if (fields.length > 0) {
    return NextResponse.json(
      {
        error: "VALIDATION_ERROR",
        message: `${fields.length} field(s) failed validation.`,
        details: { fields },
      },
      { status: 422 },
    );
  }

  try {
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

    return NextResponse.json({ user }, { status: 200 });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { error: error.code, message: error.message, details: error.details },
        { status: error.status === 0 ? 502 : error.status },
      );
    }
    return NextResponse.json(
      { error: "INTERNAL_ERROR", message: "Sign in failed unexpectedly." },
      { status: 500 },
    );
  }
}
