import { fireEvent, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useEscapeKey } from "./useEscapeKey";

describe("useEscapeKey", () => {
  it("calls the latest handler on Escape while active", () => {
    const first = vi.fn();
    const latest = vi.fn();
    const { rerender } = renderHook(
      ({ handler }) => {
        useEscapeKey(handler);
      },
      { initialProps: { handler: first } },
    );

    rerender({ handler: latest });
    fireEvent.keyDown(document, { key: "Escape" });

    expect(first).not.toHaveBeenCalled();
    expect(latest).toHaveBeenCalledOnce();
  });

  it("ignores other keys and does nothing while inactive", () => {
    const handler = vi.fn();
    const { rerender } = renderHook(
      ({ isActive }) => {
        useEscapeKey(handler, isActive);
      },
      { initialProps: { isActive: true } },
    );

    fireEvent.keyDown(document, { key: "Enter" });
    rerender({ isActive: false });
    fireEvent.keyDown(document, { key: "Escape" });

    expect(handler).not.toHaveBeenCalled();
  });
});
