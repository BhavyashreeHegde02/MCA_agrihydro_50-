"use client";

import { useState } from "react";
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import { ApiError } from "@/lib/api/errors";

/**
 * A session that ended while the tab was open is the one failure the whole app
 * has to handle the same way, wherever it happens. Rather than checking for 401
 * in every screen, both caches funnel it here and the user is sent to the login
 * page with a note saying why.
 */
function isSessionOver(error: unknown): boolean {
  return error instanceof ApiError && error.isAuthError;
}

/**
 * Leave through the route handler that clears the dead cookies.
 *
 * A full document navigation, deliberately. `/api/auth/expired` is a route
 * handler rather than a page, so the client router cannot render it, and the
 * Set-Cookie it returns has to be applied by the browser before the login page
 * loads — otherwise proxy.ts still sees a session and bounces back. The hard
 * navigation also discards this QueryClient, which is what stops one farmer's
 * cached data being on screen while the next one signs in.
 */
function endSession(): void {
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- see above
  window.location.assign("/api/auth/expired");
}

export function Providers({ children }: { children: React.ReactNode }) {
  // useState, not a module-level client: on the server a module-level client
  // would be shared between requests, and one farmer's cached farms could be
  // served to another.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error) => {
            if (isSessionOver(error)) {
              endSession();
            }
          },
        }),
        mutationCache: new MutationCache({
          onError: (error) => {
            if (isSessionOver(error)) {
              endSession();
            }
          },
        }),
        defaultOptions: {
          queries: {
            // Farm records change when this farmer changes them, not on their
            // own, so refetching on every window focus is noise on a phone.
            refetchOnWindowFocus: false,
            staleTime: 30_000,
            retry: (failureCount, error) => {
              // Retrying a 401, 403, 404 or a validation failure cannot
              // succeed; retrying a dropped connection can.
              if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                return false;
              }
              return failureCount < 2;
            },
          },
          mutations: {
            // A mutation that is retried automatically can create two farms.
            retry: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
