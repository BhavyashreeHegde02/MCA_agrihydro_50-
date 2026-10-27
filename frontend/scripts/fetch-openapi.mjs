/**
 * Refresh openapi.json from a running backend.
 *
 *   npm run api:spec        # defaults to http://127.0.0.1:8000
 *   npm run api:spec -- http://localhost:8011
 *
 * The spec is committed so `npm run build` works without the backend up. Run
 * this, then `npm run api:types`, whenever a backend endpoint or schema
 * changes; `npm run typecheck` will then fail loudly anywhere the frontend
 * still assumes the old shape, which is the point.
 */

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const base = (process.argv[2] ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
const url = `${base}/openapi.json`;
const target = join(dirname(fileURLToPath(import.meta.url)), "..", "openapi.json");

try {
  const response = await fetch(url, { signal: AbortSignal.timeout(15_000) });
  if (!response.ok) {
    console.error(`${url} returned ${response.status}`);
    process.exit(1);
  }
  const spec = await response.json();
  const pathCount = Object.keys(spec.paths ?? {}).length;
  const schemaCount = Object.keys(spec.components?.schemas ?? {}).length;
  writeFileSync(target, `${JSON.stringify(spec, null, 1)}\n`, "utf-8");
  console.log(`wrote openapi.json — ${pathCount} paths, ${schemaCount} schemas`);
  console.log("now run: npm run api:types");
} catch (error) {
  console.error(`could not fetch ${url}: ${error.message}`);
  console.error("Start the backend first:");
  console.error("  python -m uvicorn app.main:app --app-dir backend");
  process.exit(1);
}
