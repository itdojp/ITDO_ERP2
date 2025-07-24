import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Image } from "./Image";

// Mock IntersectionObserver for lazy loading tests
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
});
window.IntersectionObserver = mockIntersectionObserver;

describe("Image", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders image with src prop", () => {
    render(<Image src="/test-image.jpg" alt="Test image" />);
    const img = screen.getByRole("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/test-image.jpg");
    expect(img).toHaveAttribute("alt", "Test image");
  });

  it("renders image with custom className", () => {
    render(<Image src="/test.jpg" alt="Test" className="custom-image" />);
    const container = screen.getByTestId("image-container");
    expect(container).toHaveClass("custom-image");
  });

  it("supports different sizes", () => {
    const sizes = ["xs", "sm", "md", "lg", "xl", "full"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(
        <Image src="/test.jpg" alt="Test" size={size} />,
      );
      const container = screen.getByTestId("image-container");
      expect(container).toBeInTheDocument();
      unmount();
    });
  });

  it("supports custom width and height", () => {
    render(<Image src="/test.jpg" alt="Test" width={200} height={150} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("width", "200");
    expect(img).toHaveAttribute("height", "150");
  });

  it("supports different object fit modes", () => {
    const objectFits = [
      "contain",
      "cover",
      "fill",
      "none",
      "scale-down",
    ] as const;

    objectFits.forEach((objectFit) => {
      const { unmount } = render(
        <Image src="/test.jpg" alt="Test" objectFit={objectFit} />,
      );
      const img = screen.getByRole("img");
      expect(img).toHaveClass(`object-${objectFit}`);
      unmount();
    });
  });

  it("supports rounded corners", () => {
    const radiuses = ["none", "sm", "md", "lg", "full"] as const;

    radiuses.forEach((radius) => {
      const { unmount } = render(
        <Image src="/test.jpg" alt="Test" radius={radius} />,
      );
      const img = screen.getByRole("img");
      expect(img).toBeInTheDocument();
      unmount();
    });
  });

  it("supports shadow effects", () => {
    render(<Image src="/test.jpg" alt="Test" shadow="lg" />);
    const img = screen.getByRole("img");
    expect(img).toHaveClass("shadow-lg");
  });

  it("supports border styles", () => {
    render(
      <Image src="/test.jpg" alt="Test" border={{ width: 2, color: "blue" }} />,
    );
    const img = screen.getByRole("img");
    expect(img).toHaveClass("border-2", "border-blue-500");
  });

  it("shows loading spinner initially", () => {
    render(<Image src="/test.jpg" alt="Test" />);
    expect(screen.getByTestId("image-loading")).toBeInTheDocument();
  });

  it("handles image load event", async () => {
    const onLoad = vi.fn();
    render(<Image src="/test.jpg" alt="Test" onLoad={onLoad} />);

    const img = screen.getByRole("img");
    fireEvent.load(img);

    expect(onLoad).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.queryByTestId("image-loading")).not.toBeInTheDocument();
    });
  });

  it("handles image error event", async () => {
    const onError = vi.fn();
    render(<Image src="/invalid.jpg" alt="Test" onError={onError} />);

    const img = screen.getByRole("img");
    fireEvent.error(img);

    expect(onError).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.getByTestId("image-error")).toBeInTheDocument();
    });
  });

  it("shows fallback image on error", async () => {
    render(<Image src="/invalid.jpg" alt="Test" fallback="/fallback.jpg" />);

    const img = screen.getByRole("img");
    fireEvent.error(img);

    await waitFor(() => {
      expect(img).toHaveAttribute("src", "/fallback.jpg");
    });
  });

  it("supports lazy loading", () => {
    render(<Image src="/test.jpg" alt="Test" lazy />);

    expect(mockIntersectionObserver).toHaveBeenCalled();
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("loading", "lazy");
  });

  it("supports eager loading", () => {
    render(<Image src="/test.jpg" alt="Test" loading="eager" />);

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("loading", "eager");
  });

  it("supports placeholder while loading", async () => {
    render(
      <Image src="/test.jpg" alt="Test" placeholder="/placeholder.jpg" lazy />,
    );

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "/placeholder.jpg");
  });

  it("supports blur effect while loading", () => {
    render(<Image src="/test.jpg" alt="Test" blur />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("blur-sm");
  });

  it("supports grayscale effect", () => {
    render(<Image src="/test.jpg" alt="Test" grayscale />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("grayscale");
  });

  it("supports sepia effect", () => {
    render(<Image src="/test.jpg" alt="Test" sepia />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("sepia");
  });

  it("supports opacity control", () => {
    render(<Image src="/test.jpg" alt="Test" opacity={0.8} />);

    const img = screen.getByRole("img");
    expect(img).toHaveStyle({ opacity: "0.8" });
  });

  it("supports hover effects", () => {
    render(<Image src="/test.jpg" alt="Test" hoverEffect="zoom" />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("hover:scale-110");
  });

  it("supports aspect ratio", () => {
    render(<Image src="/test.jpg" alt="Test" aspectRatio="16/9" />);

    const container = screen.getByTestId("image-container");
    expect(container).toHaveClass("aspect-video");
  });

  it("supports responsive images with srcset", () => {
    const srcSet = "/image-400.jpg 400w, /image-800.jpg 800w";
    render(<Image src="/test.jpg" alt="Test" srcSet={srcSet} />);

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("srcset", srcSet);
  });

  it("supports sizes attribute for responsive images", () => {
    render(
      <Image
        src="/test.jpg"
        alt="Test"
        sizes="(max-width: 768px) 100vw, 50vw"
      />,
    );

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("sizes", "(max-width: 768px) 100vw, 50vw");
  });

  it("supports draggable control", () => {
    render(<Image src="/test.jpg" alt="Test" draggable={false} />);

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("draggable", "false");
  });

  it("supports click events", () => {
    const onClick = vi.fn();
    render(<Image src="/test.jpg" alt="Test" onClick={onClick} />);

    const img = screen.getByRole("img");
    fireEvent.click(img);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("supports custom loading component", () => {
    const CustomLoader = () => (
      <div data-testid="custom-loader">Loading...</div>
    );
    render(
      <Image src="/test.jpg" alt="Test" loadingComponent={<CustomLoader />} />,
    );

    expect(screen.getByTestId("custom-loader")).toBeInTheDocument();
  });

  it("supports custom error component", async () => {
    const CustomError = () => (
      <div data-testid="custom-error">Failed to load</div>
    );
    render(
      <Image src="/invalid.jpg" alt="Test" errorComponent={<CustomError />} />,
    );

    const img = screen.getByRole("img");
    fireEvent.error(img);

    await waitFor(() => {
      expect(screen.getByTestId("custom-error")).toBeInTheDocument();
    });
  });

  it("supports caption", () => {
    render(<Image src="/test.jpg" alt="Test" caption="Image caption" />);

    expect(screen.getByText("Image caption")).toBeInTheDocument();
  });

  it("supports preview mode", () => {
    render(<Image src="/test.jpg" alt="Test" preview />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("cursor-pointer");
  });

  it("supports overlay content", () => {
    const overlay = <div data-testid="overlay">Overlay content</div>;
    render(<Image src="/test.jpg" alt="Test" overlay={overlay} />);

    expect(screen.getByTestId("overlay")).toBeInTheDocument();
  });

  it("supports loading progress", () => {
    render(<Image src="/test.jpg" alt="Test" showProgress />);

    expect(screen.getByTestId("image-progress")).toBeInTheDocument();
  });

  it("supports zoom on hover", () => {
    render(<Image src="/test.jpg" alt="Test" zoomOnHover />);

    const img = screen.getByRole("img");
    expect(img).toHaveClass("hover:scale-110");
  });

  it("supports retina/high-DPI displays", () => {
    render(<Image src="/test.jpg" alt="Test" retina="/test@2x.jpg" />);

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("srcset");
  });

  it("supports WebP format with fallback", () => {
    render(<Image src="/test.jpg" alt="Test" webp="/test.webp" />);

    const picture = screen
      .getByTestId("image-container")
      .querySelector("picture");
    expect(picture).toBeInTheDocument();
  });

  it("supports custom data attributes", () => {
    render(
      <Image
        src="/test.jpg"
        alt="Test"
        data-category="product"
        data-id="123"
      />,
    );

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("data-category", "product");
    expect(img).toHaveAttribute("data-id", "123");
  });
});
