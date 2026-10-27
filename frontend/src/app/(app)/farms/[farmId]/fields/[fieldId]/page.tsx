import type { Metadata } from "next";

import { FieldDetailScreen } from "./field-detail-screen";

export const metadata: Metadata = { title: "Field" };

export default async function FieldPage(
  props: PageProps<"/farms/[farmId]/fields/[fieldId]">,
) {
  const { farmId, fieldId } = await props.params;
  return (
    <FieldDetailScreen farmId={Number(farmId)} fieldId={Number(fieldId)} />
  );
}
