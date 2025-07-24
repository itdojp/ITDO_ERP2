import React, { useEffect, useRef } from "react";

interface StepData {
  title: string;
  description?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  content?: React.ReactNode;
  status?: "pending" | "active" | "completed" | "error";
  disabled?: boolean;
  type?: "navigation" | "inline";
}

interface StepperProps {
  steps: StepData[];
  current: number;
  onChange?: (step: number) => void;
  onStepValidate?: (step: number) => boolean;
  direction?: "horizontal" | "vertical";
  size?: "small" | "medium" | "large";
  showProgress?: boolean;
  className?: string;
  dot?: boolean;
  labelPlacement?: "horizontal" | "vertical";
  responsive?: boolean;
  alternating?: boolean;
  connector?: "solid" | "dashed" | "dotted";
  animated?: boolean;
  stepRender?: (step: StepData, index: number) => React.ReactNode;
}

const Stepper: React.FC<StepperProps> = ({
  steps,
  current,
  onChange,
  onStepValidate,
  direction = "horizontal",
  size = "medium",
  showProgress = false,
  className = "",
  dot = false,
  labelPlacement = "horizontal",
  responsive = false,
  alternating = false,
  connector = "solid",
  animated = false,
  stepRender,
}) => {
  const stepperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (animated && stepperRef.current) {
      stepperRef.current.classList.add("animate-fade-in");
    }
  }, [animated]);

  const getSizeClasses = () => {
    const sizeMap = {
      small: {
        step: "w-6 h-6 text-xs",
        title: "text-sm",
        description: "text-xs",
      },
      medium: {
        step: "w-8 h-8 text-sm",
        title: "text-base",
        description: "text-sm",
      },
      large: {
        step: "w-10 h-10 text-base",
        title: "text-lg",
        description: "text-base",
      },
    };
    return sizeMap[size];
  };

  const getStepStatus = (index: number, step: StepData) => {
    if (step.status) return step.status;
    if (index < current) return "completed";
    if (index === current) return "active";
    return "pending";
  };

  const getStepClasses = (index: number, step: StepData) => {
    const status = getStepStatus(index, step);
    const sizeClasses = getSizeClasses();

    const baseClasses = [
      "rounded-full border-2 flex items-center justify-center font-medium transition-all duration-200",
      sizeClasses.step,
    ];

    const statusClasses = {
      completed: "bg-green-500 border-green-500 text-white",
      active: "bg-blue-500 border-blue-500 text-white",
      error: "bg-red-500 border-red-500 text-white",
      pending: "bg-gray-100 border-gray-300 text-gray-500",
    };

    if (step.disabled) {
      baseClasses.push("opacity-50 cursor-not-allowed");
    } else if (onChange && !step.disabled) {
      baseClasses.push("cursor-pointer hover:scale-105");
    }

    return [...baseClasses, statusClasses[status]].join(" ");
  };

  const getConnectorClasses = () => {
    const connectorMap = {
      solid: "border-solid",
      dashed: "border-dashed",
      dotted: "border-dotted",
    };

    const baseClasses = [
      "flex-1 border-t-2 border-gray-300",
      connectorMap[connector],
    ];

    if (direction === "vertical") {
      return baseClasses
        .join(" ")
        .replace("border-t-2", "border-l-2 h-8 w-0 ml-4");
    }

    return baseClasses.join(" ");
  };

  const handleStepClick = (index: number, step: StepData) => {
    if (!onChange || step.disabled) return;

    if (onStepValidate && current < index) {
      if (!onStepValidate(current)) {
        return;
      }
    }

    onChange(index);
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (!onChange) return;

    let newIndex = index;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      newIndex = Math.min(steps.length - 1, index + 1);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      newIndex = Math.max(0, index - 1);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleStepClick(index, steps[index]);
      return;
    }

    if (newIndex !== index && !steps[newIndex].disabled) {
      onChange(newIndex);
    }
  };

  const renderStepIcon = (step: StepData, index: number) => {
    const status = getStepStatus(index, step);

    if (step.icon) {
      return step.icon;
    }

    if (dot) {
      return <div className="w-3 h-3 rounded-full bg-current" />;
    }

    if (status === "completed") {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    if (status === "error") {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    return index + 1;
  };

  const renderStepContent = (step: StepData, index: number) => {
    if (stepRender) {
      return stepRender(step, index);
    }

    const sizeClasses = getSizeClasses();
    const isVerticalLabels =
      labelPlacement === "vertical" || direction === "vertical";
    const isAlternating =
      alternating && direction === "horizontal" && index % 2 === 1;

    return (
      <div
        className={`flex ${isVerticalLabels ? "flex-col items-center" : "items-center"} ${isAlternating ? "flex-col-reverse" : ""}`}
      >
        <div
          className={getStepClasses(index, step)}
          onClick={() => handleStepClick(index, step)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          tabIndex={onChange && !step.disabled ? 0 : -1}
          role="button"
          aria-current={index === current ? "step" : undefined}
          aria-disabled={step.disabled}
        >
          {renderStepIcon(step, index)}
        </div>

        <div
          className={`${isVerticalLabels ? "mt-2 text-center" : "ml-3"} ${isAlternating ? "mb-2" : ""}`}
        >
          <div
            className={`font-medium ${sizeClasses.title} ${getStepStatus(index, step) === "active" ? "text-blue-600" : "text-gray-900"}`}
          >
            {step.title}
          </div>
          {step.subtitle && (
            <div className={`${sizeClasses.description} text-gray-500 mt-1`}>
              {step.subtitle}
            </div>
          )}
          {step.description && (
            <div className={`${sizeClasses.description} text-gray-500 mt-1`}>
              {step.description}
            </div>
          )}
          {step.content && <div className="mt-2">{step.content}</div>}
        </div>
      </div>
    );
  };

  const renderConnector = (index: number) => {
    if (index === steps.length - 1) return null;

    const isCompleted = index < current;
    const connectorClasses = getConnectorClasses();

    return (
      <div
        className={`${connectorClasses} ${isCompleted ? "border-green-500" : ""}`}
      />
    );
  };

  const progressPercentage = Math.round(((current + 1) / steps.length) * 100);

  const containerClasses = [
    "stepper",
    direction === "vertical" ? "flex flex-col" : "flex items-center",
    responsive ? "responsive" : "",
    animated ? "transition-all duration-300" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={stepperRef} className={containerClasses}>
      {showProgress && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
              role="progressbar"
              aria-valuenow={progressPercentage}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
      )}

      <div
        className={
          direction === "vertical"
            ? "space-y-4"
            : "flex items-center space-x-4 w-full"
        }
      >
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <div className={direction === "vertical" ? "flex items-start" : ""}>
              {renderStepContent(step, index)}
            </div>
            {direction === "horizontal" && renderConnector(index)}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export { Stepper };
export default Stepper;
