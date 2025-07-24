import React from "react";

interface DividerProps {
  children?: React.ReactNode;
  orientation?: "horizontal" | "vertical";
  textAlign?: "left" | "center" | "right";
  variant?: "solid" | "dashed" | "dotted";
  thickness?: "thin" | "medium" | "thick";
  color?: "gray" | "red" | "blue" | "green" | "yellow" | "purple";
  spacing?: "small" | "medium" | "large";
  icon?: React.ReactNode;
  className?: string;
  plain?: boolean;
  flex?: boolean;
  gradient?: boolean;
  animated?: boolean;
  width?: string;
  height?: string;
  margin?: string;
  shadow?: boolean;
  borderless?: boolean;
  inset?: boolean;
  rounded?: boolean;
  opacity?: number;
  pattern?: "wavy" | "zigzag" | "dots";
  type?: "default" | "section";
  responsive?: boolean;
  style?: React.CSSProperties;
  [key: string]: any; // For custom data attributes
}

const Divider: React.FC<DividerProps> = ({
  children,
  orientation = "horizontal",
  textAlign = "center",
  variant = "solid",
  thickness = "medium",
  color = "gray",
  spacing = "medium",
  icon,
  className = "",
  plain = false,
  flex = false,
  gradient = false,
  animated = false,
  width,
  height,
  margin,
  shadow = false,
  borderless = false,
  inset = false,
  rounded = false,
  opacity = 1,
  pattern,
  type = "default",
  responsive = false,
  style,
  ...props
}) => {
  const hasContent = children || icon;
  const isVertical = orientation === "vertical";

  const getThicknessClass = () => {
    const thicknessMap = {
      thin: isVertical ? "w-px" : "h-px",
      medium: isVertical ? "w-0.5" : "h-0.5",
      thick: isVertical ? "w-1" : "h-1",
    };
    return thicknessMap[thickness];
  };

  const getColorClass = () => {
    if (borderless) return "";

    const colorMap = {
      gray: "border-gray-300",
      red: "border-red-300",
      blue: "border-blue-300",
      green: "border-green-300",
      yellow: "border-yellow-300",
      purple: "border-purple-300",
    };
    return colorMap[color];
  };

  const getVariantClass = () => {
    if (borderless) return "";

    const variantMap = {
      solid: "border-solid",
      dashed: "border-dashed",
      dotted: "border-dotted",
    };
    return variantMap[variant];
  };

  const getSpacingClass = () => {
    const spacingMap = {
      small: isVertical ? "mx-2" : "my-2",
      medium: isVertical ? "mx-4" : "my-4",
      large: isVertical ? "mx-6" : "my-6",
    };
    return spacingMap[spacing];
  };

  const getTextAlignClass = () => {
    const alignMap = {
      left: "justify-start",
      center: "justify-center",
      right: "justify-end",
    };
    return alignMap[textAlign];
  };

  const getPatternElement = () => {
    if (!pattern) return null;

    switch (pattern) {
      case "wavy":
        return (
          <svg className="w-full h-2" viewBox="0 0 100 10" fill="none">
            <path
              d="M0 5 Q 25 0, 50 5 T 100 5"
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
          </svg>
        );
      case "zigzag":
        return (
          <svg className="w-full h-2" viewBox="0 0 100 10" fill="none">
            <path
              d="M0 5 L 20 0 L 40 10 L 60 0 L 80 10 L 100 5"
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
          </svg>
        );
      case "dots":
        return (
          <div className="flex items-center justify-center space-x-1">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="w-1 h-1 rounded-full bg-current" />
            ))}
          </div>
        );
      default:
        return null;
    }
  };

  const dividerStyles: React.CSSProperties = {
    ...style,
    ...(width && { width }),
    ...(height && { height }),
    ...(margin && { margin }),
    ...(opacity !== 1 && { opacity }),
  };

  const containerClasses = [
    "divider",
    isVertical ? "flex flex-col items-center" : "flex items-center",
    getSpacingClass(),
    flex ? "flex-1" : "",
    responsive ? "responsive-divider" : "",
    inset ? (isVertical ? "mx-4" : "my-4") : "",
    shadow ? "drop-shadow-sm" : "",
    animated ? "transition-all duration-300" : "",
    type === "section" ? "section-divider" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const lineClasses = [
    "border-0",
    isVertical ? "h-full border-l" : "w-full border-t",
    getThicknessClass(),
    getColorClass(),
    getVariantClass(),
    rounded ? "rounded-full" : "",
    gradient
      ? "bg-gradient-to-r from-transparent via-current to-transparent"
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (plain || (!hasContent && !pattern)) {
    return (
      <hr
        role="separator"
        aria-orientation={orientation}
        className={[containerClasses, lineClasses].join(" ")}
        style={dividerStyles}
        {...props}
      />
    );
  }

  if (isVertical) {
    return (
      <div
        role="separator"
        aria-orientation="vertical"
        className={containerClasses}
        style={dividerStyles}
        {...props}
      >
        {!borderless && <div className={lineClasses} />}
        {hasContent && (
          <div className="px-2 py-1 bg-white text-sm text-gray-600 flex items-center">
            {icon && <span className="mr-1">{icon}</span>}
            {children}
          </div>
        )}
        {pattern && <div className="my-2">{getPatternElement()}</div>}
        {!borderless && <div className={lineClasses} />}
      </div>
    );
  }

  // Horizontal divider with content
  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      className={[containerClasses, getTextAlignClass()].join(" ")}
      style={dividerStyles}
      {...props}
    >
      {!borderless && textAlign !== "left" && (
        <div className={[lineClasses, "flex-1"].join(" ")} />
      )}

      {hasContent && (
        <div className="px-3 py-1 bg-white text-sm text-gray-600 flex items-center whitespace-nowrap">
          {icon && <span className="mr-2">{icon}</span>}
          {children}
        </div>
      )}

      {pattern && !hasContent && (
        <div className="flex-1">{getPatternElement()}</div>
      )}

      {!borderless && textAlign !== "right" && (
        <div className={[lineClasses, "flex-1"].join(" ")} />
      )}
    </div>
  );
};

export { Divider };
export default Divider;
