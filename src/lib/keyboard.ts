/**
 * Roving-focus navigation for a horizontal tab list: the index that should receive focus
 * after `key` is pressed, or `undefined` if the key isn't a navigation key.
 */
export function getTabIndexForKey(
  key: string,
  activeIndex: number,
  count: number,
): number | undefined {
  const targets: Partial<Record<string, number>> = {
    ArrowRight: activeIndex + 1,
    ArrowLeft: activeIndex - 1,
    Home: 0,
    End: count - 1,
  };
  const target = targets[key];
  return target === undefined ? undefined : (target + count) % count;
}
