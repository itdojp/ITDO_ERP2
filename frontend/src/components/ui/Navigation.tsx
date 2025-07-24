import React, { useState, useEffect, useRef, useMemo } from "react";
import { cn } from "@/lib/utils";

export interface NavigationItem {
  id: string;
  label: string;
  href?: string;
  current?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  badge?: string | number;
  children?: NavigationItem[];
  onClick?: (e: React.MouseEvent) => void;
}

export interface NavigationProps {
  items: NavigationItem[];
  type?: "default" | "breadcrumb";
  orientation?: "horizontal" | "vertical";
  size?: "sm" | "md" | "lg";
  variant?: "default" | "pills" | "tabs" | "underline";
  theme?: "light" | "dark";
  separator?: string | React.ReactNode;
  collapsible?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  keyboardNavigation?: boolean;
  sticky?: boolean;
  fullWidth?: boolean;
  centered?: boolean;
  responsive?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  brand?: React.ReactNode;
  actions?: React.ReactNode;
  menuPosition?: "top" | "bottom" | "left" | "right";
  currentPath?: string;
  exactMatch?: boolean;
  maxItems?: number;
  showHomeIcon?: boolean;
  homeIcon?: React.ReactNode;
  renderItem?: (item: NavigationItem, level?: number) => React.ReactNode;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const Navigation: React.FC<NavigationProps> = ({
  items,
  type = "default",
  orientation = "horizontal",
  size = "md",
  variant = "default",
  theme = "light",
  separator = "/",
  collapsible = false,
  searchable = false,
  searchPlaceholder = "Search navigation...",
  keyboardNavigation = false,
  sticky = false,
  fullWidth = false,
  centered = false,
  responsive = false,
  loading = false,
  loadingComponent,
  brand,
  actions,
  menuPosition = "bottom",
  currentPath,
  exactMatch = false,
  maxItems,
  showHomeIcon = false,
  homeIcon = "🏠",
  renderItem,
  className,
  "data-testid": dataTestId = "navigation-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isCollapsed, setIsCollapsed] = useState(collapsible);
  const [searchQuery, setSearchQuery] = useState("");
  const [openSubmenus, setOpenSubmenus] = useState<Set<string>>(new Set());
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const navRef = useRef<HTMLElement>(null);

  const sizeClasses = {
    sm: "text-sm py-1 px-2",
    md: "text-base py-2 px-3",
    lg: "text-lg py-3 px-4",
  };

  const variantClasses = {
    default: "",
    pills: "rounded-full",
    tabs: "border-b-2 border-transparent",
    underline: "border-b-2 border-transparent hover:border-gray-300",
  };

  const themeClasses = {
    light: "bg-white text-gray-900",
    dark: "bg-gray-900 text-white",
  };

  // Filter items based on search query
  const filteredItems = useMemo(() => {
    if (!searchable || !searchQuery) return items;

    const filterItems = (items: NavigationItem[]): NavigationItem[] => {
      return items
        .filter((item) => {
          const matchesSearch = item.label
            .toLowerCase()
            .includes(searchQuery.toLowerCase());
          if (matchesSearch) return true;

          if (item.children) {
            const filteredChildren = filterItems(item.children);
            return filteredChildren.length > 0;
          }

          return false;
        })
        .map((item) => ({
          ...item,
          children: item.children ? filterItems(item.children) : undefined,
        }));
    };

    return filterItems(items);
  }, [items, searchQuery, searchable]);

  // Determine current item based on path
  const getIsCurrentItem = (item: NavigationItem): boolean => {
    if (item.current) return true;
    if (!currentPath || !item.href) return false;

    if (exactMatch) {
      return currentPath === item.href;
    } else {
      return currentPath.startsWith(item.href);
    }
  };

  // Handle keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation || !navRef.current) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const focusableItems = filteredItems.filter((item) => !item.disabled);
      const totalItems = focusableItems.length;

      switch (e.key) {
        case "ArrowRight":
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) => (prev + 1) % totalItems);
          break;
        case "ArrowLeft":
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => (prev - 1 + totalItems) % totalItems);
          break;
        case "Enter":
        case " ":
          e.preventDefault();
          if (focusedIndex >= 0) {
            const currentItem = focusableItems[focusedIndex];
            if (currentItem?.onClick) {
              currentItem.onClick({} as React.MouseEvent);
            }
          }
          break;
      }
    };

    const navElement = navRef.current;
    navElement.addEventListener("keydown", handleKeyDown);
    return () => navElement.removeEventListener("keydown", handleKeyDown);
  }, [keyboardNavigation, filteredItems, focusedIndex]);

  const handleSubMenuToggle = (itemId: string) => {
    setOpenSubmenus((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const renderBreadcrumbItems = () => {
    let displayItems = filteredItems;

    // Handle max items with ellipsis
    if (maxItems && displayItems.length > maxItems) {
      const firstItem = displayItems[0];
      const lastItems = displayItems.slice(-maxItems + 1);
      displayItems = [
        firstItem,
        { id: "ellipsis", label: "...", href: "#" },
        ...lastItems,
      ];
    }

    return displayItems.map((item, index) => {
      const isLast = index === displayItems.length - 1;
      const isCurrent = getIsCurrentItem(item);

      return (
        <React.Fragment key={item.id}>
          {index === 0 && showHomeIcon && (
            <span className="mr-2">{homeIcon}</span>
          )}

          {item.id === "ellipsis" ? (
            <span className="text-gray-400">...</span>
          ) : (
            <>
              {item.href && !isCurrent ? (
                <a
                  href={item.href}
                  className={cn(
                    "hover:text-blue-600 transition-colors",
                    item.disabled && "opacity-50 pointer-events-none",
                  )}
                  onClick={item.onClick}
                  aria-disabled={item.disabled}
                >
                  {item.label}
                </a>
              ) : (
                <span
                  className={cn(
                    isCurrent && "font-medium text-gray-900",
                    item.disabled && "opacity-50",
                  )}
                >
                  {item.label}
                </span>
              )}
            </>
          )}

          {!isLast && <span className="mx-2 text-gray-400">{separator}</span>}
        </React.Fragment>
      );
    });
  };

  const renderNavigationItem = (
    item: NavigationItem,
    level: number = 0,
  ): React.ReactNode => {
    if (renderItem) {
      return <div key={item.id}>{renderItem(item, level)}</div>;
    }

    const isCurrent = getIsCurrentItem(item);
    const hasChildren = item.children && item.children.length > 0;
    const isOpen = openSubmenus.has(item.id);

    return (
      <div key={item.id} className={cn(level > 0 && "ml-4")}>
        <a
          href={item.href}
          className={cn(
            "relative flex items-center gap-2 transition-colors",
            sizeClasses[size],
            variantClasses[variant],
            item.disabled && "opacity-50 pointer-events-none",
            !item.disabled && "hover:text-blue-600",
            isCurrent && variant === "default" && "bg-blue-100 text-blue-700",
            isCurrent &&
              variant === "pills" &&
              "bg-blue-500 text-white rounded-full",
            isCurrent && variant === "tabs" && "border-blue-500 text-blue-600",
            isCurrent &&
              variant === "underline" &&
              "border-blue-500 text-blue-600",
          )}
          onClick={(e) => {
            if (hasChildren) {
              e.preventDefault();
              handleSubMenuToggle(item.id);
            }
            item.onClick?.(e);
          }}
          onMouseEnter={() => {
            if (hasChildren && !collapsible) {
              setOpenSubmenus((prev) => new Set([...prev, item.id]));
            }
          }}
          onMouseLeave={() => {
            if (hasChildren && !collapsible) {
              setTimeout(() => {
                setOpenSubmenus((prev) => {
                  const newSet = new Set(prev);
                  newSet.delete(item.id);
                  return newSet;
                });
              }, 100);
            }
          }}
          aria-disabled={item.disabled}
        >
          {item.icon && <span className="flex-shrink-0">{item.icon}</span>}

          <span className="flex-1">{item.label}</span>

          {item.badge && (
            <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
              {item.badge}
            </span>
          )}

          {hasChildren && (
            <span
              className={cn("ml-1 transition-transform", isOpen && "rotate-90")}
            >
              ▶
            </span>
          )}
        </a>

        {hasChildren && isOpen && (
          <div
            className={cn(
              "mt-1",
              menuPosition === "bottom" && "border-l border-gray-200 pl-2 ml-2",
            )}
          >
            {item.children!.map((child) =>
              renderNavigationItem(child, level + 1),
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div
        data-testid="navigation-loading"
        className="flex items-center justify-center py-4"
      >
        {loadingComponent || (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading navigation...</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <nav
      ref={navRef}
      role="navigation"
      tabIndex={keyboardNavigation ? 0 : -1}
      className={cn(
        "navigation",
        orientation === "horizontal" ? "flex flex-row" : "flex flex-col",
        themeClasses[theme],
        sticky && "sticky top-0 z-50",
        fullWidth && "w-full",
        centered && "justify-center",
        responsive && "responsive-nav",
        `theme-${theme}`,
        keyboardNavigation && "focus:outline-none",
        className,
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      {/* Brand/Logo */}
      {brand && <div className="brand mr-8">{brand}</div>}

      {/* Mobile Toggle */}
      {collapsible && (
        <button
          data-testid="mobile-nav-toggle"
          className="md:hidden p-2 rounded-md hover:bg-gray-100"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span className="sr-only">Toggle navigation</span>
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      )}

      {/* Search */}
      {searchable && (
        <div className="search-container mb-4 md:mb-0 md:mr-4">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Navigation Items */}
      <div
        data-testid="navigation-items"
        className={cn(
          "navigation-items flex-1",
          orientation === "horizontal"
            ? "flex flex-row space-x-1"
            : "flex flex-col space-y-1",
          collapsible && "md:flex",
          collapsible && !isCollapsed
            ? "block"
            : collapsible
              ? "hidden"
              : "block",
        )}
      >
        {type === "breadcrumb" ? (
          <div className="flex items-center space-x-1 text-sm">
            {renderBreadcrumbItems()}
          </div>
        ) : (
          filteredItems.map((item) => renderNavigationItem(item))
        )}
      </div>

      {/* Actions */}
      {actions && <div className="actions ml-auto">{actions}</div>}
    </nav>
  );
};

export default Navigation;
