import { describe, expect, it } from "vitest";

import spec from "../../../openapi.json";
import {
  IRRIGATION_METHODS,
  MAX_AREA_HA,
  PASSWORD_MAX,
  PASSWORD_MIN,
  farmSchema,
  fieldSchema,
  irrigationRecordSchema,
  loginSchema,
  plantingSchema,
  profileSchema,
  registerSchema,
  soilSchema,
  weatherSchema,
} from "./schemas";

/** The slice of the OpenAPI document these tests read. */
interface SpecProperty {
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  minLength?: number;
  maxLength?: number;
  enum?: string[];
  anyOf?: SpecProperty[];
}
interface SpecShape {
  components: {
    schemas: Record<string, { properties?: Record<string, SpecProperty> }>;
  };
}

const doc = spec as unknown as SpecShape;

/** Read a numeric constraint straight out of the committed backend spec. */
function bound(
  schemaName: string,
  property: string,
  key: "minimum" | "maximum" | "exclusiveMinimum" | "minLength" | "maxLength",
): number | undefined {
  const prop = doc.components.schemas[schemaName]?.properties?.[property];
  if (!prop) throw new Error(`${schemaName}.${property} is not in openapi.json`);
  if (prop[key] !== undefined) return prop[key];
  // Optional fields are `anyOf: [{...}, {type: null}]`; the constraint sits on
  // the first branch.
  return prop.anyOf?.[0]?.[key];
}

/**
 * These tests are the reason the form bounds can be trusted. If someone widens
 * `total_area_ha` in the backend and regenerates openapi.json without touching
 * this app, the mirror below fails rather than the app silently rejecting input
 * the backend would have accepted.
 */
describe("form bounds mirror the backend spec", () => {
  it("farm area", () => {
    expect(bound("FarmCreate", "total_area_ha", "exclusiveMinimum")).toBe(0);
    expect(bound("FarmCreate", "total_area_ha", "maximum")).toBe(MAX_AREA_HA);
  });

  it("field area", () => {
    expect(bound("FieldCreate", "area_ha", "exclusiveMinimum")).toBe(0);
    expect(bound("FieldCreate", "area_ha", "maximum")).toBe(MAX_AREA_HA);
  });

  it("password length", () => {
    expect(bound("RegisterRequest", "password", "minLength")).toBe(PASSWORD_MIN);
    expect(bound("RegisterRequest", "password", "maxLength")).toBe(PASSWORD_MAX);
  });

  it("soil pH", () => {
    expect(bound("SoilDataCreate", "ph_level", "minimum")).toBe(0);
    expect(bound("SoilDataCreate", "ph_level", "maximum")).toBe(14);
  });

  it("irrigation depth", () => {
    expect(bound("IrrigationRecordCreate", "water_applied_mm", "minimum")).toBe(0);
    expect(bound("IrrigationRecordCreate", "water_applied_mm", "maximum")).toBe(1000);
  });

  it("weather ranges", () => {
    expect(bound("WeatherInputSchema", "humidity_pct", "maximum")).toBe(100);
    expect(bound("WeatherInputSchema", "temperature_max_c", "maximum")).toBe(65);
    expect(bound("WeatherInputSchema", "rainfall_mm", "maximum")).toBe(1500);
  });

  it("irrigation methods", () => {
    const prop =
      doc.components.schemas.FieldCreate.properties?.irrigation_method;
    const fromSpec = prop?.anyOf?.find((branch) => branch.enum)?.enum ?? [];
    expect(fromSpec.length).toBeGreaterThan(0);
    expect([...IRRIGATION_METHODS].sort()).toEqual([...fromSpec].sort());
  });
});

describe("loginSchema", () => {
  it("accepts a normal sign-in", () => {
    expect(
      loginSchema.safeParse({ email: "farmer@example.com", password: "secret" })
        .success,
    ).toBe(true);
  });

  it("rejects an empty form and names both fields", () => {
    const result = loginSchema.safeParse({ email: "", password: "" });
    expect(result.success).toBe(false);
    const paths = result.error!.issues.map((i) => i.path[0]);
    expect(paths).toContain("email");
    expect(paths).toContain("password");
  });

  it("rejects a malformed email", () => {
    expect(loginSchema.safeParse({ email: "farmer", password: "x" }).success).toBe(
      false,
    );
  });
});

describe("registerSchema", () => {
  const valid = {
    full_name: "A Farmer",
    email: "a@b.co",
    password: "Long-enough1!",
    confirm_password: "Long-enough1!",
    phone: "9876543210",
    state: "",
    district: "",
    taluk: "",
  };

  it("accepts a complete registration and nulls the blank optionals", () => {
    const result = registerSchema.safeParse(valid);
    expect(result.success).toBe(true);
    expect(result.data!.phone).toBe("9876543210");
    expect(result.data!.district).toBeNull();
  });

  it("rejects a password shorter than the backend accepts", () => {
    const result = registerSchema.safeParse({
      ...valid,
      password: "short",
      confirm_password: "short",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a password without all required character classes", () => {
    const result = registerSchema.safeParse({
      ...valid,
      password: "longenough1",
      confirm_password: "longenough1",
    });
    expect(result.success).toBe(false);
    expect(result.error!.issues.some((issue) => issue.path[0] === "password")).toBe(true);
  });

  it.each(["1234567890", "987654321", "98765 43210", "98765432101"])(
    "rejects invalid Indian mobile number %s",
    (phone) => {
      expect(registerSchema.safeParse({ ...valid, phone }).success).toBe(false);
    },
  );

  it("rejects a password longer than bcrypt can hash", () => {
    const long = "x".repeat(PASSWORD_MAX + 1);
    const result = registerSchema.safeParse({
      ...valid,
      password: long,
      confirm_password: long,
    });
    expect(result.success).toBe(false);
  });

  it("catches a mismatched confirmation and blames the confirm field", () => {
    const result = registerSchema.safeParse({
      ...valid,
      confirm_password: "somethingelse",
    });
    expect(result.success).toBe(false);
    expect(result.error!.issues[0].path).toEqual(["confirm_password"]);
  });
});

describe("farmSchema", () => {
  it("rejects zero area, which is the boundary the backend excludes", () => {
    const result = farmSchema.safeParse({ name: "F", total_area_ha: "0" });
    expect(result.success).toBe(false);
  });

  it("rejects a negative area", () => {
    expect(farmSchema.safeParse({ name: "F", total_area_ha: "-2" }).success).toBe(
      false,
    );
  });

  it("rejects text where a number belongs", () => {
    expect(
      farmSchema.safeParse({ name: "F", total_area_ha: "two hectares" }).success,
    ).toBe(false);
  });

  it("rejects an unnamed farm", () => {
    expect(farmSchema.safeParse({ name: "   ", total_area_ha: "1" }).success).toBe(
      false,
    );
  });

  it("rejects an impossible latitude", () => {
    const result = farmSchema.safeParse({
      name: "F",
      total_area_ha: "1",
      latitude: "120",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a farm with no coordinates at all", () => {
    const result = farmSchema.safeParse({
      name: "Green Acres",
      total_area_ha: "3.5",
      latitude: "",
      longitude: "",
    });
    expect(result.success).toBe(true);
    expect(result.data!.latitude).toBeNull();
    expect(result.data!.total_area_ha).toBe(3.5);
  });
});

describe("fieldSchema", () => {
  it("rejects an efficiency above 1, which is physically impossible", () => {
    const result = fieldSchema.safeParse({
      name: "Plot",
      area_ha: "1",
      irrigation_efficiency: "1.4",
      irrigation_method: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an irrigation method the backend does not know", () => {
    const result = fieldSchema.safeParse({
      name: "Plot",
      area_ha: "1",
      irrigation_method: "telepathy",
    });
    expect(result.success).toBe(false);
  });

  it("accepts every method the backend lists", () => {
    for (const method of IRRIGATION_METHODS) {
      const result = fieldSchema.safeParse({
        name: "Plot",
        area_ha: "1",
        irrigation_method: method,
      });
      expect(result.success, method).toBe(true);
    }
  });
});

describe("plantingSchema", () => {
  it("requires a crop and a sowing date", () => {
    expect(plantingSchema.safeParse({ crop_id: "", sowing_date: "" }).success).toBe(
      false,
    );
  });

  it("rejects a sowing date that is not a date", () => {
    expect(
      plantingSchema.safeParse({ crop_id: "3", sowing_date: "last monsoon" })
        .success,
    ).toBe(false);
  });

  it("accepts a valid planting", () => {
    const result = plantingSchema.safeParse({
      crop_id: "3",
      sowing_date: "2026-07-25",
      planting_area_ha: "1.2",
      notes: "",
    });
    expect(result.success).toBe(true);
    expect(result.data!.crop_id).toBe(3);
  });
});

describe("soilSchema", () => {
  it("rejects a pH outside 0-14", () => {
    expect(soilSchema.safeParse({ ph_level: "15", sample_date: "" }).success).toBe(
      false,
    );
  });

  it("rejects negative nutrients", () => {
    expect(
      soilSchema.safeParse({ nitrogen: "-5", sample_date: "" }).success,
    ).toBe(false);
  });

  it("rejects a reading with nothing in it", () => {
    const result = soilSchema.safeParse({
      sample_date: "",
      ph_level: "",
      nitrogen: "",
      phosphorus: "",
      potassium: "",
      organic_matter: "",
      texture: "",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a partial reading, because a farmer may know only pH", () => {
    const result = soilSchema.safeParse({
      sample_date: "",
      ph_level: "6.4",
      nitrogen: "",
      phosphorus: "",
      potassium: "",
      organic_matter: "",
      texture: "",
    });
    expect(result.success).toBe(true);
    expect(result.data!.ph_level).toBe(6.4);
    expect(result.data!.nitrogen).toBeNull();
  });

  it("does not turn an untouched box into a measured zero", () => {
    const result = soilSchema.safeParse({
      sample_date: "",
      ph_level: "7",
      nitrogen: "",
    });
    expect(result.data!.nitrogen).toBeNull();
    expect(result.data!.nitrogen).not.toBe(0);
  });
});

describe("weatherSchema", () => {
  const base = {
    temperature_mean_c: "27",
    temperature_min_c: "21",
    temperature_max_c: "33",
    humidity_pct: "64",
    rainfall_mm: "3",
    wind_speed_ms: "",
    solar_radiation_mj_m2: "",
  };

  it("accepts a coherent reading", () => {
    expect(weatherSchema.safeParse(base).success).toBe(true);
  });

  it("rejects humidity above 100", () => {
    expect(
      weatherSchema.safeParse({ ...base, humidity_pct: "140" }).success,
    ).toBe(false);
  });

  it("rejects a minimum above the maximum", () => {
    const result = weatherSchema.safeParse({
      ...base,
      temperature_min_c: "40",
      temperature_max_c: "30",
      temperature_mean_c: "35",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a mean outside its own min and max", () => {
    const result = weatherSchema.safeParse({ ...base, temperature_mean_c: "50" });
    expect(result.success).toBe(false);
  });

  it("requires the four measurements the backend requires", () => {
    const result = weatherSchema.safeParse({
      temperature_mean_c: "",
      temperature_min_c: "",
      temperature_max_c: "",
      humidity_pct: "",
    });
    expect(result.success).toBe(false);
    expect(result.error!.issues.length).toBeGreaterThanOrEqual(4);
  });
});

describe("irrigationRecordSchema", () => {
  it("rejects a duration beyond 48 hours", () => {
    const result = irrigationRecordSchema.safeParse({
      irrigation_date: "2026-09-25",
      water_applied_mm: "6",
      duration_hours: "60",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a normal application", () => {
    const result = irrigationRecordSchema.safeParse({
      irrigation_date: "2026-09-25",
      water_applied_mm: "6",
      duration_hours: "2",
      method: "drip",
      notes: "",
    });
    expect(result.success).toBe(true);
  });
});

describe("profileSchema", () => {
  it("rejects a one-character name", () => {
    expect(profileSchema.safeParse({ full_name: "A" }).success).toBe(false);
  });

  it("accepts a name with the optional fields blank", () => {
    const result = profileSchema.safeParse({
      full_name: "Some Farmer",
      phone: "",
      state: "",
      district: "",
      taluk: "",
      address: "",
    });
    expect(result.success).toBe(true);
    expect(result.data!.phone).toBeNull();
  });
});
