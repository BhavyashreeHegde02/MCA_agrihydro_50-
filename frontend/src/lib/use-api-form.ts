"use client";

/**
 * Attach a backend failure to the form that caused it.
 *
 * Every create and update form in this app has the same job after a failed
 * request: put each field-level complaint under the input it belongs to, and
 * show whatever is left over as one message at the top. Doing that in each form
 * would be the same twenty lines repeated; doing it here means a farmer always
 * sees the error next to the box they need to fix.
 */

import { useState } from "react";
import type { FieldValues, Path, UseFormSetError } from "react-hook-form";

import { ApiError, humanMessage } from "@/lib/api/errors";

export function useApiFormError<T extends FieldValues>(
  setError: UseFormSetError<T>,
  knownFields: readonly Path<T>[],
) {
  const [formError, setFormError] = useState<string | null>(null);

  function clear() {
    setFormError(null);
  }

  function report(error: unknown) {
    if (error instanceof ApiError) {
      let attached = false;
      for (const [field, problem] of Object.entries(error.fieldMap())) {
        if ((knownFields as readonly string[]).includes(field)) {
          setError(field as Path<T>, { message: problem });
          attached = true;
        }
      }
      // A complaint about a field this form does not render would otherwise
      // vanish silently, so it is promoted to the banner.
      if (attached && error.fields.length === Object.keys(error.fieldMap()).length) {
        setFormError(null);
        return;
      }
    }
    setFormError(humanMessage(error));
  }

  return { formError, report, clear, setFormError };
}
