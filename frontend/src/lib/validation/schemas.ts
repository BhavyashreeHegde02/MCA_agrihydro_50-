/**
 * Form validation, mirroring the backend's own constraints.
 *
 * Every bound here is taken from the FastAPI service's OpenAPI document, not
 * invented. `openapi.json` is the reference: `total_area_ha` is
 * `exclusiveMinimum: 0, maximum: 100000`, so that is what this file says.
 *
 * This is a convenience, not a security boundary. The backend validates every
 * request again regardless of what the browser did, and
 * `src/lib/validation/schemas.test.ts` checks these bounds against the
 * committed spec so the two cannot drift apart silently.
 *
 * Messages are written for a farmer reading them on a phone: they say what to
 * do, not which constraint failed.
 */

import { z } from "zod";

/**
 * An optional text input.
 *
 * A browser sends "" for an untouched box, but the backend wants null for
 * absent. Without this every optional string would arrive as an empty string
 * and be stored as one.
 *
 * `undefined` is accepted as well as "": a caller that simply omits the key —
 * a partial update, or a form that does not render the input at all — means
 * the same thing as a farmer who left the box alone.
 */
const optionalText = (max?: number) =>
  z
    .union([z.string(), z.null()])
    .transform((value) => {
      const text = typeof value === "string" ? value.trim() : "";
      return text === "" ? null : text;
    })
    .superRefine((value, ctx) => {
      if (value === null || max === undefined) return;
      if (value.length > max) {
        ctx.addIssue({
          code: "custom",
          message: `Use at most ${max} characters.`,
        });
      }
    })
    // Zod 4 decides a key is required from the schema itself, not from whether
    // its union happens to admit `undefined`. `.default(null)` is what makes an
    // absent key both accepted and normalised to null in the output.
    .default(null);

/**
 * An optional number typed into a text input.
 *
 * `z.coerce.number()` turns "" into 0, which would silently record a pH of
 * zero for a farmer who left the box alone. Empty is mapped to null first.
 */
const optionalNumber = (rules: (schema: z.ZodNumber) => z.ZodNumber) =>
  z
    .union([z.string(), z.number(), z.null()])
    .transform((value) =>
      value === "" || value === null ? null : Number(value),
    )
    .refine((value) => value === null || Number.isFinite(value), {
      message: "Enter a number.",
    })
    .superRefine((value, ctx) => {
      if (value === null) return;
      const result = rules(z.number()).safeParse(value);
      if (!result.success) {
        for (const issue of result.error.issues) {
          ctx.addIssue({ code: "custom", message: issue.message });
        }
      }
    })
    // See the note on optionalText: this is what makes the key optional.
    .default(null);

const requiredNumber = (rules: (schema: z.ZodNumber) => z.ZodNumber) =>
  z
    .union([z.string(), z.number()])
    .refine((value) => value !== "" && value !== null, {
      message: "This is required.",
    })
    .transform((value) => Number(value))
    .refine(Number.isFinite, { message: "Enter a number." })
    .superRefine((value, ctx) => {
      const result = rules(z.number()).safeParse(value);
      if (!result.success) {
        for (const issue of result.error.issues) {
          ctx.addIssue({ code: "custom", message: issue.message });
        }
      }
    });

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------

/** bcrypt truncates at 72 bytes, and the backend rejects anything longer. */
export const PASSWORD_MAX = 72;
export const PASSWORD_MIN = 8;

export const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});
export type LoginValues = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(2, "Enter your name.")
      .max(255, "That name is too long."),
    email: z.email("Enter a valid email address."),
    password: z
      .string()
      .min(
        PASSWORD_MIN,
        "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character.",
      )
      .max(PASSWORD_MAX, `Use at most ${PASSWORD_MAX} characters.`)
      .regex(
        /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z\d]).+$/,
        "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character.",
      ),
    confirm_password: z.string(),
    phone: z.string().trim().superRefine((value, ctx) => {
      if (!/^\d{10}$/.test(value)) {
        ctx.addIssue({
          code: "custom",
          message: "Mobile number must contain exactly 10 digits.",
        });
      } else if (!/^[6-9]\d{9}$/.test(value)) {
        ctx.addIssue({
          code: "custom",
          message: "Mobile number must start with 6, 7, 8 or 9.",
        });
      }
    }),
    state: optionalText(),
    district: optionalText(),
    taluk: optionalText(),
  })
  .refine((values) => values.password === values.confirm_password, {
    message: "The two passwords do not match.",
    path: ["confirm_password"],
  });
export type RegisterValues = z.infer<typeof registerSchema>;

// ---------------------------------------------------------------------------
// Farmer profile
// ---------------------------------------------------------------------------

export const profileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(2, "Enter your name.")
    .max(255, "That name is too long."),
  phone: optionalText(32),
  state: optionalText(),
  district: optionalText(),
  taluk: optionalText(),
  address: optionalText(),
});
export type ProfileValues = z.infer<typeof profileSchema>;

// ---------------------------------------------------------------------------
// Farm
// ---------------------------------------------------------------------------

export const MAX_AREA_HA = 100_000;

export const farmSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Give the farm a name.")
    .max(255, "That name is too long."),
  total_area_ha: requiredNumber((n) =>
    n
      .gt(0, "Area must be greater than zero.")
      .max(MAX_AREA_HA, `Area must be at most ${MAX_AREA_HA} hectares.`),
  ),
  state: optionalText(),
  district: optionalText(),
  taluk: optionalText(),
  latitude: optionalNumber((n) =>
    n.min(-90, "Latitude runs from -90 to 90.").max(90, "Latitude runs from -90 to 90."),
  ),
  longitude: optionalNumber((n) =>
    n
      .min(-180, "Longitude runs from -180 to 180.")
      .max(180, "Longitude runs from -180 to 180."),
  ),
});
export type FarmValues = z.infer<typeof farmSchema>;

// ---------------------------------------------------------------------------
// Field
// ---------------------------------------------------------------------------

export const IRRIGATION_METHODS = [
  "drip",
  "sprinkler",
  "furrow",
  "flood",
  "basin",
  "surface",
] as const;
export type IrrigationMethod = (typeof IRRIGATION_METHODS)[number];

export const fieldSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Give the field a name.")
    .max(255, "That name is too long."),
  area_ha: requiredNumber((n) =>
    n
      .gt(0, "Area must be greater than zero.")
      .max(MAX_AREA_HA, `Area must be at most ${MAX_AREA_HA} hectares.`),
  ),
  soil_type: optionalText(64),
  irrigation_method: z
    .union([z.enum(IRRIGATION_METHODS), z.literal(""), z.null()])
    .transform((value) => (value === "" ? null : value))
    .default(null),
  irrigation_efficiency: optionalNumber((n) =>
    n
      .gt(0, "Efficiency must be greater than 0.")
      .max(1, "Efficiency is a fraction between 0 and 1."),
  ),
});
export type FieldValues = z.infer<typeof fieldSchema>;

// ---------------------------------------------------------------------------
// Planting
// ---------------------------------------------------------------------------

export const plantingSchema = z.object({
  crop_id: requiredNumber((n) => n.int("Choose a crop.").positive("Choose a crop.")),
  sowing_date: z.iso.date("Enter a valid date."),
  planting_area_ha: optionalNumber((n) => n.gt(0, "Area must be greater than zero.")),
  notes: optionalText(),
});
export type PlantingValues = z.infer<typeof plantingSchema>;

// ---------------------------------------------------------------------------
// Soil
// ---------------------------------------------------------------------------

export const soilSchema = z
  .object({
    sample_date: z
      .union([z.iso.date("Enter a valid date."), z.literal(""), z.null()])
      .transform((value) => (value === "" ? null : value))
      .default(null),
    ph_level: optionalNumber((n) =>
      n.min(0, "pH runs from 0 to 14.").max(14, "pH runs from 0 to 14."),
    ),
    nitrogen: optionalNumber((n) => n.min(0, "Cannot be negative.")),
    phosphorus: optionalNumber((n) => n.min(0, "Cannot be negative.")),
    potassium: optionalNumber((n) => n.min(0, "Cannot be negative.")),
    organic_matter: optionalNumber((n) =>
      n.min(0, "Cannot be negative.").max(100, "This is a percentage, so at most 100."),
    ),
    texture: optionalText(64),
  })
  .refine(
    (values) =>
      // Every field is individually optional, but a reading with nothing in it
      // is not a reading. The backend accepts it; storing it helps nobody.
      Object.entries(values).some(
        ([key, value]) => key !== "sample_date" && value !== null,
      ),
    { message: "Enter at least one soil measurement.", path: ["ph_level"] },
  );
export type SoilValues = z.infer<typeof soilSchema>;

// ---------------------------------------------------------------------------
// Weather entered by hand
// ---------------------------------------------------------------------------

export const weatherSchema = z
  .object({
    temperature_mean_c: requiredNumber((n) =>
      n.min(-50, "That is outside any recorded range.").max(60, "That is outside any recorded range."),
    ),
    temperature_min_c: requiredNumber((n) =>
      n.min(-60, "That is outside any recorded range.").max(55, "That is outside any recorded range."),
    ),
    temperature_max_c: requiredNumber((n) =>
      n.min(-40, "That is outside any recorded range.").max(65, "That is outside any recorded range."),
    ),
    humidity_pct: requiredNumber((n) =>
      n.min(0, "Humidity runs from 0 to 100.").max(100, "Humidity runs from 0 to 100."),
    ),
    rainfall_mm: optionalNumber((n) =>
      n.min(0, "Cannot be negative.").max(1500, "That is more rain than any recorded day."),
    ),
    wind_speed_ms: optionalNumber((n) => n.min(0, "Cannot be negative.").max(60, "That is a cyclone.")),
    solar_radiation_mj_m2: optionalNumber((n) =>
      n.min(0, "Cannot be negative.").max(45, "That exceeds the solar constant at the surface."),
    ),
  })
  .refine((v) => v.temperature_min_c <= v.temperature_max_c, {
    message: "The minimum cannot be above the maximum.",
    path: ["temperature_min_c"],
  })
  .refine(
    (v) =>
      v.temperature_mean_c >= v.temperature_min_c &&
      v.temperature_mean_c <= v.temperature_max_c,
    {
      message: "The mean must sit between the minimum and the maximum.",
      path: ["temperature_mean_c"],
    },
  );
export type WeatherValues = z.infer<typeof weatherSchema>;

// ---------------------------------------------------------------------------
// Irrigation
// ---------------------------------------------------------------------------

export const irrigationRecordSchema = z.object({
  irrigation_date: z.iso.date("Enter a valid date."),
  water_applied_mm: requiredNumber((n) =>
    n.min(0, "Cannot be negative.").max(1000, "That is more than any single application."),
  ),
  method: optionalText(64),
  duration_hours: optionalNumber((n) =>
    n.min(0, "Cannot be negative.").max(48, "A single application cannot run beyond 48 hours."),
  ),
  application_efficiency: optionalNumber((n) =>
    n.gt(0, "Efficiency must be greater than 0.").max(1, "Efficiency is a fraction between 0 and 1."),
  ),
  notes: optionalText(),
});
export type IrrigationRecordValues = z.infer<typeof irrigationRecordSchema>;

export const irrigationCalcSchema = z.object({
  irrigation_efficiency: optionalNumber((n) =>
    n.gt(0, "Efficiency must be greater than 0.").max(1, "Efficiency is a fraction between 0 and 1."),
  ),
  forecast_rainfall_mm: optionalNumber((n) =>
    n.min(0, "Cannot be negative.").max(1500, "That is more rain than any recorded day."),
  ),
  area_ha: optionalNumber((n) => n.gt(0, "Area must be greater than zero.")),
});
export type IrrigationCalcValues = z.infer<typeof irrigationCalcSchema>;
