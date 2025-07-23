import React, { useState, useRef, useEffect } from "react";

interface TagProps {
  children: React.ReactNode;
  color?:
    | "default"
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "error"
    | "info";
  size?: "small" | "medium" | "large";
  variant?: "solid" | "outlined" | "subtle";
  closable?: boolean;
  onClose?: () => void;
  beforeClose?: () => boolean;
  closeIcon?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  clickable?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  radius?: "none" | "small" | "medium" | "large" | "full";
  dot?: boolean;
  animated?: boolean;
  checkable?: boolean;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
  maxWidth?: number;
  truncate?: boolean;
  tooltip?: string;
  value?: string;
  [key: string]: any; // For custom data attributes
}

interface TagGroupProps {
  children: React.ReactNode;
  value?: string[];
  defaultValue?: string[];
  onChange?: (values: string[]) => void;
  multiple?: boolean;
  className?: string;
}

interface TagStatusProps {
  children: React.ReactNode;
  status:
    | "active"
    | "inactive"
    | "pending"
    | "processing"
    | "success"
    | "error"
    | "warning";
  className?: string;
}

const TagComponent: React.FC<TagProps> = ({
  children,
  color = "default",
  size = "medium",
  variant = "solid",
  closable = false,
  onClose,
  beforeClose,
  closeIcon,
  icon,
  className = "",
  style,
  clickable = false,
  onClick,
  disabled = false,
  loading = false,
  radius = "medium",
  dot = false,
  animated = false,
  checkable = false,
  checked: controlledChecked,
  defaultChecked = false,
  onChange,
  maxWidth,
  truncate = false,
  tooltip,
  value,
  ...props
}) => {
  const [internalChecked, setInternalChecked] = useState(defaultChecked);
  const [isVisible, setIsVisible] = useState(true);
  const [showTooltip, setShowTooltip] = useState(false);
  const tagRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const isControlledCheckable = controlledChecked !== undefined;
  const isChecked = isControlledCheckable ? controlledChecked : internalChecked;

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => {
        if (tagRef.current) {
          tagRef.current.classList.add("animate-fade-in");
        }
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [animated]);

  const getColorClasses = () => {
    const colorMap = {
      default: {
        solid: "bg-gray-100 text-gray-800 border-gray-200",
        outlined: "bg-transparent text-gray-700 border-gray-300",
        subtle: "bg-gray-50 text-gray-600 border-transparent",
      },
      primary: {
        solid: "bg-blue-500 text-white border-blue-500",
        outlined: "bg-transparent text-blue-600 border-blue-500",
        subtle: "bg-blue-50 text-blue-600 border-transparent",
      },
      secondary: {
        solid: "bg-gray-500 text-white border-gray-500",
        outlined: "bg-transparent text-gray-600 border-gray-500",
        subtle: "bg-gray-50 text-gray-600 border-transparent",
      },
      success: {
        solid: "bg-green-500 text-white border-green-500",
        outlined: "bg-transparent text-green-600 border-green-500",
        subtle: "bg-green-50 text-green-600 border-transparent",
      },
      warning: {
        solid: "bg-yellow-500 text-white border-yellow-500",
        outlined: "bg-transparent text-yellow-600 border-yellow-500",
        subtle: "bg-yellow-50 text-yellow-600 border-transparent",
      },
      error: {
        solid: "bg-red-500 text-white border-red-500",
        outlined: "bg-transparent text-red-600 border-red-500",
        subtle: "bg-red-50 text-red-600 border-transparent",
      },
      info: {
        solid: "bg-blue-400 text-white border-blue-400",
        outlined: "bg-transparent text-blue-500 border-blue-400",
        subtle: "bg-blue-50 text-blue-500 border-transparent",
      },
    };
    return colorMap[color][variant];
  };

  const getSizeClasses = () => {
    const sizeMap = {
      small: "px-2 py-0.5 text-xs",
      medium: "px-3 py-1 text-sm",
      large: "px-4 py-1.5 text-base",
    };
    return sizeMap[size];
  };

  const getRadiusClasses = () => {
    const radiusMap = {
      none: "rounded-none",
      small: "rounded-sm",
      medium: "rounded-md",
      large: "rounded-lg",
      full: "rounded-full",
    };
    return radiusMap[radius];
  };

  const handleClick = () => {
    if (disabled || loading) return;

    if (checkable) {
      const newChecked = !isChecked;
      if (!isControlledCheckable) {
        setInternalChecked(newChecked);
      }
      onChange?.(newChecked);
    }

    if (clickable && onClick) {
      onClick();
    }
  };

  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();

    if (beforeClose && !beforeClose()) {
      return;
    }

    setIsVisible(false);
    onClose?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled || loading) return;

    if (checkable && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      const newChecked = e.key === "Enter" ? !isChecked : !isChecked;
      if (!isControlledCheckable) {
        setInternalChecked(newChecked);
      }
      onChange?.(newChecked);
    }
  };

  const handleMouseEnter = () => {
    if (tooltip) {
      setShowTooltip(true);
    }
  };

  const handleMouseLeave = () => {
    if (tooltip) {
      setShowTooltip(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  const tagClasses = [
    "inline-flex items-center gap-1 border font-medium transition-all duration-200",
    getSizeClasses(),
    getColorClasses(),
    getRadiusClasses(),
    clickable || checkable ? "cursor-pointer hover:opacity-80" : "",
    disabled ? "opacity-50 cursor-not-allowed" : "",
    loading ? "opacity-75" : "",
    checkable && isChecked ? "ring-2 ring-blue-300" : "",
    animated ? "transform transition-transform" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const contentStyle: React.CSSProperties = {
    ...style,
    ...(maxWidth && { maxWidth: `${maxWidth}px` }),
    ...(truncate &&
      maxWidth && {
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }),
  };

  return (
    <span className="relative inline-block">
      <span
        ref={tagRef}
        className={tagClasses}
        style={contentStyle}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        tabIndex={clickable || checkable ? 0 : undefined}
        role={checkable ? "checkbox" : clickable ? "button" : undefined}
        aria-checked={checkable ? isChecked : undefined}
        aria-disabled={disabled}
        {...props}
      >
        {dot && (
          <span
            data-testid="tag-dot"
            className={`w-2 h-2 rounded-full ${getColorClasses().includes("bg-") ? "bg-current" : "bg-gray-400"}`}
          />
        )}

        {loading && (
          <svg
            className="w-3 h-3 animate-spin"
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
        )}

        {icon && <span>{icon}</span>}

        <span className={truncate && maxWidth ? "truncate" : ""}>
          {children}
        </span>

        {closable && (
          <button
            type="button"
            onClick={handleClose}
            className="ml-1 hover:opacity-70 transition-opacity"
            disabled={disabled}
          >
            {closeIcon || (
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            )}
          </button>
        )}
      </span>

      {tooltip && showTooltip && (
        <div
          ref={tooltipRef}
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-black rounded shadow-lg z-50 whitespace-nowrap"
        >
          {tooltip}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black"></div>
        </div>
      )}
    </span>
  );
};

const TagGroup: React.FC<TagGroupProps> = ({
  children,
  value: controlledValue,
  defaultValue = [],
  onChange,
  multiple = true,
  className = "",
}) => {
  const [internalValue, setInternalValue] = useState<string[]>(defaultValue);

  const isControlled = controlledValue !== undefined;
  const currentValue = isControlled ? controlledValue : internalValue;

  const handleTagChange = (tagValue: string, checked: boolean) => {
    let newValue: string[];

    if (multiple) {
      if (checked) {
        newValue = [...currentValue, tagValue];
      } else {
        newValue = currentValue.filter((v) => v !== tagValue);
      }
    } else {
      newValue = checked ? [tagValue] : [];
    }

    if (!isControlled) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  const enhancedChildren = React.Children.map(children, (child) => {
    if (React.isValidElement(child) && child.type === TagComponent) {
      const tagValue = child.props.value || "";
      const isSelected = currentValue.includes(tagValue);

      return React.cloneElement(child, {
        ...child.props,
        checkable: true,
        checked: isSelected,
        onChange: (checked: boolean) => handleTagChange(tagValue, checked),
      });
    }
    return child;
  });

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {enhancedChildren}
    </div>
  );
};

const TagStatus: React.FC<TagStatusProps> = ({
  children,
  status,
  className = "",
}) => {
  const statusConfig = {
    active: { color: "success" as const, dot: true },
    inactive: { color: "default" as const, dot: true },
    pending: { color: "warning" as const, dot: true },
    processing: { color: "info" as const, loading: true },
    success: { color: "success" as const, icon: "✓" },
    error: { color: "error" as const, icon: "✗" },
    warning: { color: "warning" as const, icon: "⚠" },
  };

  const config = statusConfig[status];

  return (
    <TagComponent
      {...config}
      className={className}
      icon={config.icon ? <span>{config.icon}</span> : undefined}
    >
      {children}
    </TagComponent>
  );
};

type TagType = typeof TagComponent & {
  Group: typeof TagGroup;
  Status: typeof TagStatus;
};

const Tag = TagComponent as TagType;
Tag.Group = TagGroup;
Tag.Status = TagStatus;

export { Tag };
export default Tag;
