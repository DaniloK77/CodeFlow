import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { mockMatchMedia } from "./matchMedia";
import { server } from "./server";

mockMatchMedia(false);
// jsdom doesn't lay anything out, so it has no scrolling either.
Element.prototype.scrollIntoView = () => undefined;

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  vi.restoreAllMocks();
  mockMatchMedia(false);
  window.localStorage.clear();
  window.history.replaceState(null, "", "/");
});

afterAll(() => {
  server.close();
});
