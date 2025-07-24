import React, { useState, forwardRef } from "react";

interface AvatarProps {
  src?: string | string[];
  name?: string;
  initials?: string;
  alt?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "2xl";
  customSize?: string;
  shape?: "circle" | "square";
  status?: "online" | "away" | "busy" | "offline";
  backgroundColor?: string;
  textColor?: string;
  gradient?: string;
  border?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  verified?: boolean;
  loading?: boolean;
  hover?: boolean;
  animate?: boolean;
  draggable?: boolean;
  showTooltip?: boolean;
  className?: string;
  style?: React.CSSProperties;
  role?: string;
  tabIndex?: number;
  "aria-label"?: string;
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  onDragStart?: (event: React.DragEvent<HTMLDivElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLDivElement>) => void;
}

interface AvatarGroupProps {
  children: React.ReactNode;
  max?: number;
  spacing?: string;
  className?: string;
}

const generateColorFromName = (name: string): string => {
  const colors = [
    "bg-red-500",
    "bg-blue-500",
    "bg-green-500",
    "bg-yellow-500",
    "bg-purple-500",
    "bg-pink-500",
    "bg-indigo-500",
    "bg-teal-500",
    "bg-orange-500",
    "bg-cyan-500",
  ];

  const hash = name
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
};

const generateInitials = (name: string): string => {
  if (!name || !name.trim()) return "";

  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].charAt(0).toUpperCase();

  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
};

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  (
    {
      src,
      name = "",
      initials,
      alt,
      size = "md",
      customSize,
      shape = "circle",
      status,
      backgroundColor,
      textColor = "text-white",
      gradient,
      border,
      icon,
      badge,
      verified = false,
      loading = false,
      hover = false,
      animate = false,
      draggable = false,
      showTooltip = false,
      className = "",
      style,
      role,
      tabIndex,
      "aria-label": ariaLabel,
      onClick,
      onDragStart,
      onKeyDown,
    },
    ref,
  ) => {
    const [imageFailed, setImageFailed] = useState(false);
    const [currentSrcIndex, setCurrentSrcIndex] = useState(0);

    const getSizeClasses = () => {
      if (customSize) return customSize;

      const sizeMap = {
        xs: "w-6 h-6 text-xs",
        sm: "w-8 h-8 text-sm",
        md: "w-10 h-10 text-base",
        lg: "w-12 h-12 text-lg",
        xl: "w-16 h-16 text-xl",
        "2xl": "w-20 h-20 text-2xl",
      };
      return sizeMap[size];
    };

    const getShapeClasses = () => {
      return shape === "circle" ? "rounded-full" : "rounded-md";
    };

    const getStatusClasses = () => {
      if (!status) return "";

      const statusMap = {
        online: "bg-green-400",
        away: "bg-yellow-400",
        busy: "bg-red-400",
        offline: "bg-gray-400",
      };
      return statusMap[status];
    };

    const getBackgroundColor = () => {
      if (gradient) {
        return `bg-gradient-to-br ${gradient}`;
      }
      if (backgroundColor) return backgroundColor;
      if (name) return generateColorFromName(name);
      return "bg-gray-500";
    };

    const getDisplayInitials = () => {
      if (initials) return initials;
      return generateInitials(name);
    };

    const getCurrentSrc = () => {
      if (typeof src === "string") return src;
      if (Array.isArray(src) && src[currentSrcIndex])
        return src[currentSrcIndex];
      return undefined;
    };

    const handleImageError = () => {
      if (Array.isArray(src) && currentSrcIndex < src.length - 1) {
        setCurrentSrcIndex((prev) => prev + 1);
      } else {
        setImageFailed(true);
      }
    };

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
      if (!loading && onClick) {
        onClick(event);
      }
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handleClick(event as any);
      }
      if (onKeyDown) {
        onKeyDown(event);
      }
    };

    const shouldShowImage = getCurrentSrc() && !imageFailed;
    const shouldShowInitials = !shouldShowImage && !icon && !loading;
    const displayInitials = getDisplayInitials();

    if (loading) {
      return (
        <div
          ref={ref}
          className={`
          ${getSizeClasses()} ${getShapeClasses()}
          bg-gray-200 animate-pulse
          ${border || ""}
          ${className}
        `}
          style={style}
          role="img"
          aria-hidden="true"
        />
      );
    }

    return (
      <div
        ref={ref}
        className={`
        relative inline-flex items-center justify-center overflow-hidden
        ${getSizeClasses()} ${getShapeClasses()}
        ${shouldShowImage ? "" : getBackgroundColor()}
        ${border || ""}
        ${hover ? "hover:scale-110 transition-transform cursor-pointer" : ""}
        ${animate ? "animate-pulse" : ""}
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
        style={style}
        role={role}
        tabIndex={onClick ? (tabIndex ?? 0) : tabIndex}
        aria-label={ariaLabel || (name ? `${name}'s avatar` : "Avatar")}
        title={showTooltip ? name : undefined}
        draggable={draggable}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragStart={onDragStart}
      >
        {shouldShowImage && (
          <img
            src={getCurrentSrc()}
            alt={alt || name || "Avatar"}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={handleImageError}
          />
        )}

        {icon && !shouldShowImage && (
          <div className={`${textColor}`}>{icon}</div>
        )}

        {shouldShowInitials && displayInitials && (
          <span className={`font-medium ${textColor}`}>{displayInitials}</span>
        )}

        {!shouldShowImage && !icon && !displayInitials && (
          <div
            data-testid="avatar-placeholder"
            className={`w-full h-full flex items-center justify-center ${textColor}`}
          >
            <svg
              className="w-3/5 h-3/5"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
            </svg>
          </div>
        )}

        {status && (
          <div
            data-testid="avatar-status"
            className={`
            absolute -bottom-0 -right-0 w-3 h-3 rounded-full border-2 border-white
            ${getStatusClasses()}
          `}
          />
        )}

        {badge && <div className="absolute -top-1 -right-1">{badge}</div>}

        {verified && (
          <div
            data-testid="verified-badge"
            className="absolute -bottom-0 -right-0 w-4 h-4 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center"
          >
            <svg
              className="w-2 h-2 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>
    );
  },
);

Avatar.displayName = "Avatar";

const AvatarGroup: React.FC<AvatarGroupProps> = ({
  children,
  max = 3,
  spacing = "-space-x-2",
  className = "",
}) => {
  const childrenArray = React.Children.toArray(children);
  const visibleChildren = childrenArray.slice(0, max);
  const overflowCount = Math.max(0, childrenArray.length - max);

  return (
    <div
      data-testid="avatar-group"
      className={`flex items-center ${spacing} ${className}`}
    >
      {visibleChildren}
      {overflowCount > 0 && (
        <div className="relative inline-flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 border-2 border-white text-sm font-medium text-gray-600">
          +{overflowCount}
        </div>
      )}
    </div>
  );
};

Avatar.Group = AvatarGroup;

export default Avatar;
