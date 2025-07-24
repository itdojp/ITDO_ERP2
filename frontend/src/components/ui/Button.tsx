import React, { forwardRef } from "react";

interface ButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "size"> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "link" | "danger";
  size?: "sm" | "md" | "lg" | "xl";
  loading?: boolean;
  disabled?: boolean;
  block?: boolean;
  shape?: "default" | "circle" | "round";
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  href?: string;
  target?: string;
  htmlType?: "button" | "submit" | "reset";
  className?: string;
  children?: React.ReactNode;
}

export const Button = forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  ButtonProps
>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      disabled = false,
      block = false,
      shape = "default",
      icon,
      iconPosition = "left",
      href,
      target,
      htmlType = "button",
      className = "",
      children,
      onClick,
      ...props
    },
    ref,
  ) => {
    const getVariantClasses = () => {
      const variantMap = {
        primary: `
        bg-blue-600 text-white border border-blue-600
        hover:bg-blue-700 hover:border-blue-700
        focus:bg-blue-700 focus:border-blue-700
        active:bg-blue-800 active:border-blue-800
        disabled:bg-blue-300 disabled:border-blue-300 disabled:cursor-not-allowed
      `,
        secondary: `
        bg-gray-100 text-gray-900 border border-gray-300
        hover:bg-gray-200 hover:border-gray-400
        focus:bg-gray-200 focus:border-gray-400
        active:bg-gray-300 active:border-gray-500
        disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed
      `,
        outline: `
        bg-transparent text-blue-600 border border-blue-600
        hover:bg-blue-50 hover:text-blue-700
        focus:bg-blue-50 focus:text-blue-700
        active:bg-blue-100 active:text-blue-800
        disabled:text-blue-300 disabled:border-blue-200 disabled:cursor-not-allowed
      `,
        ghost: `
        bg-transparent text-gray-600 border border-transparent
        hover:bg-gray-100 hover:text-gray-700
        focus:bg-gray-100 focus:text-gray-700
        active:bg-gray-200 active:text-gray-800
        disabled:text-gray-300 disabled:cursor-not-allowed
      `,
        link: `
        bg-transparent text-blue-600 border border-transparent
        hover:text-blue-700 hover:underline
        focus:text-blue-700 focus:underline
        active:text-blue-800
        disabled:text-blue-300 disabled:cursor-not-allowed disabled:no-underline
      `,
        danger: `
        bg-red-600 text-white border border-red-600
        hover:bg-red-700 hover:border-red-700
        focus:bg-red-700 focus:border-red-700
        active:bg-red-800 active:border-red-800
        disabled:bg-red-300 disabled:border-red-300 disabled:cursor-not-allowed
      `,
      };
      return variantMap[variant];
    };

    const getSizeClasses = () => {
      if (shape === "circle") {
        const circleSizeMap = {
          sm: "w-8 h-8 p-0",
          md: "w-10 h-10 p-0",
          lg: "w-12 h-12 p-0",
          xl: "w-14 h-14 p-0",
        };
        return circleSizeMap[size];
      }

      const sizeMap = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-4 py-2 text-sm",
        lg: "px-6 py-3 text-base",
        xl: "px-8 py-4 text-lg",
      };
      return sizeMap[size];
    };

    const getShapeClasses = () => {
      const shapeMap = {
        default: "rounded-md",
        circle: "rounded-full",
        round: "rounded-full",
      };
      return shapeMap[shape];
    };

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled) {
        event.preventDefault();
        return;
      }
      onClick?.(event);
    };

    const renderLoadingSpinner = () => (
      <div className="flex items-center justify-center">
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      </div>
    );

    const renderIcon = () => {
      if (loading) {
        return renderLoadingSpinner();
      }
      return icon;
    };

    const renderContent = () => {
      const hasChildren = React.Children.count(children) > 0;
      const iconElement = renderIcon();

      if (shape === "circle") {
        return iconElement || children;
      }

      if (!hasChildren && iconElement) {
        return iconElement;
      }

      if (!iconElement) {
        return children;
      }

      const iconSpacing =
        size === "sm"
          ? "gap-1.5"
          : size === "lg" || size === "xl"
            ? "gap-3"
            : "gap-2";

      return (
        <div className={`flex items-center justify-center ${iconSpacing}`}>
          {iconPosition === "left" && iconElement}
          {hasChildren && <span>{children}</span>}
          {iconPosition === "right" && iconElement}
        </div>
      );
    };

    const baseClasses = `
    inline-flex items-center justify-center font-medium transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
    ${getVariantClasses()}
    ${getSizeClasses()}
    ${getShapeClasses()}
    ${block ? "w-full" : ""}
    ${loading ? "pointer-events-none opacity-75" : ""}
    ${className}
  `;

    // Render as anchor if href is provided
    if (href && !disabled && !loading) {
      return (
        <a
          ref={ref as React.RefObject<HTMLAnchorElement>}
          href={href}
          target={target}
          className={baseClasses}
          role="button"
          {...(props as React.AnchorHTMLAttributes<HTMLAnchorElement>)}
        >
          {renderContent()}
        </a>
      );
    }

    // Render as button
    return (
      <button
        ref={ref as React.RefObject<HTMLButtonElement>}
        type={htmlType}
        disabled={disabled || loading}
        onClick={handleClick}
        className={baseClasses}
        aria-busy={loading}
        aria-disabled={disabled || loading}
        {...props}
      >
        {renderContent()}
      </button>
    );
  },
);

Button.displayName = "Button";

// Button.Group component
interface ButtonGroupProps {
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "primary" | "secondary" | "outline" | "ghost" | "link" | "danger";
  className?: string;
  vertical?: boolean;
}

const ButtonGroup: React.FC<ButtonGroupProps> = ({
  children,
  size,
  variant,
  className = "",
  vertical = false,
}) => {
  const groupClasses = `
    inline-flex
    ${vertical ? "flex-col" : "flex-row"}
    ${className}
  `;

  const clonedChildren = React.Children.map(children, (child, index) => {
    if (React.isValidElement(child) && child.type === Button) {
      const isFirst = index === 0;
      const isLast = index === React.Children.count(children) - 1;
      const isMiddle = !isFirst && !isLast;

      let roundedClasses = "";
      if (vertical) {
        if (isFirst) roundedClasses = "rounded-b-none";
        else if (isLast) roundedClasses = "rounded-t-none";
        else if (isMiddle) roundedClasses = "rounded-none";
      } else {
        if (isFirst) roundedClasses = "rounded-r-none";
        else if (isLast) roundedClasses = "rounded-l-none";
        else if (isMiddle) roundedClasses = "rounded-none";
      }

      const borderClasses = vertical
        ? isLast
          ? ""
          : "-mb-px"
        : isLast
          ? ""
          : "-mr-px";

      return React.cloneElement(child, {
        ...child.props,
        size: child.props.size || size,
        variant: child.props.variant || variant,
        className:
          `${child.props.className || ""} ${roundedClasses} ${borderClasses}`.trim(),
      });
    }
    return child;
  });

  return (
    <div className={groupClasses} role="group">
      {clonedChildren}
    </div>
  );
};

// Attach ButtonGroup as a static property
(Button as any).Group = ButtonGroup;

export default Button;
