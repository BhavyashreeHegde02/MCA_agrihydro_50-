import { AppShell } from "@/components/layout/nav";
import { rscGet } from "@/lib/api/rsc";
import type { UserOut } from "@/lib/api/types";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  // Resolved on the server so the shell renders with the farmer's name already
  // in place, rather than flashing a placeholder that then swaps.
  const user = await rscGet<UserOut>("/api/v1/auth/me");

  return <AppShell farmerName={user.full_name}>{children}</AppShell>;
}
