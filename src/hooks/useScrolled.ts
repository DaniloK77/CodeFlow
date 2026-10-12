import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void) {
  window.addEventListener("scroll", onChange, { passive: true });
  return () => {
    window.removeEventListener("scroll", onChange);
  };
}

/**
 * Whether the page is scrolled past `threshold` pixels. Components re-render only when
 * the boolean flips, not on every scroll event.
 */
export function useScrolled(threshold = 50): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.scrollY > threshold,
    () => false,
  );
}
