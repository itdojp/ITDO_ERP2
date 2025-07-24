import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Icon } from "./Icon";

describe("Icon", () => {
  it("renders icon with name prop", () => {
    render(<Icon name="home" />);
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });

  it("renders icon with custom className", () => {
    render(<Icon name="home" className="custom-icon" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("custom-icon");
  });

  it("supports different sizes", () => {
    const sizes = ["xs", "sm", "md", "lg", "xl", "2xl"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Icon name="home" size={size} />);
      const icon = screen.getByTestId("icon");
      expect(icon).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different colors", () => {
    const colors = [
      "primary",
      "secondary",
      "success",
      "warning",
      "danger",
      "info",
    ] as const;

    colors.forEach((color) => {
      const { unmount } = render(<Icon name="home" color={color} />);
      const icon = screen.getByTestId("icon");
      expect(icon).toBeInTheDocument();
      unmount();
    });
  });

  it("supports custom color with hex value", () => {
    render(<Icon name="home" color="#ff0000" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ color: "#ff0000" });
  });

  it("supports rotation", () => {
    const rotations = [90, 180, 270] as const;

    rotations.forEach((rotation) => {
      const { unmount } = render(<Icon name="home" rotation={rotation} />);
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveStyle({ transform: `rotate(${rotation}deg)` });
      unmount();
    });
  });

  it("supports spin animation", () => {
    render(<Icon name="loading" spin />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("animate-spin");
  });

  it("supports pulse animation", () => {
    render(<Icon name="heart" pulse />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("animate-pulse");
  });

  it("supports bounce animation", () => {
    render(<Icon name="arrow" bounce />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("animate-bounce");
  });

  it("supports different icon sets", () => {
    const iconSets = ["heroicons", "lucide", "feather", "material"] as const;

    iconSets.forEach((iconSet) => {
      const { unmount } = render(<Icon name="home" iconSet={iconSet} />);
      expect(screen.getByTestId("icon")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports solid and outline variants", () => {
    const variants = ["solid", "outline"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(<Icon name="home" variant={variant} />);
      expect(screen.getByTestId("icon")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports custom SVG content", () => {
    const customSvg = '<path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>';
    render(<Icon svg={customSvg} />);
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });

  it("supports click events", () => {
    const onClick = vi.fn();
    render(<Icon name="home" onClick={onClick} />);

    const icon = screen.getByTestId("icon");
    fireEvent.click(icon);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("supports hover events", () => {
    const onMouseEnter = vi.fn();
    const onMouseLeave = vi.fn();

    render(
      <Icon
        name="home"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      />,
    );

    const icon = screen.getByTestId("icon");
    fireEvent.mouseEnter(icon);
    fireEvent.mouseLeave(icon);

    expect(onMouseEnter).toHaveBeenCalledTimes(1);
    expect(onMouseLeave).toHaveBeenCalledTimes(1);
  });

  it("supports custom style", () => {
    const customStyle = { fontSize: "24px", margin: "10px" };
    render(<Icon name="home" style={customStyle} />);

    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle(customStyle);
  });

  it("supports title for accessibility", () => {
    render(<Icon name="home" title="Home Icon" />);
    expect(screen.getByTitle("Home Icon")).toBeInTheDocument();
  });

  it("supports aria-label for accessibility", () => {
    render(<Icon name="home" aria-label="Navigate to home page" />);
    expect(screen.getByLabelText("Navigate to home page")).toBeInTheDocument();
  });

  it("supports custom viewBox", () => {
    render(<Icon name="home" viewBox="0 0 32 32" />);
    const icon = screen.getByTestId("icon");
    expect(icon.querySelector("svg")).toHaveAttribute("viewBox", "0 0 32 32");
  });

  it("supports stroke width customization", () => {
    render(<Icon name="home" strokeWidth={3} />);
    const icon = screen.getByTestId("icon");
    expect(icon).toBeInTheDocument();
  });

  it("supports gradient fills", () => {
    render(<Icon name="home" gradient={{ from: "#ff0000", to: "#0000ff" }} />);
    const icon = screen.getByTestId("icon");
    expect(icon.querySelector("defs")).toBeInTheDocument();
  });

  it("supports shadow effects", () => {
    render(<Icon name="home" shadow />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("drop-shadow-md");
  });

  it("supports outline effects", () => {
    render(<Icon name="home" outline />);
    const icon = screen.getByTestId("icon");
    const svg = icon.querySelector("svg");
    expect(svg).toHaveClass("stroke-current");
  });

  it("supports badge overlay", () => {
    render(<Icon name="bell" badge="5" />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("supports dot indicator", () => {
    render(<Icon name="bell" dot />);
    const icon = screen.getByTestId("icon");
    expect(icon.querySelector(".icon-dot")).toBeInTheDocument();
  });

  it("supports disabled state", () => {
    render(<Icon name="home" disabled />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("opacity-50");
    expect(icon).toHaveClass("cursor-not-allowed");
  });

  it("supports loading state", () => {
    render(<Icon name="home" loading />);
    expect(screen.getByTestId("loading-icon")).toBeInTheDocument();
  });

  it("supports interactive hover effects", () => {
    render(<Icon name="home" interactive />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveClass("hover:scale-110");
    expect(icon).toHaveClass("transition-transform");
  });

  it("supports custom data attributes", () => {
    render(<Icon name="home" data-category="navigation" data-id="main-nav" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveAttribute("data-category", "navigation");
    expect(icon).toHaveAttribute("data-id", "main-nav");
  });

  it("supports flip transformations", () => {
    render(<Icon name="arrow" flip="horizontal" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ transform: "scaleX(-1)" });
  });

  it("supports vertical flip", () => {
    render(<Icon name="arrow" flip="vertical" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ transform: "scaleY(-1)" });
  });

  it("supports both horizontal and vertical flip", () => {
    render(<Icon name="arrow" flip="both" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ transform: "scaleX(-1) scaleY(-1)" });
  });

  it("handles missing icon gracefully", () => {
    render(<Icon name="nonexistent-icon" />);
    const icon = screen.getByTestId("icon");
    expect(icon).toBeInTheDocument();
  });

  it("supports custom icon rendering", () => {
    const customRenderer = (name: string) => (
      <div data-testid="custom-icon">{name}</div>
    );
    render(<Icon name="home" renderIcon={customRenderer} />);
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
    expect(screen.getByText("home")).toBeInTheDocument();
  });

  it("supports icon composition with multiple icons", () => {
    render(
      <Icon name="home">
        <Icon name="plus" size="xs" className="absolute -top-1 -right-1" />
      </Icon>,
    );
    expect(screen.getAllByTestId("icon")).toHaveLength(2);
  });

  it("supports responsive sizing", () => {
    render(<Icon name="home" responsive={{ sm: "sm", md: "md", lg: "lg" }} />);
    const icon = screen.getByTestId("icon");
    expect(icon).toBeInTheDocument();
  });

  it("supports theme variants", () => {
    const themes = ["light", "dark", "auto"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Icon name="home" theme={theme} />);
      expect(screen.getByTestId("icon")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports animation delay", () => {
    render(<Icon name="loading" spin animationDelay={500} />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ animationDelay: "500ms" });
  });

  it("supports animation duration", () => {
    render(<Icon name="loading" spin animationDuration={2000} />);
    const icon = screen.getByTestId("icon");
    expect(icon).toHaveStyle({ animationDuration: "2000ms" });
  });
});
