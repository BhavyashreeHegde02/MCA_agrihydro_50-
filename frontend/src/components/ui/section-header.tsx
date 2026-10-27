import {
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * A card heading built from props rather than four composed children.
 *
 * shadcn's CardHeader/CardTitle/CardDescription/CardAction give full control,
 * which matters when a heading is unusual. Every heading in this application is
 * the same shape — a title, a sentence explaining what the panel means, and at
 * most one action — so composing those four elements by hand at every call site
 * would only create opportunities to leave the description off.
 *
 * `divided` draws the rule between the heading and the body, which is what the
 * data-heavy panels here use.
 */
export function SectionHeader({
  title,
  description,
  action,
  divided = true,
  className,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  divided?: boolean;
  className?: string;
}) {
  return (
    <CardHeader className={cn(divided && "border-b", className)}>
      <CardTitle>{title}</CardTitle>
      {description && <CardDescription>{description}</CardDescription>}
      {action && <CardAction>{action}</CardAction>}
    </CardHeader>
  );
}
