import { cn } from "@/lib/cn";

interface SectionHeadingProps {
  id: string;
  title: string;
  /** Second line, rendered with the brand gradient. */
  highlight: string;
  description?: string;
  align?: "center" | "start";
  className?: string;
}

export function SectionHeading({
  id,
  title,
  highlight,
  description,
  align = "center",
  className,
}: SectionHeadingProps) {
  const isCentered = align === "center";

  return (
    <div
      className={cn(
        "text-center",
        !isCentered && "lg:text-left",
        className ?? "mb-12 sm:mb-16 lg:mb-20",
      )}
    >
      <h2 id={id} className="mb-4 text-4xl font-bold sm:mb-6 md:text-5xl lg:text-6xl">
        <span className="block bg-linear-to-b from-white to-gray-300 bg-clip-text text-transparent">
          {title}
        </span>
        <span className="block bg-linear-to-b from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          {highlight}
        </span>
      </h2>
      {description && (
        <p
          className={cn(
            "mx-auto max-w-2xl text-base text-gray-400 sm:text-lg",
            !isCentered && "lg:mx-0",
          )}
        >
          {description}
        </p>
      )}
    </div>
  );
}
