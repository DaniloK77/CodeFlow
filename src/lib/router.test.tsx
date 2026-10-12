import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { navigate, usePathname } from "./navigation";
import { Link } from "./router";

function Where() {
  return <p data-testid="where">{usePathname()}</p>;
}

const scrollTo = vi.fn();

describe("router", () => {
  beforeEach(() => {
    scrollTo.mockClear();
  });

  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
      callback(0);
      return 0;
    });
    window.scrollTo = scrollTo;
  });

  it("follows a link without reloading and updates the path", async () => {
    render(
      <>
        <Link to="/grade">Grade</Link>
        <Where />
      </>,
    );

    await userEvent.click(screen.getByRole("link", { name: "Grade" }));

    expect(window.location.pathname).toBe("/grade");
    expect(screen.getByTestId("where")).toHaveTextContent("/grade");
    expect(scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it("leaves modified clicks to the browser, so links still open in a new tab", async () => {
    const user = userEvent.setup();
    render(<Link to="/grade">Grade</Link>);

    await user.keyboard("{Control>}");
    await user.click(screen.getByRole("link", { name: "Grade" }));
    await user.keyboard("{/Control}");

    expect(window.location.pathname).toBe("/");
  });

  it("scrolls to the hash target after navigating", () => {
    const target = document.createElement("section");
    target.id = "pricing";
    const scrollIntoView = vi.fn();
    target.scrollIntoView = scrollIntoView;
    document.body.append(target);

    navigate("/#pricing");

    expect(scrollIntoView).toHaveBeenCalled();
    target.remove();
  });

  it("reacts to the back button", () => {
    render(<Where />);

    navigate("/grade");
    window.history.replaceState(null, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));

    expect(screen.getByTestId("where")).toHaveTextContent("/");
  });
});
