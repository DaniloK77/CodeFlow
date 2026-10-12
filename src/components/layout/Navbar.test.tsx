import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { nth } from "@/test/utils";

import { Navbar } from "./Navbar";

function renderNavbar() {
  const user = userEvent.setup();
  render(<Navbar />);
  const toggle = screen.getByRole("button", { name: /open menu/i });
  const mobileMenu = document.getElementById("mobile-menu");
  if (!mobileMenu) throw new Error("mobile menu is not rendered");
  return { user, toggle, mobileMenu };
}

describe("Navbar", () => {
  it("opens and closes the mobile menu from the toggle button", async () => {
    const { user, toggle, mobileMenu } = renderNavbar();
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(mobileMenu).not.toBeVisible();

    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(toggle).toHaveAccessibleName("Close menu");
    expect(mobileMenu).toBeVisible();

    await user.click(toggle);
    expect(mobileMenu).not.toBeVisible();
  });

  it("closes on Escape and returns focus to the toggle", async () => {
    const { user, toggle, mobileMenu } = renderNavbar();
    await user.click(toggle);

    await user.keyboard("{Escape}");

    expect(mobileMenu).not.toBeVisible();
    expect(toggle).toHaveFocus();
  });

  it("closes after a menu link is chosen", async () => {
    const { user, toggle, mobileMenu } = renderNavbar();
    await user.click(toggle);

    const mobilePricingLink = nth(screen.getAllByRole("link", { name: "Pricing" }), 1);
    await user.click(mobilePricingLink);

    expect(mobileMenu).not.toBeVisible();
  });

  it("opens the grading screen from the mobile menu and closes the menu", async () => {
    const { user, toggle, mobileMenu } = renderNavbar();
    await user.click(toggle);

    await user.click(nth(screen.getAllByRole("link", { name: "Grade my solution" }), 1));

    expect(mobileMenu).not.toBeVisible();
    expect(window.location.pathname).toBe("/grade");
  });

  it("has no grade button on the grading screen itself", () => {
    window.history.replaceState(null, "", "/grade");
    renderNavbar();

    expect(screen.queryByRole("link", { name: "Grade my solution" })).not.toBeInTheDocument();
  });

  it("switches to the solid style once the page is scrolled", () => {
    render(<Navbar />);
    const header = screen.getByRole("banner");
    expect(header).not.toHaveClass("border-b");

    act(() => {
      window.scrollY = 200;
      fireEvent.scroll(window);
    });

    expect(header).toHaveClass("border-b");
    window.scrollY = 0;
  });
});
