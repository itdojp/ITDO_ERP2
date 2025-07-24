import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ComponentCatalog } from '@/pages/ComponentCatalog';
import { ComponentShowcase } from '@/pages/ComponentShowcase';

// Mock basic components
vi.mock('@/components/ui/Button', () => ({
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>
}));

vi.mock('@/components/ui/Input', () => ({
  Input: (props: any) => <input {...props} />
}));

vi.mock('@/components/ui/Select', () => ({
  Select: ({ options, placeholder, ...props }: any) => (
    <select {...props}>
      <option value="">{placeholder}</option>
      {options?.map((opt: any) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  )
}));

// Mock advanced components
vi.mock('@/components/ui/AnalyticsDashboard', () => ({
  AnalyticsDashboard: () => <div data-testid="analytics-dashboard-mock">Analytics Dashboard</div>
}));

vi.mock('@/components/ui/ChartSystem', () => ({
  ChartSystem: () => <div data-testid="chart-system-mock">Chart System</div>
}));

vi.mock('@/components/ui/FormBuilder', () => ({
  FormBuilder: () => <div data-testid="form-builder-mock">Form Builder</div>
}));

vi.mock('@/components/ui/EnhancedDataTable', () => ({
  EnhancedDataTable: () => <div data-testid="enhanced-data-table-mock">Enhanced Data Table</div>
}));

vi.mock('@/components/ui/WorkflowEditor', () => ({
  WorkflowEditor: () => <div data-testid="workflow-editor-mock">Workflow Editor</div>
}));

vi.mock('@/components/ui/NotificationCenter', () => ({
  NotificationCenter: () => <div data-testid="notification-center-mock">Notification Center</div>
}));

vi.mock('@/components/ui/ThemeSystem', () => ({
  ThemeSystem: () => <div data-testid="theme-system-mock">Theme System</div>
}));

vi.mock('@/components/ui/PermissionUI', () => ({
  PermissionUI: () => <div data-testid="permission-ui-mock">Permission UI</div>
}));

// Mock remaining UI components individually
vi.mock('@/components/ui/Switch', () => ({
  Switch: () => <div data-testid="switch-mock">Switch</div>
}));

vi.mock('@/components/ui/Slider', () => ({
  Slider: () => <div data-testid="slider-mock">Slider</div>
}));

vi.mock('@/components/ui/Progress', () => ({
  Progress: () => <div data-testid="progress-mock">Progress</div>
}));

vi.mock('@/components/ui/Spinner', () => ({
  Spinner: () => <div data-testid="spinner-mock">Spinner</div>
}));

vi.mock('@/components/ui/Avatar', () => ({
  Avatar: () => <div data-testid="avatar-mock">Avatar</div>
}));

vi.mock('@/components/ui/Badge', () => ({
  Badge: () => <div data-testid="badge-mock">Badge</div>
}));

vi.mock('@/components/ui/Checkbox', () => ({
  Checkbox: () => <div data-testid="checkbox-mock">Checkbox</div>
}));

vi.mock('@/components/ui/Radio', () => ({
  Radio: () => <div data-testid="radio-mock">Radio</div>
}));

vi.mock('@/components/ui/Textarea', () => ({
  Textarea: () => <div data-testid="textarea-mock">Textarea</div>
}));

vi.mock('@/components/ui/Tooltip', () => ({
  Tooltip: () => <div data-testid="tooltip-mock">Tooltip</div>
}));

vi.mock('@/components/ui/Dropdown', () => ({
  Dropdown: () => <div data-testid="dropdown-mock">Dropdown</div>
}));

vi.mock('@/components/ui/Tag', () => ({
  Tag: () => <div data-testid="tag-mock">Tag</div>
}));

vi.mock('@/components/ui/Stepper', () => ({
  Stepper: () => <div data-testid="stepper-mock">Stepper</div>
}));

vi.mock('@/components/ui/Upload', () => ({
  Upload: () => <div data-testid="upload-mock">Upload</div>
}));

vi.mock('@/components/ui/Divider', () => ({
  Divider: () => <div data-testid="divider-mock">Divider</div>
}));

vi.mock('@/components/ui/Loading', () => ({
  Loading: () => <div data-testid="loading-mock">Loading</div>
}));

vi.mock('@/components/ui/Empty', () => ({
  Empty: () => <div data-testid="empty-mock">Empty</div>
}));

vi.mock('@/components/ui/BackTop', () => ({
  BackTop: () => <div data-testid="backtop-mock">BackTop</div>
}));

vi.mock('@/components/ui/Icon', () => ({
  Icon: () => <div data-testid="icon-mock">Icon</div>
}));

vi.mock('@/components/ui/Image', () => ({
  Image: () => <div data-testid="image-mock">Image</div>
}));

vi.mock('@/components/ui/Carousel', () => ({
  Carousel: () => <div data-testid="carousel-mock">Carousel</div>
}));

vi.mock('@/components/ui/Calendar', () => ({
  Calendar: () => <div data-testid="calendar-mock">Calendar</div>
}));

vi.mock('@/components/ui/DatePicker', () => ({
  DatePicker: () => <div data-testid="datepicker-mock">DatePicker</div>
}));

vi.mock('@/components/ui/TimePicker', () => ({
  TimePicker: () => <div data-testid="timepicker-mock">TimePicker</div>
}));

vi.mock('@/components/ui/ColorPicker', () => ({
  ColorPicker: () => <div data-testid="colorpicker-mock">ColorPicker</div>
}));

vi.mock('@/components/ui/RichTextEditor', () => ({
  RichTextEditor: () => <div data-testid="richtexteditor-mock">RichTextEditor</div>
}));

vi.mock('@/components/ui/FileUpload', () => ({
  FileUpload: () => <div data-testid="fileupload-mock">FileUpload</div>
}));

vi.mock('@/components/ui/Autocomplete', () => ({
  Autocomplete: () => <div data-testid="autocomplete-mock">Autocomplete</div>
}));

vi.mock('@/components/ui/Notification', () => ({
  Notification: () => <div data-testid="notification-mock">Notification</div>
}));

vi.mock('@/components/ui/SearchBox', () => ({
  SearchBox: () => <div data-testid="searchbox-mock">SearchBox</div>
}));

vi.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton-mock">Skeleton</div>
}));

vi.mock('@/components/ui/Toast', () => ({
  Toast: () => <div data-testid="toast-mock">Toast</div>
}));

vi.mock('@/components/ui/Toolbar', () => ({
  Toolbar: () => <div data-testid="toolbar-mock">Toolbar</div>
}));

vi.mock('@/components/ui/Panel', () => ({
  Panel: () => <div data-testid="panel-mock">Panel</div>
}));

vi.mock('@/components/ui/DataGrid', () => ({
  DataGrid: () => <div data-testid="datagrid-mock">DataGrid</div>
}));

vi.mock('@/components/ui/VirtualList', () => ({
  VirtualList: () => <div data-testid="virtuallist-mock">VirtualList</div>
}));

vi.mock('@/components/ui/Dashboard', () => ({
  Dashboard: () => <div data-testid="dashboard-mock">Dashboard</div>
}));

describe('ComponentCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the component catalog correctly', () => {
      render(<ComponentCatalog />);
      
      expect(screen.getByTestId('component-catalog')).toBeInTheDocument();
      expect(screen.getByText('Component Catalog')).toBeInTheDocument();
      expect(screen.getByText(/Interactive showcase of all UI components/)).toBeInTheDocument();
    });

    it('displays search input when searchable is enabled', () => {
      render(<ComponentCatalog searchable={true} />);
      
      expect(screen.getByTestId('search-input')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search components...')).toBeInTheDocument();
    });

    it('hides search input when searchable is disabled', () => {
      render(<ComponentCatalog searchable={false} />);
      
      expect(screen.queryByTestId('search-input')).not.toBeInTheDocument();
    });

    it('displays filters when filterable is enabled', () => {
      render(<ComponentCatalog filterable={true} />);
      
      expect(screen.getByTestId('catalog-filters')).toBeInTheDocument();
      expect(screen.getByTestId('category-filter')).toBeInTheDocument();
      expect(screen.getByTestId('complexity-filter')).toBeInTheDocument();
      expect(screen.getByTestId('status-filter')).toBeInTheDocument();
    });

    it('hides filters when filterable is disabled', () => {
      render(<ComponentCatalog filterable={false} />);
      
      expect(screen.queryByTestId('catalog-filters')).not.toBeInTheDocument();
    });
  });

  describe('Component Display', () => {
    it('displays component showcases', () => {
      render(<ComponentCatalog />);
      
      // Check for basic components
      expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
      expect(screen.getByTestId('component-showcase-input')).toBeInTheDocument();
      expect(screen.getByTestId('component-showcase-select')).toBeInTheDocument();
      
      // Check for advanced components
      expect(screen.getByTestId('component-showcase-analytics-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('component-showcase-chart-system')).toBeInTheDocument();
    });

    it('displays component information correctly', () => {
      render(<ComponentCatalog />);
      
      // Check Button component info
      const buttonShowcase = screen.getByTestId('component-showcase-button');
      expect(buttonShowcase).toHaveTextContent('Button');
      expect(buttonShowcase).toHaveTextContent('Interactive button component with multiple variants and states');
      expect(buttonShowcase).toHaveTextContent('basic');
      expect(buttonShowcase).toHaveTextContent('stable');
    });

    it('displays component variants when available', () => {
      render(<ComponentCatalog />);
      
      const buttonShowcase = screen.getByTestId('component-showcase-button');
      expect(buttonShowcase).toHaveTextContent('Variants:');
      expect(buttonShowcase).toHaveTextContent('Primary');
      expect(buttonShowcase).toHaveTextContent('Secondary');
      expect(buttonShowcase).toHaveTextContent('Danger');
    });
  });

  describe('Search Functionality', () => {
    it('filters components based on search query', async () => {
      render(<ComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'button' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-input')).not.toBeInTheDocument();
      });
    });

    it('shows empty state when no components match search', async () => {
      render(<ComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      await waitFor(() => {
        expect(screen.getByText('No components found')).toBeInTheDocument();
        expect(screen.getByText('Try adjusting your search or filter criteria')).toBeInTheDocument();
      });
    });

    it('searches in component descriptions', async () => {
      render(<ComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'interactive' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    it('filters components by category', async () => {
      render(<ComponentCatalog />);
      
      const categoryFilter = screen.getByTestId('category-filter');
      fireEvent.change(categoryFilter, { target: { value: 'Basic' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.getByTestId('component-showcase-input')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-analytics-dashboard')).not.toBeInTheDocument();
      });
    });

    it('filters components by complexity', async () => {
      render(<ComponentCatalog />);
      
      const complexityFilter = screen.getByTestId('complexity-filter');
      fireEvent.change(complexityFilter, { target: { value: 'advanced' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-analytics-dashboard')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-button')).not.toBeInTheDocument();
      });
    });

    it('filters components by status', async () => {
      render(<ComponentCatalog />);
      
      const statusFilter = screen.getByTestId('status-filter');
      fireEvent.change(statusFilter, { target: { value: 'stable' } });
      
      await waitFor(() => {
        // All components in our mock registry are stable
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.getByTestId('component-showcase-analytics-dashboard')).toBeInTheDocument();
      });
    });
  });

  describe('Layout Controls', () => {
    it('switches between grid and list layouts', () => {
      render(<ComponentCatalog />);
      
      const gridButton = screen.getByTestId('grid-layout-button');
      const listButton = screen.getByTestId('list-layout-button');
      
      expect(gridButton).toHaveClass('bg-blue-500'); // Default is grid
      expect(listButton).toHaveClass('bg-white');
      
      fireEvent.click(listButton);
      
      expect(listButton).toHaveClass('bg-blue-500');
      expect(gridButton).toHaveClass('bg-white');
    });
  });

  describe('Component Actions', () => {
    it('displays props button when showProps is enabled', () => {
      render(<ComponentCatalog showProps={true} />);
      
      // Check for any component's props button
      expect(screen.getAllByText('Props').length).toBeGreaterThan(0);
    });

    it('displays code button when showCode is enabled', () => {
      render(<ComponentCatalog showCode={true} />);
      
      // Check for any component's code button
      expect(screen.getAllByText('Code').length).toBeGreaterThan(0);
    });

    it('hides action buttons when respective props are disabled', () => {
      render(<ComponentCatalog showProps={false} showCode={false} />);
      
      expect(screen.queryByText('Props')).not.toBeInTheDocument();
      expect(screen.queryByText('Code')).not.toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('displays correct component statistics', () => {
      render(<ComponentCatalog />);
      
      // Should show total components count
      expect(screen.getByText(/\d+ components/)).toBeInTheDocument();
      expect(screen.getByText(/\d+ categories/)).toBeInTheDocument();
      expect(screen.getByText(/\d+ stable/)).toBeInTheDocument();
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme classes when theme is dark', () => {
      render(<ComponentCatalog theme="dark" />);
      
      const catalog = screen.getByTestId('component-catalog');
      expect(catalog).toHaveClass('bg-gray-900', 'text-white');
    });

    it('applies light theme by default', () => {
      render(<ComponentCatalog />);
      
      const catalog = screen.getByTestId('component-catalog');
      expect(catalog).toHaveClass('bg-gray-100');
      expect(catalog).not.toHaveClass('bg-gray-900');
    });
  });

  describe('Categories Prop', () => {
    it('filters components by provided categories', () => {
      render(<ComponentCatalog categories={['Basic']} />);
      
      // Should only show basic components
      expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
      expect(screen.queryByTestId('component-showcase-analytics-dashboard')).not.toBeInTheDocument();
    });
  });
});

describe('ComponentShowcase', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the component showcase correctly', () => {
      render(<ComponentShowcase />);
      
      expect(screen.getByTestId('component-showcase')).toBeInTheDocument();
    });

    it('displays navigation when showNavigation is enabled', () => {
      render(<ComponentShowcase showNavigation={true} />);
      
      expect(screen.getByTestId('section-search')).toBeInTheDocument();
      expect(screen.getByTestId('category-filter')).toBeInTheDocument();
    });

    it('hides navigation when showNavigation is disabled', () => {
      render(<ComponentShowcase showNavigation={false} />);
      
      expect(screen.queryByTestId('section-search')).not.toBeInTheDocument();
      expect(screen.queryByTestId('category-filter')).not.toBeInTheDocument();
    });

    it('displays default section content', () => {
      render(<ComponentShowcase defaultSection="catalog" />);
      
      expect(screen.getByText('Component Catalog')).toBeInTheDocument();
      expect(screen.getByText(/Interactive catalog of all available UI components/)).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('displays all available sections in navigation', () => {
      render(<ComponentShowcase />);
      
      expect(screen.getByTestId('section-nav-catalog')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-analytics-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-chart-system')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-form-builder')).toBeInTheDocument();
    });

    it('switches sections when navigation items are clicked', () => {
      render(<ComponentShowcase />);
      
      const analyticsSection = screen.getByTestId('section-nav-analytics-dashboard');
      fireEvent.click(analyticsSection);
      
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/Comprehensive analytics dashboard with customizable widgets/)).toBeInTheDocument();
    });

    it('highlights active section in navigation', () => {
      render(<ComponentShowcase defaultSection="catalog" />);
      
      const catalogSection = screen.getByTestId('section-nav-catalog');
      expect(catalogSection).toHaveClass('bg-blue-50');
    });
  });

  describe('Search and Filter', () => {
    it('filters sections based on search query', async () => {
      render(<ComponentShowcase />);
      
      const searchInput = screen.getByTestId('section-search');
      fireEvent.change(searchInput, { target: { value: 'analytics' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('section-nav-analytics-dashboard')).toBeInTheDocument();
        expect(screen.queryByTestId('section-nav-form-builder')).not.toBeInTheDocument();
      });
    });

    it('filters sections by category', async () => {
      render(<ComponentShowcase />);
      
      const categoryFilter = screen.getByTestId('category-filter');
      fireEvent.change(categoryFilter, { target: { value: 'basic' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('section-nav-catalog')).toBeInTheDocument();
        expect(screen.queryByTestId('section-nav-analytics-dashboard')).not.toBeInTheDocument();
      });
    });
  });

  describe('Section Content', () => {
    it('renders section components with correct props', () => {
      render(<ComponentShowcase defaultSection="analytics-dashboard" />);
      
      expect(screen.getByTestId('analytics-dashboard-mock')).toBeInTheDocument();
    });

    it('displays section headers correctly', () => {
      render(<ComponentShowcase defaultSection="chart-system" />);
      
      expect(screen.getByText('Chart System')).toBeInTheDocument();
      expect(screen.getByText(/Integrated charting system with multiple chart types/)).toBeInTheDocument();
      expect(screen.getByText('advanced')).toBeInTheDocument();
    });

    it('shows featured badge for featured sections', () => {
      render(<ComponentShowcase defaultSection="analytics-dashboard" />);
      
      expect(screen.getByText('Featured')).toBeInTheDocument();
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme when specified', () => {
      render(<ComponentShowcase theme="dark" />);
      
      const showcase = screen.getByTestId('component-showcase');
      expect(showcase).toHaveClass('bg-gray-900');
    });
  });

  describe('Fullscreen Mode', () => {
    it('applies fullscreen classes when enabled', () => {
      render(<ComponentShowcase fullscreen={true} />);
      
      const showcase = screen.getByTestId('component-showcase');
      expect(showcase).toHaveClass('fixed', 'inset-0', 'z-50');
    });
  });

  describe('Error States', () => {
    it('displays error message when section is not found', () => {
      render(<ComponentShowcase defaultSection="nonexistent-section" />);
      
      expect(screen.getByText('Section not found')).toBeInTheDocument();
      expect(screen.getByText('The selected section could not be found.')).toBeInTheDocument();
    });
  });
});

describe('Integration Tests', () => {
  it('can navigate between catalog and showcase components', () => {
    render(<ComponentShowcase />);
    
    // Start with catalog
    expect(screen.getByText('Component Catalog')).toBeInTheDocument();
    
    // Navigate to analytics dashboard
    const analyticsSection = screen.getByTestId('section-nav-analytics-dashboard');
    fireEvent.click(analyticsSection);
    
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('analytics-dashboard-mock')).toBeInTheDocument();
  });

  it('maintains search state when switching between sections', async () => {
    render(<ComponentShowcase />);
    
    const searchInput = screen.getByTestId('section-search');
    fireEvent.change(searchInput, { target: { value: 'dashboard' } });
    
    await waitFor(() => {
      expect(screen.getByTestId('section-nav-analytics-dashboard')).toBeInTheDocument();
      expect(screen.queryByTestId('section-nav-form-builder')).not.toBeInTheDocument();
    });
    
    // Click on analytics dashboard
    const analyticsSection = screen.getByTestId('section-nav-analytics-dashboard');
    fireEvent.click(analyticsSection);
    
    // Search should still be active
    expect(searchInput).toHaveValue('dashboard');
  });
});