type Listener = () => void;

export interface MatchMediaController {
  /** Flips every query's result and notifies subscribers, like a real viewport change. */
  setMatches: (matches: boolean) => void;
}

/** jsdom has no `matchMedia`; this installs a controllable stand-in. */
export function mockMatchMedia(initialMatches: boolean): MatchMediaController {
  let matches = initialMatches;
  const listeners = new Set<Listener>();

  window.matchMedia = (query: string) =>
    ({
      get matches() {
        return matches;
      },
      media: query,
      onchange: null,
      addEventListener: (_type: string, listener: Listener) => listeners.add(listener),
      removeEventListener: (_type: string, listener: Listener) => listeners.delete(listener),
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList;

  return {
    setMatches(next) {
      matches = next;
      listeners.forEach((listener) => {
        listener();
      });
    },
  };
}
