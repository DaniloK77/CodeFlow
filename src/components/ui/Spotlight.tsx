import { useEffect, useRef } from "react";

import { useMediaQuery } from "@/hooks/useMediaQuery";

const GRADIENT =
  "radial-gradient(600px circle at var(--spotlight-x, 50%) var(--spotlight-y, 30%), rgb(59 130 246 / 0.15), transparent 40%)";

/**
 * Cursor-following glow. The pointer position is written straight to CSS custom properties
 * once per animation frame, so moving the mouse never triggers a React re-render.
 * Skipped on touch devices and for users who prefer reduced motion.
 */
export function Spotlight() {
  const ref = useRef<HTMLDivElement>(null);
  const isEnabled = useMediaQuery("(hover: hover) and (prefers-reduced-motion: no-preference)");

  useEffect(() => {
    const element = ref.current;
    if (!isEnabled || !element) return;

    let frame = 0;
    const handlePointerMove = (event: PointerEvent) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const bounds = element.getBoundingClientRect();
        element.style.setProperty("--spotlight-x", `${event.clientX - bounds.left}px`);
        element.style.setProperty("--spotlight-y", `${event.clientY - bounds.top}px`);
      });
    };

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", handlePointerMove);
    };
  }, [isEnabled]);

  return (
    <div
      ref={ref}
      aria-hidden="true"
      data-testid="spotlight"
      className="pointer-events-none absolute inset-0 opacity-30"
      style={{ background: GRADIENT }}
    />
  );
}
