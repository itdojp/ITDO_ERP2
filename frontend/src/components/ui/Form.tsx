import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';

export interface FormField {
  name: string;
  value: any;
  error?: string;
  touched?: boolean;
  dirty?: boolean;
}

export interface FormState {
  fields: Record<string, FormField>;
  isSubmitting: boolean;
  isValidating: boolean;
  submitCount: number;
}

export interface ValidationRule {
  required?: boolean | string;
  min?: number | string;
  max?: number | string;
  pattern?: RegExp | string;
  validate?: (value: any, allValues: Record<string, any>) => string | undefined;
}

export interface FormFieldConfig {
  name: string;
  initialValue?: any;
  rules?: ValidationRule[];
}

interface FormProps {
  children: React.ReactNode;
  initialValues?: Record<string, any>;
  validationRules?: Record<string, ValidationRule[]>;
  onSubmit: (values: Record<string, any>, formApi: FormApi) => void | Promise<void>;
  onValuesChange?: (changedValues: Record<string, any>, allValues: Record<string, any>) => void;
  layout?: 'vertical' | 'horizontal' | 'inline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  className?: string;
  labelCol?: number;
  wrapperCol?: number;
  requiredMark?: boolean | 'optional';
}

interface FormApi {
  getFieldValue: (name: string) => any;
  setFieldValue: (name: string, value: any) => void;
  getFieldError: (name: string) => string | undefined;
  setFieldError: (name: string, error: string | undefined) => void;
  resetFields: (names?: string[]) => void;
  validateFields: (names?: string[]) => Promise<boolean>;
  submit: () => void;
  isFieldTouched: (name: string) => boolean;
  isFieldDirty: (name: string) => boolean;
  getValues: () => Record<string, any>;
  setValues: (values: Record<string, any>) => void;
}

type FormAction =
  | { type: 'SET_FIELD_VALUE'; name: string; value: any }
  | { type: 'SET_FIELD_ERROR'; name: string; error: string | undefined }
  | { type: 'SET_FIELD_TOUCHED'; name: string; touched: boolean }
  | { type: 'SET_SUBMITTING'; isSubmitting: boolean }
  | { type: 'SET_VALIDATING'; isValidating: boolean }
  | { type: 'INCREMENT_SUBMIT_COUNT' }
  | { type: 'RESET_FIELDS'; names?: string[] }
  | { type: 'INITIALIZE'; initialValues: Record<string, any> };

const formReducer = (state: FormState, action: FormAction): FormState => {
  switch (action.type) {
    case 'SET_FIELD_VALUE':
      return {
        ...state,
        fields: {
          ...state.fields,
          [action.name]: {
            ...state.fields[action.name],
            name: action.name,
            value: action.value,
            dirty: true,
          },
        },
      };
    case 'SET_FIELD_ERROR':
      return {
        ...state,
        fields: {
          ...state.fields,
          [action.name]: {
            ...state.fields[action.name],
            name: action.name,
            error: action.error,
          },
        },
      };
    case 'SET_FIELD_TOUCHED':
      return {
        ...state,
        fields: {
          ...state.fields,
          [action.name]: {
            ...state.fields[action.name],
            name: action.name,
            touched: action.touched,
          },
        },
      };
    case 'SET_SUBMITTING':
      return {
        ...state,
        isSubmitting: action.isSubmitting,
      };
    case 'SET_VALIDATING':
      return {
        ...state,
        isValidating: action.isValidating,
      };
    case 'INCREMENT_SUBMIT_COUNT':
      return {
        ...state,
        submitCount: state.submitCount + 1,
      };
    case 'RESET_FIELDS':
      const fieldsToReset = action.names || Object.keys(state.fields);
      const resetFields = { ...state.fields };
      fieldsToReset.forEach(name => {
        if (resetFields[name]) {
          resetFields[name] = {
            ...resetFields[name],
            value: undefined,
            error: undefined,
            touched: false,
            dirty: false,
          };
        }
      });
      return {
        ...state,
        fields: resetFields,
      };
    case 'INITIALIZE':
      const initialFields: Record<string, FormField> = {};
      Object.entries(action.initialValues).forEach(([name, value]) => {
        initialFields[name] = {
          name,
          value,
          error: undefined,
          touched: false,
          dirty: false,
        };
      });
      return {
        ...state,
        fields: initialFields,
      };
    default:
      return state;
  }
};

const FormContext = createContext<{
  state: FormState;
  dispatch: React.Dispatch<FormAction>;
  props: FormProps;
  formApi: FormApi;
} | null>(null);

export const useFormContext = () => {
  const context = useContext(FormContext);
  if (!context) {
    throw new Error('useFormContext must be used within a Form component');
  }
  return context;
};

export const Form: React.FC<FormProps> = ({
  children,
  initialValues = {},
  validationRules = {},
  onSubmit,
  onValuesChange,
  layout = 'vertical',
  size = 'md',
  disabled = false,
  validateOnChange = true,
  validateOnBlur = true,
  className = '',
  labelCol,
  wrapperCol,
  requiredMark = true
}) => {
  const [state, dispatch] = useReducer(formReducer, {
    fields: {},
    isSubmitting: false,
    isValidating: false,
    submitCount: 0,
  });

  const validateField = useCallback(async (name: string, value: any, allValues: Record<string, any>): Promise<string | undefined> => {
    const rules = validationRules[name] || [];
    
    for (const rule of rules) {
      if (rule.required) {
        const message = typeof rule.required === 'string' ? rule.required : `${name} is required`;
        if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
          return message;
        }
      }
      
      if (rule.min !== undefined && value != null) {
        const minValue = typeof rule.min === 'number' ? rule.min : Number(rule.min);
        if (typeof value === 'string' && value.length < minValue) {
          return `${name} must be at least ${minValue} characters`;
        }
        if (typeof value === 'number' && value < minValue) {
          return `${name} must be at least ${minValue}`;
        }
      }
      
      if (rule.max !== undefined && value != null) {
        const maxValue = typeof rule.max === 'number' ? rule.max : Number(rule.max);
        if (typeof value === 'string' && value.length > maxValue) {
          return `${name} must be at most ${maxValue} characters`;
        }
        if (typeof value === 'number' && value > maxValue) {
          return `${name} must be at most ${maxValue}`;
        }
      }
      
      if (rule.pattern && value != null && value !== '') {
        const pattern = typeof rule.pattern === 'string' ? new RegExp(rule.pattern) : rule.pattern;
        if (!pattern.test(String(value))) {
          return `${name} format is invalid`;
        }
      }
      
      if (rule.validate && value != null) {
        const result = await rule.validate(value, allValues);
        if (result) return result;
      }
    }
    
    return undefined;
  }, [validationRules]);

  const formApi: FormApi = {
    getFieldValue: (name: string) => state.fields[name]?.value,
    
    setFieldValue: (name: string, value: any) => {
      dispatch({ type: 'SET_FIELD_VALUE', name, value });
      
      if (validateOnChange) {
        const allValues = Object.entries(state.fields).reduce((acc, [key, field]) => {
          acc[key] = key === name ? value : field.value;
          return acc;
        }, {} as Record<string, any>);
        
        validateField(name, value, allValues).then(error => {
          dispatch({ type: 'SET_FIELD_ERROR', name, error });
        });
      }
      
      if (onValuesChange) {
        const changedValues = { [name]: value };
        const allValues = Object.entries(state.fields).reduce((acc, [key, field]) => {
          acc[key] = key === name ? value : field.value;
          return acc;
        }, {} as Record<string, any>);
        onValuesChange(changedValues, allValues);
      }
    },
    
    getFieldError: (name: string) => state.fields[name]?.error,
    
    setFieldError: (name: string, error: string | undefined) => {
      dispatch({ type: 'SET_FIELD_ERROR', name, error });
    },
    
    resetFields: (names?: string[]) => {
      dispatch({ type: 'RESET_FIELDS', names });
    },
    
    validateFields: async (names?: string[]): Promise<boolean> => {
      dispatch({ type: 'SET_VALIDATING', isValidating: true });
      
      const fieldsToValidate = names || Object.keys(state.fields);
      const allValues = Object.entries(state.fields).reduce((acc, [key, field]) => {
        acc[key] = field.value;
        return acc;
      }, {} as Record<string, any>);
      
      let hasErrors = false;
      
      for (const name of fieldsToValidate) {
        const value = allValues[name];
        const error = await validateField(name, value, allValues);
        dispatch({ type: 'SET_FIELD_ERROR', name, error });
        if (error) hasErrors = true;
      }
      
      dispatch({ type: 'SET_VALIDATING', isValidating: false });
      return !hasErrors;
    },
    
    submit: async () => {
      dispatch({ type: 'INCREMENT_SUBMIT_COUNT' });
      dispatch({ type: 'SET_SUBMITTING', isSubmitting: true });
      
      // Mark all fields as touched
      Object.keys(state.fields).forEach(name => {
        dispatch({ type: 'SET_FIELD_TOUCHED', name, touched: true });
      });
      
      const isValid = await formApi.validateFields();
      
      if (isValid) {
        try {
          const values = formApi.getValues();
          await onSubmit(values, formApi);
        } catch (error) {
          console.error('Form submission error:', error);
        }
      }
      
      dispatch({ type: 'SET_SUBMITTING', isSubmitting: false });
    },
    
    isFieldTouched: (name: string) => !!state.fields[name]?.touched,
    
    isFieldDirty: (name: string) => !!state.fields[name]?.dirty,
    
    getValues: () => {
      return Object.entries(state.fields).reduce((acc, [name, field]) => {
        acc[name] = field.value;
        return acc;
      }, {} as Record<string, any>);
    },
    
    setValues: (values: Record<string, any>) => {
      Object.entries(values).forEach(([name, value]) => {
        dispatch({ type: 'SET_FIELD_VALUE', name, value });
      });
    }
  };

  // Initialize form with initial values
  useEffect(() => {
    dispatch({ type: 'INITIALIZE', initialValues });
  }, [initialValues]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    formApi.submit();
  };

  const getLayoutClasses = () => {
    switch (layout) {
      case 'horizontal':
        return 'space-y-4';
      case 'inline':
        return 'flex flex-wrap items-start gap-4';
      case 'vertical':
      default:
        return 'space-y-4';
    }
  };

  const getSizeClasses = () => {
    const sizeMap = {
      sm: 'text-sm',
      md: 'text-sm',
      lg: 'text-base'
    };
    return sizeMap[size];
  };

  const formProps = {
    initialValues,
    validationRules,
    onSubmit,
    onValuesChange,
    layout,
    size,
    disabled,
    validateOnChange,
    validateOnBlur,
    className,
    labelCol,
    wrapperCol,
    requiredMark
  };

  return (
    <FormContext.Provider value={{ state, dispatch, props: formProps, formApi }}>
      <form
        onSubmit={handleSubmit}
        className={`
          ${getLayoutClasses()}
          ${getSizeClasses()}
          ${disabled ? 'opacity-50 pointer-events-none' : ''}
          ${className}
        `}
        noValidate
      >
        {children}
      </form>
    </FormContext.Provider>
  );
};

// Form.Item component for form fields
interface FormItemProps {
  name: string;
  label?: string;
  children: React.ReactNode;
  required?: boolean;
  help?: string;
  validateStatus?: 'success' | 'warning' | 'error' | 'validating';
  className?: string;
  labelClassName?: string;
  wrapperClassName?: string;
  colon?: boolean;
}

export const FormItem: React.FC<FormItemProps> = ({
  name,
  label,
  children,
  required,
  help,
  validateStatus,
  className = '',
  labelClassName = '',
  wrapperClassName = '',
  colon = true
}) => {
  const { state, dispatch, props } = useFormContext();
  const field = state.fields[name];
  const hasError = !!field?.error;
  const showError = hasError && field?.touched;

  const handleBlur = () => {
    dispatch({ type: 'SET_FIELD_TOUCHED', name, touched: true });
  };

  const isRequired = required ?? props.validationRules?.[name]?.some(rule => rule.required);
  const showRequiredMark = props.requiredMark && isRequired;

  const getStatusClasses = () => {
    if (validateStatus === 'error' || showError) return 'text-red-600';
    if (validateStatus === 'success') return 'text-green-600';
    if (validateStatus === 'warning') return 'text-yellow-600';
    if (validateStatus === 'validating') return 'text-blue-600';
    return 'text-gray-700';
  };

  const renderLabel = () => {
    if (!label) return null;

    return (
      <label className={`block font-medium ${getStatusClasses()} ${labelClassName}`}>
        {label}
        {showRequiredMark && <span className="text-red-500 ml-1">*</span>}
        {colon && ':'}
      </label>
    );
  };

  const renderChildren = () => {
    return React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, {
          ...child.props,
          onBlur: (e: any) => {
            handleBlur();
            child.props.onBlur?.(e);
          }
        });
      }
      return child;
    });
  };

  const formItemClasses = `
    ${props.layout === 'horizontal' ? 'flex items-start gap-4' : ''}
    ${className}
  `;

  const labelColStyle = props.labelCol ? { flex: `0 0 ${props.labelCol * 100 / 24}%` } : {};
  const wrapperColStyle = props.wrapperCol ? { flex: `0 0 ${props.wrapperCol * 100 / 24}%` } : { flex: 1 };

  return (
    <div className={formItemClasses}>
      {props.layout === 'horizontal' ? (
        <>
          <div style={labelColStyle} className={labelClassName}>
            {renderLabel()}
          </div>
          <div style={wrapperColStyle} className={wrapperClassName}>
            {renderChildren()}
            {showError && (
              <div className="text-red-600 text-sm mt-1">{field.error}</div>
            )}
            {help && !showError && (
              <div className="text-gray-500 text-sm mt-1">{help}</div>
            )}
          </div>
        </>
      ) : (
        <>
          {renderLabel()}
          <div className={`mt-1 ${wrapperClassName}`}>
            {renderChildren()}
            {showError && (
              <div className="text-red-600 text-sm mt-1">{field.error}</div>
            )}
            {help && !showError && (
              <div className="text-gray-500 text-sm mt-1">{help}</div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

Form.Item = FormItem;

export default Form;