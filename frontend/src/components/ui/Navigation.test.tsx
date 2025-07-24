import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { Navigation } from "./Navigation";

describe("Navigation", () => {
  const mockNavItems = [
    { id: "1", label: "Home", href: "/", current: true },
    { id: "2", label: "About", href: "/about" },
    {
      id: "3",
      label: "Services",
      href: "/services",
      children: [
        { id: "3-1", label: "Web Design", href: "/services/web-design" },
        { id: "3-2", label: "Development", href: "/services/development" },
      ],
    },
    { id: "4", label: "Contact", href: "/contact", disabled: true },
  ];

  const breadcrumbItems = [
    { id: "1", label: "Home", href: "/" },
    { id: "2", label: "Category", href: "/category" },
    { id: "3", label: "Subcategory", href: "/category/subcategory" },
    { id: "4", label: "Current Page", current: true },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders navigation with items", () => {
    render(<Navigation items={mockNavItems} />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("About")).toBeInTheDocument();
    expect(screen.getByText("Services")).toBeInTheDocument();
  });

  it("highlights current item", () => {
    render(<Navigation items={mockNavItems} />);

    const homeLink = screen.getByText("Home").closest("a");
    expect(homeLink).toHaveClass("bg-blue-100");
  });

  it("disables disabled items", () => {
    render(<Navigation items={mockNavItems} />);

    const contactLink = screen.getByText("Contact").closest("a");
    expect(contactLink).toHaveClass("opacity-50");
    expect(contactLink).toHaveAttribute("aria-disabled", "true");
  });

  it("renders breadcrumb navigation", () => {
    render(<Navigation items={breadcrumbItems} type="breadcrumb" />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("Current Page")).toBeInTheDocument();
  });

  it("renders breadcrumb separators", () => {
    render(<Navigation items={breadcrumbItems} type="breadcrumb" />);

    const separators = screen.getAllByText("/");
    expect(separators).toHaveLength(3); // 3 separators for 4 items
  });

  it("supports custom breadcrumb separator", () => {
    render(
      <Navigation items={breadcrumbItems} type="breadcrumb" separator=">" />,
    );

    const separators = screen.getAllByText(">");
    expect(separators).toHaveLength(3);
  });

  it("supports different orientations", () => {
    const orientations = ["horizontal", "vertical"] as const;

    orientations.forEach((orientation) => {
      const { unmount } = render(
        <Navigation items={mockNavItems} orientation={orientation} />,
      );
      const nav = screen.getByTestId("navigation-container");

      if (orientation === "horizontal") {
        expect(nav).toHaveClass("flex-row");
      } else {
        expect(nav).toHaveClass("flex-col");
      }
      unmount();
    });
  });

  it("supports different sizes", () => {
    const sizes = ["sm", "md", "lg"] as const;

    sizes.forEach((size) => {
      const { unmount } = render(
        <Navigation items={mockNavItems} size={size} />,
      );
      expect(screen.getByTestId("navigation-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports different variants", () => {
    const variants = ["default", "pills", "tabs", "underline"] as const;

    variants.forEach((variant) => {
      const { unmount } = render(
        <Navigation items={mockNavItems} variant={variant} />,
      );
      expect(screen.getByTestId("navigation-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("handles item clicks", () => {
    const onClick = vi.fn();
    const itemsWithClick = [{ id: "1", label: "Home", href: "/", onClick }];

    render(<Navigation items={itemsWithClick} />);

    const homeLink = screen.getByText("Home");
    fireEvent.click(homeLink);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("renders nested navigation items", async () => {
    render(<Navigation items={mockNavItems} />);

    const servicesItem = screen.getByText("Services");
    fireEvent.mouseEnter(servicesItem);

    await waitFor(() => {
      expect(screen.getByText("Web Design")).toBeInTheDocument();
      expect(screen.getByText("Development")).toBeInTheDocument();
    });
  });

  it("supports collapsible mobile navigation", () => {
    render(<Navigation items={mockNavItems} collapsible />);

    const toggleButton = screen.getByTestId("mobile-nav-toggle");
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);

    const navItems = screen.getByTestId("navigation-items");
    expect(navItems).toHaveClass("block");
  });

  it("supports search functionality", () => {
    render(<Navigation items={mockNavItems} searchable />);

    expect(
      screen.getByPlaceholderText("Search navigation..."),
    ).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Search navigation...");
    fireEvent.change(searchInput, { target: { value: "About" } });

    expect(screen.getByText("About")).toBeInTheDocument();
    expect(screen.queryByText("Home")).not.toBeInTheDocument();
  });

  it("supports icons in navigation items", () => {
    const itemsWithIcons = [
      { id: "1", label: "Home", href: "/", icon: "🏠" },
      { id: "2", label: "Profile", href: "/profile", icon: "👤" },
    ];

    render(<Navigation items={itemsWithIcons} />);

    expect(screen.getByText("🏠")).toBeInTheDocument();
    expect(screen.getByText("👤")).toBeInTheDocument();
  });

  it("supports badges in navigation items", () => {
    const itemsWithBadges = [
      { id: "1", label: "Messages", href: "/messages", badge: "5" },
      { id: "2", label: "Notifications", href: "/notifications", badge: "12" },
    ];

    render(<Navigation items={itemsWithBadges} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("supports custom item rendering", () => {
    const customRenderer = (item: any) => (
      <div data-testid={`custom-${item.id}`}>Custom: {item.label}</div>
    );

    render(<Navigation items={mockNavItems} renderItem={customRenderer} />);

    expect(screen.getByTestId("custom-1")).toBeInTheDocument();
    expect(screen.getByText("Custom: Home")).toBeInTheDocument();
  });

  it("supports keyboard navigation", () => {
    render(<Navigation items={mockNavItems} keyboardNavigation />);

    const nav = screen.getByTestId("navigation-container");
    fireEvent.keyDown(nav, { key: "ArrowRight" });

    // Should handle keyboard navigation without errors
    expect(nav).toBeInTheDocument();
  });

  it("supports sticky navigation", () => {
    render(<Navigation items={mockNavItems} sticky />);

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveClass("sticky");
  });

  it("supports full width layout", () => {
    render(<Navigation items={mockNavItems} fullWidth />);

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveClass("w-full");
  });

  it("supports centered layout", () => {
    render(<Navigation items={mockNavItems} centered />);

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveClass("justify-center");
  });

  it("supports logo/brand element", () => {
    const logo = <div data-testid="brand-logo">Brand</div>;
    render(<Navigation items={mockNavItems} brand={logo} />);

    expect(screen.getByTestId("brand-logo")).toBeInTheDocument();
  });

  it("supports custom actions", () => {
    const actions = <button data-testid="custom-action">Login</button>;
    render(<Navigation items={mockNavItems} actions={actions} />);

    expect(screen.getByTestId("custom-action")).toBeInTheDocument();
  });

  it("supports loading state", () => {
    render(<Navigation items={mockNavItems} loading />);

    expect(screen.getByTestId("navigation-loading")).toBeInTheDocument();
  });

  it("supports custom loading component", () => {
    const LoadingComponent = () => (
      <div data-testid="custom-loading">Loading nav...</div>
    );
    render(
      <Navigation
        items={mockNavItems}
        loading
        loadingComponent={<LoadingComponent />}
      />,
    );

    expect(screen.getByTestId("custom-loading")).toBeInTheDocument();
  });

  it("supports responsive behavior", () => {
    render(<Navigation items={mockNavItems} responsive />);

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveClass("responsive-nav");
  });

  it("supports theme variants", () => {
    const themes = ["light", "dark"] as const;

    themes.forEach((theme) => {
      const { unmount } = render(
        <Navigation items={mockNavItems} theme={theme} />,
      );
      const nav = screen.getByTestId("navigation-container");
      expect(nav).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it("supports custom className", () => {
    render(<Navigation items={mockNavItems} className="custom-nav" />);

    expect(screen.getByTestId("navigation-container")).toHaveClass(
      "custom-nav",
    );
  });

  it("supports menu positioning", () => {
    const positions = ["bottom", "top", "left", "right"] as const;

    positions.forEach((position) => {
      const { unmount } = render(
        <Navigation items={mockNavItems} menuPosition={position} />,
      );
      expect(screen.getByTestId("navigation-container")).toBeInTheDocument();
      unmount();
    });
  });

  it("supports route matching", () => {
    const currentPath = "/about";
    render(<Navigation items={mockNavItems} currentPath={currentPath} />);

    const aboutLink = screen.getByText("About").closest("a");
    expect(aboutLink).toHaveClass("bg-blue-100");
  });

  it("supports exact route matching", () => {
    const items = [
      { id: "1", label: "Products", href: "/products" },
      { id: "2", label: "Product Detail", href: "/products/detail" },
    ];

    render(<Navigation items={items} currentPath="/products" exactMatch />);

    const productsLink = screen.getByText("Products").closest("a");
    expect(productsLink).toHaveClass("bg-blue-100");

    const detailLink = screen.getByText("Product Detail").closest("a");
    expect(detailLink).not.toHaveClass("bg-blue-100");
  });

  it("supports custom data attributes", () => {
    render(
      <Navigation
        items={mockNavItems}
        data-category="main-nav"
        data-id="primary"
      />,
    );

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveAttribute("data-category", "main-nav");
    expect(nav).toHaveAttribute("data-id", "primary");
  });

  it("supports accessibility features", () => {
    render(<Navigation items={mockNavItems} />);

    const nav = screen.getByTestId("navigation-container");
    expect(nav).toHaveAttribute("role", "navigation");

    const links = screen.getAllByRole("link");
    links.forEach((link) => {
      expect(link).toHaveAttribute("href");
    });
  });

  it("supports multi-level nesting", () => {
    const deepNestedItems = [
      {
        id: "1",
        label: "Level 1",
        href: "/level1",
        children: [
          {
            id: "1-1",
            label: "Level 2",
            href: "/level1/level2",
            children: [
              { id: "1-1-1", label: "Level 3", href: "/level1/level2/level3" },
            ],
          },
        ],
      },
    ];

    render(<Navigation items={deepNestedItems} />);

    expect(screen.getByText("Level 1")).toBeInTheDocument();
  });

  it("supports breadcrumb with max items", () => {
    const manyBreadcrumbs = Array.from({ length: 10 }, (_, i) => ({
      id: String(i),
      label: `Item ${i}`,
      href: `/item${i}`,
      current: i === 9,
    }));

    render(
      <Navigation items={manyBreadcrumbs} type="breadcrumb" maxItems={5} />,
    );

    expect(screen.getByText("...")).toBeInTheDocument();
  });

  it("supports breadcrumb home icon", () => {
    render(
      <Navigation
        items={breadcrumbItems}
        type="breadcrumb"
        showHomeIcon
        homeIcon="🏠"
      />,
    );

    expect(screen.getByText("🏠")).toBeInTheDocument();
  });
});
