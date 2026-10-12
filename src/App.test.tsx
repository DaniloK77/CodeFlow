import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { NAV_LINKS } from "./content/site";

describe("App", () => {
  it("renders the page landmarks", () => {
    render(<App />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/describe the task/i);
  });

  it("offers a skip link that targets the main content", () => {
    render(<App />);

    expect(screen.getByRole("link", { name: /skip to content/i })).toHaveAttribute("href", "#main");
    expect(document.getElementById("main")).toBe(screen.getByRole("main"));
  });

  it.each(NAV_LINKS)("navigation link '$label' points to a section on the page", ({ href }) => {
    render(<App />);

    expect(document.querySelector(href.replace("/", ""))).toBeInstanceOf(HTMLElement);
  });

  it("serves the grading screen at /grade and the landing page everywhere else", async () => {
    window.history.replaceState(null, "", "/grade");
    const { unmount } = render(<App />);
    expect(
      await screen.findByRole(
        "heading",
        { level: 1, name: "Grade your solution" },
        { timeout: 5_000 },
      ),
    ).toBeInTheDocument();
    unmount();

    window.history.replaceState(null, "", "/no-such-page");
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/describe the task/i);
  });

  it("gives every section landmark an accessible name", () => {
    render(<App />);

    const sections = document.querySelectorAll("section");
    expect(sections.length).toBeGreaterThan(0);
    sections.forEach((section) => {
      const labelId = section.getAttribute("aria-labelledby");
      expect(labelId && document.getElementById(labelId)).toBeTruthy();
    });
  });
});
