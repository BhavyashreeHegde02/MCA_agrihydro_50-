import type { Metadata } from "next";

import { WaterBudgetScreen } from "./water-budget-screen";

export const metadata: Metadata = { title: "Water budget" };

export default function WaterBudgetPage() {
  return <WaterBudgetScreen />;
}
