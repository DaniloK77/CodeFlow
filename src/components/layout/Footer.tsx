import { Logo } from "@/components/ui/Logo";
import { FOOTER_LINK_GROUPS, LEGAL_LINKS, SOCIAL_LINKS } from "@/content/footer";
import { SITE_NAME, SITE_TAGLINE } from "@/content/site";
import { Link } from "@/lib/router";

const LINK_CLASSES = "text-gray-400 transition-colors duration-200 hover:text-white";

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950/60 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8 lg:py-16">
        <div className="mb-10 grid gap-10 lg:grid-cols-6 lg:gap-12">
          <Brand />
          <SiteMap />
        </div>
        <BottomBar />
      </div>
    </footer>
  );
}

function Brand() {
  return (
    <div className="text-center sm:text-left lg:col-span-2">
      <Logo className="justify-center sm:justify-start" />
      <p className="mx-auto mt-4 mb-6 max-w-xs text-sm leading-relaxed text-gray-400 sm:mx-0 sm:text-base">
        {SITE_TAGLINE}
      </p>
      <ul aria-label="Social media" className="flex justify-center gap-4 sm:justify-start">
        {SOCIAL_LINKS.map(({ label, href, icon: Icon }) => {
          return (
            <li key={label}>
              <a
                href={href}
                aria-label={label}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg bg-slate-800 p-2.5 transition-all duration-200 hover:scale-110 hover:bg-slate-700"
              >
                <Icon aria-hidden="true" className="size-5 text-gray-300" />
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function SiteMap() {
  return (
    <nav aria-label="Footer" className="grid grid-cols-2 gap-8 lg:col-span-4">
      {FOOTER_LINK_GROUPS.map((group) => (
        <div key={group.title}>
          <h2 className="mb-4 text-sm font-semibold text-white sm:text-base">{group.title}</h2>
          <ul className="space-y-2.5 text-sm">
            {group.links.map((link) => (
              <li key={link.label}>
                <FooterLink href={link.href}>{link.label}</FooterLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function BottomBar() {
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-800 pt-6 sm:flex-row">
      <p className="text-center text-xs text-gray-400 sm:text-left sm:text-sm">
        © {new Date().getFullYear()} {SITE_NAME}. All rights reserved.
      </p>
      <ul className="flex items-center gap-5 text-xs sm:text-sm">
        {LEGAL_LINKS.map((link) => (
          <li key={link.label}>
            <FooterLink href={link.href}>{link.label}</FooterLink>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** In-app paths navigate without a reload; everything else is an external link. */
function FooterLink({ href, children }: { href: string; children: string }) {
  if (href.startsWith("/")) {
    return (
      <Link to={href} className={LINK_CLASSES}>
        {children}
      </Link>
    );
  }
  return (
    <a href={href} target="_blank" rel="noreferrer" className={LINK_CLASSES}>
      {children}
    </a>
  );
}
