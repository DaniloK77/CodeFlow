import { cn } from "@/lib/cn";

const DOT_COLORS = ["bg-red-500", "bg-yellow-500", "bg-green-500"] as const;

/** macOS-style traffic lights for the faux editor windows. Decorative only. */
export function WindowControls() {
  return (
    <div aria-hidden="true" className="flex items-center gap-1 sm:gap-2">
      {DOT_COLORS.map((color) => (
        <span key={color} className={cn("size-2 rounded-full sm:size-3", color)} />
      ))}
    </div>
  );
}
