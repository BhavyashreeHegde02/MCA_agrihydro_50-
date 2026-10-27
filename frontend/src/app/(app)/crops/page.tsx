import type { Metadata } from "next";

import { CropsScreen } from "./crops-screen";

export const metadata: Metadata = { title: "Crop reference" };

export default function CropsPage() {
  return <CropsScreen />;
}
