import React from 'react';

interface RadioOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface RadioButtonProps {
  name: string;
  options: RadioOption[];
  value?: string;
  onChange: (value: string) => void;
  label?: string;
  error?: string;
  direction?: 'horizontal' | 'vertical';
}

export const RadioButton: React.FC<RadioButtonProps> = ({
  name,
  options,
  value,
  onChange,
  label,
  error,
  direction = 'vertical'
}) => {
  const hasError = !!error;
  const containerClass = direction === 'horizontal' 
    ? 'flex space-x-6' 
    : 'space-y-4';

  return (
    <div>
      {label && (
        <div className="text-sm font-medium text-gray-700 mb-3">
          {label}
        </div>
      )}
      
      <div className={containerClass}>
        {options.map((option) => (
          <div key={option.value} className="relative flex items-start">
            <div className="flex items-center h-5">
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                disabled={option.disabled}
                className={`
                  focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300
                  ${hasError ? 'border-red-300' : ''}
                  ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              />
            </div>
            <div className="ml-3 text-sm">
              <label className={`font-medium cursor-pointer ${hasError ? 'text-red-900' : 'text-gray-700'}`}>
                {option.label}
              </label>
              {option.description && (
                <p className={`${hasError ? 'text-red-600' : 'text-gray-500'}`}>
                  {option.description}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};