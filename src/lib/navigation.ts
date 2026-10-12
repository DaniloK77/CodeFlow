import { useSyncExternalStore } from "react";

// Navigation for a two-page app: the History API plus one subscription. Everything a router
// library would add (nested routes, loaders, params) would be unused weight here.

const NAVIGATION_EVENT = "codeflow:navigate";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  window.addEventListener(NAVIGATION_EVENT, onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(NAVIGATION_EVENT, onChange);
  };
}

/** The current path, without query or hash. Re-renders when the page navigates. */
export function usePathname(): string {
  return useSyncExternalStore(subscribe, () => window.location.pathname);
}

/** Moves to `to` ("/grade", "/#pricing") without reloading, then scrolls to its target. */
export function navigate(to: string): void {
  const url = new URL(to, window.location.href);
  const target = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (target !== current) window.history.pushState(null, "", target);
  window.dispatchEvent(new Event(NAVIGATION_EVENT));
  // Wait for the new page to render before looking for the hash target.
  requestAnimationFrame(() => {
    const anchor = url.hash ? document.getElementById(decodeURIComponent(url.hash.slice(1))) : null;
    if (anchor) anchor.scrollIntoView();
    else window.scrollTo(0, 0);
  });
}
