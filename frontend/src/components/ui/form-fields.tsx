"use client";

/**
 * Label, hint, control and error as one unit, over shadcn's primitives.
 *
 * react-hook-form's `register()` returns a ref and handlers that have to reach
 * the real input element, so these wrappers forward refs rather than wrapping
 * in a controlled component. The error is wired with `aria-describedby` and
 * `aria-invalid`, so a screen reader announces the problem *with* the input
 * rather than leaving red text floating unattached, and `role="alert"` makes a
 * newly appearing error announce itself.
 */

import { forwardRef, useId } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ShellProps {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  /** Shown beside the label, e.g. "ha", "mm/day", "0 to 1". */
  unit?: string;
  children: (props: {
    id: string;
    describedBy: string | undefined;
    invalid: boolean;
  }) => React.ReactNode;
}

export function FieldShell({
  label,
  hint,
  error,
  required,
  unit,
  children,
}: ShellProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="space-y-1.5">
      <Label
        htmlFor={id}
        className="flex items-baseline justify-between gap-2 text-sm"
      >
        <span>
          {label}
          {required && (
            <span aria-hidden className="ml-0.5 text-danger">
              *
            </span>
          )}
        </span>
        {unit && (
          <span className="text-xs font-normal text-muted-foreground">
            {unit}
          </span>
        )}
      </Label>
      {hint && (
        <p id={hintId} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
      {children({ id, describedBy, invalid: Boolean(error) })}
      {error && (
        <p
          id={errorId}
          role="alert"
          className="text-sm font-medium text-danger"
        >
          {error}
        </p>
      )}
    </div>
  );
}

export interface TextFieldProps
  extends Omit<React.ComponentProps<"input">, "id"> {
  label: string;
  hint?: string;
  error?: string;
  unit?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  function TextField(
    { label, hint, error, unit, required, className, ...rest },
    ref,
  ) {
    return (
      <FieldShell
        label={label}
        hint={hint}
        error={error}
        unit={unit}
        required={required}
      >
        {({ id, describedBy, invalid }) => (
          <Input
            {...rest}
            ref={ref}
            id={id}
            required={required}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            className={cn("h-11 text-[15px]", className)}
          />
        )}
      </FieldShell>
    );
  },
);

export const NumberField = forwardRef<HTMLInputElement, TextFieldProps>(
  function NumberField({ inputMode = "decimal", ...rest }, ref) {
    /*
     * type="text" with inputMode="decimal", not type="number". The numeric
     * keypad still opens on a phone, but the scroll-wheel and spinner
     * behaviour is gone — those silently change a figure the farmer already
     * entered, and here that figure is how much water to apply.
     */
    return <TextField {...rest} ref={ref} type="text" inputMode={inputMode} />;
  },
);

export interface SelectFieldProps
  extends Omit<React.ComponentProps<"select">, "id"> {
  label: string;
  hint?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(
  function SelectField(
    { label, hint, error, options, placeholder, required, className, ...rest },
    ref,
  ) {
    /*
     * A native <select>, not shadcn's Radix Select. Radix's version renders a
     * button plus a portal and does not expose a form-associated element, so
     * react-hook-form's `register()` cannot bind to it without a Controller
     * per field. The native control is also the one a low-end Android phone
     * renders as a full-screen picker, which is easier to use in the field.
     */
    return (
      <FieldShell label={label} hint={hint} error={error} required={required}>
        {({ id, describedBy, invalid }) => (
          <select
            {...rest}
            ref={ref}
            id={id}
            required={required}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            className={cn(
              "h-11 w-full rounded-lg border bg-background px-3 text-[15px] text-foreground",
              "focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
              "disabled:cursor-not-allowed disabled:opacity-60",
              invalid ? "border-destructive" : "border-input",
              className,
            )}
          >
            {placeholder && <option value="">{placeholder}</option>}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )}
      </FieldShell>
    );
  },
);

export interface TextAreaFieldProps
  extends Omit<React.ComponentProps<"textarea">, "id"> {
  label: string;
  hint?: string;
  error?: string;
}

export const TextAreaField = forwardRef<
  HTMLTextAreaElement,
  TextAreaFieldProps
>(function TextAreaField(
  { label, hint, error, required, rows = 3, className, ...rest },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} required={required}>
      {({ id, describedBy, invalid }) => (
        <Textarea
          {...rest}
          ref={ref}
          id={id}
          rows={rows}
          required={required}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          className={cn("text-[15px]", className)}
        />
      )}
    </FieldShell>
  );
});
