import { describe, expect, it } from "vitest";

import { cn } from "./cn";
import { formatBytes, formatPrice, getInitials } from "./format";
import { getTabIndexForKey } from "./keyboard";

describe("cn", () => {
  it("joins truthy class names and skips falsy ones", () => {
    expect(cn("a", false, undefined, "b", null, "")).toBe("a b");
  });
});

describe("formatPrice", () => {
  it.each([
    [0, "€0"],
    [20, "€20"],
    [19.99, "€19.99"],
    [1000.5, "€1,000.50"],
  ])("formats %d as %s", (amount, expected) => {
    expect(formatPrice(amount)).toBe(expected);
  });
});

describe("getInitials", () => {
  it.each([
    ["Sarah Chen", "SC"],
    ["marcus  de la rodriguez", "MD"],
    ["Cher", "C"],
    ["", ""],
  ])("turns %j into %j", (name, expected) => {
    expect(getInitials(name)).toBe(expected);
  });
});

describe("getTabIndexForKey", () => {
  it.each([
    ["ArrowRight", 0, 1],
    ["ArrowRight", 2, 0],
    ["ArrowLeft", 0, 2],
    ["Home", 2, 0],
    ["End", 0, 2],
    ["Enter", 1, undefined],
  ])("%s from tab %d of 3 → %s", (key, activeIndex, expected) => {
    expect(getTabIndexForKey(key, activeIndex, 3)).toBe(expected);
  });
});

describe("formatBytes", () => {
  it.each([
    [512, "512 B"],
    [1536, "1.5 KB"],
    [200 * 1024, "200 KB"],
    [5 * 1024 * 1024, "5.0 MB"],
  ])("formats %d as %s", (bytes, expected) => {
    expect(formatBytes(bytes)).toBe(expected);
  });
});
