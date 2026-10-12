/** Index access that fails the test loudly instead of returning `undefined`. */
export function nth<T>(items: readonly T[], index: number): T {
  const item = items.at(index);
  if (item === undefined) {
    throw new Error(`Expected an item at index ${index}, but there are only ${items.length}`);
  }
  return item;
}
