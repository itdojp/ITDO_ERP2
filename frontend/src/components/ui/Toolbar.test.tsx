import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Toolbar } from "./Toolbar";

describe("Toolbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTools = [
    { id: "save", label: "Save", icon: "💾", onClick: vi.fn() },
    { id: "copy", label: "Copy", icon: "📋", onClick: vi.fn() },
    { id: "paste", label: "Paste", icon: "📄", onClick: vi.fn() },
    { id: "undo", label: "Undo", icon: "↶", onClick: vi.fn() },
    { id: "redo", label: "Redo", icon: "↷", onClick: vi.fn() },
  ];

  it("renders toolbar with tools", () => {
    render(<Toolbar tools={mockTools} showLabels />);

    expect(screen.getByTestId("toolbar-container")).toBeInTheDocument();
    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Copy")).toBeInTheDocument();
  });

  it("handles tool click events", () => {
    render(<Toolbar tools={mockTools} />);

    const saveButton = screen.getByTestId("tool-save");
    fireEvent.click(saveButton);

    expect(mockTools[0].onClick).toHaveBeenCalled();
  });

  it("supports different orientations", () => {
    const orientations = ["horizontal", "vertical"] as const;

    orientations.forEach((orientation) => {
      const { unmount } = render(
        <Toolbar tools={mockTools} orientation={orientation} />,
      );
      const container = screen.getByTestId("toolbar-container");
      expect(container).toHaveClass(`orientation-${orientation}`);
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(<Toolbar tools={mockTools} size={size} />);
      const container = screen.getByTestId("toolbar-container");
      expect(container).toHaveClass(`size-${size}`);
      unmount();
    });
  });

  it("supports different themes", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(<Toolbar tools={mockTools} theme={theme} />);
      const container = screen.getByTestId("toolbar-container");
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("displays tool icons when provided", () => {
    render(<Toolbar tools={mockTools} showIcons />);

    expect(screen.getByText("💾")).toBeInTheDocument();
    expect(screen.getByText("📋")).toBeInTheDocument();
  });

  it("displays tool labels when showLabels is true", () => {
    render(<Toolbar tools={mockTools} showLabels />);

    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Copy")).toBeInTheDocument();
  });

  it("shows tooltips on hover", () => {
    render(<Toolbar tools={mockTools} showTooltips />);

    const saveButton = screen.getByTestId("tool-save");
    fireEvent.mouseEnter(saveButton);

    expect(screen.getByTestId("tooltip-save")).toBeInTheDocument();
  });

  it("supports disabled tools", () => {
    const toolsWithDisabled = [
      {
        id: "save",
        label: "Save",
        icon: "💾",
        onClick: vi.fn(),
        disabled: true,
      },
      { id: "copy", label: "Copy", icon: "📋", onClick: vi.fn() },
    ];

    render(<Toolbar tools={toolsWithDisabled} />);

    const saveButton = screen.getByTestId("tool-save");
    const copyButton = screen.getByTestId("tool-copy");

    expect(saveButton).toBeDisabled();
    expect(copyButton).not.toBeDisabled();
  });

  it("supports tool groups with separators", () => {
    const groupedTools = [
      {
        id: "save",
        label: "Save",
        icon: "💾",
        onClick: vi.fn(),
        group: "file",
      },
      {
        id: "copy",
        label: "Copy",
        icon: "📋",
        onClick: vi.fn(),
        group: "edit",
      },
      {
        id: "paste",
        label: "Paste",
        icon: "📄",
        onClick: vi.fn(),
        group: "edit",
      },
    ];

    render(<Toolbar tools={groupedTools} showSeparators />);

    expect(screen.getByTestId("separator-file-edit")).toBeInTheDocument();
  });

  it("supports compact mode", () => {
    render(<Toolbar tools={mockTools} compact />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("compact");
  });

  it("supports sticky positioning", () => {
    render(<Toolbar tools={mockTools} sticky />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("sticky");
  });

  it("handles keyboard navigation", () => {
    render(<Toolbar tools={mockTools} />);

    const firstTool = screen.getByTestId("tool-save");
    firstTool.focus();

    fireEvent.keyDown(firstTool, { key: "ArrowRight" });

    const secondTool = screen.getByTestId("tool-copy");
    expect(secondTool).toHaveFocus();
  });

  it("supports dropdown tools", () => {
    const dropdownTool = {
      id: "format",
      label: "Format",
      icon: "📝",
      type: "dropdown" as const,
      items: [
        { id: "bold", label: "Bold", onClick: vi.fn() },
        { id: "italic", label: "Italic", onClick: vi.fn() },
      ],
    };

    render(<Toolbar tools={[dropdownTool]} />);

    const formatButton = screen.getByTestId("tool-format");
    fireEvent.click(formatButton);

    expect(screen.getByTestId("dropdown-format")).toBeInTheDocument();
    expect(screen.getByText("Bold")).toBeInTheDocument();
    expect(screen.getByText("Italic")).toBeInTheDocument();
  });

  it("supports toggle tools", () => {
    const toggleTool = {
      id: "bold",
      label: "Bold",
      icon: "B",
      type: "toggle" as const,
      active: false,
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[toggleTool]} />);

    const boldButton = screen.getByTestId("tool-bold");
    expect(boldButton).not.toHaveClass("active");

    fireEvent.click(boldButton);
    expect(toggleTool.onClick).toHaveBeenCalled();
  });

  it("supports custom tool rendering", () => {
    const customTool = {
      id: "custom",
      label: "Custom",
      render: () => <div data-testid="custom-tool">Custom Tool</div>,
    };

    render(<Toolbar tools={[customTool]} />);

    expect(screen.getByTestId("custom-tool")).toBeInTheDocument();
  });

  it("handles overflow with more button", () => {
    render(<Toolbar tools={mockTools} showOverflow maxVisibleTools={3} />);

    expect(screen.getByTestId("more-tools-button")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("more-tools-button"));
    expect(screen.getByTestId("overflow-menu")).toBeInTheDocument();
  });

  it("supports search functionality", () => {
    render(<Toolbar tools={mockTools} searchable showLabels />);

    expect(screen.getByTestId("toolbar-search")).toBeInTheDocument();

    const searchInput = screen.getByTestId("toolbar-search-input");
    fireEvent.change(searchInput, { target: { value: "save" } });

    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.queryByText("Copy")).not.toBeInTheDocument();
  });

  it("supports different positions", () => {
    const positions = ["top", "bottom", "left", "right"] as const;

    positions.forEach((position) => {
      const { unmount } = render(
        <Toolbar tools={mockTools} position={position} />,
      );
      const container = screen.getByTestId("toolbar-container");
      expect(container).toHaveClass(`position-${position}`);
      unmount();
    });
  });

  it("supports floating toolbar", () => {
    render(<Toolbar tools={mockTools} floating />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("floating");
  });

  it("handles tool shortcuts", () => {
    const toolWithShortcut = {
      id: "save",
      label: "Save",
      icon: "💾",
      shortcut: "Ctrl+S",
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[toolWithShortcut]} showShortcuts />);

    expect(screen.getByText("Ctrl+S")).toBeInTheDocument();
  });

  it("supports customizable tool spacing", () => {
    render(<Toolbar tools={mockTools} spacing="lg" />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("spacing-lg");
  });

  it("handles tool badge/notifications", () => {
    const toolWithBadge = {
      id: "notifications",
      label: "Notifications",
      icon: "🔔",
      badge: 5,
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[toolWithBadge]} />);

    expect(screen.getByTestId("tool-badge-notifications")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("supports different button variants", () => {
    const variants = ["default", "ghost", "outline"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <Toolbar tools={mockTools} variant={variant} />,
      );
      const container = screen.getByTestId("toolbar-container");
      expect(container).toHaveClass(`variant-${variant}`);
      unmount();
    });
  });

  it("handles toolbar customization", () => {
    const onCustomize = vi.fn();
    render(
      <Toolbar tools={mockTools} customizable onCustomize={onCustomize} />,
    );

    const customizeButton = screen.getByTestId("customize-button");
    fireEvent.click(customizeButton);

    expect(onCustomize).toHaveBeenCalled();
  });

  it("supports tool reordering", () => {
    const onReorder = vi.fn();
    render(<Toolbar tools={mockTools} reorderable onReorder={onReorder} />);

    const firstTool = screen.getByTestId("tool-save");

    fireEvent.dragStart(firstTool);
    fireEvent.dragOver(screen.getByTestId("tool-copy"));
    fireEvent.drop(screen.getByTestId("tool-copy"));

    expect(onReorder).toHaveBeenCalled();
  });

  it("shows loading state", () => {
    render(<Toolbar tools={mockTools} loading />);

    expect(screen.getByTestId("toolbar-loading")).toBeInTheDocument();
  });

  it("supports responsive behavior", () => {
    render(<Toolbar tools={mockTools} responsive />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("responsive");
  });

  it("handles accessibility attributes", () => {
    render(<Toolbar tools={mockTools} ariaLabel="Main toolbar" />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveAttribute("aria-label", "Main toolbar");
    expect(container).toHaveAttribute("role", "toolbar");
  });

  it("supports custom styling", () => {
    render(<Toolbar tools={mockTools} className="custom-toolbar" />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("custom-toolbar");
  });

  it("supports custom data attributes", () => {
    render(
      <Toolbar
        tools={mockTools}
        data-category="editor"
        data-id="main-toolbar"
      />,
    );

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveAttribute("data-category", "editor");
    expect(container).toHaveAttribute("data-id", "main-toolbar");
  });

  it("handles tool context menus", () => {
    const toolWithContextMenu = {
      id: "save",
      label: "Save",
      icon: "💾",
      onClick: vi.fn(),
      contextMenu: [
        { label: "Save As...", onClick: vi.fn() },
        { label: "Save All", onClick: vi.fn() },
      ],
    };

    render(<Toolbar tools={[toolWithContextMenu]} />);

    const saveButton = screen.getByTestId("tool-save");
    fireEvent.contextMenu(saveButton);

    expect(screen.getByTestId("context-menu-save")).toBeInTheDocument();
  });

  it("supports tool descriptions", () => {
    const toolWithDescription = {
      id: "save",
      label: "Save",
      icon: "💾",
      description: "Save the current document",
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[toolWithDescription]} showDescriptions />);

    expect(screen.getByText("Save the current document")).toBeInTheDocument();
  });

  it("handles tool selection state", () => {
    const selectableTool = {
      id: "select",
      label: "Select",
      icon: "👆",
      selected: true,
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[selectableTool]} />);

    const selectButton = screen.getByTestId("tool-select");
    expect(selectButton).toHaveClass("selected");
  });

  it("supports nested tool groups", () => {
    const nestedTools = {
      id: "text",
      label: "Text",
      icon: "📝",
      type: "group" as const,
      tools: [
        { id: "bold", label: "Bold", icon: "B", onClick: vi.fn() },
        { id: "italic", label: "Italic", icon: "I", onClick: vi.fn() },
      ],
    };

    render(<Toolbar tools={[nestedTools]} />);

    const textGroup = screen.getByTestId("tool-group-text");
    expect(textGroup).toBeInTheDocument();
  });

  it("handles tool visibility conditions", () => {
    const conditionalTool = {
      id: "admin",
      label: "Admin",
      icon: "⚙️",
      visible: false,
      onClick: vi.fn(),
    };

    render(<Toolbar tools={[conditionalTool]} />);

    expect(screen.queryByTestId("tool-admin")).not.toBeInTheDocument();
  });

  it("supports tool animations", () => {
    render(<Toolbar tools={mockTools} animated />);

    const container = screen.getByTestId("toolbar-container");
    expect(container).toHaveClass("animated");
  });
});
