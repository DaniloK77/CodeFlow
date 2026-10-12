import type { AnchorHTMLAttributes, MouseEvent, ReactNode } from "react";

import { navigate } from "./navigation";

interface LinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> {
  to: string;
  children: ReactNode;
}

const isPlainLeftClick = (event: MouseEvent) =>
  event.button === 0 && !(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);

/** An ordinary `<a>` that navigates in-app. New-tab clicks and `target` keep working. */
export function Link({ to, onClick, target, children, ...rest }: LinkProps) {
  return (
    <a
      {...rest}
      href={to}
      {...(target !== undefined && { target })}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented || target === "_blank" || !isPlainLeftClick(event)) return;
        event.preventDefault();
        navigate(to);
      }}
    >
      {children}
    </a>
  );
}
