import type { Metadata } from "next";

import { HistoryScreen } from "./history-screen";

export const metadata: Metadata = { title: "Prediction history" };

export default function PredictionsPage() {
  return <HistoryScreen />;
}
