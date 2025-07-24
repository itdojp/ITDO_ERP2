import React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps {
  variant?: "text" | "circular" | "rectangular" | "rounded";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  animation?: "pulse" | "wave" | "none";
  theme?: "light" | "dark";
  intensity?: "low" | "medium" | "high";
  width?: number | string;
  height?: number | string;
  aspectRatio?: string;
  loading?: boolean;
  lines?: number;
  lineWidths?: string[];
  rounded?: boolean;
  borderRadius?: string;
  shimmer?: boolean;
  shimmerColor?: string;
  fadeIn?: boolean;
  avatar?: boolean;
  card?: boolean;
  listItem?: boolean;
  tableRow?: boolean;
  columns?: number;
  paragraph?: boolean;
  image?: boolean;
  button?: boolean;
  input?: boolean;
  withLabel?: boolean;
  complex?: boolean;
  responsive?: boolean;
  gradient?: boolean;
  gradientColors?: string[];
  randomAnimation?: boolean;
  staggered?: boolean;
  staggerDelay?: number;
  transition?: boolean;
  count?: number;
  animationDuration?: string;
  animationDelay?: string;
  ariaLabel?: string;
  screenReaderText?: string;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = "rectangular",
  size = "md",
  animation = "pulse",
  theme = "light",
  intensity = "medium",
  width,
  height,
  aspectRatio,
  loading = true,
  lines = 1,
  lineWidths,
  rounded = false,
  borderRadius,
  shimmer = false,
  shimmerColor,
  fadeIn = false,
  avatar = false,
  card = false,
  listItem = false,
  tableRow = false,
  columns = 3,
  paragraph = false,
  image = false,
  button = false,
  input = false,
  withLabel = false,
  complex = false,
  responsive = false,
  gradient = false,
  gradientColors = ["#f0f0f0", "#e0e0e0", "#d0d0d0"],
  randomAnimation = false,
  staggered = false,
  staggerDelay = 0.1,
  transition = false,
  count = 1,
  animationDuration,
  animationDelay,
  ariaLabel,
  screenReaderText,
  children,
  className,
  style,
  "data-testid": dataTestId = "skeleton-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const sizeClasses = {
    xs: "size-xs h-3",
    sm: "size-sm h-4",
    md: "size-md h-5",
    lg: "size-lg h-6",
    xl: "size-xl h-8",
  };

  const variantClasses = {
    text: "variant-text h-4",
    circular: "variant-circular rounded-full aspect-square",
    rectangular: "variant-rectangular",
    rounded: "variant-rounded rounded-lg",
  };

  const animationClasses = {
    pulse: "animation-pulse animate-pulse",
    wave: "animation-wave animate-pulse",
    none: "animation-none",
  };

  const themeClasses = {
    light: "theme-light bg-gray-200",
    dark: "theme-dark bg-gray-700",
  };

  const intensityClasses = {
    low: "intensity-low opacity-40",
    medium: "intensity-medium opacity-60",
    high: "intensity-high opacity-80",
  };

  // Don't render skeleton if not loading and has children
  if (!loading && children) {
    return (
      <div
        className={cn(
          fadeIn && "fade-in",
          transition && "transition-opacity duration-300",
        )}
      >
        {children}
      </div>
    );
  }

  // Don't render if not loading and no children
  if (!loading) {
    return null;
  }

  const getInlineStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {};

    if (width !== undefined) {
      styles.width = typeof width === "number" ? `${width}px` : width;
    }
    if (height !== undefined) {
      styles.height = typeof height === "number" ? `${height}px` : height;
    }
    if (aspectRatio) {
      styles.aspectRatio = aspectRatio;
    }
    if (borderRadius) {
      styles.borderRadius = borderRadius;
    }
    if (shimmerColor) {
      styles["--shimmer-color" as any] = shimmerColor;
    }
    if (animationDuration) {
      styles.animationDuration = animationDuration;
    }
    if (animationDelay) {
      styles.animationDelay = animationDelay;
    }
    if (gradient && gradientColors.length >= 3) {
      styles["--gradient-start" as any] = gradientColors[0];
      styles["--gradient-middle" as any] = gradientColors[1];
      styles["--gradient-end" as any] = gradientColors[2];
    }
    if (staggered) {
      styles["--stagger-delay" as any] = `${staggerDelay}s`;
    }

    return styles;
  };

  const renderTextLines = () => {
    const lineElements = [];

    for (let i = 0; i < lines; i++) {
      let lineWidth = "w-full";

      if (lineWidths && lineWidths[i]) {
        // Use custom width from lineWidths array
        lineElements.push(
          <div
            key={i}
            className={cn(
              "h-4 bg-current mb-2 last:mb-0",
              variantClasses[variant],
              animationClasses[animation],
            )}
            style={{ width: lineWidths[i] }}
            data-testid="skeleton-line"
          />,
        );
      } else {
        // Default behavior: last line is 3/4 width
        if (i === lines - 1 && lines > 1) {
          lineWidth = "w-3/4";
        }

        lineElements.push(
          <div
            key={i}
            className={cn(
              "h-4 bg-current mb-2 last:mb-0",
              lineWidth,
              variantClasses[variant],
              animationClasses[animation],
            )}
            data-testid="skeleton-line"
          />,
        );
      }
    }

    return lineElements;
  };

  const renderCard = () => (
    <div className="space-y-4" data-testid="skeleton-card">
      <div
        className={cn("h-6 bg-current rounded", animationClasses[animation])}
        data-testid="skeleton-card-header"
      />
      <div className="space-y-2" data-testid="skeleton-card-content">
        <div
          className={cn(
            "h-4 bg-current rounded w-full",
            animationClasses[animation],
          )}
        />
        <div
          className={cn(
            "h-4 bg-current rounded w-3/4",
            animationClasses[animation],
          )}
        />
        <div
          className={cn(
            "h-4 bg-current rounded w-1/2",
            animationClasses[animation],
          )}
        />
      </div>
    </div>
  );

  const renderListItem = () => (
    <div
      className="flex items-center space-x-3"
      data-testid="skeleton-list-item"
    >
      <div
        className={cn(
          "w-10 h-10 bg-current rounded-full flex-shrink-0",
          animationClasses[animation],
        )}
        data-testid="skeleton-list-avatar"
      />
      <div className="flex-1 space-y-2" data-testid="skeleton-list-content">
        <div
          className={cn(
            "h-4 bg-current rounded w-1/4",
            animationClasses[animation],
          )}
        />
        <div
          className={cn(
            "h-3 bg-current rounded w-3/4",
            animationClasses[animation],
          )}
        />
      </div>
    </div>
  );

  const renderTableRow = () => (
    <div className="flex space-x-4" data-testid="skeleton-table-row">
      {Array.from({ length: columns }, (_, i) => (
        <div
          key={i}
          className={cn(
            "h-4 bg-current rounded flex-1",
            animationClasses[animation],
          )}
          data-testid="skeleton-table-cell"
        />
      ))}
    </div>
  );

  const renderParagraph = () => (
    <div className="space-y-2" data-testid="skeleton-paragraph">
      {renderTextLines()}
    </div>
  );

  const renderInput = () => (
    <div className="space-y-2">
      {withLabel && (
        <div
          className={cn(
            "h-4 bg-current rounded w-1/4",
            animationClasses[animation],
          )}
          data-testid="skeleton-input-label"
        />
      )}
      <div
        className={cn(
          "h-10 bg-current rounded w-full",
          animationClasses[animation],
        )}
        data-testid="skeleton-input-field"
      />
    </div>
  );

  const renderComplex = () => (
    <div className="space-y-4" data-testid="skeleton-complex">
      <div
        className={cn(
          "h-12 bg-current rounded w-full",
          animationClasses[animation],
        )}
        data-testid="skeleton-complex-header"
      />
      <div className="flex space-x-4">
        <div
          className={cn(
            "w-1/4 h-64 bg-current rounded",
            animationClasses[animation],
          )}
          data-testid="skeleton-complex-sidebar"
        />
        <div
          className="flex-1 space-y-3"
          data-testid="skeleton-complex-content"
        >
          <div
            className={cn(
              "h-6 bg-current rounded w-3/4",
              animationClasses[animation],
            )}
          />
          <div
            className={cn(
              "h-4 bg-current rounded w-full",
              animationClasses[animation],
            )}
          />
          <div
            className={cn(
              "h-4 bg-current rounded w-5/6",
              animationClasses[animation],
            )}
          />
          <div
            className={cn(
              "h-4 bg-current rounded w-2/3",
              animationClasses[animation],
            )}
          />
        </div>
      </div>
    </div>
  );

  const renderSkeletonContent = () => {
    if (card) return renderCard();
    if (listItem) return renderListItem();
    if (tableRow) return renderTableRow();
    if (paragraph) return renderParagraph();
    if (input) return renderInput();
    if (complex) return renderComplex();

    if (variant === "text" && lines > 1) {
      return renderTextLines();
    }

    return null;
  };

  const renderSingleSkeleton = (index?: number) => {
    const content = renderSkeletonContent();

    if (content) {
      return (
        <div
          key={index}
          className={cn(
            "skeleton-wrapper",
            sizeClasses[size],
            themeClasses[theme],
            intensityClasses[intensity],
            rounded && "rounded",
            shimmer && "shimmer",
            avatar && "avatar",
            image && "image",
            button && "button",
            responsive && "responsive",
            gradient && "gradient",
            randomAnimation && "random-animation",
            staggered && "staggered",
            transition && "transition",
            loading && "loading",
            className,
          )}
          style={{ ...getInlineStyles(), ...style }}
          aria-label={ariaLabel}
          aria-busy={loading}
          data-testid={count > 1 ? `${dataTestId}-${index}` : dataTestId}
          data-category={dataCategory}
          data-id={dataId}
          {...props}
        >
          {screenReaderText && (
            <span className="sr-only">{screenReaderText}</span>
          )}
          {content}
        </div>
      );
    }

    return (
      <div
        key={index}
        className={cn(
          "skeleton-container bg-current",
          sizeClasses[size],
          variantClasses[variant],
          animationClasses[animation],
          themeClasses[theme],
          intensityClasses[intensity],
          rounded && "rounded",
          shimmer && "shimmer",
          avatar && "avatar",
          image && "image",
          button && "button",
          responsive && "responsive",
          gradient && "gradient",
          randomAnimation && "random-animation",
          staggered && "staggered",
          transition && "transition",
          loading && "loading",
          className,
        )}
        style={{ ...getInlineStyles(), ...style }}
        aria-label={ariaLabel}
        aria-busy={loading}
        data-testid={count > 1 ? `${dataTestId}-${index}` : dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        {...props}
      >
        {screenReaderText && (
          <span className="sr-only">{screenReaderText}</span>
        )}
      </div>
    );
  };

  if (count > 1) {
    return (
      <>{Array.from({ length: count }, (_, i) => renderSingleSkeleton(i))}</>
    );
  }

  return renderSingleSkeleton();
};

export default Skeleton;
