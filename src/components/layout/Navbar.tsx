import { Menu, X } from "lucide-react";
import { type Ref, useRef, useState } from "react";

import { Logo } from "@/components/ui/Logo";
import { NAV_LINKS } from "@/content/site";
import { useEscapeKey } from "@/hooks/useEscapeKey";
import { useScrolled } from "@/hooks/useScrolled";
import { cn } from "@/lib/cn";
import { usePathname } from "@/lib/navigation";
import { Link } from "@/lib/router";
import { GRADE_PATH } from "@/lib/routes";
import { GradeLink } from "@/components/ui/GradeLink";

const MOBILE_MENU_ID = "mobile-menu";

export function Navbar() {
  const isScrolled = useScrolled(50);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  useEscapeKey(() => {
    closeMenu();
    toggleRef.current?.focus();
  }, isMenuOpen);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-colors duration-300",
        isScrolled || isMenuOpen
          ? "border-b border-slate-800 bg-slate-950/80 backdrop-blur-lg"
          : "bg-slate-950/20 backdrop-blur-sm",
      )}
    >
      <nav
        aria-label="Primary"
        className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:h-16 sm:px-6 md:h-20 lg:px-8"
      >
        <Logo />
        <div className="hidden items-center gap-6 md:flex lg:gap-8">
          <NavLinks className="flex items-center gap-6 lg:gap-8" />
          <GradeButton />
        </div>
        <MenuToggle
          ref={toggleRef}
          isOpen={isMenuOpen}
          onToggle={() => {
            setIsMenuOpen((open) => !open);
          }}
        />
      </nav>

      <div
        id={MOBILE_MENU_ID}
        hidden={!isMenuOpen}
        className="border-t border-slate-800 bg-slate-900/95 backdrop-blur-lg motion-safe:animate-fade-in-down md:hidden"
      >
        <div className="space-y-4 px-4 py-4 sm:py-6">
          <NavLinks
            className="space-y-3 sm:space-y-4"
            linkClassName="block"
            onNavigate={closeMenu}
          />
          <GradeButton onOpen={closeMenu} />
        </div>
      </div>
    </header>
  );
}

interface NavLinksProps {
  className: string;
  linkClassName?: string;
  onNavigate?: () => void;
}

function NavLinks({ className, linkClassName, onNavigate }: NavLinksProps) {
  return (
    <ul className={className}>
      {NAV_LINKS.map((link) => (
        <li key={link.href}>
          <Link
            to={link.href}
            onClick={onNavigate}
            className={cn(
              "text-sm text-gray-300 transition-colors hover:text-white lg:text-base",
              linkClassName,
            )}
          >
            {link.label}
          </Link>
        </li>
      ))}
    </ul>
  );
}

interface MenuToggleProps {
  ref: Ref<HTMLButtonElement>;
  isOpen: boolean;
  onToggle: () => void;
}

function MenuToggle({ ref, isOpen, onToggle }: MenuToggleProps) {
  const Icon = isOpen ? X : Menu;
  return (
    <button
      ref={ref}
      type="button"
      aria-expanded={isOpen}
      aria-controls={MOBILE_MENU_ID}
      aria-label={isOpen ? "Close menu" : "Open menu"}
      onClick={onToggle}
      className="rounded-md p-2 text-gray-300 hover:text-white md:hidden"
    >
      <Icon aria-hidden="true" className="size-5 sm:size-6" />
    </button>
  );
}

function GradeButton({ onOpen }: { onOpen?: () => void }) {
  // Already on the grading screen: the button would only point at where you are.
  if (usePathname() === GRADE_PATH) return null;
  return (
    <GradeLink
      {...(onOpen && { onNavigate: onOpen })}
      className="block w-full rounded-lg bg-linear-to-b from-blue-500 to-cyan-500 px-4 py-2 text-center text-sm font-semibold transition-opacity hover:opacity-90 md:w-auto"
    >
      Grade my solution
    </GradeLink>
  );
}
