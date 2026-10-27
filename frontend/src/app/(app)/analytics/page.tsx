import type { Metadata } from "next";

import { AnalyticsScreen } from "./analytics-screen";

export const metadata: Metadata = { title: "Water analytics" };

export default function AnalyticsPage() {
  return <AnalyticsScreen />;
}
