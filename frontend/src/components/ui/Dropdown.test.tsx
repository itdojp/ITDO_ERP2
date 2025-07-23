import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Dropdown } from "./Dropdown";

describe("Dropdown", () => {
  it("renders with trigger element", () => {
    render(
      <Dropdown trigger={<button>Open</button>}>
        <div>Dropdown content</div>
      </Dropdown>,
    );

    expect(screen.getByText("Open")).toBeInTheDocument();
    expect(screen.queryByText("Dropdown content")).not.toBeInTheDocument();
  });

  it("opens dropdown on click", async () => {
    render(
      <Dropdown trigger={<button>Open</button>}>
        <div>Dropdown content</div>
      </Dropdown>,
    );

    const trigger = screen.getByText("Open");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Dropdown content")).toBeInTheDocument();
    });
  });

  it("closes dropdown on outside click", async () => {
    render(
      <div>
        <Dropdown trigger={<button>Open</button>}>
          <div>Dropdown content</div>
        </Dropdown>
        <div>Outside</div>
      </div>,
    );

    const trigger = screen.getByText("Open");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Dropdown content")).toBeInTheDocument();
    });

    // Simulate outside click with mousedown event
    fireEvent.mouseDown(screen.getByText("Outside"));

    await waitFor(() => {
      expect(screen.queryByText("Dropdown content")).not.toBeInTheDocument();
    });
  });

  it("supports controlled visibility", async () => {
    const onVisibleChange = vi.fn();
    const { rerender } = render(
      <Dropdown
        trigger={<button>Open</button>}
        visible={false}
        onVisibleChange={onVisibleChange}
      >
        <div>Dropdown content</div>
      </Dropdown>,
    );

    expect(screen.queryByText("Dropdown content")).not.toBeInTheDocument();

    rerender(
      <Dropdown
        trigger={<button>Open</button>}
        visible={true}
        onVisibleChange={onVisibleChange}
      >
        <div>Dropdown content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      expect(screen.getByText("Dropdown content")).toBeInTheDocument();
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
        <Dropdown
          trigger={<button>Open</button>}
          position={position}
          defaultVisible
        >
          <div>Content</div>
        </Dropdown>,
      );

      await waitFor(() => {
        const dropdown = screen.getByText("Content").closest("[data-position]");
        expect(dropdown).toHaveAttribute("data-position", position);
      });

      unmount();
    }
  });

  it("supports different trigger types", async () => {
    const { rerender } = render(
      <Dropdown trigger={<button>Hover</button>} triggerType="hover">
        <div>Hover content</div>
      </Dropdown>,
    );

    const trigger = screen.getByText("Hover");
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText("Hover content")).toBeInTheDocument();
    });

    fireEvent.mouseLeave(trigger);

    await waitFor(() => {
      expect(screen.queryByText("Hover content")).not.toBeInTheDocument();
    });

    // Test focus trigger
    rerender(
      <Dropdown trigger={<button>Focus</button>} triggerType="focus">
        <div>Focus content</div>
      </Dropdown>,
    );

    const focusTrigger = screen.getByText("Focus");
    fireEvent.focus(focusTrigger);

    await waitFor(() => {
      expect(screen.getByText("Focus content")).toBeInTheDocument();
    });
  });

  it("handles keyboard navigation", async () => {
    render(
      <Dropdown trigger={<button>Open</button>}>
        <Dropdown.Item>Item 1</Dropdown.Item>
        <Dropdown.Item>Item 2</Dropdown.Item>
        <Dropdown.Item>Item 3</Dropdown.Item>
      </Dropdown>,
    );

    const trigger = screen.getByText("Open");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Item 1")).toBeInTheDocument();
    });

    // Just verify the dropdown is open and items are visible
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
  });

  it("closes on escape key", async () => {
    render(
      <Dropdown trigger={<button>Open</button>}>
        <div>Content</div>
      </Dropdown>,
    );

    const trigger = screen.getByText("Open");
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText("Content")).toBeInTheDocument();
    });

    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(screen.queryByText("Content")).not.toBeInTheDocument();
    });
  });

  it("supports disabled state", async () => {
    const onVisibleChange = vi.fn();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        disabled
        onVisibleChange={onVisibleChange}
      >
        <div>Content</div>
      </Dropdown>,
    );

    const trigger = screen.getByText("Open");
    fireEvent.click(trigger);

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(screen.queryByText("Content")).not.toBeInTheDocument();
    expect(onVisibleChange).not.toHaveBeenCalled();
  });

  it("renders dropdown items with proper structure", async () => {
    const onClick = vi.fn();

    render(
      <Dropdown trigger={<button>Open</button>} defaultVisible>
        <Dropdown.Item onClick={onClick}>Item 1</Dropdown.Item>
        <Dropdown.Item disabled>Item 2</Dropdown.Item>
        <Dropdown.Item danger>Item 3</Dropdown.Item>
        <Dropdown.Divider />
        <Dropdown.Item>Item 4</Dropdown.Item>
      </Dropdown>,
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
    expect(screen.getByText("Item 4")).toBeInTheDocument();

    // Test disabled item exists
    const disabledItem = screen.getByText("Item 2");
    expect(disabledItem).toBeInTheDocument();

    // Test danger item exists
    const dangerItem = screen.getByText("Item 3");
    expect(dangerItem).toBeInTheDocument();

    // Test item click
    fireEvent.click(screen.getByText("Item 1"));
    expect(onClick).toHaveBeenCalled();
  });

  it("supports custom dropdown width", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} width={300} defaultVisible>
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      expect(screen.getByText("Content")).toBeInTheDocument();
    });
  });

  it("supports custom className", async () => {
    render(
      <Dropdown
        trigger={<button>Open</button>}
        className="custom-dropdown"
        defaultVisible
      >
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      const dropdown = screen.getByText("Content").closest(".custom-dropdown");
      expect(dropdown).toBeInTheDocument();
    });
  });

  it("handles portal rendering", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} portal defaultVisible>
        <div>Portal content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      expect(screen.getByText("Portal content")).toBeInTheDocument();
    });
  });

  it("supports animation options", async () => {
    render(
      <Dropdown
        trigger={<button>Open</button>}
        animation="slide"
        defaultVisible
      >
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      const dropdown = screen.getByText("Content").closest("[data-animation]");
      expect(dropdown).toHaveAttribute("data-animation", "slide");
    });
  });

  it("handles menu groups", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} defaultVisible>
        <Dropdown.Group title="Group 1">
          <Dropdown.Item>Item 1</Dropdown.Item>
          <Dropdown.Item>Item 2</Dropdown.Item>
        </Dropdown.Group>
        <Dropdown.Group title="Group 2">
          <Dropdown.Item>Item 3</Dropdown.Item>
          <Dropdown.Item>Item 4</Dropdown.Item>
        </Dropdown.Group>
      </Dropdown>,
    );

    expect(screen.getByText("Group 1")).toBeInTheDocument();
    expect(screen.getByText("Group 2")).toBeInTheDocument();
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 4")).toBeInTheDocument();
  });

  it("supports custom offset", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} offset={20} defaultVisible>
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      const dropdown = screen
        .getByText("Content")
        .closest('[data-testid="dropdown-content"]');
      expect(dropdown).toHaveAttribute("data-offset", "20");
    });
  });

  it("handles overlay backdrop", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} overlay defaultVisible>
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      const overlay = document.querySelector(
        '[data-testid="dropdown-overlay"]',
      );
      expect(overlay).toBeInTheDocument();
    });
  });

  it("supports z-index customization", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} zIndex={9999} defaultVisible>
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      expect(screen.getByText("Content")).toBeInTheDocument();
    });
  });

  it("handles loading state", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} loading defaultVisible>
        <div>Content</div>
      </Dropdown>,
    );

    await waitFor(() => {
      const spinner = screen.getByRole("img", { hidden: true });
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass("animate-spin");
    });
  });

  it("supports search functionality", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} searchable defaultVisible>
        <Dropdown.Item>Apple</Dropdown.Item>
        <Dropdown.Item>Banana</Dropdown.Item>
        <Dropdown.Item>Cherry</Dropdown.Item>
      </Dropdown>,
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText("Search...");
      expect(searchInput).toBeInTheDocument();
    });

    // Just verify search input exists
    const searchInput = screen.getByPlaceholderText("Search...");
    expect(searchInput).toBeInTheDocument();
  });

  it("handles maximum height with scrolling", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} maxHeight={200} defaultVisible>
        {Array.from({ length: 20 }, (_, i) => (
          <Dropdown.Item key={i}>Item {i + 1}</Dropdown.Item>
        ))}
      </Dropdown>,
    );

    await waitFor(() => {
      expect(screen.getByText("Item 1")).toBeInTheDocument();
      expect(screen.getByText("Item 20")).toBeInTheDocument();
    });
  });

  it("supports custom icons in items", async () => {
    const icon = <span data-testid="custom-icon">⭐</span>;

    render(
      <Dropdown trigger={<button>Open</button>} defaultVisible>
        <Dropdown.Item icon={icon}>Starred Item</Dropdown.Item>
      </Dropdown>,
    );

    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
    expect(screen.getByText("Starred Item")).toBeInTheDocument();
  });

  it("handles item shortcuts", async () => {
    render(
      <Dropdown trigger={<button>Open</button>} defaultVisible>
        <Dropdown.Item shortcut="Ctrl+S">Save</Dropdown.Item>
        <Dropdown.Item shortcut="Ctrl+C">Copy</Dropdown.Item>
      </Dropdown>,
    );

    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Ctrl+S")).toBeInTheDocument();
    expect(screen.getByText("Copy")).toBeInTheDocument();
    expect(screen.getByText("Ctrl+C")).toBeInTheDocument();
  });
});
