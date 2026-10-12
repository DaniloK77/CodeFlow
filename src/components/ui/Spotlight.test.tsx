import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { mockMatchMedia } from "@/test/matchMedia";

import { Spotlight } from "./Spotlight";

function runAnimationFramesImmediately() {
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
    callback(0);
    return 1;
  });
}

describe("Spotlight", () => {
  it("follows the pointer through CSS variables when motion is allowed", () => {
    mockMatchMedia(true);
    runAnimationFramesImmediately();
    render(<Spotlight />);

    fireEvent.pointerMove(window, { clientX: 120, clientY: 80 });

    const spotlight = screen.getByTestId("spotlight");
    expect(spotlight.style.getPropertyValue("--spotlight-x")).toBe("120px");
    expect(spotlight.style.getPropertyValue("--spotlight-y")).toBe("80px");
  });

  it("stays still for reduced-motion and touch users", () => {
    mockMatchMedia(false);
    runAnimationFramesImmediately();
    render(<Spotlight />);

    fireEvent.pointerMove(window, { clientX: 120, clientY: 80 });

    expect(screen.getByTestId("spotlight").style.getPropertyValue("--spotlight-x")).toBe("");
  });

  it("stops tracking when the media query stops matching", () => {
    const media = mockMatchMedia(true);
    runAnimationFramesImmediately();
    render(<Spotlight />);

    act(() => {
      media.setMatches(false);
    });
    fireEvent.pointerMove(window, { clientX: 10, clientY: 10 });

    expect(screen.getByTestId("spotlight").style.getPropertyValue("--spotlight-x")).toBe("");
  });
});
