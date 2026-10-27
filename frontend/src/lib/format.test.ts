import { describe, expect, it } from "vitest";

import {
  LOCALE,
  demandTone,
  depthToLitres,
  formatArea,
  formatDate,
  formatDepth,
  formatLitres,
  formatNumber,
  formatPercent,
  humaniseSlug,
  priorityTone,
  todayIso,
  toneBadge,
} from "./format";

describe("formatNumber", () => {
  it("shows an em dash rather than NaN for missing values", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
    expect(formatNumber(Number.NaN)).toBe("—");
    expect(formatNumber(Number.POSITIVE_INFINITY)).toBe("—");
  });

  it("keeps a fixed number of decimals so columns line up", () => {
    expect(formatNumber(5, 2)).toBe("5.00");
    expect(formatNumber(5.126, 2)).toBe("5.13");
  });

  it("does not treat zero as missing", () => {
    // A measured zero and an absent reading mean different things in this
    // domain: no rain is a fact, no reading is not.
    expect(formatNumber(0, 2)).toBe("0.00");
  });
});

describe("formatDepth", () => {
  it("uses two decimals, the precision the backend reports", () => {
    expect(formatDepth(5.628)).toBe("5.63");
    expect(formatDepth(0)).toBe("0.00");
  });
});

describe("formatLitres", () => {
  it("rounds whole and groups, because these run to six figures", () => {
    expect(formatLitres(81315.2)).toBe("81,315");
  });

  it("reports a missing volume as missing", () => {
    expect(formatLitres(null)).toBe("—");
  });
});

describe("formatPercent", () => {
  it("renders an efficiency fraction as a percentage", () => {
    expect(formatPercent(0.9)).toBe("90%");
    expect(formatPercent(0.75)).toBe("75%");
  });

  it("does not invent a value when the fraction is absent", () => {
    expect(formatPercent(null)).toBe("—");
  });
});

describe("formatDate", () => {
  /*
   * The backend sends a bare `YYYY-MM-DD`. `new Date("2026-09-25")` parses that
   * as midnight UTC, which renders as the 24th anywhere west of Greenwich —
   * a prediction would appear to be for the wrong day. These tests exist to
   * keep that fix in place.
   */
  it("keeps the calendar day the backend sent", () => {
    expect(formatDate("2026-09-25")).toMatch(/25/);
    expect(formatDate("2026-01-01")).toMatch(/1/);
    expect(formatDate("2026-01-01")).toMatch(/2026/);
  });

  it("handles a full timestamp as well as a bare date", () => {
    expect(formatDate("2026-09-25T14:24:18")).toMatch(/25/);
  });

  it("reports a missing date rather than 'Invalid Date'", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
    expect(formatDate("")).toBe("—");
  });

  it("returns the input unchanged when it is not a date at all", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("todayIso", () => {
  it("produces a zero-padded local date the backend will accept", () => {
    expect(todayIso()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe("humaniseSlug", () => {
  it("turns a backend slug into a readable label", () => {
    expect(humaniseSlug("mid_season")).toBe("Mid season");
    expect(humaniseSlug("late-season")).toBe("Late season");
  });

  it("handles missing values", () => {
    expect(humaniseSlug(null)).toBe("—");
    expect(humaniseSlug("")).toBe("—");
  });
});

describe("depthToLitres", () => {
  it("applies the 1 mm over 1 ha = 10,000 L conversion", () => {
    expect(depthToLitres(1, 1)).toBe(10_000);
    // The figure the backend produced for the demo field, to the litre.
    expect(depthToLitres(5.4210, 1.5)).toBeCloseTo(81_315, 0);
  });
});

describe("tone mapping", () => {
  it("colours demand bands by the backend's own scale", () => {
    expect(demandTone("low")).toBe("ok");
    expect(demandTone("moderate")).toBe("warn");
    expect(demandTone("high")).toBe("danger");
    expect(demandTone("very high")).toBe("danger");
  });

  it("falls back to neutral for an unrecognised band", () => {
    expect(demandTone("unheard of")).toBe("neutral");
    expect(demandTone(null)).toBe("neutral");
  });

  it("colours advisory priorities", () => {
    expect(priorityTone("high")).toBe("danger");
    expect(priorityTone("medium")).toBe("warn");
    expect(priorityTone("low")).toBe("ok");
  });

  it("translates neutral to the Badge variant that exists", () => {
    // Badge has no "neutral"; shadcn calls it "secondary".
    expect(toneBadge("neutral")).toBe("secondary");
    expect(toneBadge("danger")).toBe("danger");
  });
});

describe("formatArea", () => {
  it("uses two decimals for hectares", () => {
    expect(formatArea(1.5)).toBe("1.50");
    expect(formatArea(null)).toBe("—");
  });
});


describe("locale is pinned, not inherited", () => {
  /*
   * These guard against a hydration mismatch, which is how this surfaced.
   *
   * `toLocaleString(undefined, ...)` resolves against the ambient locale.
   * Node renders "Sep 25, 2026"; a UK browser renders "25 Sept 2026". React
   * compares the server HTML with the client render, finds different text and
   * throws away the server tree. The output has to be identical on both sides,
   * which means the locale has to be chosen rather than inherited.
   */
  it("declares one locale for the whole application", () => {
    expect(LOCALE).toBe("en-IN");
  });

  it("formats a date identically regardless of the ambient locale", () => {
    const formatted = formatDate("2026-09-25");
    // Whatever the host locale is, this is what both sides must produce.
    expect(formatted).toBe(
      new Date(2026, 8, 25).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
    );
  });

  it("formats numbers identically regardless of the ambient locale", () => {
    expect(formatNumber(1234.5, 2)).toBe(
      (1234.5).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    );
  });

  it("formats volumes identically regardless of the ambient locale", () => {
    expect(formatLitres(81315)).toBe((81315).toLocaleString("en-IN"));
  });

  it("does not fall back to the ambient locale for any helper", () => {
    // A helper that resolved against the host would differ between a machine
    // set to en-US and one set to de-DE. Pinning makes the output stable.
    const samples = [
      formatDate("2026-01-05"),
      formatNumber(1_000_000, 0),
      formatLitres(1_000_000),
    ];
    expect(samples.every((value) => value !== "—")).toBe(true);
    expect(samples[1]).not.toContain(".");
  });
});
