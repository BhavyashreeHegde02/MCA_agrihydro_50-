import type { Metadata } from "next";

import { PredictionDetailScreen } from "./prediction-detail-screen";

export const metadata: Metadata = { title: "Prediction" };

export default async function PredictionPage(
  props: PageProps<"/predictions/[predictionId]">,
) {
  const { predictionId } = await props.params;
  return <PredictionDetailScreen predictionId={Number(predictionId)} />;
}
