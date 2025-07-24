import React, { useState, useRef, forwardRef } from "react";

interface RadioProps {
  label?: string;
  value: string;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (value: string) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "success" | "warning" | "danger";
  color?: string;
  background?: string;
  rounded?: boolean;
  loading?: boolean;
  animate?: boolean;
  icon?: React.ReactNode;
  description?: string;
  error?: string;
  success?: string;
  warning?: string;
  tooltip?: string;
  labelPosition?: "left" | "right";
  card?: boolean;
  name?: string;
  className?: string;
  style?: React.CSSProperties;
  "aria-describedby"?: string;
  "aria-required"?: string;
  role?: string;
}

interface RadioGroupProps {
  children: React.ReactNode;
  label?: string;
  name: string;
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  error?: string;
  success?: string;
  warning?: string;
  description?: string;
  inline?: boolean;
  orientation?: "horizontal" | "vertical";
  spacing?: string;
  className?: string;
}

const RadioComponent = forwardRef<HTMLInputElement, RadioProps>(
  (
    {
      label,
      value,
      checked,
      defaultChecked,
      onChange,
      onFocus,
      onBlur,
      disabled = false,
      readonly = false,
      required = false,
      size = "md",
      variant = "primary",
      color,
      background,
      rounded = false,
      loading = false,
      animate = false,
      icon,
      description,
      error,
      success,
      warning,
      tooltip,
      labelPosition = "right",
      card = false,
      name,
      className = "",
      style,
      "aria-describedby": ariaDescribedBy,
      "aria-required": ariaRequired,
      role,
      ...props
    },
    ref,
  ) => {
    const [isChecked, setIsChecked] = useState(defaultChecked || false);
    const radioRef = useRef<HTMLInputElement>(null);

    const isControlled = checked !== undefined;
    const checkedState = isControlled ? checked : isChecked;

    const getSizeClasses = () => {
      const sizeMap = {
        sm: "w-4 h-4",
        md: "w-5 h-5",
        lg: "w-6 h-6",
      };
      return sizeMap[size];
    };

    const getVariantClasses = () => {
      if (error) return "border-red-500 text-red-600 focus:ring-red-500";
      if (success)
        return "border-green-500 text-green-600 focus:ring-green-500";
      if (warning)
        return "border-yellow-500 text-yellow-600 focus:ring-yellow-500";

      if (color) return `text-${color}-600 focus:ring-${color}-500`;

      const variantMap = {
        primary: "text-blue-600 focus:ring-blue-500",
        secondary: "text-gray-600 focus:ring-gray-500",
        success: "text-green-600 focus:ring-green-500",
        warning: "text-yellow-600 focus:ring-yellow-500",
        danger: "text-red-600 focus:ring-red-500",
      };

      return variantMap[variant];
    };

    const getStateClasses = () => {
      let classes = "";

      if (disabled) {
        classes += " opacity-50 cursor-not-allowed";
      } else {
        classes += " cursor-pointer hover:bg-gray-50";
      }

      if (animate) {
        classes += " transition-all duration-200";
      }

      if (rounded) {
        classes += " rounded-lg";
      }

      return classes;
    };

    const getFlexDirection = () => {
      return labelPosition === "left" ? "flex-row-reverse" : "flex-row";
    };

    const getCardClasses = () => {
      if (!card) return "";

      let cardClasses =
        "border rounded-lg p-4 hover:border-gray-400 transition-colors";

      if (checkedState) {
        cardClasses += " border-blue-500 bg-blue-50";
      }

      if (disabled) {
        cardClasses += " opacity-50 cursor-not-allowed";
      }

      return cardClasses;
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled || readonly) return;

      const newValue = e.target.value;

      if (!isControlled) {
        setIsChecked(true);
      }

      onChange?.(newValue);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === " ") {
        e.preventDefault();
        handleChange({
          target: { value },
        } as React.ChangeEvent<HTMLInputElement>);
      }
    };

    const radioId = `radio-${name || "radio"}-${value}`;

    const radioElement = (
      <div className="relative">
        <input
          ref={(node) => {
            radioRef.current = node;
            if (typeof ref === "function") {
              ref(node);
            } else if (ref) {
              ref.current = node;
            }
          }}
          id={radioId}
          type="radio"
          name={name}
          value={value}
          checked={checkedState}
          onChange={handleChange}
          onFocus={onFocus}
          onBlur={onBlur}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          readOnly={readonly}
          required={required}
          title={tooltip}
          aria-describedby={ariaDescribedBy}
          aria-required={ariaRequired}
          role={role}
          className={[
            getSizeClasses(),
            getVariantClasses(),
            getStateClasses(),
            "border-gray-300 bg-white focus:ring-2 focus:ring-offset-2",
          ].join(" ")}
          {...props}
        />

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <svg
              className="w-3 h-3 animate-spin text-current"
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
          </div>
        )}
      </div>
    );

    const labelElement = label && (
      <label
        htmlFor={radioId}
        className={`select-none ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"} ${labelPosition === "left" ? "mr-3" : "ml-3"}`}
      >
        <div className="flex items-center">
          {icon && <span className="mr-2">{icon}</span>}
          <span className="text-sm font-medium text-gray-900">{label}</span>
        </div>
        {description && (
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        )}
      </label>
    );

    const messageElement = (error || success || warning) && (
      <div className="mt-2">
        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-600">{success}</p>}
        {warning && <p className="text-sm text-yellow-600">{warning}</p>}
      </div>
    );

    const content = (
      <div
        className={["flex items-start", getFlexDirection(), background || ""]
          .filter(Boolean)
          .join(" ")}
      >
        {radioElement}
        {labelElement}
      </div>
    );

    return (
      <div className={className} style={style}>
        {card ? <div className={getCardClasses()}>{content}</div> : content}
        {messageElement}
      </div>
    );
  },
);

RadioComponent.displayName = "Radio";

const RadioGroup: React.FC<RadioGroupProps> = ({
  children,
  label,
  name,
  value,
  defaultValue,
  onChange,
  disabled = false,
  error,
  success,
  warning,
  description,
  inline = false,
  orientation = "vertical",
  spacing = "space-y-3",
  className = "",
}) => {
  const [selectedValue, setSelectedValue] = useState<string>(
    defaultValue || "",
  );

  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : selectedValue;

  const handleChildChange = (childValue: string) => {
    if (!isControlled) {
      setSelectedValue(childValue);
    }

    onChange?.(childValue);
  };

  const getGroupSpacing = () => {
    if (inline || orientation === "horizontal") {
      return spacing.replace("space-y-", "space-x-");
    }
    return spacing;
  };

  const getGroupDirection = () => {
    if (inline || orientation === "horizontal") {
      return "flex-row";
    }
    return "flex-col";
  };

  return (
    <div className={className}>
      {label && (
        <div className="mb-4">
          <h3 className="text-base font-medium text-gray-900">{label}</h3>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
      )}

      <div className={`flex ${getGroupDirection()} ${getGroupSpacing()}`}>
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child;

          const childValue = child.props.value;
          const isChecked = currentValue === childValue;

          return React.cloneElement(child as React.ReactElement<RadioProps>, {
            ...child.props,
            name: name,
            checked: isChecked,
            onChange: handleChildChange,
            disabled: disabled || child.props.disabled,
          });
        })}
      </div>

      {(error || success || warning) && (
        <div className="mt-3">
          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-green-600">{success}</p>}
          {warning && <p className="text-sm text-yellow-600">{warning}</p>}
        </div>
      )}
    </div>
  );
};

type RadioType = typeof RadioComponent & {
  Group: typeof RadioGroup;
};

const Radio = RadioComponent as RadioType;
Radio.Group = RadioGroup;

export { Radio };
export default Radio;
