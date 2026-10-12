import { cn } from "@/lib/cn";
import { Link } from "@/lib/router";
import { HOME_PATH } from "@/lib/routes";

export function Logo({ className }: { className?: string }) {
  return (
    <Link to={HOME_PATH} className={cn("flex items-center gap-2 rounded-md", className)}>
      <img src="/logo.png" alt="" width={32} height={32} className="size-7 sm:size-8" />
      <span className="text-xl font-semibold sm:text-2xl">
        Code
        <span className="bg-linear-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Flow
        </span>
      </span>
    </Link>
  );
}
