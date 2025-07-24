import React, { useState, useEffect, forwardRef } from "react";

interface BadgeProps {
  children?: React.ReactNode;
  count?: number;
  max?: number;
  showZero?: boolean;
  variant?:
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "default";
  size?: "sm" | "md" | "lg";
  color?: string;
  outlined?: boolean;
  dot?: boolean;
  pulse?: boolean;
  loading?: boolean;
  closable?: boolean;
  removable?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  status?: "success" | "processing" | "error" | "warning" | "default";
  position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  shape?: "rounded" | "square" | "pill";
  gradient?: string;
  border?: string;
  shadow?: "sm" | "md" | "lg" | "xl";
  ribbon?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  textTransform?: "uppercase" | "lowercase" | "capitalize";
  theme?: "light" | "dark";
  animateChange?: boolean;
  animated?: boolean;
  bordered?: boolean;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
  role?: string;
  "aria-label"?: string;
  onClick?: (event: React.MouseEvent<HTMLSpanElement>) => void;
  onClose?: () => void;
  onRemove?: () => void;
  href?: string;
  disabled?: boolean;
}

interface BadgeGroupProps {
  children: React.ReactNode;
  className?: string;
  spacing?: string;
}

const BadgeComponent = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      count,
      max = 99,
      showZero = false,
      variant = "primary",
      size = "md",
      color,
      outlined = false,
      dot = false,
      pulse = false,
      loading = false,
      closable = false,
      removable = false,
      icon,
      iconPosition = "left",
      status,
      position,
      shape = "rounded",
      gradient,
      border,
      shadow,
      ribbon,
      textTransform,
      theme = "light",
      animateChange = false,
      animated = false,
      bordered = false,
      className = "",
      style,
      title,
      role,
      "aria-label": ariaLabel,
      onClick,
      onClose,
      onRemove,
      href,
      disabled = false,
    },
    ref,
  ) => {
    const [isAnimating, setIsAnimating] = useState(false);
    const [prevCount, setPrevCount] = useState(count);

    useEffect(() => {
      if (animateChange && count !== prevCount) {
        setIsAnimating(true);
        const timer = setTimeout(() => setIsAnimating(false), 300);
        setPrevCount(count);
        return () => clearTimeout(timer);
      }
    }, [count, prevCount, animateChange]);

    const getVariantClasses = () => {
      if (gradient) return `bg-gradient-to-r ${gradient}`;
      if (color) return `bg-${color}-500 text-white`;
      if (theme === "dark") return "bg-gray-800 text-white";

      const baseClasses = outlined ? "border-2 bg-transparent" : "";

      const variantMap = {
        default: outlined
          ? `${baseClasses} border-gray-300 text-gray-700 hover:bg-gray-50`
          : "bg-gray-100 text-gray-800 hover:bg-gray-200",
        primary: outlined
          ? `${baseClasses} border-blue-500 text-blue-500 hover:bg-blue-50`
          : "bg-blue-500 text-white hover:bg-blue-600",
        secondary: outlined
          ? `${baseClasses} border-gray-600 text-gray-600 hover:bg-gray-50`
          : "bg-gray-600 text-white hover:bg-gray-700",
        success: outlined
          ? `${baseClasses} border-green-500 text-green-600 hover:bg-green-50`
          : "bg-green-500 text-white hover:bg-green-600",
        warning: outlined
          ? `${baseClasses} border-yellow-500 text-yellow-600 hover:bg-yellow-50`
          : "bg-yellow-500 text-white hover:bg-yellow-600",
        danger: outlined
          ? `${baseClasses} border-red-500 text-red-600 hover:bg-red-50`
          : "bg-red-500 text-white hover:bg-red-600",
        info: outlined
          ? `${baseClasses} border-cyan-500 text-cyan-600 hover:bg-cyan-50`
          : "bg-cyan-500 text-white hover:bg-cyan-600",
      };

      return variantMap[variant];
    };

    const getSizeClasses = () => {
      if (dot) {
        const dotSizeMap = {
          sm: "w-2 h-2",
          md: "w-3 h-3",
          lg: "w-4 h-4",
        };
        return dotSizeMap[size];
      }

      const sizeMap = {
        sm: "text-xs px-2 py-0.5",
        md: "text-sm px-2.5 py-1",
        lg: "text-base px-3 py-1.5",
      };
      return sizeMap[size];
    };

    const getShapeClasses = () => {
      if (dot) return "rounded-full";

      const shapeMap = {
        rounded: "rounded-md",
        pill: "rounded-full",
        square: "rounded-none",
      };
      return shapeMap[shape];
    };

    const getPositionClasses = () => {
      if (!position) return "";

      const positionMap = {
        "top-left": "absolute -top-1 -left-1",
        "top-right": "absolute -top-1 -right-1",
        "bottom-left": "absolute -bottom-1 -left-1",
        "bottom-right": "absolute -bottom-1 -right-1",
      };
      return positionMap[position];
    };

    const getRibbonClasses = () => {
      if (!ribbon) return "";

      const ribbonMap = {
        "top-left":
          "absolute top-0 left-0 transform -rotate-45 -translate-x-4 -translate-y-1",
        "top-right":
          "absolute top-0 right-0 transform rotate-45 translate-x-4 -translate-y-1",
        "bottom-left":
          "absolute bottom-0 left-0 transform rotate-45 -translate-x-4 translate-y-1",
        "bottom-right":
          "absolute bottom-0 right-0 transform -rotate-45 translate-x-4 translate-y-1",
      };
      return ribbonMap[ribbon];
    };

    const getShadowClasses = () => {
      if (!shadow) return "";
      return `shadow-${shadow}`;
    };

    const getStatusClasses = () => {
      if (!status) return "";

      const statusMap = {
        success: "bg-green-500",
        processing: "bg-blue-500",
        error: "bg-red-500",
        warning: "bg-yellow-500",
        default: "bg-gray-500",
      };
      return statusMap[status];
    };

    const getTextTransformClasses = () => {
      if (!textTransform) return "";
      return textTransform;
    };

    const shouldShowBadge = () => {
      if (count !== undefined) {
        return showZero || count > 0;
      }
      return true;
    };

    const getDisplayText = () => {
      if (count !== undefined) {
        return count > max ? `${max}+` : count.toString();
      }
      return children;
    };

    const handleRemove = (event: React.MouseEvent) => {
      event.stopPropagation();
      if (onRemove) onRemove();
      if (onClose) onClose();
    };

    const handleClick = (event: React.MouseEvent) => {
      if (disabled) {
        event.preventDefault();
        return;
      }
      onClick?.(event);
    };

    const handleKeyDown = (event: React.KeyboardEvent) => {
      if (disabled) return;

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onClick?.(event as any as React.MouseEvent<HTMLSpanElement>);
      }
    };

    if (!shouldShowBadge()) {
      return null;
    }

    if (dot) {
      return (
        <span
          ref={ref}
          data-testid="badge-dot"
          className={`inline-block ${getShapeClasses()} ${getVariantClasses()} ${getPositionClasses()} ${pulse ? "animate-pulse" : ""} ${className}`}
          style={style}
          title={title}
          role={role}
          aria-label={
            ariaLabel ||
            (typeof children === "string" ? children : "Badge indicator")
          }
        />
      );
    }

    if (!children && count === undefined) {
      return (
        <span
          ref={ref}
          data-testid="empty-badge"
          className={`inline-block w-2 h-2 rounded-full bg-gray-400 ${className}`}
        />
      );
    }

    const isClickable = !!(onClick || href);
    const hasRemoveButton = closable || removable;
    const Element =
      href && !disabled
        ? "a"
        : isClickable && hasRemoveButton
          ? "div"
          : isClickable
            ? "button"
            : "span";

    const badgeClasses = `
      inline-flex items-center justify-center gap-1 font-medium leading-none transition-colors duration-200
      ${getVariantClasses()}
      ${getSizeClasses()}
      ${getShapeClasses()}
      ${getPositionClasses()}
      ${getRibbonClasses()}
      ${getShadowClasses()}
      ${getTextTransformClasses()}
      ${outlined || bordered ? "border" : ""}
      ${border || ""}
      ${pulse ? "animate-pulse" : ""}
      ${isAnimating ? "animate-bounce" : ""}
      ${animated ? "transition-all duration-300 ease-in-out" : ""}
      ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      ${isClickable && !disabled ? "cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" : ""}
      ${className}
    `;

    const elementProps: any = {
      className: badgeClasses.trim(),
      style,
      title,
      role,
      "aria-label": ariaLabel,
      onClick: handleClick,
      onKeyDown: handleKeyDown,
    };

    if (Element === "a") {
      elementProps.href = href;
      elementProps.role = "link";
    } else if (isClickable) {
      if (Element === "button") {
        elementProps.type = "button";
      }
      elementProps.role = elementProps.role || "button";
      elementProps.tabIndex = disabled ? -1 : 0;
    }

    if (disabled) {
      elementProps["aria-disabled"] = "true";
    }

    const renderIcon = (position: "left" | "right") => {
      if (!icon || iconPosition !== position) return null;
      return <span className="flex-shrink-0">{icon}</span>;
    };

    const renderRemoveButton = () => {
      if (!hasRemoveButton) return null;

      return (
        <button
          onClick={handleRemove}
          className="ml-1 flex-shrink-0 rounded-full p-0.5 hover:bg-black hover:bg-opacity-20 focus:outline-none focus:bg-black focus:bg-opacity-20 transition-colors duration-200"
          aria-label="Remove badge"
          type="button"
          tabIndex={0}
        >
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
        </button>
      );
    };

    const displayContent = getDisplayText();

    return (
      <Element {...elementProps} ref={ref}>
        {status && (
          <span
            data-testid="badge-status"
            className={`w-2 h-2 rounded-full mr-2 ${getStatusClasses()}`}
          />
        )}

        {loading && (
          <svg
            className="w-3 h-3 mr-1 animate-spin"
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

        {renderIcon("left")}
        <span className="truncate">{displayContent}</span>
        {renderIcon("right")}
        {renderRemoveButton()}
      </Element>
    );
  },
);

BadgeComponent.displayName = "Badge";

const BadgeGroup: React.FC<BadgeGroupProps> = ({
  children,
  className = "",
  spacing = "space-x-1",
}) => {
  return (
    <div className={`inline-flex items-center ${spacing} ${className}`}>
      {children}
    </div>
  );
};

type BadgeType = typeof BadgeComponent & {
  Group: typeof BadgeGroup;
};

const Badge = BadgeComponent as BadgeType;
Badge.Group = BadgeGroup;

export { Badge };
export default Badge;
