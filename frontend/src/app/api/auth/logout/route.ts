/**
 * Sign out.
 *
 * Clearing the cookies is what actually ends the session for this browser, and
 * it happens whatever the backend says. The backend is still told, because it
 * keeps the audit line, but a network failure there must not leave a farmer
 * apparently signed in on a shared phone.
 */

import { NextResponse } from "next/server";

import { callBackend } from "@/lib/api/server";
import { clearSession, readAccessToken } from "@/lib/auth/session";

export async function POST(): Promise<NextResponse> {
  const token = await readAccessToken();

  if (token) {
    try {
      await callBackend({ method: "POST", path: "/api/v1/auth/logout", token });
    } catch {
      // Deliberately swallowed. See the note above: the local session ends
      // regardless, and reporting a failure here would be misleading.
    }
  }

  await clearSession();
  return NextResponse.json({ message: "Signed out." }, { status: 200 });
}
