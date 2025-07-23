import React from "react";

interface EmptyProps {
  children?: React.ReactNode;
  description?: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  image?: React.ReactNode;
  imageType?: "default" | "simple" | "search" | "generic" | false;
  imageUrl?: string;
  imageSize?: number;
  imageAlt?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  actions?: React.ReactNode[];
  extra?: React.ReactNode;
  footer?: React.ReactNode;
  helpText?: string;
  size?: "small" | "medium" | "large";
  theme?: "default" | "simple" | "minimal";
  align?: "left" | "center" | "right";
  padding?: "small" | "medium" | "large";
  centered?: boolean;
  inline?: boolean;
  background?: boolean;
  bordered?: boolean;
  animated?: boolean;
  responsive?: boolean;
  overlay?: boolean;
  loading?: boolean;
  error?: boolean;
  success?: boolean;
  errorMessage?: string;
  successMessage?: string;
  onRetry?: () => void;
  className?: string;
  style?: React.CSSProperties;
  [key: string]: any; // For custom data attributes
}

const Empty: React.FC<EmptyProps> = ({
  children,
  description = "No data",
  title,
  subtitle,
  image,
  imageType = "default",
  imageUrl,
  imageSize = 80,
  imageAlt = "Empty state",
  icon,
  action,
  actions,
  extra,
  footer,
  helpText,
  size = "medium",
  theme = "default",
  align = "center",
  padding = "medium",
  centered = false,
  inline = false,
  background = false,
  bordered = false,
  animated = false,
  responsive = false,
  overlay = false,
  loading = false,
  error = false,
  success = false,
  errorMessage = "Something went wrong",
  successMessage = "Success!",
  onRetry,
  className = "",
  style,
  ...props
}) => {
  const getSizeClasses = () => {
    const sizeMap = {
      small: {
        container: "p-4",
        image: "w-12 h-12",
        title: "text-base",
        description: "text-sm",
      },
      medium: {
        container: "p-6",
        image: "w-16 h-16",
        title: "text-lg",
        description: "text-base",
      },
      large: {
        container: "p-8",
        image: "w-20 h-20",
        title: "text-xl",
        description: "text-lg",
      },
    };
    return sizeMap[size];
  };

  const getPaddingClasses = () => {
    const paddingMap = {
      small: "p-4",
      medium: "p-6",
      large: "p-8",
    };
    return paddingMap[padding];
  };

  const getAlignClasses = () => {
    const alignMap = {
      left: "text-left items-start",
      center: "text-center items-center",
      right: "text-right items-end",
    };
    return alignMap[align];
  };

  const renderDefaultImage = () => {
    if (imageType === false) return null;
    if (image) return image;
    if (icon) return icon;
    if (imageUrl) {
      return (
        <img
          src={imageUrl}
          alt={imageAlt}
          style={{ width: imageSize, height: imageSize }}
          role="img"
          aria-hidden="true"
        />
      );
    }

    const sizeClasses = getSizeClasses();

    if (loading) {
      return (
        <svg
          className={`${sizeClasses.image} text-gray-400 animate-spin`}
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
      );
    }

    if (error) {
      return (
        <svg
          className={`${sizeClasses.image} text-red-400`}
          fill="currentColor"
          viewBox="0 0 20 20"
          role="img"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    if (success) {
      return (
        <svg
          className={`${sizeClasses.image} text-green-400`}
          fill="currentColor"
          viewBox="0 0 20 20"
          role="img"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    switch (imageType) {
      case "simple":
        return (
          <div
            className={`${sizeClasses.image} bg-gray-100 rounded-full flex items-center justify-center`}
          >
            <svg
              className="w-8 h-8 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
              role="img"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M3 4a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 2v8h10V6H5z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        );

      case "search":
        return (
          <svg
            className={`${sizeClasses.image} text-gray-400`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        );

      case "generic":
        return (
          <svg
            className={`${sizeClasses.image} text-gray-400`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        );

      default:
        return (
          <svg
            className={`${sizeClasses.image} text-gray-400`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        );
    }
  };

  const renderContent = () => {
    const sizeClasses = getSizeClasses();

    if (children) {
      return children;
    }

    const displayDescription = error
      ? errorMessage
      : success
        ? successMessage
        : description;

    return (
      <>
        {title && (
          <h3
            className={`${sizeClasses.title} font-semibold text-gray-900 mb-2`}
          >
            {title}
          </h3>
        )}

        {displayDescription && (
          <p className={`${sizeClasses.description} text-gray-600 mb-4`}>
            {displayDescription}
          </p>
        )}

        {subtitle && <p className="text-sm text-gray-500 mb-4">{subtitle}</p>}

        {(action || actions || (error && onRetry)) && (
          <div className="flex flex-wrap gap-2 justify-center">
            {error && onRetry && (
              <button
                onClick={onRetry}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Retry
              </button>
            )}
            {action}
            {actions?.map((actionItem, index) => (
              <React.Fragment key={index}>{actionItem}</React.Fragment>
            ))}
          </div>
        )}

        {extra && <div className="mt-4">{extra}</div>}

        {helpText && <p className="text-xs text-gray-500 mt-4">{helpText}</p>}

        {footer && <div className="mt-6">{footer}</div>}
      </>
    );
  };

  const containerClasses = [
    "empty-component",
    inline ? "inline-flex" : "flex flex-col",
    getAlignClasses(),
    centered ? "justify-center" : "",
    getPaddingClasses(),
    background ? "bg-gray-50" : "",
    bordered ? "border border-gray-200 rounded-lg" : "",
    animated ? "transition-all duration-300" : "",
    responsive ? "responsive-empty" : "",
    overlay ? "absolute inset-0 z-10 bg-white bg-opacity-90" : "",
    theme === "minimal" ? "minimal-theme" : "",
    theme === "simple" ? "simple-theme" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={containerClasses}
      style={style}
      data-testid="empty-container"
      {...props}
    >
      {!inline && renderDefaultImage()}

      <div className={inline ? "ml-3" : "mt-4"}>{renderContent()}</div>

      {inline && renderDefaultImage()}
    </div>
  );
};

export { Empty };
export default Empty;
