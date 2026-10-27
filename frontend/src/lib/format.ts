/**
 * Formatting for the quantities this application deals in.
 *
 * Water is reported in three different units that are easy to confuse:
 * millimetres per day (a depth over an area, which is how agronomy states crop
 * demand), litres (what a pump delivers), and hectares (area). A helper per
 * quantity keeps the precision consistent and keeps the unit attached.
 *
 * Nothing here rounds a value the backend computed before it is displayed in a
 * chart or a table — rounding is presentation only.
 */

const DEPTH_PRECISION = 2;

/**
 * One locale, used everywhere, chosen rather than inherited.
 *
 * `toLocaleString(undefined, ...)` resolves against whatever ambient locale the
 * runtime has. On the server that is Node's, in the browser it is the user's,
 * and the two disagree: Node renders "Sep 25, 2026" where a UK browser renders
 * "25 Sept 2026". React sees different text on each side and throws a
 * hydration mismatch, discarding the server-rendered tree.
 *
 * en-IN is the deliberate choice, not just a deterministic one: this is an
 * Indian agricultural application, and en-IN also groups large numbers in the
 * lakh/crore style its readers expect.
 */
export const LOCALE = "en-IN";

export function formatNumber(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return value.toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** A water depth, e.g. 6.62 mm/day. */
export function formatDepth(value: number | null | undefined): string {
  return formatNumber(value, DEPTH_PRECISION);
}

/**
 * A volume in litres.
 *
 * Irrigation volumes reach the hundreds of thousands for even a small field, so
 * these are shown whole and grouped: 78,252 rather than 78252.00.
 */
export function formatLitres(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return Math.round(value).toLocaleString(LOCALE);
}

export function formatArea(value: number | null | undefined): string {
  return formatNumber(value, 2);
}

/** A fraction shown as a percentage, e.g. 0.9 -> "90%". */
export function formatPercent(
  fraction: number | null | undefined,
  digits = 0,
): string {
  if (fraction === null || fraction === undefined || !Number.isFinite(fraction)) {
    return "—";
  }
  return `${(fraction * 100).toFixed(digits)}%`;
}

/**
 * An ISO date as a farmer would read it.
 *
 * The backend sends plain `YYYY-MM-DD` with no timezone. Passing that to
 * `new Date()` parses it as midnight UTC, which displays as the previous day
 * anywhere west of Greenwich. Splitting the parts avoids that entirely.
 */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [datePart] = iso.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  if (!year || !month || !day) return iso;
  return new Date(year, month - 1, day).toLocaleDateString(LOCALE, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Today in the `YYYY-MM-DD` form the backend expects, in local time. */
export function todayIso(): string {
  const now = new Date();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** `mid_season` -> `Mid season`. Growth stages arrive as slugs. */
export function humaniseSlug(slug: string | null | undefined): string {
  if (!slug) return "—";
  const spaced = slug.replace(/[_-]+/g, " ").trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/**
 * Convert a depth in millimetres over an area in hectares to litres.
 *
 * 1 mm over 1 ha is 10 m³, which is 10 000 L. The backend computes this too,
 * and the smoke test asserts the two agree; this exists for the cases where the
 * interface needs the figure before a prediction has been stored.
 */
export function depthToLitres(depthMm: number, areaHa: number): number {
  return depthMm * areaHa * 10_000;
}

export type Tone = "neutral" | "ok" | "warn" | "danger";

/**
 * Translate a semantic tone into the Badge variant that renders it.
 *
 * Badge has no "neutral"; shadcn calls that "secondary". Keeping the domain
 * vocabulary separate from the component vocabulary means the thresholds below
 * read as agronomy rather than as styling.
 */
export function toneBadge(
  tone: Tone,
): "secondary" | "ok" | "warn" | "danger" {
  return tone === "neutral" ? "secondary" : tone;
}

/**
 * Colour for a crop-demand band.
 *
 * The bands are the backend's own (`advisory_service.water_need_status`):
 * low, moderate, high, very high, split at 2, 5 and 8 mm/day. The backend is
 * explicit that these are a presentation choice rather than a physical
 * boundary, and the interface repeats that where it shows them.
 */
export function demandTone(band: string | null | undefined): Tone {
  switch (band) {
    case "low":
      return "ok";
    case "moderate":
      return "warn";
    case "high":
    case "very high":
      return "danger";
    default:
      return "neutral";
  }
}

/** Colour for an advisory priority: the backend emits low, medium or high. */
export function priorityTone(priority: string | null | undefined): Tone {
  switch (priority) {
    case "high":
      return "danger";
    case "medium":
      return "warn";
    case "low":
      return "ok";
    default:
      return "neutral";
  }
}
