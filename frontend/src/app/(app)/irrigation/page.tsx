import type { Metadata } from "next";

import { IrrigationScreen } from "./irrigation-screen";

export const metadata: Metadata = { title: "Irrigation" };

export default function IrrigationPage() {
  return <IrrigationScreen />;
}
