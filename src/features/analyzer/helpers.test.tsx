import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LIMITS, SOURCE_EXTENSIONS } from "./constants";
import { languageForPath } from "@/lib/languages";

import { RichMessage } from "./report/RichMessage";
import { describeRule } from "./ruleDocs";
import { validateFile } from "./validation";

const rules = { maxBytes: LIMITS.sourceFileBytes, extensions: SOURCE_EXTENSIONS };

function fileOfSize(name: string, bytes: number): File {
  return new File([new Uint8Array(bytes)], name);
}

describe("validateFile", () => {
  it("accepts supported files within the limit", () => {
    expect(validateFile(fileOfSize("Button.TSX", 10), rules)).toBeNull();
  });

  it.each([
    ["notes.txt", 10, "isn't supported"],
    ["empty.ts", 0, "is empty"],
    ["huge.ts", LIMITS.sourceFileBytes + 1, "the free plan accepts up to 200 KB"],
  ])("rejects %s", (name, bytes, reason) => {
    expect(validateFile(fileOfSize(name, bytes), rules)).toContain(reason);
  });
});

describe("languageForPath", () => {
  it.each([
    ["a.py", "python"],
    ["a.tsx", "tsx"],
    ["a.TS", "typescript"],
    ["a.jsx", "jsx"],
    ["a.mjs", "javascript"],
  ])("%s → %s", (path, language) => {
    expect(languageForPath(path)).toBe(language);
  });
});

describe("describeRule", () => {
  it("explains known rules and falls back to the rule id", () => {
    expect(describeRule("index-as-key").title).toBe("Index used as key");
    expect(describeRule("brand-new-rule")).toEqual({
      title: "brand-new-rule",
      why: "",
      dimension: null,
    });
  });
});

describe("RichMessage", () => {
  it("renders backticked identifiers as code", () => {
    const { container } = render(<RichMessage text="`var` is function-scoped; use `const`" />);

    expect([...container.querySelectorAll("code")].map((node) => node.textContent)).toEqual([
      "var",
      "const",
    ]);
    expect(screen.getByText(/is function-scoped/)).toBeInTheDocument();
  });
});
