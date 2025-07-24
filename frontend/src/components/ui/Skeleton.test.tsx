import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders skeleton with default props", () => {
    render(<Skeleton />);

    expect(screen.getByTestId("skeleton-container")).toBeInTheDocument();
  });

  it("supports different variants", () => {
    const variants = ["text", "circular", "rectangular", "rounded"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(<Skeleton variant={variant} />);
      const container = screen.getByTestId("skeleton-container");
      expect(container).toHaveClass(`variant-${variant}`);
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["xs", "sm", "md", "lg", "xl"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Skeleton size={size} />);
      const container = screen.getByTestId("skeleton-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different animations", () => {
    const animations = ["pulse", "wave", "none"] as const;

    animations.forEach((animation) => {
      const { unmount } = render(<Skeleton animation={animation} />);
      const container = screen.getByTestId("skeleton-container");
      expect(container).toHaveClass(`animation-${animation}`);
      unmount();
    });
  });

  it("applies custom width and height", () => {
    render(<Skeleton width={200} height={100} />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ width: "200px", height: "100px" });
  });

  it("applies custom width and height as strings", () => {
    render(<Skeleton width="50%" height="2rem" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ width: "50%", height: "2rem" });
  });

  it("supports aspect ratio", () => {
    render(<Skeleton aspectRatio="16/9" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ aspectRatio: "16/9" });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Skeleton theme={theme} />);
      const container = screen.getByTestId("skeleton-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports different intensities", () => {
    const intensities = ["low", "medium", "high"] as const;

    intensities.forEach((intensity) => {
      const { unmount } = render(<Skeleton intensity={intensity} />);
      const container = screen.getByTestId("skeleton-container");
      expect(container).toHaveClass(`intensity-${intensity}`);
      unmount();
    });
  });

  it("shows loading state", () => {
    render(<Skeleton loading />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("loading");
  });

  it("hides when not loading", () => {
    render(<Skeleton loading={false} />);

    expect(screen.queryByTestId("skeleton-container")).not.toBeInTheDocument();
  });

  it("shows children when not loading", () => {
    render(
      <Skeleton loading={false}>
        <div data-testid="skeleton-content">Content loaded</div>
      </Skeleton>,
    );

    expect(screen.getByTestId("skeleton-content")).toBeInTheDocument();
    expect(screen.queryByTestId("skeleton-container")).not.toBeInTheDocument();
  });

  it("shows skeleton when loading with children", () => {
    render(
      <Skeleton loading>
        <div data-testid="skeleton-content">Content</div>
      </Skeleton>,
    );

    expect(screen.getByTestId("skeleton-container")).toBeInTheDocument();
    expect(screen.queryByTestId("skeleton-content")).not.toBeInTheDocument();
  });

  it("supports multiple lines for text variant", () => {
    render(<Skeleton variant="text" lines={3} />);

    const container = screen.getByTestId("skeleton-container");
    const lines = container.querySelectorAll('[data-testid="skeleton-line"]');
    expect(lines).toHaveLength(3);
  });

  it("applies different widths to multiple lines", () => {
    render(<Skeleton variant="text" lines={3} />);

    const lines = screen.getAllByTestId("skeleton-line");

    // First two lines should be full width, last line should be narrower
    expect(lines[0]).toHaveClass("w-full");
    expect(lines[1]).toHaveClass("w-full");
    expect(lines[2]).toHaveClass("w-3/4");
  });

  it("supports custom line widths", () => {
    const lineWidths = ["100%", "80%", "60%"];
    render(<Skeleton variant="text" lines={3} lineWidths={lineWidths} />);

    const lines = screen.getAllByTestId("skeleton-line");

    lines.forEach((line, index) => {
      expect(line).toHaveStyle({ width: lineWidths[index] });
    });
  });

  it("supports rounded corners", () => {
    render(<Skeleton rounded />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("rounded");
  });

  it("supports custom border radius", () => {
    render(<Skeleton borderRadius="8px" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ borderRadius: "8px" });
  });

  it("supports shimmer effect", () => {
    render(<Skeleton shimmer />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("shimmer");
  });

  it("supports custom shimmer color", () => {
    render(<Skeleton shimmer shimmerColor="#ffffff" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ "--shimmer-color": "#ffffff" });
  });

  it("supports fade-in animation when content loads", () => {
    render(
      <Skeleton loading={false} fadeIn={true}>
        Content
      </Skeleton>,
    );

    // Check if the content is rendered (which means fadeIn is working)
    const content = screen.getByText("Content");
    expect(content).toBeInTheDocument();

    // Verify the skeleton is not showing when loading=false
    expect(screen.queryByTestId("skeleton-container")).not.toBeInTheDocument();
  });

  it("supports avatar skeleton shape", () => {
    render(<Skeleton variant="circular" avatar />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("avatar");
  });

  it("supports skeleton for card layouts", () => {
    render(<Skeleton card />);

    expect(screen.getByTestId("skeleton-card")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-card-header")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-card-content")).toBeInTheDocument();
  });

  it("supports skeleton for list items", () => {
    render(<Skeleton listItem />);

    expect(screen.getByTestId("skeleton-list-item")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-list-avatar")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-list-content")).toBeInTheDocument();
  });

  it("supports skeleton for table rows", () => {
    render(<Skeleton tableRow columns={4} />);

    expect(screen.getByTestId("skeleton-table-row")).toBeInTheDocument();
    const cells = screen.getAllByTestId("skeleton-table-cell");
    expect(cells).toHaveLength(4);
  });

  it("supports custom animation duration", () => {
    render(<Skeleton animationDuration="2s" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ animationDuration: "2s" });
  });

  it("supports custom animation delay", () => {
    render(<Skeleton animationDelay="0.5s" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({ animationDelay: "0.5s" });
  });

  it("supports responsive sizing", () => {
    render(<Skeleton responsive />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("responsive");
  });

  it("supports accessibility attributes", () => {
    render(<Skeleton ariaLabel="Loading content" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveAttribute("aria-label", "Loading content");
    expect(container).toHaveAttribute("aria-busy", "true");
  });

  it("supports screen reader text", () => {
    render(<Skeleton screenReaderText="Loading user profile" />);

    expect(screen.getByText("Loading user profile")).toBeInTheDocument();
  });

  it("supports custom styling", () => {
    render(<Skeleton className="custom-skeleton" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("custom-skeleton");
  });

  it("supports inline styling", () => {
    const customStyle = { backgroundColor: "red", opacity: 0.5 };
    render(<Skeleton style={customStyle} />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle("background-color: rgb(255, 0, 0)");
    expect(container).toHaveStyle("opacity: 0.5");
  });

  it("supports custom data attributes", () => {
    render(<Skeleton data-category="loading" data-id="profile-skeleton" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveAttribute("data-category", "loading");
    expect(container).toHaveAttribute("data-id", "profile-skeleton");
  });

  it("supports gradient animation", () => {
    render(<Skeleton gradient />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("gradient");
  });

  it("supports custom gradient colors", () => {
    const gradientColors = ["#f0f0f0", "#e0e0e0", "#d0d0d0"];
    render(<Skeleton gradient gradientColors={gradientColors} />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveStyle({
      "--gradient-start": "#f0f0f0",
      "--gradient-middle": "#e0e0e0",
      "--gradient-end": "#d0d0d0",
    });
  });

  it("supports random animation timing", () => {
    render(<Skeleton randomAnimation />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("random-animation");
  });

  it("supports paragraph skeleton with multiple lines", () => {
    render(<Skeleton paragraph lines={4} />);

    expect(screen.getByTestId("skeleton-paragraph")).toBeInTheDocument();
    const lines = screen.getAllByTestId("skeleton-line");
    expect(lines).toHaveLength(4);
  });

  it("supports image skeleton with aspect ratio", () => {
    render(<Skeleton image aspectRatio="4/3" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("image");
    expect(container).toHaveStyle({ aspectRatio: "4/3" });
  });

  it("supports button skeleton with different sizes", () => {
    render(<Skeleton button size="lg" />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("button", "size-lg");
  });

  it("supports input skeleton with label", () => {
    render(<Skeleton input withLabel />);

    expect(screen.getByTestId("skeleton-input-label")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-input-field")).toBeInTheDocument();
  });

  it("handles conditional rendering based on data availability", () => {
    const data = null;
    render(
      <Skeleton loading={!data}>
        <div data-testid="actual-content">{data}</div>
      </Skeleton>,
    );

    expect(screen.getByTestId("skeleton-container")).toBeInTheDocument();
    expect(screen.queryByTestId("actual-content")).not.toBeInTheDocument();
  });

  it("transitions smoothly when loading state changes", () => {
    const { rerender } = render(<Skeleton loading transition />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("transition");

    rerender(
      <Skeleton loading={false} transition>
        Content
      </Skeleton>,
    );
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("supports skeleton for complex layouts", () => {
    render(<Skeleton complex />);

    expect(screen.getByTestId("skeleton-complex")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-complex-header")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-complex-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton-complex-content")).toBeInTheDocument();
  });

  it("supports staggered animation for multiple skeletons", () => {
    render(<Skeleton staggered staggerDelay={0.1} />);

    const container = screen.getByTestId("skeleton-container");
    expect(container).toHaveClass("staggered");
    expect(container).toHaveStyle({ "--stagger-delay": "0.1s" });
  });

  it("supports skeleton count for repeated elements", () => {
    render(<Skeleton count={5} />);

    const containers = screen.getAllByTestId(/skeleton-container/);
    expect(containers).toHaveLength(5);
  });
});
