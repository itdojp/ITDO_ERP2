import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' | 'outline';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  children,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className = '',
  ...props
}) => {
  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-md
    transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${fullWidth ? 'w-full' : ''}
  `;

  const variantClasses = {
    primary: `
      bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500
      disabled:hover:bg-blue-600
    `,
    secondary: `
      bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500
      disabled:hover:bg-gray-600
    `,
    success: `
      bg-green-600 text-white hover:bg-green-700 focus:ring-green-500
      disabled:hover:bg-green-600
    `,
    warning: `
      bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500
      disabled:hover:bg-yellow-600
    `,
    error: `
      bg-red-600 text-white hover:bg-red-700 focus:ring-red-500
      disabled:hover:bg-red-600
    `,
    ghost: `
      text-gray-700 hover:bg-gray-100 focus:ring-gray-500
      disabled:hover:bg-transparent
    `,
    outline: `
      border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500
      disabled:hover:bg-transparent
    `,
  };

  const sizeClasses = {
    xs: 'px-2.5 py-1.5 text-xs gap-1.5',
    sm: 'px-3 py-2 text-sm gap-2',
    md: 'px-4 py-2.5 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
    xl: 'px-8 py-4 text-lg gap-3',
  };

  const finalClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${className}
  `;

  const isDisabled = disabled || loading;

  return (
    <button
      className={finalClasses}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
      ) : (
        leftIcon && <span className="flex-shrink-0">{leftIcon}</span>
      )}
      
      <span>{children}</span>
      
      {!loading && rightIcon && (
        <span className="flex-shrink-0">{rightIcon}</span>
      )}
    </button>
  );
};