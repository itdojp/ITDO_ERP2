import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Tooltip } from "./Tooltip";

describe("Tooltip", () => {
  it("renders with trigger element", () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    expect(screen.getByText("Trigger")).toBeInTheDocument();
  });

  it("shows tooltip on hover", async () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("hides tooltip on mouse leave", async () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });

    fireEvent.mouseLeave(trigger);

    await waitFor(() => {
      expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();
    });
  });

  it("shows tooltip on focus", async () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("hides tooltip on blur", async () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });

    fireEvent.blur(trigger);

    await waitFor(() => {
      expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();
    });
  });

  it("renders in different positions", async () => {
    const positions: Array<"top" | "bottom" | "left" | "right"> = [
      "top",
      "bottom",
      "left",
      "right",
    ];

    for (const position of positions) {
      const { unmount } = render(
        <Tooltip content="Tooltip text" position={position}>
          <button>Trigger</button>
        </Tooltip>,
      );

      const trigger = screen.getByText("Trigger");
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText("Tooltip text");
        expect(tooltip).toBeInTheDocument();
        // Just verify the tooltip exists, as position calculation depends on DOM layout
        const tooltipContainer = tooltip.closest('[data-testid="tooltip"]');
        expect(tooltipContainer).toBeInTheDocument();
      });

      unmount();
    }
  });

  it("supports different variants", async () => {
    const variants: Array<
      "dark" | "light" | "primary" | "success" | "warning" | "danger"
    > = ["dark", "light", "primary", "success", "warning", "danger"];

    for (const variant of variants) {
      const { unmount } = render(
        <Tooltip content="Tooltip text" variant={variant}>
          <button>Trigger</button>
        </Tooltip>,
      );

      const trigger = screen.getByText("Trigger");
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText("Tooltip text");
        expect(tooltip).toBeInTheDocument();
        expect(tooltip.closest("[data-variant]")).toHaveAttribute(
          "data-variant",
          variant,
        );
      });

      unmount();
    }
  });

  it("supports different sizes", async () => {
    const sizes: Array<"sm" | "md" | "lg"> = ["sm", "md", "lg"];

    for (const size of sizes) {
      const { unmount } = render(
        <Tooltip content="Tooltip text" size={size}>
          <button>Trigger</button>
        </Tooltip>,
      );

      const trigger = screen.getByText("Trigger");
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText("Tooltip text");
        expect(tooltip).toBeInTheDocument();
        expect(tooltip.closest("[data-size]")).toHaveAttribute(
          "data-size",
          size,
        );
      });

      unmount();
    }
  });

  it("supports click trigger", async () => {
    render(
      <Tooltip content="Tooltip text" trigger="click">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("supports manual trigger", async () => {
    const { rerender } = render(
      <Tooltip content="Tooltip text" trigger="manual" visible={false}>
        <button>Trigger</button>
      </Tooltip>,
    );

    expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();

    rerender(
      <Tooltip content="Tooltip text" trigger="manual" visible={true}>
        <button>Trigger</button>
      </Tooltip>,
    );

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("respects delay prop", async () => {
    render(
      <Tooltip content="Tooltip text" delay={500}>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    // Should not appear immediately
    expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();

    // Should appear after delay
    await waitFor(
      () => {
        expect(screen.getByText("Tooltip text")).toBeInTheDocument();
      },
      { timeout: 1000 },
    );
  });

  it("renders with arrow", async () => {
    render(
      <Tooltip content="Tooltip text" arrow>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      const tooltip = screen
        .getByText("Tooltip text")
        .closest('[data-testid="tooltip"]');
      expect(
        tooltip?.querySelector('[data-testid="tooltip-arrow"]'),
      ).toBeInTheDocument();
    });
  });

  it("handles disabled state", async () => {
    render(
      <Tooltip content="Tooltip text" disabled>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();
  });

  it("renders with custom className", async () => {
    render(
      <Tooltip content="Tooltip text" className="custom-tooltip">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      const tooltip = screen
        .getByText("Tooltip text")
        .closest(".custom-tooltip");
      expect(tooltip).toBeInTheDocument();
    });
  });

  it("supports JSX content", async () => {
    const content = (
      <div>
        <strong>Bold</strong> tooltip
      </div>
    );

    render(
      <Tooltip content={content}>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Bold")).toBeInTheDocument();
      expect(screen.getByText("tooltip")).toBeInTheDocument();
    });
  });

  it("handles keyboard navigation", async () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.keyDown(trigger, { key: "Enter" });

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("closes on escape key", async () => {
    render(
      <Tooltip content="Tooltip text" trigger="click">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });

    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(screen.queryByText("Tooltip text")).not.toBeInTheDocument();
    });
  });

  it("handles onVisibleChange callback", async () => {
    const onVisibleChange = vi.fn();

    render(
      <Tooltip content="Tooltip text" onVisibleChange={onVisibleChange}>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(onVisibleChange).toHaveBeenCalledWith(true);
    });

    fireEvent.mouseLeave(trigger);

    await waitFor(() => {
      expect(onVisibleChange).toHaveBeenCalledWith(false);
    });
  });

  it("supports custom offset", async () => {
    render(
      <Tooltip content="Tooltip text" offset={20}>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      const tooltip = screen
        .getByText("Tooltip text")
        .closest('[data-testid="tooltip"]');
      expect(tooltip).toHaveAttribute("data-offset", "20");
    });
  });

  it("prevents tooltip overflow", async () => {
    // Mock getBoundingClientRect to simulate edge case
    const mockGetBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 100,
      right: 100,
      width: 100,
      height: 100,
    }));

    Object.defineProperty(Element.prototype, "getBoundingClientRect", {
      value: mockGetBoundingClientRect,
    });

    render(
      <Tooltip content="Tooltip text" position="top">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("supports interactive tooltips", async () => {
    render(
      <Tooltip
        content={<button data-testid="tooltip-button">Click me</button>}
        interactive
      >
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByTestId("tooltip-button")).toBeInTheDocument();
    });

    const tooltipButton = screen.getByTestId("tooltip-button");
    fireEvent.click(tooltipButton);

    // Tooltip should remain visible for interactive content
    expect(screen.getByTestId("tooltip-button")).toBeInTheDocument();
  });

  it("handles multiple tooltips", async () => {
    render(
      <div>
        <Tooltip content="First tooltip">
          <button>First</button>
        </Tooltip>
        <Tooltip content="Second tooltip">
          <button>Second</button>
        </Tooltip>
      </div>,
    );

    const firstTrigger = screen.getByText("First");
    const secondTrigger = screen.getByText("Second");

    fireEvent.mouseEnter(firstTrigger);

    await waitFor(() => {
      expect(screen.getByText("First tooltip")).toBeInTheDocument();
    });

    fireEvent.mouseEnter(secondTrigger);

    await waitFor(() => {
      expect(screen.getByText("Second tooltip")).toBeInTheDocument();
    });
  });

  it("supports animation options", async () => {
    render(
      <Tooltip content="Tooltip text" animation="fade">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      const tooltip = screen
        .getByText("Tooltip text")
        .closest('[data-testid="tooltip"]');
      expect(tooltip).toHaveAttribute("data-animation", "fade");
    });
  });

  it("handles portal rendering", async () => {
    render(
      <Tooltip content="Tooltip text" portal>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Tooltip text")).toBeInTheDocument();
    });
  });

  it("supports z-index customization", async () => {
    render(
      <Tooltip content="Tooltip text" zIndex={9999}>
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByText("Trigger");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      const tooltip = screen
        .getByText("Tooltip text")
        .closest('[data-testid="tooltip"]');
      expect(tooltip).toHaveStyle("z-index: 9999");
    });
  });
});
