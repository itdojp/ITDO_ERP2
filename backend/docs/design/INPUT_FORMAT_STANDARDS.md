# Input Format Standards and Validation Guidelines

**Document ID**: ITDO-ERP-DD-IFS-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

This document defines the comprehensive input format standards and validation guidelines for the ITDO ERP2 UI components. These standards ensure consistency, accessibility, and data integrity across all user input interfaces.

## 2. Input Field Standards

### 2.1 General Input Field Requirements

#### 2.1.1 Visual Design Standards
```typescript
interface InputVisualStandards {
  height: {
    sm: '32px',
    md: '40px',
    lg: '48px'
  };
  padding: {
    sm: '6px 12px',
    md: '8px 16px',
    lg: '12px 20px'
  };
  borderRadius: {
    sm: '4px',
    md: '6px',
    lg: '8px'
  };
  borderWidth: '1px';
  fontSize: {
    sm: '14px',
    md: '16px',
    lg: '18px'
  };
  minTouchTarget: '44px'; // For accessibility
}
```

#### 2.1.2 State-Based Styling
```typescript
interface InputStates {
  default: {
    border: '#e5e7eb',
    background: '#ffffff',
    text: '#111827',
    placeholder: '#9ca3af'
  };
  focus: {
    border: '#3b82f6',
    background: '#ffffff',
    text: '#111827',
    shadow: '0 0 0 3px rgba(59, 130, 246, 0.1)'
  };
  error: {
    border: '#ef4444',
    background: '#fef2f2',
    text: '#111827',
    shadow: '0 0 0 3px rgba(239, 68, 68, 0.1)'
  };
  disabled: {
    border: '#d1d5db',
    background: '#f9fafb',
    text: '#6b7280',
    cursor: 'not-allowed'
  };
  readonly: {
    border: '#e5e7eb',
    background: '#f9fafb',
    text: '#374151',
    cursor: 'default'
  };
}
```

### 2.2 Input Type Specifications

#### 2.2.1 Text Input
```typescript
interface TextInputProps {
  type: 'text';
  placeholder?: string;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  autoComplete?: string;
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  spellCheck?: boolean;
}

// Validation Rules
const textInputValidation = {
  required: 'This field is required',
  minLength: (min: number) => `Must be at least ${min} characters`,
  maxLength: (max: number) => `Must not exceed ${max} characters`,
  pattern: (pattern: string) => `Must match required format`,
};
```

#### 2.2.2 Email Input
```typescript
interface EmailInputProps {
  type: 'email';
  placeholder?: string;
  autoComplete: 'email';
  multiple?: boolean; // For multiple email addresses
}

// Validation Rules
const emailValidation = {
  required: 'Email address is required',
  format: 'Please enter a valid email address',
  multiple: 'Please enter valid email addresses separated by commas',
};

// Email Pattern
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
```

#### 2.2.3 Password Input
```typescript
interface PasswordInputProps {
  type: 'password';
  placeholder?: string;
  autoComplete?: 'current-password' | 'new-password';
  showToggle?: boolean; // Show/hide password toggle
  strengthIndicator?: boolean; // Password strength indicator
  minLength?: number;
  maxLength?: number;
}

// Password Strength Requirements
const passwordStrength = {
  weak: {
    minLength: 8,
    requirements: ['lowercase', 'uppercase', 'number']
  },
  medium: {
    minLength: 10,
    requirements: ['lowercase', 'uppercase', 'number', 'special']
  },
  strong: {
    minLength: 12,
    requirements: ['lowercase', 'uppercase', 'number', 'special', 'noCommon']
  }
};
```

#### 2.2.4 Number Input
```typescript
interface NumberInputProps {
  type: 'number';
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  precision?: number; // Decimal places
  thousandSeparator?: boolean;
  currencySymbol?: string;
  unit?: string;
}

// Validation Rules
const numberValidation = {
  required: 'This field is required',
  min: (min: number) => `Must be at least ${min}`,
  max: (max: number) => `Must not exceed ${max}`,
  step: (step: number) => `Must be a multiple of ${step}`,
  integer: 'Must be a whole number',
  positive: 'Must be a positive number',
  negative: 'Must be a negative number',
};
```

#### 2.2.5 Date Input
```typescript
interface DateInputProps {
  type: 'date';
  min?: string; // ISO date format
  max?: string; // ISO date format
  format?: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';
  placeholder?: string;
  showCalendar?: boolean;
  disabledDates?: string[];
  highlightedDates?: string[];
}

// Date Validation
const dateValidation = {
  required: 'Please select a date',
  min: (min: string) => `Date must be on or after ${min}`,
  max: (max: string) => `Date must be on or before ${max}`,
  format: 'Please enter a valid date',
  business: 'Please select a business day',
  future: 'Please select a future date',
  past: 'Please select a past date',
};
```

#### 2.2.6 Search Input
```typescript
interface SearchInputProps {
  type: 'search';
  placeholder?: string;
  debounceMs?: number;
  clearable?: boolean;
  suggestions?: string[];
  minQueryLength?: number;
  maxResults?: number;
  onSearch?: (query: string) => void;
  onClear?: () => void;
}

// Search Behavior
const searchBehavior = {
  debounceDelay: 300, // milliseconds
  minQueryLength: 2,
  maxResults: 10,
  highlightMatches: true,
  showRecentSearches: true,
};
```

## 3. Form Validation Standards

### 3.1 Validation Types

#### 3.1.1 Client-Side Validation
```typescript
interface ValidationRules {
  required?: boolean | string;
  minLength?: number | { value: number; message: string };
  maxLength?: number | { value: number; message: string };
  pattern?: RegExp | { value: RegExp; message: string };
  validate?: (value: any) => boolean | string;
  custom?: (value: any) => Promise<boolean | string>;
}

// Example Usage
const userFormValidation = {
  email: {
    required: 'Email is required',
    pattern: {
      value: EMAIL_REGEX,
      message: 'Please enter a valid email address'
    }
  },
  password: {
    required: 'Password is required',
    minLength: {
      value: 8,
      message: 'Password must be at least 8 characters'
    },
    validate: (value: string) => {
      const hasUppercase = /[A-Z]/.test(value);
      const hasLowercase = /[a-z]/.test(value);
      const hasNumber = /\d/.test(value);
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value);
      
      if (!hasUppercase) return 'Password must contain uppercase letter';
      if (!hasLowercase) return 'Password must contain lowercase letter';
      if (!hasNumber) return 'Password must contain number';
      if (!hasSpecial) return 'Password must contain special character';
      
      return true;
    }
  }
};
```

#### 3.1.2 Server-Side Validation
```typescript
interface ServerValidationResponse {
  success: boolean;
  errors?: {
    field: string;
    message: string;
    code: string;
  }[];
  data?: any;
}

// Example Server Response
const serverValidationExample = {
  success: false,
  errors: [
    {
      field: 'email',
      message: 'Email address is already in use',
      code: 'EMAIL_DUPLICATE'
    },
    {
      field: 'username',
      message: 'Username must be unique',
      code: 'USERNAME_DUPLICATE'
    }
  ]
};
```

### 3.2 Validation Timing

#### 3.2.1 Real-Time Validation
```typescript
interface ValidationTiming {
  onBlur: boolean;     // Validate when field loses focus
  onChange: boolean;   // Validate on every keystroke
  onSubmit: boolean;   // Validate on form submission
  debounced: boolean;  // Debounce validation to avoid excessive calls
}

// Field-Specific Timing
const fieldValidationTiming = {
  email: {
    onBlur: true,
    onChange: false,
    onSubmit: true,
    debounced: true,
    debounceMs: 500
  },
  password: {
    onBlur: true,
    onChange: true,
    onSubmit: true,
    debounced: false
  },
  search: {
    onBlur: false,
    onChange: true,
    onSubmit: false,
    debounced: true,
    debounceMs: 300
  }
};
```

### 3.3 Error Message Standards

#### 3.3.1 Message Structure
```typescript
interface ErrorMessage {
  field: string;
  message: string;
  type: 'required' | 'format' | 'length' | 'custom' | 'server';
  priority: 'high' | 'medium' | 'low';
  suggestion?: string;
}

// Error Message Templates
const errorMessages = {
  required: (fieldName: string) => `${fieldName} is required`,
  email: 'Please enter a valid email address',
  password: {
    minLength: 'Password must be at least 8 characters',
    uppercase: 'Password must contain at least one uppercase letter',
    lowercase: 'Password must contain at least one lowercase letter',
    number: 'Password must contain at least one number',
    special: 'Password must contain at least one special character'
  },
  date: {
    invalid: 'Please enter a valid date',
    past: 'Date cannot be in the past',
    future: 'Date cannot be in the future'
  },
  number: {
    invalid: 'Please enter a valid number',
    min: (min: number) => `Must be at least ${min}`,
    max: (max: number) => `Must not exceed ${max}`
  }
};
```

#### 3.3.2 Error Display Standards
```typescript
interface ErrorDisplayProps {
  position: 'below' | 'above' | 'inline' | 'tooltip';
  icon: boolean;
  color: string;
  animation: 'fade' | 'slide' | 'none';
  persistance: 'until-valid' | 'until-focus' | 'timeout';
  grouping: boolean; // Group related errors
}

// Error Display Configuration
const errorDisplay = {
  position: 'below',
  icon: true,
  color: '#ef4444',
  animation: 'fade',
  persistance: 'until-valid',
  fontSize: '14px',
  marginTop: '4px',
  lineHeight: '1.4'
};
```

## 4. Accessibility Standards

### 4.1 ARIA Attributes

#### 4.1.1 Required ARIA Labels
```typescript
interface ARIAAttributes {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-required'?: boolean;
  'aria-invalid'?: boolean;
  'aria-errormessage'?: string;
  'aria-autocomplete'?: 'none' | 'inline' | 'list' | 'both';
  'aria-expanded'?: boolean;
  'aria-haspopup'?: boolean;
}

// Example Implementation
const accessibleInput = {
  'aria-label': 'Email address',
  'aria-describedby': 'email-help',
  'aria-required': true,
  'aria-invalid': false,
  'aria-errormessage': 'email-error'
};
```

#### 4.1.2 Label Association
```typescript
interface LabelAssociation {
  htmlFor: string;        // Explicit label association
  'aria-labelledby': string; // Multiple label references
  'aria-describedby': string; // Help text association
}

// Example Structure
const labelStructure = `
<label htmlFor="email-input" className="form-label">
  Email Address <span className="required">*</span>
</label>
<input 
  id="email-input"
  type="email"
  aria-describedby="email-help email-error"
  aria-required="true"
  aria-invalid={hasError}
/>
<div id="email-help" className="help-text">
  We'll never share your email with anyone else.
</div>
<div id="email-error" className="error-message" aria-live="polite">
  {errorMessage}
</div>
`;
```

### 4.2 Keyboard Navigation

#### 4.2.1 Tab Order
```typescript
interface TabOrder {
  tabIndex: number;
  skipLink?: boolean;
  trapFocus?: boolean;
  initialFocus?: boolean;
}

// Tab Order Standards
const tabOrderStandards = {
  formFields: {
    tabIndex: 0,
    naturalOrder: true,
    skipDisabled: true
  },
  submitButton: {
    tabIndex: 0,
    position: 'last'
  },
  cancelButton: {
    tabIndex: 0,
    position: 'beforeSubmit'
  }
};
```

#### 4.2.2 Keyboard Shortcuts
```typescript
interface KeyboardShortcuts {
  submit: 'Enter' | 'Ctrl+Enter';
  cancel: 'Escape';
  clear: 'Ctrl+K';
  save: 'Ctrl+S';
  search: 'Ctrl+F' | '/';
}

// Implementation
const keyboardHandlers = {
  onKeyDown: (e: KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
        if (e.ctrlKey || e.metaKey) {
          handleSubmit();
        }
        break;
      case 'Escape':
        handleCancel();
        break;
      case 'k':
        if (e.ctrlKey || e.metaKey) {
          handleClear();
          e.preventDefault();
        }
        break;
    }
  }
};
```

### 4.3 Screen Reader Support

#### 4.3.1 Announcements
```typescript
interface ScreenReaderAnnouncements {
  errorMessages: 'polite' | 'assertive';
  statusUpdates: 'polite' | 'assertive';
  formSubmission: 'polite' | 'assertive';
  validationSuccess: 'polite' | 'assertive';
}

// Live Region Configuration
const liveRegions = {
  errorMessages: {
    'aria-live': 'polite',
    'aria-atomic': true,
    'aria-relevant': 'additions text'
  },
  statusUpdates: {
    'aria-live': 'polite',
    'aria-atomic': false,
    'aria-relevant': 'additions'
  },
  alerts: {
    'aria-live': 'assertive',
    'aria-atomic': true,
    'aria-relevant': 'additions text'
  }
};
```

## 5. Form Layout Standards

### 5.1 Form Structure

#### 5.1.1 Vertical Layout
```typescript
interface VerticalFormLayout {
  spacing: {
    fieldGap: '16px',
    groupGap: '24px',
    sectionGap: '32px'
  };
  labelPosition: 'above';
  alignment: 'left';
  maxWidth: '400px';
}

// CSS Classes
const verticalFormClasses = {
  form: 'space-y-6',
  fieldGroup: 'space-y-4',
  field: 'space-y-2',
  label: 'block text-sm font-medium text-gray-700',
  input: 'block w-full px-3 py-2 border border-gray-300 rounded-md',
  error: 'mt-1 text-sm text-red-600'
};
```

#### 5.1.2 Horizontal Layout
```typescript
interface HorizontalFormLayout {
  spacing: {
    fieldGap: '16px',
    groupGap: '24px',
    sectionGap: '32px'
  };
  labelPosition: 'left';
  labelWidth: '140px';
  alignment: 'top';
}

// CSS Classes
const horizontalFormClasses = {
  form: 'space-y-6',
  fieldGroup: 'space-y-4',
  field: 'flex items-start space-x-4',
  label: 'flex-shrink-0 w-35 pt-2 text-sm font-medium text-gray-700',
  inputWrapper: 'flex-1 min-w-0',
  input: 'block w-full px-3 py-2 border border-gray-300 rounded-md',
  error: 'mt-1 text-sm text-red-600'
};
```

### 5.2 Responsive Behavior

#### 5.2.1 Breakpoint Adaptations
```typescript
interface ResponsiveFormBehavior {
  mobile: {
    layout: 'vertical';
    columns: 1;
    padding: '16px';
    spacing: '12px';
  };
  tablet: {
    layout: 'vertical';
    columns: 2;
    padding: '24px';
    spacing: '16px';
  };
  desktop: {
    layout: 'horizontal';
    columns: 2;
    padding: '32px';
    spacing: '20px';
  };
}
```

#### 5.2.2 Touch Optimization
```typescript
interface TouchOptimization {
  minTouchTarget: '44px';
  touchSpacing: '12px';
  gestureSupport: {
    swipe: boolean;
    pinch: boolean;
    tap: boolean;
  };
  hoverAlternatives: {
    focus: boolean;
    active: boolean;
    selected: boolean;
  };
}
```

## 6. Data Formatting Standards

### 6.1 Input Formatting

#### 6.1.1 Phone Number
```typescript
interface PhoneNumberFormat {
  mask: '(999) 999-9999';
  placeholder: '(555) 123-4567';
  validation: /^\(\d{3}\) \d{3}-\d{4}$/;
  international: boolean;
  countryCode: string;
}

// Implementation
const phoneFormatter = {
  format: (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    return match ? `(${match[1]}) ${match[2]}-${match[3]}` : value;
  },
  validate: (value: string) => /^\(\d{3}\) \d{3}-\d{4}$/.test(value)
};
```

#### 6.1.2 Currency
```typescript
interface CurrencyFormat {
  currency: 'USD' | 'EUR' | 'JPY';
  symbol: '$' | '€' | '¥';
  position: 'before' | 'after';
  thousandSeparator: ',';
  decimalSeparator: '.';
  decimalPlaces: 2;
  negativeFormat: '($1,234.56)' | '-$1,234.56';
}

// Implementation
const currencyFormatter = {
  format: (value: number, options: CurrencyFormat) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: options.currency,
      minimumFractionDigits: options.decimalPlaces,
      maximumFractionDigits: options.decimalPlaces
    }).format(value);
  }
};
```

#### 6.1.3 Date Formatting
```typescript
interface DateFormat {
  format: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';
  separator: '/' | '-' | '.';
  locale: string;
  timeZone: string;
}

// Implementation
const dateFormatter = {
  format: (date: Date, options: DateFormat) => {
    return new Intl.DateTimeFormat(options.locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: options.timeZone
    }).format(date);
  },
  parse: (value: string, format: string) => {
    // Parse date string according to format
  }
};
```

### 6.2 Output Formatting

#### 6.2.1 Text Truncation
```typescript
interface TextTruncation {
  maxLength: number;
  truncateAt: 'end' | 'middle' | 'start';
  ellipsis: '...' | '…';
  wordBoundary: boolean;
}

// Implementation
const textTruncator = {
  truncate: (text: string, options: TextTruncation) => {
    if (text.length <= options.maxLength) return text;
    
    const ellipsis = options.ellipsis;
    const maxWithEllipsis = options.maxLength - ellipsis.length;
    
    switch (options.truncateAt) {
      case 'end':
        return text.substring(0, maxWithEllipsis) + ellipsis;
      case 'middle':
        const halfLength = Math.floor(maxWithEllipsis / 2);
        return text.substring(0, halfLength) + ellipsis + text.substring(text.length - halfLength);
      case 'start':
        return ellipsis + text.substring(text.length - maxWithEllipsis);
    }
  }
};
```

## 7. Validation Implementation

### 7.1 React Hook Form Integration

```typescript
import { useForm, FieldErrors } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

// Validation Schema
const userSchema = yup.object().shape({
  email: yup
    .string()
    .required('Email is required')
    .email('Please enter a valid email address'),
  password: yup
    .string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters')
    .matches(/[A-Z]/, 'Password must contain uppercase letter')
    .matches(/[a-z]/, 'Password must contain lowercase letter')
    .matches(/\d/, 'Password must contain number')
    .matches(/[!@#$%^&*(),.?":{}|<>]/, 'Password must contain special character'),
  confirmPassword: yup
    .string()
    .required('Please confirm your password')
    .oneOf([yup.ref('password')], 'Passwords must match'),
  phone: yup
    .string()
    .matches(/^\(\d{3}\) \d{3}-\d{4}$/, 'Please enter a valid phone number'),
  birthDate: yup
    .date()
    .max(new Date(), 'Birth date cannot be in the future')
    .min(new Date('1900-01-01'), 'Please enter a valid birth date')
});

// Form Implementation
const UserForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isValid },
    watch,
    trigger
  } = useForm({
    resolver: yupResolver(userSchema),
    mode: 'onBlur'
  });

  const onSubmit = async (data: any) => {
    try {
      await submitUserData(data);
    } catch (error) {
      // Handle server errors
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="space-y-2">
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email Address <span className="text-red-500">*</span>
        </label>
        <input
          id="email"
          type="email"
          {...register('email')}
          className={`block w-full px-3 py-2 border rounded-md ${
            errors.email ? 'border-red-500' : 'border-gray-300'
          }`}
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <p id="email-error" className="text-sm text-red-600" role="alert">
            {errors.email.message}
          </p>
        )}
      </div>
      
      <button
        type="submit"
        disabled={!isValid || isSubmitting}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50"
      >
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
};
```

### 7.2 Custom Validation Hooks

```typescript
// useValidation.ts
import { useState, useCallback } from 'react';

interface ValidationResult {
  isValid: boolean;
  error?: string;
}

interface UseValidationProps {
  rules: ValidationRule[];
  validateOnChange?: boolean;
  debounceMs?: number;
}

export const useValidation = ({ rules, validateOnChange = false, debounceMs = 0 }: UseValidationProps) => {
  const [error, setError] = useState<string | null>(null);
  const [isValid, setIsValid] = useState(true);

  const validate = useCallback(async (value: any): Promise<ValidationResult> => {
    for (const rule of rules) {
      const result = await rule(value);
      if (result !== true) {
        setError(result);
        setIsValid(false);
        return { isValid: false, error: result };
      }
    }
    
    setError(null);
    setIsValid(true);
    return { isValid: true };
  }, [rules]);

  const debouncedValidate = useCallback(
    debounce(validate, debounceMs),
    [validate, debounceMs]
  );

  return {
    error,
    isValid,
    validate: debounceMs > 0 ? debouncedValidate : validate
  };
};

// Validation Rules
export const validationRules = {
  required: (message: string = 'This field is required') => (value: any) => {
    return value && value.toString().trim().length > 0 ? true : message;
  },
  
  email: (message: string = 'Please enter a valid email') => (value: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value) ? true : message;
  },
  
  minLength: (min: number, message?: string) => (value: string) => {
    const msg = message || `Must be at least ${min} characters`;
    return value.length >= min ? true : msg;
  },
  
  maxLength: (max: number, message?: string) => (value: string) => {
    const msg = message || `Must not exceed ${max} characters`;
    return value.length <= max ? true : msg;
  },
  
  pattern: (regex: RegExp, message: string) => (value: string) => {
    return regex.test(value) ? true : message;
  },
  
  custom: (fn: (value: any) => boolean | string) => fn
};
```

## 8. Performance Optimization

### 8.1 Debouncing and Throttling

```typescript
// Debounced validation
const useDebouncedValidation = (
  validateFn: (value: any) => Promise<boolean>,
  delay: number = 300
) => {
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedValidate = useCallback(
    debounce(async (value: any) => {
      setIsValidating(true);
      try {
        const result = await validateFn(value);
        setError(result ? null : 'Validation failed');
      } catch (err) {
        setError('Validation error');
      } finally {
        setIsValidating(false);
      }
    }, delay),
    [validateFn, delay]
  );

  return { debouncedValidate, isValidating, error };
};

// Throttled search
const useThrottledSearch = (
  searchFn: (query: string) => Promise<any[]>,
  delay: number = 500
) => {
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const throttledSearch = useCallback(
    throttle(async (query: string) => {
      if (query.length < 2) return;
      
      setIsSearching(true);
      try {
        const results = await searchFn(query);
        setResults(results);
      } catch (err) {
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, delay),
    [searchFn, delay]
  );

  return { throttledSearch, results, isSearching };
};
```

### 8.2 Memoization

```typescript
// Memoized validation
const useMemoizedValidation = (value: any, rules: ValidationRule[]) => {
  return useMemo(() => {
    for (const rule of rules) {
      const result = rule(value);
      if (result !== true) {
        return { isValid: false, error: result };
      }
    }
    return { isValid: true, error: null };
  }, [value, rules]);
};

// Memoized formatter
const useMemoizedFormatter = (value: any, formatter: (value: any) => string) => {
  return useMemo(() => formatter(value), [value, formatter]);
};
```

## 9. Testing Standards

### 9.1 Unit Testing

```typescript
// Input.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from './Input';

describe('Input Component', () => {
  it('renders with correct attributes', () => {
    render(
      <Input
        type="email"
        placeholder="Enter email"
        required
        aria-label="Email address"
      />
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');
    expect(input).toHaveAttribute('placeholder', 'Enter email');
    expect(input).toHaveAttribute('required');
    expect(input).toHaveAccessibleName('Email address');
  });

  it('validates input on blur', async () => {
    const user = userEvent.setup();
    const mockValidate = jest.fn().mockResolvedValue('Invalid email');
    
    render(
      <Input
        type="email"
        onValidate={mockValidate}
        validateOn="blur"
      />
    );
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'invalid-email');
    await user.tab();
    
    await waitFor(() => {
      expect(mockValidate).toHaveBeenCalledWith('invalid-email');
    });
  });

  it('displays error message with correct ARIA attributes', async () => {
    render(
      <Input
        type="email"
        error="Please enter a valid email"
        aria-describedby="email-error"
      />
    );
    
    const input = screen.getByRole('textbox');
    const errorMessage = screen.getByText('Please enter a valid email');
    
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'email-error');
    expect(errorMessage).toHaveAttribute('role', 'alert');
  });
});
```

### 9.2 Integration Testing

```typescript
// Form.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserForm } from './UserForm';

describe('UserForm Integration', () => {
  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockSubmit = jest.fn();
    
    render(<UserForm onSubmit={mockSubmit} />);
    
    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/password/i), 'Password123!');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'Password123!'
      });
    });
  });

  it('prevents submission with invalid data', async () => {
    const user = userEvent.setup();
    const mockSubmit = jest.fn();
    
    render(<UserForm onSubmit={mockSubmit} />);
    
    await user.type(screen.getByLabelText(/email/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(screen.getByText('Please enter a valid email')).toBeInTheDocument();
    expect(mockSubmit).not.toHaveBeenCalled();
  });
});
```

## 10. Implementation Checklist

### 10.1 Component Development
- [ ] Implement all input types with proper validation
- [ ] Add accessibility attributes and ARIA labels
- [ ] Implement keyboard navigation
- [ ] Add error handling and display
- [ ] Implement responsive design
- [ ] Add animation and transitions
- [ ] Write comprehensive tests
- [ ] Document component usage

### 10.2 Form Integration
- [ ] Integrate with React Hook Form
- [ ] Implement validation schemas
- [ ] Add form layout components
- [ ] Implement error aggregation
- [ ] Add form submission handling
- [ ] Implement progressive enhancement
- [ ] Add form persistence
- [ ] Write integration tests

### 10.3 Performance Optimization
- [ ] Implement debouncing for validation
- [ ] Add throttling for search inputs
- [ ] Implement memoization where appropriate
- [ ] Optimize bundle size
- [ ] Add performance monitoring
- [ ] Implement lazy loading
- [ ] Add caching strategies
- [ ] Monitor runtime performance

---

**Document Status**: ✅ Complete and Ready for Implementation  
**Dependencies**: Design tokens, component library architecture  
**Next Steps**: Component implementation following these standards  

---

*This document serves as the definitive guide for all input-related components and forms in the ITDO ERP2 project.*