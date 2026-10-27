/**
 * Reads for server components.
 *
 * A server component cannot set cookies, so it cannot refresh an expired token
 * — that happens in the `/api/proxy` route on the browser's next request. What
 * this does instead is fail cleanly: a rejected token sends the farmer to the
 * login screen with a reason, rather than rendering a shell full of error
 * cards.
 */

import "server-only";

import { redirect } from "next/navigation";

import { ApiError } from "./errors";
import { callBackend } from "./server";
import { readAccessToken } from "@/lib/auth/session";

/**
 * Where to send someone whose token the backend has rejected.
 *
 * Not /login directly: the dead cookie is still set, so proxy.ts would treat
 * them as signed in and bounce them back, looping. This route clears the
 * cookies first — see src/app/api/auth/expired/route.ts.
 */
const EXPIRED_ROUTE = "/api/auth/expired";

/** Fetch as the signed-in farmer, or redirect to sign in. */
export async function rscGet<T>(
  path: string,
  query?: Record<string, string | number | boolean | null | undefined>,
): Promise<T> {
  const token = await readAccessToken();
  if (!token) redirect(EXPIRED_ROUTE);

  try {
    const { data } = await callBackend<T>({ path, token, query });
    return data;
  } catch (error) {
    if (error instanceof ApiError && error.isAuthError) {
      redirect(EXPIRED_ROUTE);
    }
    throw error;
  }
}

/**
 * Fetch, or return null if the call fails for any reason other than the session
 * being over.
 *
 * For panels that are useful but not essential: a dashboard should still render
 * the farmer's fields when the weather provider happens to be down.
 */
export async function rscGetOptional<T>(
  path: string,
  query?: Record<string, string | number | boolean | null | undefined>,
): Promise<T | null> {
  const token = await readAccessToken();
  if (!token) redirect(EXPIRED_ROUTE);

  try {
    const { data } = await callBackend<T>({ path, token, query });
    return data;
  } catch (error) {
    if (error instanceof ApiError && error.isAuthError) {
      redirect(EXPIRED_ROUTE);
    }
    return null;
  }
}
