import React, { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'filled' | 'outlined';
  inputSize?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'default',
  inputSize = 'md',
  fullWidth = true,
  className = '',
  ...props
}, ref) => {
  const baseClasses = `
    transition-colors duration-200 focus:outline-none
    ${fullWidth ? 'w-full' : ''}
    ${leftIcon ? 'pl-10' : ''}
    ${rightIcon ? 'pr-10' : ''}
  `;

  const variantClasses = {
    default: `
      border border-gray-300 rounded-md bg-white
      focus:ring-2 focus:ring-blue-500 focus:border-blue-500
      disabled:bg-gray-50 disabled:text-gray-500
    `,
    filled: `
      border-0 border-b-2 border-gray-300 rounded-t-md bg-gray-50
      focus:ring-0 focus:border-blue-500 focus:bg-white
      disabled:bg-gray-100 disabled:text-gray-500
    `,
    outlined: `
      border-2 border-gray-300 rounded-md bg-transparent
      focus:ring-0 focus:border-blue-500
      disabled:bg-gray-50 disabled:text-gray-500 disabled:border-gray-200
    `,
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-3 py-2.5 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  const errorClasses = error ? `
    border-red-300 focus:ring-red-500 focus:border-red-500
    ${variant === 'filled' ? 'focus:border-red-500' : ''}
    ${variant === 'outlined' ? 'border-red-300 focus:border-red-500' : ''}
  ` : '';

  const inputClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[inputSize]}
    ${errorClasses}
    ${className}
  `;

  return (
    <div className={fullWidth ? 'w-full' : 'inline-block'}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400">{leftIcon}</span>
          </div>
        )}
        
        <input
          ref={ref}
          className={inputClasses}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-gray-400">{rightIcon}</span>
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <div className="mt-1">
          {error ? (
            <p className="text-sm text-red-600 flex items-center">
              <svg className="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </p>
          ) : helperText ? (
            <p className="text-sm text-gray-500">{helperText}</p>
          ) : null}
        </div>
      )}
    </div>
  );
});