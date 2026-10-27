import type { Metadata } from "next";

import { WaterProductivityScreen } from "./water-productivity-screen";

export const metadata: Metadata = { title: "Crop per drop" };

export default function WaterProductivityPage() {
  return <WaterProductivityScreen />;
}
