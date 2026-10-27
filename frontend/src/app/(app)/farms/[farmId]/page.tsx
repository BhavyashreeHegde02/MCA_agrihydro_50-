import type { Metadata } from "next";

import { FarmDetailScreen } from "./farm-detail-screen";

export const metadata: Metadata = { title: "Farm" };

export default async function FarmPage(props: PageProps<"/farms/[farmId]">) {
  // params is a promise in Next 16; reading it synchronously no longer works.
  const { farmId } = await props.params;
  return <FarmDetailScreen farmId={Number(farmId)} />;
}
