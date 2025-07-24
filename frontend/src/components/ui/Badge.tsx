import React, { useState, useEffect, forwardRef } from "react";

interface BadgeProps {
  children?: React.ReactNode;
  count?: number;
  max?: number;
  showZero?: boolean;
  variant?: "primary" | "secondary" | "success" | "warning" | "danger" | "info";
  size?: "sm" | "md" | "lg";
  color?: string;
  outlined?: boolean;
  dot?: boolean;
  pulse?: boolean;
  loading?: boolean;
  closable?: boolean;
  icon?: React.ReactNode;
  status?: "success" | "processing" | "error" | "warning" | "default";
  position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  shape?: "rounded" | "square";
  gradient?: string;
  border?: string;
  shadow?: "sm" | "md" | "lg" | "xl";
  ribbon?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  textTransform?: "uppercase" | "lowercase" | "capitalize";
  theme?: "light" | "dark";
  animateChange?: boolean;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
  role?: string;
  "aria-label"?: string;
  onClick?: (event: React.MouseEvent<HTMLSpanElement>) => void;
  onClose?: () => void;
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
      size = "sm",
      color,
      outlined = false,
      dot = false,
      pulse = false,
      loading = false,
      closable = false,
      icon,
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
      className = "",
      style,
      title,
      role,
      "aria-label": ariaLabel,
      onClick,
      onClose,
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

      const variantMap = {
        primary: outlined
          ? "border-blue-500 text-blue-500 bg-transparent"
          : "bg-blue-500 text-white",
        secondary: outlined
          ? "border-gray-500 text-gray-500 bg-transparent"
          : "bg-gray-500 text-white",
        success: outlined
          ? "border-green-500 text-green-500 bg-transparent"
          : "bg-green-500 text-white",
        warning: outlined
          ? "border-yellow-500 text-yellow-500 bg-transparent"
          : "bg-yellow-500 text-white",
        danger: outlined
          ? "border-red-500 text-red-500 bg-transparent"
          : "bg-red-500 text-white",
        info: outlined
          ? "border-cyan-500 text-cyan-500 bg-transparent"
          : "bg-cyan-500 text-white",
      };

      return variantMap[variant];
    };

    const getSizeClasses = () => {
      const sizeMap = {
        sm: "text-xs px-2 py-0.5",
        md: "text-sm px-2.5 py-1",
        lg: "text-base px-3 py-1.5",
      };
      return sizeMap[size];
    };

    const getShapeClasses = () => {
      if (dot) return "w-2 h-2 rounded-full";
      if (shape === "square") return "rounded-none";
      return "rounded-full";
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
          aria-label={ariaLabel}
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

    return (
      <span
        ref={ref}
        className={[
          "inline-flex items-center font-medium leading-none",
          getSizeClasses(),
          getShapeClasses(),
          getVariantClasses(),
          getPositionClasses(),
          getRibbonClasses(),
          getShadowClasses(),
          getTextTransformClasses(),
          outlined ? "border" : "",
          border || "",
          pulse ? "animate-pulse" : "",
          isAnimating ? "animate-bounce" : "",
          onClick ? "hover:opacity-80 cursor-pointer" : "",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        style={style}
        title={title}
        role={role}
        aria-label={ariaLabel}
        onClick={onClick}
      >
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

        {icon && <span className="mr-1">{icon}</span>}

        <span>{getDisplayText()}</span>

        {closable && (
          <button
            type="button"
            className="ml-1 hover:opacity-70 focus:outline-none"
            onClick={(e) => {
              e.stopPropagation();
              onClose?.();
            }}
            aria-label="Remove badge"
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
        )}
      </span>
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
