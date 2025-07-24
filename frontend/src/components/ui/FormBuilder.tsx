import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface FormField {
  id: string;
  type: 'text' | 'email' | 'number' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'file' | 'custom';
  label: string;
  required?: boolean;
  placeholder?: string;
  defaultValue?: any;
  options?: { value: string; label: string }[];
  validation?: {
    minLength?: number;
    maxLength?: number;
    min?: number;
    max?: number;
    pattern?: RegExp;
    custom?: (value: any) => string | null;
  };
  conditional?: {
    field: string;
    operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'greater_than' | 'less_than';
    value: any;
  };
  dependencies?: string[];
  dependencyRules?: Record<string, { operator: 'not_empty' | 'empty' | 'equals'; value?: any }>;
  group?: string;
  section?: string;
  helpText?: string;
  mask?: string;
  optionsLoader?: () => Promise<{ value: string; label: string }[]>;
  render?: () => React.ReactNode;
  width?: 'full' | 'half' | 'third' | 'quarter';
  disabled?: boolean;
  hidden?: boolean;
}

export interface FormTemplate {
  id: string;
  name: string;
  description?: string;
  fields: FormField[];
}

export interface FormStep {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
}

export interface FormSection {
  id: string;
  title: string;
  description?: string;
  fields: string[];
}

export interface FormCollaborator {
  id: string;
  name: string;
  avatar?: string;
  active: boolean;
}

export interface FormBuilderProps {
  fields?: FormField[];
  template?: FormTemplate;
  steps?: FormStep[];
  sections?: FormSection[];
  theme?: 'default' | 'modern' | 'minimal';
  layout?: 'vertical' | 'horizontal' | 'grid';
  mode?: 'builder' | 'form' | 'preview';
  previewMode?: boolean;
  draggable?: boolean;
  sortable?: boolean;
  editable?: boolean;
  duplicatable?: boolean;
  deletable?: boolean;
  searchable?: boolean;
  grouped?: boolean;
  multiStep?: boolean;
  responsive?: boolean;
  exportable?: boolean;
  importable?: boolean;
  undoable?: boolean;
  versioningEnabled?: boolean;
  showStats?: boolean;
  showProgress?: boolean;
  showHelp?: boolean;
  autosave?: boolean;
  enablePerformanceMonitoring?: boolean;
  collaborators?: FormCollaborator[];
  ariaLabel?: string;
  ariaDescribedBy?: string;
  onFieldAdd?: (field: FormField) => void;
  onFieldUpdate?: (fieldId: string, updates: Partial<FormField>) => void;
  onFieldDelete?: (fieldId: string) => void;
  onFieldDuplicate?: (fieldId: string) => void;
  onFieldReorder?: (fromIndex: number, toIndex: number) => void;
  onSubmit?: (data: Record<string, any>) => void;
  onDataChange?: (data: Record<string, any>) => void;
  onDataSave?: (data: Record<string, any>) => void;
  onExport?: (format: string) => void;
  onImport?: (data: any) => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onVersionSave?: (version: any) => void;
  onError?: (error: any) => void;
  onPerformanceReport?: (metrics: any) => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const FormBuilder = ({
  fields = [],
  template,
  steps,
  sections,
  theme = 'default',
  layout = 'vertical',
  mode = 'builder',
  previewMode = false,
  draggable = false,
  sortable = false,
  editable = false,
  duplicatable = false,
  deletable = false,
  searchable = false,
  grouped = false,
  multiStep = false,
  responsive = false,
  exportable = false,
  importable = false,
  undoable = false,
  versioningEnabled = false,
  showStats = false,
  showProgress = false,
  showHelp = false,
  autosave = false,
  enablePerformanceMonitoring = false,
  collaborators = [],
  ariaLabel = 'Form builder',
  ariaDescribedBy,
  onFieldAdd,
  onFieldUpdate,
  onFieldDelete,
  onFieldDuplicate,
  onFieldReorder,
  onSubmit,
  onDataChange,
  onDataSave,
  onExport,
  onImport,
  onUndo,
  onRedo,
  onVersionSave,
  onError,
  onPerformanceReport,
  className,
  'data-testid': dataTestId = 'form-builder-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}: FormBuilderProps) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [editingField, setEditingField] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [focusedFieldIndex, setFocusedFieldIndex] = useState(-1);
  const [draggedField, setDraggedField] = useState<string | null>(null);
  const [fieldOptions, setFieldOptions] = useState<Record<string, { value: string; label: string }[]>>({});

  const formRef = useRef<HTMLFormElement>(null);
  const autosaveRef = useRef<NodeJS.Timeout | null>(null);
  const performanceRef = useRef({
    renderStart: 0,
    renderEnd: 0,
    fieldCount: 0,
    validationCount: 0
  });

  // Use template fields if provided, otherwise use fields prop
  const effectiveFields = template ? template.fields : fields;
  const effectiveSteps = steps || (multiStep && effectiveFields.length > 0 ? [{ id: 'step1', title: 'Form Fields', fields: effectiveFields }] : []);

  // Get current step fields if in multi-step mode
  const currentStepFields = multiStep && effectiveSteps.length > 0 ? effectiveSteps[currentStep]?.fields || [] : effectiveFields;

  // Filter fields based on search
  const filteredFields = useMemo(() => {
    if (!searchQuery) return currentStepFields;
    
    return currentStepFields.filter(field =>
      field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      field.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [currentStepFields, searchQuery]);

  // Group fields if needed
  const groupedFields = useMemo(() => {
    if (!grouped) return { ungrouped: filteredFields };

    const groups: Record<string, FormField[]> = {};
    filteredFields.forEach(field => {
      const group = field.group || field.type;
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(field);
    });

    return groups;
  }, [filteredFields, grouped]);

  // Get visible fields based on conditions
  const visibleFields = useMemo(() => {
    return filteredFields.filter(field => {
      if (field.hidden) return false;
      
      if (field.conditional) {
        const conditionField = effectiveFields.find(f => f.id === field.conditional!.field);
        if (!conditionField) return true;
        
        const conditionValue = formData[field.conditional.field];
        const targetValue = field.conditional.value;
        
        switch (field.conditional.operator) {
          case 'equals':
            return conditionValue === targetValue;
          case 'not_equals':
            return conditionValue !== targetValue;
          case 'contains':
            return String(conditionValue || '').includes(String(targetValue));
          case 'not_contains':
            return !String(conditionValue || '').includes(String(targetValue));
          case 'greater_than':
            return Number(conditionValue || 0) > Number(targetValue);
          case 'less_than':
            return Number(conditionValue || 0) < Number(targetValue);
          default:
            return true;
        }
      }
      
      return true;
    });
  }, [filteredFields, formData, effectiveFields]);

  // Calculate form progress
  const formProgress = useMemo(() => {
    if (visibleFields.length === 0) return 0;
    
    const filledFields = visibleFields.filter(field => {
      const value = formData[field.id];
      return value !== undefined && value !== '' && value !== null;
    });
    
    return Math.round((filledFields.length / visibleFields.length) * 100);
  }, [visibleFields, formData]);

  // Get form statistics
  const formStats = useMemo(() => {
    const total = effectiveFields.length;
    const required = effectiveFields.filter(f => f.required).length;
    const optional = total - required;
    
    return { total, required, optional };
  }, [effectiveFields]);

  // Validate field
  const validateField = useCallback((field: FormField, value: any): string | null => {
    if (field.required && (!value || value === '')) {
      return `${field.label} is required`;
    }
    
    if (field.validation && value) {
      const { minLength, maxLength, min, max, pattern, custom } = field.validation;
      
      if (minLength && String(value).length < minLength) {
        return `Minimum length is ${minLength} characters`;
      }
      
      if (maxLength && String(value).length > maxLength) {
        return `Maximum length is ${maxLength} characters`;
      }
      
      if (min !== undefined && Number(value) < min) {
        return `Minimum value is ${min}`;
      }
      
      if (max !== undefined && Number(value) > max) {
        return `Maximum value is ${max}`;
      }
      
      if (pattern && !pattern.test(String(value))) {
        return `Invalid format`;
      }
      
      if (custom) {
        const customError = custom(value);
        if (customError) return customError;
      }
    }
    
    return null;
  }, []);

  // Handle field value change
  const handleFieldChange = useCallback((fieldId: string, value: any) => {
    const newFormData = { ...formData, [fieldId]: value };
    setFormData(newFormData);
    onDataChange?.(newFormData);
    
    // Clear validation error for this field
    if (validationErrors[fieldId]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldId];
        return newErrors;
      });
    }
    
    // Trigger autosave
    if (autosave) {
      if (autosaveRef.current) {
        clearTimeout(autosaveRef.current);
      }
      autosaveRef.current = setTimeout(() => {
        onDataSave?.(newFormData);
      }, 1000);
    }
    
    if (enablePerformanceMonitoring) {
      performanceRef.current.validationCount++;
    }
  }, [formData, validationErrors, autosave, onDataChange, onDataSave, enablePerformanceMonitoring]);

  // Handle field blur (validation)
  const handleFieldBlur = useCallback((field: FormField) => {
    const value = formData[field.id];
    const error = validateField(field, value);
    
    if (error) {
      setValidationErrors(prev => ({ ...prev, [field.id]: error }));
    }
  }, [formData, validateField]);

  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    const errors: Record<string, string> = {};
    visibleFields.forEach(field => {
      const value = formData[field.id];
      const error = validateField(field, value);
      if (error) {
        errors[field.id] = error;
      }
    });
    
    setValidationErrors(errors);
    
    if (Object.keys(errors).length === 0) {
      onSubmit?.(formData);
    }
  }, [visibleFields, formData, validateField, onSubmit]);

  // Handle drag and drop
  const handleDragStart = useCallback((e: React.DragEvent, fieldId: string) => {
    if (!sortable) return;
    setDraggedField(fieldId);
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
    }
  }, [sortable]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (!sortable || !draggedField) return;
    e.preventDefault();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move';
    }
  }, [sortable, draggedField]);

  const handleDrop = useCallback((e: React.DragEvent, targetFieldId: string) => {
    if (!sortable || !draggedField) return;
    e.preventDefault();
    
    const fromIndex = effectiveFields.findIndex(f => f.id === draggedField);
    const toIndex = effectiveFields.findIndex(f => f.id === targetFieldId);
    
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
      onFieldReorder?.(fromIndex, toIndex);
    }
    
    setDraggedField(null);
  }, [sortable, draggedField, effectiveFields, onFieldReorder]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Tab':
        e.preventDefault();
        const nextIndex = (focusedFieldIndex + 1) % visibleFields.length;
        setFocusedFieldIndex(nextIndex);
        break;
      case 'Escape':
        setEditingField(null);
        break;
    }
  }, [focusedFieldIndex, visibleFields.length]);

  // Load dynamic options
  useEffect(() => {
    const loadOptions = async () => {
      for (const field of effectiveFields) {
        if (field.optionsLoader && !fieldOptions[field.id]) {
          try {
            const options = await field.optionsLoader();
            setFieldOptions(prev => ({ ...prev, [field.id]: options }));
          } catch (error) {
            onError?.(error);
          }
        }
      }
    };
    
    loadOptions();
  }, [effectiveFields, fieldOptions, onError]);

  // Performance monitoring
  useEffect(() => {
    if (enablePerformanceMonitoring) {
      performanceRef.current.renderStart = performance.now();
      performanceRef.current.fieldCount = effectiveFields.length;
      
      return () => {
        performanceRef.current.renderEnd = performance.now();
        const metrics = {
          renderTime: performanceRef.current.renderEnd - performanceRef.current.renderStart,
          fieldCount: performanceRef.current.fieldCount,
          validationCount: performanceRef.current.validationCount,
          timestamp: new Date()
        };
        onPerformanceReport?.(metrics);
      };
    }
  }, [enablePerformanceMonitoring, effectiveFields.length, onPerformanceReport]);

  // Render field palette for drag and drop
  const renderFieldPalette = () => {
    if (!draggable || previewMode) return null;

    const fieldTypes = [
      { type: 'text', label: 'Text Input' },
      { type: 'email', label: 'Email' },
      { type: 'number', label: 'Number' },
      { type: 'textarea', label: 'Textarea' },
      { type: 'select', label: 'Dropdown' },
      { type: 'checkbox', label: 'Checkbox' },
      { type: 'radio', label: 'Radio' },
      { type: 'date', label: 'Date' },
      { type: 'file', label: 'File Upload' }
    ];

    return (
      <div className="w-64 bg-gray-50 border-r p-4" data-testid="field-palette">
        <h3 className="font-semibold mb-4">Field Types</h3>
        <div className="space-y-2">
          {fieldTypes.map(fieldType => (
            <div
              key={fieldType.type}
              className="p-3 bg-white border border-gray-200 rounded cursor-move hover:border-blue-300"
              draggable
              data-testid={`field-palette-${fieldType.type}`}
            >
              {fieldType.label}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render toolbar
  const renderToolbar = () => {
    return (
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <div className="flex items-center space-x-4">
          {searchable && (
            <div className="flex items-center">
              <input
                type="text"
                placeholder="Search fields..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                data-testid="field-search"
              />
            </div>
          )}

          {collaborators.length > 0 && (
            <div className="flex items-center space-x-2" data-testid="form-collaborators">
              {collaborators.map(collaborator => (
                <div key={collaborator.id} className="flex items-center">
                  {collaborator.avatar && (
                    <img
                      src={collaborator.avatar}
                      alt={collaborator.name}
                      className="w-6 h-6 rounded-full"
                    />
                  )}
                  <span className="ml-1 text-sm">{collaborator.name}</span>
                  {collaborator.active && (
                    <div className="w-2 h-2 bg-green-500 rounded-full ml-1"></div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {undoable && (
            <>
              <button
                onClick={onUndo}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                data-testid="form-undo"
              >
                Undo
              </button>
              <button
                onClick={onRedo}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                data-testid="form-redo"
              >
                Redo
              </button>
            </>
          )}

          {versioningEnabled && (
            <button
              onClick={() => onVersionSave?.({})}
              className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              data-testid="save-form-version"
            >
              Save Version
            </button>
          )}

          {exportable && (
            <button
              onClick={() => onExport?.('json')}
              className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              data-testid="form-export"
            >
              Export
            </button>
          )}

          {importable && (
            <button
              onClick={() => onImport?.({})}
              className="px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
              data-testid="form-import"
            >
              Import
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render form statistics
  const renderStats = () => {
    if (!showStats) return null;

    return (
      <div className="p-4 bg-gray-50 border-b" data-testid="form-stats">
        <div className="flex items-center space-x-6 text-sm text-gray-600">
          <span>{formStats.total} fields</span>
          <span>{formStats.required} required fields</span>
          <span>{formStats.optional} optional fields</span>
        </div>
      </div>
    );
  };

  // Render form progress
  const renderProgress = () => {
    if (!showProgress) return null;

    return (
      <div className="p-4 border-b" data-testid="form-progress">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Form Progress</span>
          <span className="text-sm text-gray-500">{formProgress}% complete</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${formProgress}%` }}
          ></div>
        </div>
      </div>
    );
  };

  // Render multi-step navigation
  const renderStepNavigation = () => {
    if (!multiStep || effectiveSteps.length <= 1) return null;

    return (
      <div className="p-4 border-b" data-testid="form-steps">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">{effectiveSteps[currentStep]?.title}</h3>
          <span className="text-sm text-gray-500">
            Step {currentStep + 1} of {effectiveSteps.length}
          </span>
        </div>
        <div className="flex space-x-2">
          {effectiveSteps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                'flex-1 h-2 rounded',
                index <= currentStep ? 'bg-blue-500' : 'bg-gray-200'
              )}
            />
          ))}
        </div>
      </div>
    );
  };

  // Render form field
  const renderField = (field: FormField, index: number) => {
    const value = formData[field.id] || field.defaultValue || '';
    const error = validationErrors[field.id];
    const isFocused = index === focusedFieldIndex;
    const isDragged = draggedField === field.id;
    const isDisabled = field.disabled || (field.dependencies && field.dependencies.some(depId => {
      const depField = effectiveFields.find(f => f.id === depId);
      if (!depField || !field.dependencyRules) return false;
      
      const rule = field.dependencyRules[depId];
      const depValue = formData[depId];
      
      switch (rule.operator) {
        case 'not_empty':
          return !depValue || depValue === '';
        case 'empty':
          return depValue && depValue !== '';
        case 'equals':
          return depValue !== rule.value;
        default:
          return false;
      }
    }));

    const fieldOptions = field.options || (field.optionsLoader ? (fieldOptions[field.id] || []) : []);

    return (
      <div
        key={field.id}
        className={cn(
          'form-field p-4 border border-gray-200 rounded-lg bg-white',
          isFocused && 'focused ring-2 ring-blue-500',
          isDragged && 'opacity-50',
          field.width === 'half' && 'md:w-1/2',
          field.width === 'third' && 'md:w-1/3',
          field.width === 'quarter' && 'md:w-1/4'
        )}
        draggable={sortable}
        onDragStart={(e) => handleDragStart(e, field.id)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, field.id)}
        data-testid={`form-field-${field.id}`}
      >
        <div className="flex items-center justify-between mb-2">
          <label className={cn('block text-sm font-medium text-gray-700', field.required && 'required')}>
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          
          {!previewMode && (
            <div className="flex items-center space-x-1">
              {showHelp && field.helpText && (
                <button
                  className="p-1 text-gray-400 hover:text-gray-600"
                  data-testid={`help-${field.id}`}
                  title={field.helpText}
                >
                  ?
                </button>
              )}
              
              {editable && (
                <button
                  onClick={() => setEditingField(field.id)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  data-testid={`edit-field-${field.id}`}
                >
                  ✏
                </button>
              )}
              
              {duplicatable && (
                <button
                  onClick={() => onFieldDuplicate?.(field.id)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  data-testid={`duplicate-field-${field.id}`}
                >
                  ⧉
                </button>
              )}
              
              {deletable && (
                <button
                  onClick={() => onFieldDelete?.(field.id)}
                  className="p-1 text-red-400 hover:text-red-600"
                  data-testid={`delete-field-${field.id}`}
                >
                  ✕
                </button>
              )}
            </div>
          )}
        </div>

        {field.type === 'custom' && field.render ? (
          field.render()
        ) : field.type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            onBlur={() => handleFieldBlur(field)}
            placeholder={field.placeholder}
            disabled={isDisabled}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
              error && 'border-red-500',
              isDisabled && 'bg-gray-100 cursor-not-allowed'
            )}
            rows={4}
          />
        ) : field.type === 'select' ? (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            onBlur={() => handleFieldBlur(field)}
            disabled={isDisabled}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
              error && 'border-red-500',
              isDisabled && 'bg-gray-100 cursor-not-allowed'
            )}
          >
            <option value="">Select an option</option>
            {fieldOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : field.type === 'checkbox' ? (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleFieldChange(field.id, e.target.checked)}
              onBlur={() => handleFieldBlur(field)}
              disabled={isDisabled}
              className="mr-2"
            />
            {field.placeholder || 'Check this option'}
          </label>
        ) : field.type === 'radio' && fieldOptions.length > 0 ? (
          <div className="space-y-2">
            {fieldOptions.map(option => (
              <label key={option.value} className="flex items-center">
                <input
                  type="radio"
                  name={field.id}
                  value={option.value}
                  checked={value === option.value}
                  onChange={(e) => handleFieldChange(field.id, e.target.value)}
                  onBlur={() => handleFieldBlur(field)}
                  disabled={isDisabled}
                  className="mr-2"
                />
                {option.label}
              </label>
            ))}
          </div>
        ) : (
          <input
            type={field.type}
            value={value}
            onChange={(e) => {
              let newValue = e.target.value;
              
              // Apply mask if specified
              if (field.mask && newValue) {
                const mask = field.mask;
                const numbers = newValue.replace(/\D/g, '');
                let maskedValue = '';
                let numIndex = 0;
                
                for (let i = 0; i < mask.length && numIndex < numbers.length; i++) {
                  if (mask[i] === '9') {
                    maskedValue += numbers[numIndex];
                    numIndex++;
                  } else {
                    maskedValue += mask[i];
                  }
                }
                
                newValue = maskedValue;
              }
              
              handleFieldChange(field.id, newValue);
            }}
            onBlur={() => handleFieldBlur(field)}
            placeholder={field.placeholder}
            disabled={isDisabled}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
              error && 'border-red-500',
              isDisabled && 'bg-gray-100 cursor-not-allowed'
            )}
          />
        )}

        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}

        {showHelp && field.helpText && (
          <div
            className="mt-2 text-sm text-gray-500"
            data-testid={`help-field-${field.id}`}
          >
            {field.helpText}
          </div>
        )}
      </div>
    );
  };

  // Render grouped fields
  const renderGroupedFields = () => {
    return Object.entries(groupedFields).map(([groupName, groupFields]) => (
      <div key={groupName}>
        {grouped && groupName !== 'ungrouped' && (
          <h3 className="text-lg font-semibold mb-4 border-b pb-2" data-testid={`field-group-${groupName}`}>
            {groupName.charAt(0).toUpperCase() + groupName.slice(1)}
          </h3>
        )}
        <div className={cn(
          'grid gap-4 mb-8',
          layout === 'grid' && 'grid-cols-1 md:grid-cols-2',
          layout === 'horizontal' && 'flex flex-wrap',
          layout === 'vertical' && 'space-y-4'
        )}>
          {groupFields.map((field, index) => renderField(field, index))}
        </div>
      </div>
    ));
  };

  // Render sections
  const renderSections = () => {
    if (!sections) return renderGroupedFields();

    return sections.map(section => {
      const sectionFields = section.fields.map(fieldId => 
        visibleFields.find(f => f.id === fieldId)
      ).filter(Boolean) as FormField[];

      if (sectionFields.length === 0) return null;

      return (
        <div key={section.id} className="mb-8">
          <div className="border-b pb-4 mb-6">
            <h3 className="text-lg font-semibold">{section.title}</h3>
            {section.description && (
              <p className="text-gray-600 mt-1">{section.description}</p>
            )}
          </div>
          <div className={cn(
            'grid gap-4',
            layout === 'grid' && 'grid-cols-1 md:grid-cols-2',
            layout === 'horizontal' && 'flex flex-wrap',
            layout === 'vertical' && 'space-y-4'
          )}>
            {sectionFields.map((field, index) => renderField(field, index))}
          </div>
        </div>
      );
    });
  };

  // Render field editor panel
  const renderFieldEditor = () => {
    if (!editingField) return null;

    return (
      <div
        className="fixed right-0 top-0 bottom-0 w-80 bg-white shadow-xl border-l z-40"
        data-testid="field-editor-panel"
      >
        <div className="p-4 border-b">
          <h3 className="font-semibold">Edit Field</h3>
          <button
            onClick={() => setEditingField(null)}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        <div className="p-4">
          <p className="text-gray-600">Field editor for: {editingField}</p>
        </div>
      </div>
    );
  };

  if (effectiveFields.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center h-64 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg"
        data-testid="form-empty-state"
      >
        <div className="text-center">
          <div className="text-4xl mb-4">📝</div>
          <div className="text-lg font-medium mb-2">No fields added yet</div>
          <div className="text-sm">Drag fields from the palette to start building your form</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {renderFieldPalette()}
      
      <div
        className={cn(
          'form-builder flex-1',
          `theme-${theme}`,
          `layout-${layout}`,
          responsive && 'responsive',
          className
        )}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        role="main"
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        data-testid={dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        {...props}
      >
        {!previewMode && renderToolbar()}
        {renderStats()}
        {renderProgress()}
        {renderStepNavigation()}

        <div className="flex-1 overflow-auto">
          {previewMode ? (
            <div className="p-6" data-testid="form-preview">
              <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">
                {sections ? renderSections() : renderGroupedFields()}
                
                <div className="pt-6 border-t">
                  <button
                    type="submit"
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="form-submit"
                  >
                    Submit Form
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="p-6">
              {draggable && (
                <div
                  className="min-h-32 border-2 border-dashed border-gray-300 rounded-lg mb-6 flex items-center justify-center text-gray-500"
                  data-testid="form-builder-drag-area"
                >
                  Drag fields here to build your form
                </div>
              )}
              
              <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">
                {sections ? renderSections() : renderGroupedFields()}
                
                <div className="pt-6 border-t">
                  <button
                    type="submit"
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="form-submit"
                  >
                    Submit Form
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {renderFieldEditor()}
      </div>
    </div>
  );
};

export default FormBuilder;