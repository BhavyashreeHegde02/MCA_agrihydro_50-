/**
 * The session, held in httpOnly cookies.
 *
 * The access and refresh tokens are never handed to JavaScript. They are set by
 * this app's own route handlers, sent back by the browser automatically, and
 * read only on the server when proxying to the backend. A cross-site script
 * that manages to run in the page therefore cannot read or exfiltrate them,
 * which `localStorage` would not prevent.
 *
 * Cookie lifetimes mirror the backend's token lifetimes so the browser stops
 * sending a credential at roughly the moment the backend stops accepting it.
 */

import "server-only";

import { cookies } from "next/headers";

import { env } from "@/lib/env";

export const ACCESS_COOKIE = "jc_access";
export const REFRESH_COOKIE = "jc_refresh";

/** Backend default: ACCESS_TOKEN_EXPIRE_MINUTES=15. */
const ACCESS_MAX_AGE_SECONDS = 15 * 60;
/** Backend default: REFRESH_TOKEN_EXPIRE_MINUTES=10080 (7 days). */
export const REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

const baseCookie = {
  httpOnly: true,
  // `lax` still sends the cookie on top-level navigation, so a link into the
  // app keeps the session, while cross-site form posts do not carry it.
  sameSite: "lax",
  secure: env.cookieSecure,
  path: "/",
} as const;

export interface SessionTokens {
  accessToken: string;
  refreshToken: string;
}

export async function readAccessToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(ACCESS_COOKIE)?.value ?? null;
}

export async function readRefreshToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(REFRESH_COOKIE)?.value ?? null;
}

export async function writeSession(tokens: SessionTokens): Promise<void> {
  const store = await cookies();
  store.set(ACCESS_COOKIE, tokens.accessToken, {
    ...baseCookie,
    maxAge: ACCESS_MAX_AGE_SECONDS,
  });
  store.set(REFRESH_COOKIE, tokens.refreshToken, {
    ...baseCookie,
    maxAge: REFRESH_MAX_AGE_SECONDS,
  });
}

export async function clearSession(): Promise<void> {
  const store = await cookies();
  // maxAge 0 rather than delete(): it expires the cookie on browsers that
  // ignore a bare deletion for a cookie set with attributes.
  store.set(ACCESS_COOKIE, "", { ...baseCookie, maxAge: 0 });
  store.set(REFRESH_COOKIE, "", { ...baseCookie, maxAge: 0 });
}

/** Whether a request carries something worth trying. Not proof of validity. */
export async function hasSession(): Promise<boolean> {
  return (await readAccessToken()) !== null;
}
