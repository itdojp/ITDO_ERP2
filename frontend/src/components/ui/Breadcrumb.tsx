import React from "react";

export interface BreadcrumbItem {
  id: string;
  label: string | React.ReactNode;
  href?: string;
  onClick?: () => void;
  icon?: React.ReactNode;
  disabled?: boolean;
  current?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "underline" | "pills";
  maxItems?: number;
  showHome?: boolean;
  homeIcon?: React.ReactNode;
  className?: string;
  itemClassName?: string;
  separatorClassName?: string;
  linkClassName?: string;
  currentItemClassName?: string;
  onItemClick?: (item: BreadcrumbItem) => void;
  truncate?: boolean;
  ellipsisPosition?: "start" | "middle" | "end";
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  separator,
  size = "md",
  variant = "default",
  maxItems,
  showHome = false,
  homeIcon,
  className = "",
  itemClassName = "",
  separatorClassName = "",
  linkClassName = "",
  currentItemClassName = "",
  onItemClick,
  truncate = false,
  ellipsisPosition = "middle",
}) => {
  const getSizeClasses = () => {
    const sizeMap = {
      sm: "text-xs px-2 py-1",
      md: "text-sm px-3 py-1.5",
      lg: "text-base px-4 py-2",
    };
    return sizeMap[size];
  };

  const getVariantClasses = (isCurrent: boolean) => {
    const baseClasses = `
      inline-flex items-center gap-1.5 transition-colors duration-200
      ${getSizeClasses()}
    `;

    switch (variant) {
      case "underline":
        return `${baseClasses} ${
          isCurrent
            ? "text-blue-600 border-b-2 border-blue-600"
            : "text-gray-600 hover:text-gray-900 hover:border-b-2 hover:border-gray-300"
        }`;
      case "pills":
        return `${baseClasses} rounded-full ${
          isCurrent
            ? "bg-blue-100 text-blue-700"
            : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
        }`;
      default:
        return `${baseClasses} ${
          isCurrent
            ? "text-gray-900 font-medium"
            : "text-gray-600 hover:text-gray-900"
        }`;
    }
  };

  const defaultSeparator = (
    <svg
      className="w-4 h-4 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5l7 7-7 7"
      />
    </svg>
  );

  const renderSeparator = () => {
    return (
      <span
        className={`mx-2 flex-shrink-0 ${separatorClassName}`}
        aria-hidden="true"
      >
        {separator || defaultSeparator}
      </span>
    );
  };

  const renderEllipsis = () => {
    return (
      <>
        <button
          className={`
            ${getVariantClasses(false)}
            cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            ${itemClassName}
          `}
          aria-label="Show more breadcrumb items"
          title="Click to show more items"
        >
          <span>...</span>
        </button>
        {renderSeparator()}
      </>
    );
  };

  const truncateItems = (items: BreadcrumbItem[], maxItems: number) => {
    if (items.length <= maxItems) return items;

    const totalVisible = maxItems - 1; // Reserve one slot for ellipsis

    switch (ellipsisPosition) {
      case "start":
        return [
          ...items.slice(0, 1), // Keep first item
          { id: "ellipsis", label: "...", disabled: true },
          ...items.slice(-(totalVisible - 1)), // Keep last items
        ];
      case "end":
        return [
          ...items.slice(0, totalVisible), // Keep first items
          { id: "ellipsis", label: "...", disabled: true },
        ];
      case "middle":
      default:
        const startItems = Math.ceil(totalVisible / 2);
        const endItems = totalVisible - startItems;
        return [
          ...items.slice(0, startItems),
          { id: "ellipsis", label: "...", disabled: true },
          ...items.slice(-endItems),
        ];
    }
  };

  const handleItemClick = (item: BreadcrumbItem, event: React.MouseEvent) => {
    if (item.disabled || item.current) {
      event.preventDefault();
      return;
    }

    if (item.onClick) {
      event.preventDefault();
      item.onClick();
    }

    onItemClick?.(item);
  };

  const handleKeyDown = (item: BreadcrumbItem, event: React.KeyboardEvent) => {
    if (item.disabled || item.current) return;

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (item.onClick) {
        item.onClick();
      }
      onItemClick?.(item);
    }
  };

  const renderItem = (item: BreadcrumbItem, index: number, isLast: boolean) => {
    const isCurrent = item.current || isLast;
    const isDisabled = item.disabled;
    const isEllipsis = item.id === "ellipsis";

    const itemClasses = `
      ${getVariantClasses(isCurrent)}
      ${isDisabled ? "opacity-50 cursor-not-allowed" : ""}
      ${!isCurrent && !isDisabled ? "cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2" : ""}
      ${isCurrent ? currentItemClassName : linkClassName}
      ${itemClassName}
    `;

    if (isEllipsis) {
      return renderEllipsis();
    }

    const content = (
      <>
        {item.icon && (
          <span className="flex-shrink-0" aria-hidden="true">
            {item.icon}
          </span>
        )}
        <span className={truncate ? "truncate max-w-[8rem]" : ""}>
          {item.label}
        </span>
      </>
    );

    const Element = item.href && !isDisabled && !isCurrent ? "a" : "span";
    const elementProps: any = {
      className: itemClasses,
      onClick: (e: React.MouseEvent) => handleItemClick(item, e),
      onKeyDown: (e: React.KeyboardEvent) => handleKeyDown(item, e),
    };

    if (Element === "a") {
      elementProps.href = item.href;
      elementProps.role = "link";
      elementProps.tabIndex = 0;
    } else if (!isCurrent && !isDisabled) {
      elementProps.role = "button";
      elementProps.tabIndex = 0;
    }

    if (isCurrent) {
      elementProps["aria-current"] = "page";
    }

    if (isDisabled) {
      elementProps["aria-disabled"] = "true";
      elementProps.tabIndex = -1;
    }

    return <Element {...elementProps}>{content}</Element>;
  };

  const renderHomeItem = () => {
    if (!showHome) return null;

    const homeItem: BreadcrumbItem = {
      id: "home",
      label: homeIcon || (
        <svg
          className="w-4 h-4"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
      ),
      href: "/",
      onClick: () => onItemClick?.({ id: "home", label: "Home", href: "/" }),
    };

    return (
      <>
        {renderItem(homeItem, -1, false)}
        {items.length > 0 && renderSeparator()}
      </>
    );
  };

  const processedItems =
    maxItems && truncate ? truncateItems(items, maxItems) : items;

  return (
    <nav className={`${className}`} aria-label="Breadcrumb">
      <ol className="flex items-center flex-wrap">
        {renderHomeItem()}
        {processedItems.map((item, index) => {
          const isLast = index === processedItems.length - 1;
          return (
            <li key={`${item.id}-${index}`} className="flex items-center">
              {renderItem(item, index, isLast)}
              {!isLast && renderSeparator()}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumb;
