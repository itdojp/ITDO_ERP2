import React, { useState, useRef, useEffect, cloneElement } from "react";
import { createPortal } from "react-dom";

interface DropdownProps {
  children: React.ReactNode;
  trigger: React.ReactElement;
  visible?: boolean;
  defaultVisible?: boolean;
  onVisibleChange?: (visible: boolean) => void;
  position?: "top" | "bottom" | "left" | "right";
  triggerType?: "click" | "hover" | "focus";
  disabled?: boolean;
  width?: number | string;
  maxHeight?: number;
  offset?: number;
  zIndex?: number;
  portal?: boolean;
  overlay?: boolean;
  animation?: "fade" | "slide" | "scale";
  loading?: boolean;
  searchable?: boolean;
  className?: string;
}

interface DropdownItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  danger?: boolean;
  icon?: React.ReactNode;
  shortcut?: string;
  className?: string;
}

interface DropdownGroupProps {
  children: React.ReactNode;
  title: string;
  className?: string;
}

const DropdownComponent: React.FC<DropdownProps> = ({
  children,
  trigger,
  visible: controlledVisible,
  defaultVisible = false,
  onVisibleChange,
  position = "bottom",
  triggerType = "click",
  disabled = false,
  width = "auto",
  maxHeight,
  offset = 4,
  zIndex = 1000,
  portal = true,
  overlay = false,
  animation = "fade",
  loading = false,
  searchable = false,
  className = "",
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [searchTerm, setSearchTerm] = useState("");
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const triggerRef = useRef<HTMLElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const isControlled = controlledVisible !== undefined;
  const isVisible = isControlled ? controlledVisible : internalVisible;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isVisible &&
        triggerRef.current &&
        dropdownRef.current &&
        !triggerRef.current.contains(event.target as Node) &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        handleClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isVisible) {
        handleClose();
      }
    };

    if (isVisible) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);

      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        document.removeEventListener("keydown", handleEscape);
      };
    }
  }, [isVisible]);

  useEffect(() => {
    if (isVisible && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isVisible, searchable]);

  const handleOpen = () => {
    if (disabled) return;

    if (!isControlled) {
      setInternalVisible(true);
    }
    onVisibleChange?.(true);
  };

  const handleClose = () => {
    if (disabled) return;

    if (!isControlled) {
      setInternalVisible(false);
    }
    onVisibleChange?.(false);
    setSearchTerm("");
    setFocusedIndex(-1);
  };

  const handleToggle = () => {
    if (isVisible) {
      handleClose();
    } else {
      handleOpen();
    }
  };

  const getDropdownStyle = () => {
    if (!triggerRef.current) return {};

    const triggerRect = triggerRef.current.getBoundingClientRect();
    let top = 0;
    let left = 0;

    switch (position) {
      case "top":
        top = triggerRect.top - offset;
        left = triggerRect.left;
        break;
      case "bottom":
        top = triggerRect.bottom + offset;
        left = triggerRect.left;
        break;
      case "left":
        top = triggerRect.top;
        left = triggerRect.left - offset;
        break;
      case "right":
        top = triggerRect.top;
        left = triggerRect.right + offset;
        break;
    }

    const style: React.CSSProperties = {
      position: "fixed",
      top,
      left,
      zIndex,
      width: typeof width === "number" ? `${width}px` : width,
    };

    if (maxHeight) {
      style.maxHeight = `${maxHeight}px`;
    }

    return style;
  };

  const getAnimationClasses = () => {
    if (!isVisible) return "opacity-0 scale-95 pointer-events-none";

    const animationMap = {
      fade: "opacity-100 scale-100",
      slide: "opacity-100 translate-y-0",
      scale: "opacity-100 scale-100",
    };
    return animationMap[animation];
  };

  const getTriggerEvents = () => {
    const events: Record<string, any> = {};

    if (triggerType === "click") {
      events.onClick = handleToggle;
    }

    if (triggerType === "hover") {
      events.onMouseEnter = handleOpen;
      events.onMouseLeave = handleClose;
    }

    if (triggerType === "focus") {
      events.onFocus = handleOpen;
      events.onBlur = handleClose;
    }

    // Keyboard support
    events.onKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleToggle();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (!isVisible) {
          handleOpen();
        }
        setFocusedIndex(0);
      }
    };

    return events;
  };

  const filterChildren = (children: React.ReactNode): React.ReactNode => {
    if (!searchable || !searchTerm) return children;

    return React.Children.toArray(children).filter((child) => {
      if (React.isValidElement(child) && child.type === DropdownItem) {
        const childText = React.Children.toArray(child.props.children).join("");
        return childText.toLowerCase().includes(searchTerm.toLowerCase());
      }
      return true;
    });
  };

  const getDropdownItems = () => {
    return React.Children.toArray(filterChildren(children)).filter(
      (child) => React.isValidElement(child) && child.type === DropdownItem,
    );
  };

  const handleKeyNavigation = (e: React.KeyboardEvent) => {
    const items = getDropdownItems();

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex((prev) => (prev + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex((prev) => (prev <= 0 ? items.length - 1 : prev - 1));
    } else if (e.key === "Enter" && focusedIndex >= 0) {
      e.preventDefault();
      const focusedItem = items[
        focusedIndex
      ] as React.ReactElement<DropdownItemProps>;
      if (
        focusedItem &&
        focusedItem.props.onClick &&
        !focusedItem.props.disabled
      ) {
        focusedItem.props.onClick();
        handleClose();
      }
    }
  };

  const filteredChildren = filterChildren(children);
  let itemIndex = 0;

  const enhancedChildren = React.Children.map(filteredChildren, (child) => {
    if (React.isValidElement(child) && child.type === DropdownItem) {
      const isFocused = focusedIndex === itemIndex;
      const enhanced = React.cloneElement(child, {
        ...child.props,
        className: `${child.props.className || ""} ${isFocused ? "focus" : ""}`,
      });
      itemIndex++;
      return enhanced;
    }
    return child;
  });

  const dropdownContent = isVisible && (
    <div
      ref={dropdownRef}
      data-testid="dropdown-content"
      data-position={position}
      data-animation={animation}
      data-offset={offset}
      style={getDropdownStyle()}
      className={[
        "bg-white border border-gray-200 rounded-md shadow-lg transition-all duration-200",
        maxHeight ? "overflow-auto" : "",
        getAnimationClasses(),
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      onKeyDown={handleKeyNavigation}
      tabIndex={-1}
    >
      {loading && (
        <div className="flex items-center justify-center p-4">
          <svg
            className="w-4 h-4 animate-spin text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      )}

      {!loading && searchable && (
        <div className="p-2 border-b border-gray-100">
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {!loading && <div className="py-1">{enhancedChildren}</div>}
    </div>
  );

  const overlayContent = isVisible && overlay && (
    <div
      data-testid="dropdown-overlay"
      className="fixed inset-0 bg-black bg-opacity-25"
      style={{ zIndex: zIndex - 1 }}
      onClick={handleClose}
    />
  );

  const enhancedTrigger = cloneElement(trigger, {
    ref: triggerRef,
    ...getTriggerEvents(),
    ...trigger.props,
  });

  const portalContent = (
    <>
      {overlayContent}
      {dropdownContent}
    </>
  );

  return (
    <>
      {enhancedTrigger}
      {portal && typeof window !== "undefined"
        ? createPortal(portalContent, document.body)
        : portalContent}
    </>
  );
};

const DropdownItem: React.FC<DropdownItemProps> = ({
  children,
  onClick,
  disabled = false,
  danger = false,
  icon,
  shortcut,
  className = "",
}) => {
  const handleClick = () => {
    if (!disabled && onClick) {
      onClick();
    }
  };

  return (
    <div
      className={[
        "flex items-center justify-between px-4 py-2 text-sm cursor-pointer hover:bg-gray-50 transition-colors",
        disabled ? "disabled opacity-50 cursor-not-allowed" : "",
        danger ? "text-red-600 hover:bg-red-50" : "text-gray-700",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={handleClick}
    >
      <div className="flex items-center">
        {icon && <span className="mr-3">{icon}</span>}
        <span>{children}</span>
      </div>
      {shortcut && <span className="text-xs text-gray-400">{shortcut}</span>}
    </div>
  );
};

const DropdownDivider: React.FC = () => {
  return <div className="my-1 border-t border-gray-100" />;
};

const DropdownGroup: React.FC<DropdownGroupProps> = ({
  children,
  title,
  className = "",
}) => {
  return (
    <div className={className}>
      <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide border-b border-gray-100">
        {title}
      </div>
      <div className="py-1">{children}</div>
    </div>
  );
};

type DropdownType = typeof DropdownComponent & {
  Item: typeof DropdownItem;
  Divider: typeof DropdownDivider;
  Group: typeof DropdownGroup;
};

const Dropdown = DropdownComponent as DropdownType;
Dropdown.Item = DropdownItem;
Dropdown.Divider = DropdownDivider;
Dropdown.Group = DropdownGroup;

export { Dropdown };
export default Dropdown;
