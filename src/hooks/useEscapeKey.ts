import { useEffect, useEffectEvent } from "react";

/** Calls `onEscape` when Escape is pressed anywhere on the page, while `isActive` is true. */
export function useEscapeKey(onEscape: () => void, isActive = true): void {
  const handleEscape = useEffectEvent(onEscape);

  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") handleEscape();
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isActive]);
}
