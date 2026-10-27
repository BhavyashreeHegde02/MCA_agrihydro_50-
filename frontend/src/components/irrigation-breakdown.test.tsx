import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IrrigationBreakdown } from "./irrigation-breakdown";

/**
 * The figures below are a real backend response for the demo field, not
 * invented: ET0 4.65, Kc 1.20, ETc 5.63, effective rainfall 0.75, net 4.88,
 * efficiency 0.90, gross 5.42, 81,315 L over 1.5 ha.
 */
const REAL = {
  et0MmDay: 4.65,
  kc: 1.2,
  cwrMmDay: 5.63,
  effectiveRainfallMm: 0.75,
  netIrrigationMm: 4.88,
  grossIrrigationMm: 5.42,
  applicationEfficiency: 0.9,
  grossIrrigationLitres: 81315,
  areaHa: 1.5,
};

describe("IrrigationBreakdown", () => {
  it("shows the whole chain from reference to what to apply", () => {
    render(<IrrigationBreakdown inputs={REAL} />);
    for (const step of [
      "Reference evapotranspiration",
      "Crop coefficient",
      "Crop water requirement",
      "Usable rainfall",
      "Net irrigation requirement",
      "Application efficiency",
      "Gross irrigation — what to apply",
    ]) {
      expect(screen.getByText(step)).toBeInTheDocument();
    }
  });

  it("shows the arithmetic, not just the results", () => {
    // A farmer told only "apply 5.4 mm" cannot judge whether that is
    // reasonable. The working is the point of this component.
    render(<IrrigationBreakdown inputs={REAL} />);
    expect(screen.getByText(/ETc = ET₀ × Kc = 4\.65 × 1\.20/)).toBeInTheDocument();
    expect(screen.getByText(/5\.63 − 0\.75 = 4\.88/)).toBeInTheDocument();
    expect(screen.getByText(/4\.88 ÷ 0\.90 = 5\.42/)).toBeInTheDocument();
  });

  it("keeps gross above net, and says why", () => {
    render(<IrrigationBreakdown inputs={REAL} />);
    expect(screen.getByText("4.88 mm")).toBeInTheDocument();
    expect(screen.getByText("5.42 mm")).toBeInTheDocument();
    expect(
      screen.getByText(/This is why the next figure is larger/),
    ).toBeInTheDocument();
  });

  it("converts to litres with the conversion stated", () => {
    render(<IrrigationBreakdown inputs={REAL} />);
    expect(screen.getByText("81,315 L")).toBeInTheDocument();
    expect(
      screen.getByText(/5\.42 mm × 1\.5 ha × 10,000/),
    ).toBeInTheDocument();
  });

  it("is an ordered list, because the steps depend on each other", () => {
    render(<IrrigationBreakdown inputs={REAL} />);
    expect(screen.getByRole("list").tagName).toBe("OL");
  });

  it("omits the litre step when the backend did not supply a volume", () => {
    render(
      <IrrigationBreakdown
        inputs={{ ...REAL, grossIrrigationLitres: null }}
      />,
    );
    expect(screen.queryByText("In litres")).not.toBeInTheDocument();
    // The depth is still there; only the volume is absent.
    expect(screen.getByText("5.42 mm")).toBeInTheDocument();
  });

  it("drops the derivation when recalculating from a stored demand", () => {
    // The recalculation endpoint starts from a demand that already exists, so
    // showing ET0 and Kc there would mean inventing placeholder values.
    render(
      <IrrigationBreakdown
        inputs={{
          cwrMmDay: 5.63,
          effectiveRainfallMm: 0.75,
          netIrrigationMm: 4.88,
          grossIrrigationMm: 5.42,
          applicationEfficiency: 0.9,
        }}
      />,
    );
    expect(
      screen.queryByText("Reference evapotranspiration"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Crop coefficient")).not.toBeInTheDocument();
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();

    expect(screen.getByText("Crop water requirement")).toBeInTheDocument();
    expect(
      screen.getByText("ETc, as established by the stored prediction"),
    ).toBeInTheDocument();
  });

  it("credits expected rain against the net requirement", () => {
    render(
      <IrrigationBreakdown
        inputs={{ ...REAL, forecastRainfallMm: 12, netIrrigationMm: 2.87 }}
      />,
    );
    // 0.75 usable today plus 12 expected = 12.75 credited.
    expect(screen.getByText(/5\.63 − 12\.75 = 2\.87/)).toBeInTheDocument();
  });

  it("states the efficiency loss as a percentage a farmer can act on", () => {
    render(<IrrigationBreakdown inputs={REAL} />);
    expect(screen.getByText("90%")).toBeInTheDocument();
    expect(screen.getByText(/loses about 10%/)).toBeInTheDocument();
  });
});
