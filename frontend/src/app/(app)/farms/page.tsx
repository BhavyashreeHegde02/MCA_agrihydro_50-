import type { Metadata } from "next";

import { FarmsScreen } from "./farms-screen";

export const metadata: Metadata = { title: "Farms & fields" };

export default function FarmsPage() {
  return <FarmsScreen />;
}
