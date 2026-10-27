import type { Metadata } from "next";
import { HelpMeChooseScreen } from "./help-me-choose-screen";

export const metadata: Metadata = {
  title: "Help Me Choose — Regional Crop & Water Explorer",
  description: "Evidence-based candidate crops using actual Karnataka soil nutrients, IMD rainfall normals, and transparent water feasibility trade-offs.",
};

export default function HelpMeChoosePage() {
  return <HelpMeChooseScreen />;
}
