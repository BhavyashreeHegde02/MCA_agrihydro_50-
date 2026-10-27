import type { Metadata } from "next";

import { WeatherScreen } from "./weather-screen";

export const metadata: Metadata = { title: "Weather" };

export default function WeatherPage() {
  return <WeatherScreen />;
}
