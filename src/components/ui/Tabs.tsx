import { type KeyboardEvent, type ReactNode, useRef } from "react";

import { cn } from "@/lib/cn";
import { getTabIndexForKey } from "@/lib/keyboard";
import { tabId, tabPanelId } from "@/lib/tabs";

export interface TabItem {
  id: string;
  label: ReactNode;
}

const VARIANTS = {
  editor: {
    list: "mb-3 flex shrink-0 gap-1 overflow-x-auto sm:mb-4 sm:gap-2",
    tab: "rounded-t-lg border px-3 py-2 text-xs whitespace-nowrap backdrop-blur-sm transition-colors duration-200 sm:text-sm",
    selected: "border-blue-400/20 bg-blue-500/30 text-white",
    idle: "border-white/10 bg-white/5 text-gray-300 hover:bg-white/10",
  },
  segmented: {
    list: "grid auto-cols-fr grid-flow-col gap-1 rounded-xl border border-white/10 bg-white/5 p-1",
    tab: "flex items-center justify-center gap-2 rounded-lg px-2 py-2 text-xs font-medium transition-colors sm:px-3 sm:text-sm",
    selected: "bg-blue-500/20 text-white ring-1 ring-blue-400/40",
    idle: "text-gray-400 hover:bg-white/5 hover:text-white",
  },
} as const;

interface TabsProps {
  label: string;
  items: readonly TabItem[];
  activeIndex: number;
  onSelect: (index: number) => void;
  /** Prefix for tab/panel ids; pair the panel with `tabPanelId(idPrefix)`. */
  idPrefix: string;
  variant?: keyof typeof VARIANTS;
}

/**
 * WAI-ARIA tabs pattern: roving tabindex, ←/→ move between tabs (wrapping),
 * Home/End jump to the first/last tab.
 */
export function Tabs({
  label,
  items,
  activeIndex,
  onSelect,
  idPrefix,
  variant = "editor",
}: TabsProps) {
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const styles = VARIANTS[variant];

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const next = getTabIndexForKey(event.key, activeIndex, items.length);
    if (next === undefined) return;

    event.preventDefault();
    onSelect(next);
    tabRefs.current[next]?.focus();
  };

  return (
    <div role="tablist" aria-label={label} className={styles.list}>
      {items.map((item, index) => {
        const isSelected = index === activeIndex;
        return (
          <button
            key={item.id}
            ref={(node) => {
              tabRefs.current[index] = node;
            }}
            type="button"
            role="tab"
            id={tabId(idPrefix, item.id)}
            aria-selected={isSelected}
            aria-controls={tabPanelId(idPrefix)}
            tabIndex={isSelected ? 0 : -1}
            onKeyDown={handleKeyDown}
            onClick={() => {
              onSelect(index);
            }}
            className={cn(styles.tab, isSelected ? styles.selected : styles.idle)}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
