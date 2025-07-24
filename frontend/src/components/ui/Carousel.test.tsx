import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { vi } from "vitest";
import { Carousel } from "./Carousel";

describe("Carousel", () => {
  const mockItems = [
    { id: "1", content: <div data-testid="slide-1">Slide 1</div> },
    { id: "2", content: <div data-testid="slide-2">Slide 2</div> },
    { id: "3", content: <div data-testid="slide-3">Slide 3</div> },
  ];

  const mockImageItems = [
    { id: "1", src: "/image1.jpg", alt: "Image 1", caption: "First image" },
    { id: "2", src: "/image2.jpg", alt: "Image 2", caption: "Second image" },
    { id: "3", src: "/image3.jpg", alt: "Image 3", caption: "Third image" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders carousel with items", () => {
    render(<Carousel items={mockItems} />);

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
    expect(screen.getByTestId("carousel-container")).toBeInTheDocument();
  });

  it("renders carousel with images", () => {
    render(<Carousel images={mockImageItems} />);

    expect(screen.getByAltText("Image 1")).toBeInTheDocument();
    expect(screen.getByText("First image")).toBeInTheDocument();
  });

  it("shows navigation arrows", () => {
    render(<Carousel items={mockItems} showArrows />);

    expect(screen.getByTestId("carousel-prev")).toBeInTheDocument();
    expect(screen.getByTestId("carousel-next")).toBeInTheDocument();
  });

  it("navigates to next slide", () => {
    render(<Carousel items={mockItems} showArrows />);

    const nextButton = screen.getByTestId("carousel-next");
    fireEvent.click(nextButton);

    expect(screen.getByTestId("slide-2")).toBeInTheDocument();
  });

  it("navigates to previous slide", () => {
    render(<Carousel items={mockItems} showArrows defaultIndex={1} />);

    const prevButton = screen.getByTestId("carousel-prev");
    fireEvent.click(prevButton);

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
  });

  it("shows dots navigation", () => {
    render(<Carousel items={mockItems} showDots />);

    const dots = screen.getAllByRole("button");
    expect(dots).toHaveLength(3);
  });

  it("navigates using dots", () => {
    render(<Carousel items={mockItems} showDots />);

    const dots = screen.getAllByRole("button");
    fireEvent.click(dots[2]);

    expect(screen.getByTestId("slide-3")).toBeInTheDocument();
  });

  it("supports autoplay", async () => {
    render(<Carousel items={mockItems} autoplay autoplayInterval={1000} />);

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      expect(screen.getByTestId("slide-2")).toBeInTheDocument();
    });
  });

  it("pauses autoplay on hover", () => {
    render(
      <Carousel
        items={mockItems}
        autoplay
        autoplayInterval={1000}
        pauseOnHover
      />,
    );

    const carousel = screen.getByTestId("carousel-container");
    fireEvent.mouseEnter(carousel);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
  });

  it("resumes autoplay on mouse leave", async () => {
    render(
      <Carousel
        items={mockItems}
        autoplay
        autoplayInterval={1000}
        pauseOnHover
      />,
    );

    const carousel = screen.getByTestId("carousel-container");
    fireEvent.mouseEnter(carousel);
    fireEvent.mouseLeave(carousel);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      expect(screen.getByTestId("slide-2")).toBeInTheDocument();
    });
  });

  it("supports infinite loop", () => {
    render(<Carousel items={mockItems} infinite showArrows />);

    const nextButton = screen.getByTestId("carousel-next");

    // Start at slide 1, go to 2, then 3, then should loop back to 1
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
  });

  it("supports different variants", () => {
    const variants = ["default", "card", "fade"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <Carousel items={mockItems} variant={variant} />,
      );
      expect(screen.getByTestId("carousel-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg", "xl"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Carousel items={mockItems} size={size} />);
      expect(screen.getByTestId("carousel-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports vertical orientation", () => {
    render(<Carousel items={mockItems} orientation="vertical" />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("vertical-carousel");
  });

  it("supports multiple items per view", () => {
    render(<Carousel items={mockItems} itemsPerView={2} />);

    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
    expect(screen.getByTestId("slide-2")).toBeInTheDocument();
  });

  it("supports responsive items per view", () => {
    const responsive = {
      sm: 1,
      md: 2,
      lg: 3,
    };

    render(<Carousel items={mockItems} responsive={responsive} />);

    expect(screen.getByTestId("carousel-container")).toHaveClass(
      "responsive-carousel",
    );
  });

  it("supports custom spacing", () => {
    render(<Carousel items={mockItems} spacing="large" />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("spacing-large");
  });

  it("supports centered mode", () => {
    render(<Carousel items={mockItems} centered />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("centered-mode");
  });

  it("supports fade transition", () => {
    render(<Carousel items={mockItems} transition="fade" />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("fade-transition");
  });

  it("supports slide transitions", () => {
    render(<Carousel items={mockItems} transition="slide" />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("slide-transition");
  });

  it("handles touch/swipe gestures", () => {
    render(<Carousel items={mockItems} swipeable />);

    const carousel = screen.getByTestId("carousel-container");

    // Simulate swipe left
    fireEvent.touchStart(carousel, { touches: [{ clientX: 100, clientY: 0 }] });
    fireEvent.touchMove(carousel, { touches: [{ clientX: 50, clientY: 0 }] });
    fireEvent.touchEnd(carousel, {
      changedTouches: [{ clientX: 50, clientY: 0 }],
    });

    expect(screen.getByTestId("slide-2")).toBeInTheDocument();
  });

  it("shows thumbnails", () => {
    render(<Carousel images={mockImageItems} showThumbnails />);

    expect(screen.getByTestId("carousel-thumbnails")).toBeInTheDocument();
  });

  it("navigates using thumbnails", () => {
    render(<Carousel images={mockImageItems} showThumbnails />);

    const thumbnails = screen.getAllByTestId(/thumbnail-/);
    fireEvent.click(thumbnails[2]);

    const mainImages = screen.getAllByAltText("Image 3");
    expect(mainImages[0]).toBeInTheDocument();
  });

  it("supports keyboard navigation", () => {
    render(<Carousel items={mockItems} keyboardNavigation />);

    const carousel = screen.getByTestId("carousel-container");

    fireEvent.keyDown(carousel, { key: "ArrowRight" });
    expect(screen.getByTestId("slide-2")).toBeInTheDocument();

    fireEvent.keyDown(carousel, { key: "ArrowLeft" });
    expect(screen.getByTestId("slide-1")).toBeInTheDocument();
  });

  it("supports zoom functionality", () => {
    render(<Carousel images={mockImageItems} zoomable />);

    const image = screen.getByAltText("Image 1");
    fireEvent.click(image);

    expect(screen.getByTestId("carousel-zoom-overlay")).toBeInTheDocument();
  });

  it("closes zoom on escape key", () => {
    render(<Carousel images={mockImageItems} zoomable />);

    const image = screen.getByAltText("Image 1");
    fireEvent.click(image);

    const overlay = screen.getByTestId("carousel-zoom-overlay");
    fireEvent.keyDown(overlay, { key: "Escape" });

    expect(
      screen.queryByTestId("carousel-zoom-overlay"),
    ).not.toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(<Carousel items={mockItems} loading />);

    expect(screen.getByTestId("carousel-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading carousel...</div>
    );
    render(
      <Carousel
        items={mockItems}
        loading
        loadingComponent={<LoadingComponent />}
      />,
    );

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("handles slide change events", () => {
    const onSlideChange = vi.fn();
    render(
      <Carousel items={mockItems} onSlideChange={onSlideChange} showArrows />,
    );

    const nextButton = screen.getByTestId("carousel-next");
    fireEvent.click(nextButton);

    expect(onSlideChange).toHaveBeenCalledWith(1, mockItems[1]);
  });

  it("supports custom arrow components", () => {
    const CustomPrevArrow = () => (
      <button data-testid="custom-prev">Previous</button>
    );
    const CustomNextArrow = () => (
      <button data-testid="custom-next">Next</button>
    );

    render(
      <Carousel
        items={mockItems}
        showArrows
        prevArrow={<CustomPrevArrow />}
        nextArrow={<CustomNextArrow />}
      />,
    );

    expect(screen.getByTestId("custom-prev")).toBeInTheDocument();
    expect(screen.getByTestId("custom-next")).toBeInTheDocument();
  });

  it("supports custom dot component", () => {
    const CustomDot = ({
      active,
      onClick,
    }: {
      active: boolean;
      onClick: () => void;
    }) => (
      <button
        data-testid={`custom-dot-${active ? "active" : "inactive"}`}
        onClick={onClick}
      >
        {active ? "●" : "○"}
      </button>
    );

    render(<Carousel items={mockItems} showDots renderDot={CustomDot} />);

    expect(screen.getByTestId("custom-dot-active")).toBeInTheDocument();
    expect(screen.getAllByTestId(/custom-dot-inactive/)).toHaveLength(2);
  });

  it("supports drag to navigate", () => {
    render(<Carousel items={mockItems} draggable />);

    const carousel = screen.getByTestId("carousel-container");

    fireEvent.mouseDown(carousel, { clientX: 100 });
    fireEvent.mouseMove(carousel, { clientX: 50 });
    fireEvent.mouseUp(carousel);

    expect(screen.getByTestId("slide-2")).toBeInTheDocument();
  });

  it("supports auto height adjustment", () => {
    render(<Carousel items={mockItems} autoHeight />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("auto-height");
  });

  it("supports lazy loading", () => {
    render(<Carousel images={mockImageItems} lazyLoad />);

    const images = screen.getAllByRole("img");
    expect(images[0]).toHaveAttribute("loading", "lazy");
  });

  it("supports custom className", () => {
    render(<Carousel items={mockItems} className="custom-carousel" />);

    expect(screen.getByTestId("carousel-container")).toHaveClass(
      "custom-carousel",
    );
  });

  it("supports progress indicator", () => {
    render(<Carousel items={mockItems} showProgress />);

    expect(screen.getByTestId("carousel-progress")).toBeInTheDocument();
  });

  it("supports counter display", () => {
    render(<Carousel items={mockItems} showCounter />);

    expect(screen.getByText("1 / 3")).toBeInTheDocument();
  });

  it("supports custom counter format", () => {
    render(
      <Carousel
        items={mockItems}
        showCounter
        counterFormat={(current, total) => `${current} of ${total}`}
      />,
    );

    expect(screen.getByText("1 of 3")).toBeInTheDocument();
  });

  it("handles empty items gracefully", () => {
    render(<Carousel items={[]} />);

    expect(screen.getByTestId("carousel-container")).toBeInTheDocument();
  });

  it("supports themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Carousel items={mockItems} theme={theme} />);
      const carousel = screen.getByTestId("carousel-container");
      expect(carousel).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports adaptive height", () => {
    render(<Carousel items={mockItems} adaptiveHeight />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("adaptive-height");
  });

  it("supports slide duration customization", () => {
    render(<Carousel items={mockItems} slideDuration={500} />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveStyle({ "--slide-duration": "500ms" });
  });

  it("supports custom data attributes", () => {
    render(
      <Carousel
        items={mockItems}
        data-category="media"
        data-id="main-carousel"
      />,
    );

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveAttribute("data-category", "media");
    expect(carousel).toHaveAttribute("data-id", "main-carousel");
  });

  it("supports focus management", () => {
    render(<Carousel items={mockItems} focusOnSelect />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveAttribute("tabIndex", "0");
  });

  it("supports variable width slides", () => {
    const variableItems = [
      {
        id: "1",
        content: (
          <div data-testid="slide-1" style={{ width: "200px" }}>
            Slide 1
          </div>
        ),
      },
      {
        id: "2",
        content: (
          <div data-testid="slide-2" style={{ width: "300px" }}>
            Slide 2
          </div>
        ),
      },
    ];

    render(<Carousel items={variableItems} variableWidth />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveClass("variable-width");
  });

  it("supports slide padding", () => {
    render(<Carousel items={mockItems} slidePadding="20px" />);

    const carousel = screen.getByTestId("carousel-container");
    expect(carousel).toHaveStyle({ "--slide-padding": "20px" });
  });
});
