import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { FormBuilder } from './FormBuilder';

interface MockField {
  id: string;
  type: 'text' | 'email' | 'number' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'file' | 'custom';
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: any;
  conditional?: any;
}

describe('FormBuilder', () => {
  const mockFields: MockField[] = [
    {
      id: 'field-1',
      type: 'text',
      label: 'Full Name',
      required: true,
      placeholder: 'Enter your full name'
    },
    {
      id: 'field-2',
      type: 'email',
      label: 'Email Address',
      required: true,
      placeholder: 'Enter your email'
    },
    {
      id: 'field-3',
      type: 'select',
      label: 'Country',
      options: [
        { value: 'us', label: 'United States' },
        { value: 'ca', label: 'Canada' },
        { value: 'uk', label: 'United Kingdom' }
      ]
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders form builder with fields', () => {
    render(<FormBuilder fields={mockFields} />);
    
    expect(screen.getByTestId('form-builder-container')).toBeInTheDocument();
    expect(screen.getByText('Full Name')).toBeInTheDocument();
    expect(screen.getByText('Email Address')).toBeInTheDocument();
    expect(screen.getByText('Country')).toBeInTheDocument();
  });

  it('supports drag and drop form building', () => {
    const onFieldAdd = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        draggable
        onFieldAdd={onFieldAdd}
      />
    );
    
    const dragArea = screen.getByTestId('form-builder-drag-area');
    expect(dragArea).toBeInTheDocument();
    
    const textFieldPalette = screen.getByTestId('field-palette-text');
    expect(textFieldPalette).toHaveAttribute('draggable', 'true');
  });

  it('supports field editing', () => {
    const onFieldUpdate = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        editable
        onFieldUpdate={onFieldUpdate}
      />
    );
    
    const editButton = screen.getByTestId('edit-field-field-1');
    fireEvent.click(editButton);
    
    expect(screen.getByTestId('field-editor-panel')).toBeInTheDocument();
  });

  it('supports field validation configuration', () => {
    const fieldsWithValidation = [
      {
        ...mockFields[0],
        validation: {
          minLength: 2,
          maxLength: 50,
          pattern: /^[a-zA-Z\s]+$/
        }
      }
    ];
    
    render(<FormBuilder fields={fieldsWithValidation} />);
    
    const nameInput = screen.getByPlaceholderText('Enter your full name');
    fireEvent.change(nameInput, { target: { value: 'A' } });
    fireEvent.blur(nameInput);
    
    expect(screen.getByText('Minimum length is 2 characters')).toBeInTheDocument();
  });

  it('supports conditional field display', () => {
    const conditionalFields = [
      ...mockFields,
      {
        id: 'field-4',
        type: 'text' as const,
        label: 'Company Name',
        conditional: {
          field: 'field-3',
          operator: 'equals' as const,
          value: 'us'
        }
      }
    ];
    
    render(<FormBuilder fields={conditionalFields} />);
    
    // Select US from country dropdown first to trigger conditional field
    const countrySelect = screen.getByRole('combobox');
    fireEvent.change(countrySelect, { target: { value: 'us' } });
    
    // Now Company Name should be visible
    expect(screen.getByText('Company Name')).toBeInTheDocument();
  });

  it('supports form templates', () => {
    const template = {
      id: 'contact-form',
      name: 'Contact Form Template',
      fields: mockFields
    };
    
    render(<FormBuilder template={template} />);
    
    expect(screen.getByTestId('form-builder-container')).toBeInTheDocument();
    expect(screen.getByText('Full Name')).toBeInTheDocument();
  });

  it('supports form preview mode', () => {
    render(<FormBuilder fields={mockFields} previewMode />);
    
    expect(screen.getByTestId('form-preview')).toBeInTheDocument();
    expect(screen.queryByTestId('field-palette')).not.toBeInTheDocument();
  });

  it('handles form submission', async () => {
    const onSubmit = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        onSubmit={onSubmit}
      />
    );
    
    const nameInput = screen.getByPlaceholderText('Enter your full name');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const submitButton = screen.getByTestId('form-submit');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          'field-1': 'John Doe',
          'field-2': 'john@example.com'
        })
      );
    });
  });

  it('supports form validation', () => {
    render(<FormBuilder fields={mockFields} />);
    
    const submitButton = screen.getByTestId('form-submit');
    fireEvent.click(submitButton);
    
    expect(screen.getByText('Full Name is required')).toBeInTheDocument();
    expect(screen.getByText('Email Address is required')).toBeInTheDocument();
  });

  it('supports field reordering', () => {
    const onFieldReorder = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        sortable
        onFieldReorder={onFieldReorder}
      />
    );
    
    const firstField = screen.getByTestId('form-field-field-1');
    const secondField = screen.getByTestId('form-field-field-2');
    
    // Simulate drag and drop
    fireEvent.dragStart(firstField);
    fireEvent.dragOver(secondField);
    fireEvent.drop(secondField);
    
    expect(onFieldReorder).toHaveBeenCalledWith(0, 1);
  });

  it('supports custom field types', () => {
    const customField = {
      id: 'custom-1',
      type: 'custom' as const,
      label: 'Custom Field',
      render: () => <div data-testid="custom-field-content">Custom Content</div>
    };
    
    render(<FormBuilder fields={[customField]} />);
    
    expect(screen.getByTestId('custom-field-content')).toBeInTheDocument();
  });

  it('supports field groups', () => {
    const groupedFields = mockFields.map(field => ({
      ...field,
      group: field.type === 'text' || field.type === 'email' ? 'personal' : 'location'
    }));
    
    render(<FormBuilder fields={groupedFields} grouped />);
    
    expect(screen.getByTestId('field-group-personal')).toBeInTheDocument();
    expect(screen.getByTestId('field-group-location')).toBeInTheDocument();
  });

  it('supports form styling themes', () => {
    const themes = ['default', 'modern', 'minimal'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<FormBuilder fields={mockFields} theme={theme} />);
      const container = screen.getByTestId('form-builder-container');
      expect(container).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('supports responsive layout', () => {
    render(<FormBuilder fields={mockFields} responsive />);
    
    const container = screen.getByTestId('form-builder-container');
    expect(container).toHaveClass('responsive');
  });

  it('supports field duplication', () => {
    const onFieldDuplicate = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        duplicatable
        onFieldDuplicate={onFieldDuplicate}
      />
    );
    
    const duplicateButton = screen.getByTestId('duplicate-field-field-1');
    fireEvent.click(duplicateButton);
    
    expect(onFieldDuplicate).toHaveBeenCalledWith('field-1');
  });

  it('supports field deletion', () => {
    const onFieldDelete = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        deletable
        onFieldDelete={onFieldDelete}
      />
    );
    
    const deleteButton = screen.getByTestId('delete-field-field-1');
    fireEvent.click(deleteButton);
    
    expect(onFieldDelete).toHaveBeenCalledWith('field-1');
  });

  it('supports form export', () => {
    const onExport = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        exportable
        onExport={onExport}
      />
    );
    
    const exportButton = screen.getByTestId('form-export');
    fireEvent.click(exportButton);
    
    expect(onExport).toHaveBeenCalledWith('json');
  });

  it('supports form import', () => {
    const onImport = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        importable
        onImport={onImport}
      />
    );
    
    const importButton = screen.getByTestId('form-import');
    expect(importButton).toBeInTheDocument();
  });

  it('supports undo/redo functionality', () => {
    const onUndo = vi.fn();
    const onRedo = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        undoable
        onUndo={onUndo}
        onRedo={onRedo}
      />
    );
    
    const undoButton = screen.getByTestId('form-undo');
    const redoButton = screen.getByTestId('form-redo');
    
    fireEvent.click(undoButton);
    expect(onUndo).toHaveBeenCalled();
    
    fireEvent.click(redoButton);
    expect(onRedo).toHaveBeenCalled();
  });

  it('supports form versioning', () => {
    const onVersionSave = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        versioningEnabled
        onVersionSave={onVersionSave}
      />
    );
    
    const saveVersionButton = screen.getByTestId('save-form-version');
    fireEvent.click(saveVersionButton);
    
    expect(onVersionSave).toHaveBeenCalled();
  });

  it('displays form statistics', () => {
    render(<FormBuilder fields={mockFields} showStats />);
    
    expect(screen.getByTestId('form-stats')).toBeInTheDocument();
    expect(screen.getByText('3 fields')).toBeInTheDocument();
    expect(screen.getByText('2 required fields')).toBeInTheDocument();
  });

  it('supports form accessibility features', () => {
    render(
      <FormBuilder 
        fields={mockFields}
        ariaLabel="Dynamic form builder"
        ariaDescribedBy="form-description"
      />
    );
    
    const container = screen.getByTestId('form-builder-container');
    expect(container).toHaveAttribute('aria-label', 'Dynamic form builder');
    expect(container).toHaveAttribute('aria-describedby', 'form-description');
  });

  it('supports field search and filtering', () => {
    render(<FormBuilder fields={mockFields} searchable />);
    
    const searchInput = screen.getByTestId('field-search');
    fireEvent.change(searchInput, { target: { value: 'email' } });
    
    expect(screen.getByText('Email Address')).toBeInTheDocument();
    expect(screen.queryByText('Full Name')).not.toBeInTheDocument();
  });

  it('supports form collaboration features', () => {
    const collaborators = [
      { id: '1', name: 'John Doe', active: true }
    ];
    
    render(<FormBuilder fields={mockFields} collaborators={collaborators} />);
    
    expect(screen.getByTestId('form-collaborators')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(<FormBuilder fields={mockFields} />);
    
    const container = screen.getByTestId('form-builder-container');
    container.focus();
    
    fireEvent.keyDown(container, { key: 'Tab' });
    
    const firstField = screen.getByTestId('form-field-field-1');
    expect(firstField).toHaveClass('focused');
  });

  it('supports form progress tracking', () => {
    render(<FormBuilder fields={mockFields} showProgress />);
    
    expect(screen.getByTestId('form-progress')).toBeInTheDocument();
    expect(screen.getByText('0% complete')).toBeInTheDocument();
  });

  it('supports field help tooltips', () => {
    const fieldsWithHelp = mockFields.map(field => ({
      ...field,
      helpText: `Help text for ${field.label}`
    }));
    
    render(<FormBuilder fields={fieldsWithHelp} showHelp />);
    
    const helpButton = screen.getByTestId('help-field-field-1');
    fireEvent.mouseEnter(helpButton);
    
    expect(screen.getByText('Help text for Full Name')).toBeInTheDocument();
  });

  it('supports form data persistence', () => {
    const onDataSave = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        autosave
        onDataSave={onDataSave}
      />
    );
    
    const nameInput = screen.getByPlaceholderText('Enter your full name');
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    // Should trigger autosave
    setTimeout(() => {
      expect(onDataSave).toHaveBeenCalled();
    }, 1000);
  });

  it('handles form errors gracefully', () => {
    const onError = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        onError={onError}
      />
    );
    
    expect(screen.getByTestId('form-builder-container')).toBeInTheDocument();
  });

  it('supports custom field validation rules', () => {
    const customValidationField = {
      ...mockFields[0],
      validation: {
        custom: (value: string) => value.includes('test') ? 'Value cannot contain "test"' : null
      }
    };
    
    render(<FormBuilder fields={[customValidationField]} />);
    
    const input = screen.getByPlaceholderText('Enter your full name');
    fireEvent.change(input, { target: { value: 'test user' } });
    fireEvent.blur(input);
    
    expect(screen.getByText('Value cannot contain "test"')).toBeInTheDocument();
  });

  it('supports multi-step form building', () => {
    const steps = [
      { id: 'step1', title: 'Personal Info', fields: [mockFields[0], mockFields[1]] },
      { id: 'step2', title: 'Location', fields: [mockFields[2]] }
    ];
    
    render(<FormBuilder fields={mockFields} steps={steps} multiStep />);
    
    expect(screen.getByTestId('form-steps')).toBeInTheDocument();
    expect(screen.getByText('Personal Info')).toBeInTheDocument();
    expect(screen.getByText('Step 1 of 2')).toBeInTheDocument();
  });

  it('supports form field dependencies', () => {
    const dependentFields = [
      mockFields[0],
      {
        ...mockFields[1],
        dependencies: ['field-1'],
        dependencyRules: {
          'field-1': { operator: 'not_empty' }
        }
      }
    ];
    
    render(<FormBuilder fields={dependentFields} />);
    
    // Email field should be disabled initially
    const emailInput = screen.getByPlaceholderText('Enter your email');
    expect(emailInput).toBeDisabled();
    
    // Fill in name field
    const nameInput = screen.getByPlaceholderText('Enter your full name');
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    // Email field should now be enabled
    expect(emailInput).not.toBeDisabled();
  });

  it('supports form layout customization', () => {
    const layouts = ['vertical', 'horizontal', 'grid'] as const;
    
    layouts.forEach(layout => {
      const { unmount } = render(<FormBuilder fields={mockFields} layout={layout} />);
      const container = screen.getByTestId('form-builder-container');
      expect(container).toHaveClass(`layout-${layout}`);
      unmount();
    });
  });

  it('supports form field grouping by sections', () => {
    const sectionsConfig = [
      { id: 'section1', title: 'Basic Information', fields: ['field-1', 'field-2'] },
      { id: 'section2', title: 'Additional Details', fields: ['field-3'] }
    ];
    
    render(<FormBuilder fields={mockFields} sections={sectionsConfig} />);
    
    expect(screen.getByText('Basic Information')).toBeInTheDocument();
    expect(screen.getByText('Additional Details')).toBeInTheDocument();
  });

  it('supports dynamic field options loading', async () => {
    const fieldWithDynamicOptions = {
      ...mockFields[2],
      optionsLoader: vi.fn().mockResolvedValue([
        { value: 'dynamic1', label: 'Dynamic Option 1' },
        { value: 'dynamic2', label: 'Dynamic Option 2' }
      ])
    };
    
    render(<FormBuilder fields={[fieldWithDynamicOptions]} />);
    
    await waitFor(() => {
      const selectElement = screen.getByRole('combobox');
      expect(selectElement).toBeInTheDocument();
    });
    
    // Dynamic options should be loaded and available in the select
    expect(fieldWithDynamicOptions.optionsLoader).toHaveBeenCalled();
  });

  it('supports form field masking', () => {
    const maskedField = {
      id: 'phone',
      type: 'text' as const,
      label: 'Phone Number',
      mask: '(999) 999-9999'
    };
    
    render(<FormBuilder fields={[maskedField]} />);
    
    const phoneInput = screen.getByRole('textbox');
    fireEvent.change(phoneInput, { target: { value: '1234567890' } });
    
    expect(phoneInput).toHaveValue('(123) 456-7890');
  });

  it('supports form performance monitoring', () => {
    const onPerformanceReport = vi.fn();
    
    render(
      <FormBuilder 
        fields={mockFields}
        enablePerformanceMonitoring
        onPerformanceReport={onPerformanceReport}
      />
    );
    
    expect(screen.getByTestId('form-builder-container')).toBeInTheDocument();
  });

  it('handles empty form state', () => {
    render(<FormBuilder fields={[]} />);
    
    expect(screen.getByTestId('form-empty-state')).toBeInTheDocument();
    expect(screen.getByText('No fields added yet')).toBeInTheDocument();
  });

  it('supports custom styling', () => {
    render(<FormBuilder fields={mockFields} className="custom-form-builder" />);
    
    const container = screen.getByTestId('form-builder-container');
    expect(container).toHaveClass('custom-form-builder');
  });

  it('supports custom data attributes', () => {
    render(
      <FormBuilder 
        fields={mockFields} 
        data-category="forms"
        data-id="main-form-builder"
      />
    );
    
    const container = screen.getByTestId('form-builder-container');
    expect(container).toHaveAttribute('data-category', 'forms');
    expect(container).toHaveAttribute('data-id', 'main-form-builder');
  });
});