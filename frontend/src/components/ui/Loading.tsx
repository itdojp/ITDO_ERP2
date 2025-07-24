import React, { useState, useEffect, useRef } from "react";

interface LoadingProps {
  children?: React.ReactNode;
  loading?: boolean;
  spinning?: boolean;
  size?: "small" | "medium" | "large";
  type?: "spinner" | "dots" | "bars" | "pulse" | "ring" | "wave" | "skeleton";
  color?: "blue" | "green" | "red" | "yellow" | "purple" | "gray";
  overlay?: boolean;
  fullPage?: boolean;
  centered?: boolean;
  inline?: boolean;
  backdrop?: boolean;
  delay?: number;
  minTime?: number;
  timeout?: number;
  duration?: number;
  opacity?: number;
  icon?: React.ReactNode;
  tip?: string;
  progress?: number | boolean;
  format?: string;
  state?: "loading" | "success" | "error";
  errorMessage?: string;
  successMessage?: string;
  wrapper?: React.ReactElement;
  className?: string;
  onComplete?: () => void;
  onFinish?: () => void;
  onTimeout?: () => void;
  onRetry?: () => void;
}

interface LoadingContentProps {
  children: React.ReactNode;
}

const LoadingComponent: React.FC<LoadingProps> = ({
  children,
  loading = true,
  spinning,
  size = "medium",
  type = "spinner",
  color = "blue",
  overlay = false,
  fullPage = false,
  centered = false,
  inline = false,
  backdrop = false,
  delay = 0,
  minTime = 0,
  timeout,
  duration = 1000,
  opacity = 0.5,
  icon,
  tip,
  progress,
  format = "{percent}%",
  state = "loading",
  errorMessage,
  successMessage,
  wrapper,
  className = "",
  onComplete,
  onFinish,
  onTimeout,
  onRetry,
}) => {
  const [visible, setVisible] = useState(delay === 0);
  const [showMinTime, setShowMinTime] = useState(true);
  const delayTimer = useRef<NodeJS.Timeout>();
  const minTimeTimer = useRef<NodeJS.Timeout>();
  const timeoutTimer = useRef<NodeJS.Timeout>();

  const isControlledSpinning = spinning !== undefined;
  const isSpinning = isControlledSpinning ? spinning : loading;

  useEffect(() => {
    if (delay > 0 && loading) {
      delayTimer.current = setTimeout(() => {
        setVisible(true);
      }, delay);
    } else {
      setVisible(loading);
    }

    return () => {
      if (delayTimer.current) {
        clearTimeout(delayTimer.current);
      }
    };
  }, [loading, delay]);

  useEffect(() => {
    if (minTime > 0 && !loading && visible) {
      minTimeTimer.current = setTimeout(() => {
        setShowMinTime(false);
        onFinish?.();
      }, minTime);
    } else if (!loading) {
      setShowMinTime(false);
      onFinish?.();
    }

    return () => {
      if (minTimeTimer.current) {
        clearTimeout(minTimeTimer.current);
      }
    };
  }, [loading, visible, minTime, onFinish]);

  useEffect(() => {
    if (timeout && visible) {
      timeoutTimer.current = setTimeout(() => {
        onTimeout?.();
      }, timeout);
    }

    return () => {
      if (timeoutTimer.current) {
        clearTimeout(timeoutTimer.current);
      }
    };
  }, [visible, timeout, onTimeout]);

  useEffect(() => {
    if (!loading && onComplete) {
      onComplete();
    }
  }, [loading, onComplete]);

  const getSizeClasses = () => {
    const sizeMap = {
      small: "w-4 h-4",
      medium: "w-6 h-6",
      large: "w-8 h-8",
    };
    return sizeMap[size];
  };

  const getColorClasses = () => {
    const colorMap = {
      blue: "text-blue-500",
      green: "text-green-500",
      red: "text-red-500",
      yellow: "text-yellow-500",
      purple: "text-purple-500",
      gray: "text-gray-500",
    };
    return colorMap[color];
  };

  const renderSpinner = () => {
    if (icon) return icon;

    const sizeClasses = getSizeClasses();
    const colorClasses = getColorClasses();

    switch (type) {
      case "spinner":
        return (
          <svg
            className={`${sizeClasses} ${colorClasses} animate-spin`}
            fill="none"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
            style={{ animationDuration: `${duration}ms` }}
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

      case "dots":
        return (
          <div className={`flex space-x-1 ${colorClasses}`}>
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`${size === "small" ? "w-2 h-2" : size === "large" ? "w-3 h-3" : "w-2.5 h-2.5"} bg-current rounded-full animate-pulse`}
                style={{
                  animationDelay: `${i * 200}ms`,
                  animationDuration: `${duration}ms`,
                }}
              />
            ))}
          </div>
        );

      case "bars":
        return (
          <div className={`flex items-end space-x-1 ${colorClasses}`}>
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`${size === "small" ? "w-1" : size === "large" ? "w-2" : "w-1.5"} bg-current animate-pulse`}
                style={{
                  height: `${12 + (i % 2) * 8}px`,
                  animationDelay: `${i * 150}ms`,
                  animationDuration: `${duration}ms`,
                }}
              />
            ))}
          </div>
        );

      case "pulse":
        return (
          <div
            className={`${sizeClasses} ${colorClasses} bg-current rounded-full animate-ping`}
            style={{ animationDuration: `${duration}ms` }}
          />
        );

      case "ring":
        return (
          <div className={`${sizeClasses} relative ${colorClasses}`}>
            <div className="absolute inset-0 border-2 border-current border-opacity-20 rounded-full" />
            <div
              className="absolute inset-0 border-2 border-transparent border-t-current rounded-full animate-spin"
              style={{ animationDuration: `${duration}ms` }}
            />
          </div>
        );

      case "wave":
        return (
          <div className={`flex items-center space-x-1 ${colorClasses}`}>
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={`${size === "small" ? "w-1 h-6" : size === "large" ? "w-2 h-10" : "w-1.5 h-8"} bg-current rounded-full animate-pulse`}
                style={{
                  animationDelay: `${i * 100}ms`,
                  animationDuration: `${duration}ms`,
                }}
              />
            ))}
          </div>
        );

      case "skeleton":
        return (
          <div
            data-testid="skeleton-loader"
            className="animate-pulse space-y-2"
          >
            <div className="h-4 bg-gray-300 rounded w-3/4" />
            <div className="h-4 bg-gray-300 rounded w-1/2" />
            <div className="h-4 bg-gray-300 rounded w-5/6" />
          </div>
        );

      default:
        return null;
    }
  };

  const renderProgress = () => {
    if (progress === false || progress === undefined) return null;

    const isIndeterminate = progress === true;
    const value = typeof progress === "number" ? progress : 0;
    const displayText = format.replace("{percent}", value.toString());

    return (
      <div className="mt-2 w-full">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{displayText}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              isIndeterminate
                ? "bg-blue-600 animate-pulse w-full"
                : `bg-blue-600`
            }`}
            style={!isIndeterminate ? { width: `${value}%` } : {}}
            role="progressbar"
            aria-valuenow={isIndeterminate ? undefined : value}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>
    );
  };

  const renderStateContent = () => {
    switch (state) {
      case "success":
        return (
          <div className="flex flex-col items-center text-green-600">
            <svg
              className="w-8 h-8 mb-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            {successMessage && <p>{successMessage}</p>}
          </div>
        );

      case "error":
        return (
          <div className="flex flex-col items-center text-red-600">
            <svg
              className="w-8 h-8 mb-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {errorMessage && <p className="mb-2">{errorMessage}</p>}
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        );

      default:
        return (
          <div className="flex flex-col items-center">
            {renderSpinner()}
            {tip && <p className="mt-2 text-sm text-gray-600">{tip}</p>}
            {renderProgress()}
          </div>
        );
    }
  };

  const shouldShow = visible && (loading || showMinTime);

  if (!shouldShow && !children) return null;

  const containerClasses = [
    "loading-component",
    inline ? "inline-flex items-center" : "flex",
    centered ? "justify-center items-center" : "",
    fullPage ? "fixed inset-0 z-50" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const overlayClasses = [
    "absolute inset-0 flex items-center justify-center",
    backdrop ? "bg-black" : "bg-white",
    "transition-opacity",
  ]
    .filter(Boolean)
    .join(" ");

  if (children && !fullPage) {
    return (
      <div className="relative" data-testid="loading-container">
        {children}
        {shouldShow && (
          <>
            {(overlay || backdrop) && (
              <div
                className={overlayClasses}
                style={{ opacity }}
                data-testid={backdrop ? "loading-backdrop" : "loading-overlay"}
              >
                {renderStateContent()}
              </div>
            )}
            {!overlay && !backdrop && (
              <div className="absolute inset-0 flex items-center justify-center">
                {renderStateContent()}
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  if (wrapper && children) {
    return React.cloneElement(wrapper, {
      children: (
        <>
          {children}
          {shouldShow && renderStateContent()}
        </>
      ),
    });
  }

  return (
    <div className={containerClasses} data-testid="loading-container">
      {(overlay || backdrop || fullPage) && (
        <div
          className={overlayClasses}
          style={{ opacity }}
          data-testid={backdrop ? "loading-backdrop" : "loading-overlay"}
        >
          {renderStateContent()}
        </div>
      )}
      {!overlay && !backdrop && !fullPage && renderStateContent()}
      {children}
    </div>
  );
};

const LoadingContent: React.FC<LoadingContentProps> = ({ children }) => {
  return <div className="loading-content">{children}</div>;
};

type LoadingType = typeof LoadingComponent & {
  Content: typeof LoadingContent;
};

const Loading = LoadingComponent as LoadingType;
Loading.Content = LoadingContent;

export { Loading };
export default Loading;
