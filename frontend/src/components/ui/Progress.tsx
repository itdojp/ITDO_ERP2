import React, { useEffect, useState, useRef } from "react";

interface ProgressSegment {
  value: number;
  color?: string;
  label?: string;
}

interface ProgressProps {
  value?: number;
  min?: number;
  max?: number;
  buffer?: number;
  type?: "line" | "circle" | "steps";
  size?: "sm" | "md" | "lg";
  color?: "primary" | "success" | "warning" | "danger";
  status?: "normal" | "success" | "error" | "warning";
  showText?: boolean;
  text?: string;
  textFormatter?: (value: number, max: number) => string;
  label?: string;
  description?: string;
  striped?: boolean;
  animated?: boolean;
  indeterminate?: boolean;
  vertical?: boolean;
  loading?: boolean;
  className?: string;
  trackStyle?: React.CSSProperties;
  barStyle?: React.CSSProperties;
  trackColor?: string;
  circleSize?: number;
  strokeWidth?: number;
  gradient?: string[];
  segments?: ProgressSegment[];
  thresholds?: number[];
  icon?: React.ReactNode;
  onComplete?: () => void;
  "aria-label"?: string;
  "aria-describedby"?: string;
  "aria-labelledby"?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value = 0,
  min = 0,
  max = 100,
  buffer,
  type = "line",
  size = "md",
  color = "primary",
  status = "normal",
  showText = true,
  text,
  textFormatter,
  label,
  description,
  striped = false,
  animated = false,
  indeterminate = false,
  vertical = false,
  loading = false,
  className = "",
  trackStyle,
  barStyle,
  trackColor = "bg-gray-200",
  circleSize = 120,
  strokeWidth = 6,
  gradient,
  segments,
  thresholds,
  icon,
  onComplete,
  "aria-label": ariaLabel,
  "aria-describedby": ariaDescribedBy,
  "aria-labelledby": ariaLabelledBy,
}) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const prevValueRef = useRef(value);

  const normalizedValue = Math.min(Math.max(value, min), max);
  const percentage = ((normalizedValue - min) / (max - min)) * 100;
  const bufferPercentage = buffer
    ? ((Math.min(Math.max(buffer, min), max) - min) / (max - min)) * 100
    : 0;

  useEffect(() => {
    if (animated && !indeterminate) {
      const timer = setTimeout(() => {
        setAnimatedValue(percentage);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setAnimatedValue(percentage);
    }
  }, [percentage, animated, indeterminate]);

  useEffect(() => {
    if (prevValueRef.current < max && normalizedValue === max && onComplete) {
      onComplete();
    }
    prevValueRef.current = normalizedValue;
  }, [normalizedValue, max, onComplete]);

  const getSizeClasses = () => {
    const sizeMap = {
      sm: "h-1",
      md: "h-2",
      lg: "h-4",
    };
    return sizeMap[size];
  };

  const getColorClasses = () => {
    if (status === "success") return "bg-green-500";
    if (status === "error") return "bg-red-500";
    if (status === "warning") return "bg-yellow-500";

    const colorMap = {
      primary: "bg-blue-500",
      success: "bg-green-500",
      warning: "bg-yellow-500",
      danger: "bg-red-500",
    };
    return colorMap[color];
  };

  const getStripedClasses = () => {
    if (!striped) return "";
    return "bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:20px_20px]";
  };

  const getAnimationClasses = () => {
    if (indeterminate) return "animate-pulse";
    if (animated) return "transition-all duration-300 ease-out";
    return "";
  };

  const formatText = () => {
    if (text) return text;
    if (textFormatter) return textFormatter(normalizedValue, max);
    return `${Math.round(percentage)}%`;
  };

  const renderLineProgress = () => {
    return (
      <div
        className={`
          relative w-full ${getSizeClasses()} ${trackColor} rounded-full overflow-hidden
          ${vertical ? "h-32 w-2" : ""}
          ${className}
        `}
        style={trackStyle}
      >
        {buffer && (
          <div
            data-testid="progress-buffer"
            className={`absolute inset-0 bg-gray-300 rounded-full ${vertical ? "w-full" : "h-full"}`}
            style={
              vertical
                ? { height: `${bufferPercentage}%`, bottom: 0 }
                : { width: `${bufferPercentage}%` }
            }
          />
        )}

        {segments ? (
          <div className="flex h-full">
            {segments.map((segment, index) => {
              const segmentPercentage = (segment.value / max) * 100;
              return (
                <div
                  key={index}
                  className={`h-full ${segment.color || getColorClasses()}`}
                  style={{ width: `${segmentPercentage}%` }}
                />
              );
            })}
          </div>
        ) : (
          <div
            role="progressbar"
            aria-valuenow={normalizedValue}
            aria-valuemin={min}
            aria-valuemax={max}
            aria-label={ariaLabel}
            aria-describedby={ariaDescribedBy}
            aria-labelledby={ariaLabelledBy}
            className={`
              h-full rounded-full transition-all duration-300
              ${getColorClasses()}
              ${getStripedClasses()}
              ${getAnimationClasses()}
            `}
            style={{
              [vertical ? "height" : "width"]: `${animatedValue}%`,
              ...(vertical && {
                position: "absolute",
                bottom: 0,
                width: "100%",
              }),
              ...(gradient && {
                backgroundImage: `linear-gradient(90deg, ${gradient.join(", ")})`,
              }),
              ...barStyle,
            }}
          />
        )}

        {thresholds?.map((threshold, index) => {
          const thresholdPercentage = ((threshold - min) / (max - min)) * 100;
          return (
            <div
              key={index}
              data-testid="progress-threshold"
              className="absolute w-0.5 h-full bg-gray-600"
              style={
                vertical
                  ? {
                      bottom: `${thresholdPercentage}%`,
                      width: "100%",
                      height: "1px",
                    }
                  : { left: `${thresholdPercentage}%` }
              }
            />
          );
        })}
      </div>
    );
  };

  const renderCircleProgress = () => {
    const radius = (circleSize - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const strokeDashoffset =
      circumference - (animatedValue / 100) * circumference;

    return (
      <svg
        width={circleSize}
        height={circleSize}
        className="transform -rotate-90"
        role="progressbar"
        aria-valuenow={normalizedValue}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-labelledby={ariaLabelledBy}
      >
        <circle
          cx={circleSize / 2}
          cy={circleSize / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-gray-200"
        />
        <circle
          cx={circleSize / 2}
          cy={circleSize / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={`${getColorClasses().replace("bg-", "text-")} transition-all duration-300 ease-out`}
          strokeLinecap="round"
        />
        {showText && (
          <text
            x={circleSize / 2}
            y={circleSize / 2}
            dy="0.35em"
            textAnchor="middle"
            className="text-sm font-semibold transform rotate-90"
            fill="currentColor"
          >
            {formatText()}
          </text>
        )}
      </svg>
    );
  };

  const renderStepsProgress = () => {
    const steps = Array.from({ length: max }, (_, index) => {
      const stepNumber = index + 1;
      const isActive = stepNumber <= normalizedValue;
      const isCompleted = stepNumber < normalizedValue;

      return (
        <div
          key={index}
          data-testid="progress-step"
          className={`
            w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold
            ${isActive ? getColorClasses() : "bg-gray-200"}
            ${isCompleted ? "bg-green-500" : ""}
          `}
        >
          {isCompleted ? "✓" : stepNumber}
        </div>
      );
    });

    return (
      <div
        role="progressbar"
        aria-valuenow={normalizedValue}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-labelledby={ariaLabelledBy}
        className="flex space-x-2"
      >
        {steps}
      </div>
    );
  };

  const renderProgress = () => {
    if (type === "circle") return renderCircleProgress();
    if (type === "steps") return renderStepsProgress();
    return renderLineProgress();
  };

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div
          className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
          role="img"
          aria-hidden="true"
        />
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {icon && <span className="flex-shrink-0">{icon}</span>}
        </div>
      )}

      <div
        className={`relative ${vertical ? "flex flex-col items-center" : "flex items-center"} space-x-3`}
      >
        <div className="flex-1">{renderProgress()}</div>

        {showText && type === "line" && (
          <span className="text-sm font-medium text-gray-700 whitespace-nowrap">
            {formatText()}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1 text-xs text-gray-500">{description}</p>
      )}
    </div>
  );
};

export default Progress;
