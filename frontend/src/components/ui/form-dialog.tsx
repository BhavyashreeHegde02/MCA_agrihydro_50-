"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

/**
 * shadcn's Dialog with the shape the forms in this app actually use.
 *
 * Radix reports every open/close through one `onOpenChange`; every caller here
 * only ever needs to know about closing, and all of them have to reset the form
 * when that happens. Collapsing it to `onClose` keeps that from being written
 * out — and occasionally forgotten — at each call site.
 *
 * The body scrolls rather than the page: these forms are taller than a phone
 * screen, and a dialog that grows past the viewport puts its submit button
 * somewhere unreachable.
 */
export function FormDialog({
  open,
  onClose,
  title,
  description,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent
        className={cn("gap-0 p-0 sm:max-w-lg", className)}
        // Autofocusing the first input scrolls a phone keyboard over the
        // dialog before the farmer has read the title.
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <DialogHeader className="border-b px-5 py-4 text-left">
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
