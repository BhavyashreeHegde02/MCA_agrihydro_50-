import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Without this, a component mounted by one test is still in the document when
// the next one runs, and queries start matching the wrong element.
afterEach(() => {
  cleanup();
});
