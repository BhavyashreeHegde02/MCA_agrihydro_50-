import type { Metadata } from "next";
import { Suspense } from "react";

import { LoadingState } from "@/components/ui/states";

import { PredictScreen } from "./predict-screen";

export const metadata: Metadata = { title: "Predict demand" };

export default function PredictPage() {
  // useSearchParams needs a Suspense boundary; without one the whole route is
  // forced out of static rendering.
  return (
    <Suspense fallback={<LoadingState />}>
      <PredictScreen />
    </Suspense>
  );
}
