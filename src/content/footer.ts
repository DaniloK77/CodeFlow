import { GitHubIcon } from "@/components/ui/BrandIcons";
import type { FooterLinkGroup, NavLink, SocialLink } from "@/types/content";

import { NAV_LINKS, REPOSITORY_URL } from "./site";

// Every link goes somewhere real. Pages that don't exist (blog, careers, legal) are not listed.
export const FOOTER_LINK_GROUPS: readonly FooterLinkGroup[] = [
  { title: "Product", links: NAV_LINKS },
  {
    title: "Project",
    links: [
      { label: "Source code", href: REPOSITORY_URL },
      { label: "Documentation", href: `${REPOSITORY_URL}#readme` },
      { label: "API reference", href: `${REPOSITORY_URL}#api` },
      { label: "Command line (CLI)", href: `${REPOSITORY_URL}#the-codegrade-cli` },
      { label: "Report an issue", href: `${REPOSITORY_URL}/issues` },
    ],
  },
];

export const LEGAL_LINKS: readonly NavLink[] = [
  { label: "MIT License", href: `${REPOSITORY_URL}/blob/main/LICENSE` },
];

export const SOCIAL_LINKS: readonly SocialLink[] = [
  { label: "CodeFlow on GitHub", href: REPOSITORY_URL, icon: GitHubIcon },
];
