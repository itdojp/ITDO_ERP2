import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Empty } from "./Empty";

describe("Empty", () => {
  it("renders with default empty state", () => {
    render(<Empty />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders with custom description", () => {
    render(<Empty description="No items found" />);
    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders with custom image", () => {
    const customImage = (
      <img data-testid="custom-empty-image" src="/empty.png" alt="Empty" />
    );
    render(<Empty image={customImage} />);
    expect(screen.getByTestId("custom-empty-image")).toBeInTheDocument();
  });

  it("supports different sizes", () => {
    const sizes = ["small", "medium", "large"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Empty size={size} />);
      expect(screen.getByText("No data")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with action button", () => {
    const onClick = vi.fn();
    render(<Empty action={<button onClick={onClick}>Add Item</button>} />);

    const button = screen.getByText("Add Item");
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onClick).toHaveBeenCalled();
  });

  it("renders with children content", () => {
    render(
      <Empty>
        <div>Custom empty content</div>
      </Empty>,
    );
    expect(screen.getByText("Custom empty content")).toBeInTheDocument();
  });

  it("supports different themes", () => {
    const themes = ["default", "simple", "minimal"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Empty theme={theme} />);
      expect(screen.getByText("No data")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with custom className", () => {
    render(<Empty className="custom-empty" />);
    const container = screen.getByTestId("empty-container");
    expect(container).toHaveClass("custom-empty");
  });

  it("supports different image types", () => {
    const imageTypes = ["default", "simple", "search", "generic"] as const;

    imageTypes.forEach((imageType) => {
      const { unmount } = render(<Empty imageType={imageType} />);
      const image = screen.getByRole("img", { hidden: true });
      expect(image).toBeInTheDocument();
      unmount();
    });
  });

  it("renders without image when imageType is false", () => {
    render(<Empty imageType={false} />);
    expect(screen.queryByRole("img", { hidden: true })).not.toBeInTheDocument();
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("supports custom title", () => {
    render(
      <Empty title="Nothing Here" description="Start by adding content" />,
    );
    expect(screen.getByText("Nothing Here")).toBeInTheDocument();
    expect(screen.getByText("Start by adding content")).toBeInTheDocument();
  });

  it("renders with icon instead of image", () => {
    const icon = <span data-testid="empty-icon">📭</span>;
    render(<Empty icon={icon} />);
    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
  });

  it("supports animated state", () => {
    render(<Empty animated />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with extra content", () => {
    const extra = <div data-testid="extra-content">Additional info</div>;
    render(<Empty extra={extra} />);
    expect(screen.getByTestId("extra-content")).toBeInTheDocument();
  });

  it("supports centered layout", () => {
    render(<Empty centered />);
    const container = screen.getByTestId("empty-container");
    expect(container).toHaveClass("justify-center");
  });

  it("renders with background variant", () => {
    render(<Empty background />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("supports custom image size", () => {
    render(<Empty imageSize={120} />);
    const image = screen.getByRole("img", { hidden: true });
    expect(image).toBeInTheDocument();
  });

  it("renders with subtitle", () => {
    render(<Empty title="No Results" subtitle="Try adjusting your search" />);
    expect(screen.getByText("No Results")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your search")).toBeInTheDocument();
  });

  it("supports inline layout", () => {
    render(<Empty inline />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with loading state", () => {
    render(<Empty loading />);
    const spinner = screen.getByRole("img", { hidden: true });
    expect(spinner).toHaveClass("animate-spin");
  });

  it("supports error state", () => {
    render(<Empty error errorMessage="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders retry button in error state", () => {
    const onRetry = vi.fn();
    render(<Empty error onRetry={onRetry} />);

    const retryButton = screen.getByText("Retry");
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalled();
  });

  it("supports custom styles", () => {
    const customStyle = { backgroundColor: "lightgray" };
    render(<Empty style={customStyle} />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with image alt text", () => {
    render(<Empty imageUrl="/test.png" imageAlt="Empty state illustration" />);
    const image = screen.getByRole("img", { hidden: true });
    expect(image).toHaveAttribute("alt", "Empty state illustration");
  });

  it("supports different content alignments", () => {
    const alignments = ["left", "center", "right"] as const;

    alignments.forEach((align) => {
      const { unmount } = render(<Empty align={align} />);
      expect(screen.getByText("No data")).toBeInTheDocument();
      unmount();
    });
  });

  it("renders with multiple actions", () => {
    const actions = [
      <button key="1">Action 1</button>,
      <button key="2">Action 2</button>,
    ];

    render(<Empty actions={actions} />);
    expect(screen.getByText("Action 1")).toBeInTheDocument();
    expect(screen.getByText("Action 2")).toBeInTheDocument();
  });

  it("supports custom image URL", () => {
    render(<Empty imageUrl="/custom-empty.svg" />);
    const image = screen.getByRole("img", { hidden: true });
    expect(image).toHaveAttribute("src", "/custom-empty.svg");
  });

  it("renders with bordered style", () => {
    render(<Empty bordered />);
    const container = screen.getByTestId("empty-container");
    expect(container).toHaveClass("border");
  });

  it("supports custom padding", () => {
    render(<Empty padding="large" />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with success state", () => {
    render(<Empty success successMessage="All done!" />);
    expect(screen.getByText("All done!")).toBeInTheDocument();
  });

  it("supports custom footer content", () => {
    const footer = <div data-testid="custom-footer">Footer content</div>;
    render(<Empty footer={footer} />);
    expect(screen.getByTestId("custom-footer")).toBeInTheDocument();
  });

  it("renders with help text", () => {
    render(<Empty helpText="Need help? Contact support" />);
    expect(screen.getByText("Need help? Contact support")).toBeInTheDocument();
  });

  it("supports responsive behavior", () => {
    render(<Empty responsive />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });

  it("renders with custom data attributes", () => {
    render(<Empty data-testid="custom-empty" data-state="empty" />);
    const container = screen.getByTestId("custom-empty");
    expect(container).toHaveAttribute("data-state", "empty");
  });

  it("supports overlay mode", () => {
    render(<Empty overlay />);
    const container = screen.getByTestId("empty-container");
    expect(container).toBeInTheDocument();
  });
});
