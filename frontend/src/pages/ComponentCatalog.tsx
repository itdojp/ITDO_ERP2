import React, { useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';

// Import all components for showcase
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { Slider } from '@/components/ui/Slider';
import { Progress } from '@/components/ui/Progress';
import { Spinner } from '@/components/ui/Spinner';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Checkbox } from '@/components/ui/Checkbox';
import { Radio } from '@/components/ui/Radio';
import { Textarea } from '@/components/ui/Textarea';
import { Tooltip } from '@/components/ui/Tooltip';
import { Dropdown } from '@/components/ui/Dropdown';
import { Tag } from '@/components/ui/Tag';
import { Stepper } from '@/components/ui/Stepper';
import { Upload } from '@/components/ui/Upload';
import { Divider } from '@/components/ui/Divider';
import { Loading } from '@/components/ui/Loading';
import { Empty } from '@/components/ui/Empty';
import { BackTop } from '@/components/ui/BackTop';
import { Icon } from '@/components/ui/Icon';
import { Image } from '@/components/ui/Image';
import { Carousel } from '@/components/ui/Carousel';
import { Calendar } from '@/components/ui/Calendar';
import { DatePicker } from '@/components/ui/DatePicker';
import { TimePicker } from '@/components/ui/TimePicker';
import { ColorPicker } from '@/components/ui/ColorPicker';
import { RichTextEditor } from '@/components/ui/RichTextEditor';
import { FileUpload } from '@/components/ui/FileUpload';
import { Autocomplete } from '@/components/ui/Autocomplete';
import { Notification } from '@/components/ui/Notification';
import { SearchBox } from '@/components/ui/SearchBox';
import { Skeleton } from '@/components/ui/Skeleton';
import { Toast } from '@/components/ui/Toast';
import { Toolbar } from '@/components/ui/Toolbar';
import { Panel } from '@/components/ui/Panel';
import { DataGrid } from '@/components/ui/DataGrid';
import { VirtualList } from '@/components/ui/VirtualList';
import { Dashboard } from '@/components/ui/Dashboard';
import { FormBuilder } from '@/components/ui/FormBuilder';
import { EnhancedDataTable } from '@/components/ui/EnhancedDataTable';
import { ChartSystem } from '@/components/ui/ChartSystem';
import { WorkflowEditor } from '@/components/ui/WorkflowEditor';
import { ReportBuilder } from '@/components/ui/ReportBuilder';
import { NotificationCenter } from '@/components/ui/NotificationCenter';
import { ThemeSystem } from '@/components/ui/ThemeSystem';
import { PermissionUI } from '@/components/ui/PermissionUI';
import { AnalyticsDashboard } from '@/components/ui/AnalyticsDashboard';

export interface ComponentInfo {
  id: string;
  name: string;
  category: string;
  description: string;
  component: React.ComponentType<any>;
  props?: Record<string, any>;
  variants?: Array<{
    name: string;
    props: Record<string, any>;
  }>;
  dependencies?: string[];
  complexity: 'basic' | 'intermediate' | 'advanced';
  status: 'stable' | 'beta' | 'experimental';
  version: string;
}

export interface ComponentCatalogProps {
  searchable?: boolean;
  filterable?: boolean;
  showCode?: boolean;
  showProps?: boolean;
  theme?: 'light' | 'dark';
  layout?: 'grid' | 'list';
  categories?: string[];
  className?: string;
  'data-testid'?: string;
}

const COMPONENT_REGISTRY: ComponentInfo[] = [
  // Basic Components
  {
    id: 'button',
    name: 'Button',
    category: 'Basic',
    description: 'Interactive button component with multiple variants and states',
    component: Button,
    props: { children: 'Click me', variant: 'primary' },
    variants: [
      { name: 'Primary', props: { children: 'Primary', variant: 'primary' } },
      { name: 'Secondary', props: { children: 'Secondary', variant: 'secondary' } },
      { name: 'Danger', props: { children: 'Danger', variant: 'danger' } },
      { name: 'Loading', props: { children: 'Loading', loading: true } },
      { name: 'Disabled', props: { children: 'Disabled', disabled: true } }
    ],
    complexity: 'basic',
    status: 'stable',
    version: '1.0.0'
  },
  {
    id: 'input',
    name: 'Input',
    category: 'Basic',
    description: 'Text input field with validation and various states',
    component: Input,
    props: { placeholder: 'Enter text...', type: 'text' },
    variants: [
      { name: 'Default', props: { placeholder: 'Default input' } },
      { name: 'Password', props: { type: 'password', placeholder: 'Password' } },
      { name: 'Email', props: { type: 'email', placeholder: 'Email address' } },
      { name: 'With Error', props: { placeholder: 'Invalid input', error: 'This field is required' } }
    ],
    complexity: 'basic',
    status: 'stable',
    version: '1.0.0'
  },
  {
    id: 'select',
    name: 'Select',
    category: 'Basic',
    description: 'Dropdown selection component with search and multi-select',
    component: Select,
    props: { 
      options: [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' },
        { value: 'option3', label: 'Option 3' }
      ],
      placeholder: 'Select an option...'
    },
    complexity: 'basic',
    status: 'stable',
    version: '1.0.0'
  },
  // Advanced Components
  {
    id: 'analytics-dashboard',
    name: 'Analytics Dashboard',
    category: 'Advanced',
    description: 'Comprehensive analytics dashboard with customizable widgets and real-time data',
    component: AnalyticsDashboard,
    props: {
      widgets: [
        {
          id: 'widget1',
          type: 'metric',
          title: 'Total Sales',
          position: { row: 1, col: 1, width: 3, height: 2 },
          data: [{
            id: 'sales',
            name: 'Total Sales',
            value: 125000,
            format: 'currency',
            trend: 'up',
            change: 12.5
          }]
        }
      ]
    },
    complexity: 'advanced',
    status: 'stable',
    version: '1.0.0'
  },
  {
    id: 'chart-system',
    name: 'Chart System',
    category: 'Advanced',
    description: 'Integrated charting system with multiple chart types and real-time updates',
    component: ChartSystem,
    props: {
      datasets: [{
        id: 'dataset1',
        name: 'Sample Data',
        data: [
          { x: 'Jan', y: 65 },
          { x: 'Feb', y: 78 },
          { x: 'Mar', y: 90 },
          { x: 'Apr', y: 81 }
        ],
        color: '#3b82f6'
      }],
      type: 'line',
      height: 300
    },
    complexity: 'advanced',
    status: 'stable',
    version: '1.0.0'
  },
  {
    id: 'form-builder',
    name: 'Form Builder',
    category: 'Advanced',
    description: 'Dynamic form builder with drag-and-drop field configuration',
    component: FormBuilder,
    props: {
      fields: [
        {
          id: 'name',
          type: 'text',
          label: 'Full Name',
          required: true,
          validation: { minLength: 2, maxLength: 50 }
        },
        {
          id: 'email',
          type: 'email',
          label: 'Email Address',
          required: true
        }
      ]
    },
    complexity: 'advanced',
    status: 'stable',
    version: '1.0.0'
  },
  {
    id: 'enhanced-data-table',
    name: 'Enhanced Data Table',
    category: 'Advanced',
    description: 'Feature-rich data table with sorting, filtering, and bulk operations',
    component: EnhancedDataTable,
    props: {
      columns: [
        { key: 'id', title: 'ID', sortable: true },
        { key: 'name', title: 'Name', sortable: true },
        { key: 'email', title: 'Email', sortable: true },
        { key: 'status', title: 'Status', filterable: true }
      ],
      data: [
        { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
        { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'active' }
      ]
    },
    complexity: 'advanced',
    status: 'stable',
    version: '1.0.0'
  },
  // More components can be added here...
];

const CATEGORIES = [
  'All',
  'Basic',
  'Layout',
  'Navigation',
  'Data Display',
  'Data Entry',
  'Feedback',
  'Advanced'
];

const COMPLEXITY_LEVELS = ['All', 'basic', 'intermediate', 'advanced'];
const STATUS_LEVELS = ['All', 'stable', 'beta', 'experimental'];

export const ComponentCatalog: React.FC<ComponentCatalogProps> = ({
  searchable = true,
  filterable = true,
  showCode = true,
  showProps = true,
  theme = 'light',
  layout = 'grid',
  categories,
  className,
  'data-testid': dataTestId = 'component-catalog'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedComplexity, setSelectedComplexity] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [showCodePanel, setShowCodePanel] = useState(false);
  const [currentLayout, setCurrentLayout] = useState(layout);

  // Filter components based on search and filters
  const filteredComponents = useMemo(() => {
    let filtered = COMPONENT_REGISTRY;

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(comp =>
        comp.name.toLowerCase().includes(query) ||
        comp.description.toLowerCase().includes(query) ||
        comp.category.toLowerCase().includes(query)
      );
    }

    // Apply category filter
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(comp => comp.category === selectedCategory);
    }

    // Apply complexity filter
    if (selectedComplexity !== 'All') {
      filtered = filtered.filter(comp => comp.complexity === selectedComplexity);
    }

    // Apply status filter
    if (selectedStatus !== 'All') {
      filtered = filtered.filter(comp => comp.status === selectedStatus);
    }

    // Apply categories prop filter
    if (categories?.length) {
      filtered = filtered.filter(comp => categories.includes(comp.category));
    }

    return filtered;
  }, [searchQuery, selectedCategory, selectedComplexity, selectedStatus, categories]);

  // Group components by category
  const groupedComponents = useMemo(() => {
    const grouped: Record<string, ComponentInfo[]> = {};
    
    filteredComponents.forEach(comp => {
      if (!grouped[comp.category]) {
        grouped[comp.category] = [];
      }
      grouped[comp.category].push(comp);
    });

    return grouped;
  }, [filteredComponents]);

  // Render component showcase
  const renderComponentShowcase = useCallback((component: ComponentInfo) => {
    const Component = component.component;
    
    return (
      <div
        key={component.id}
        className={cn(
          "bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow",
          theme === 'dark' && "bg-gray-800 border-gray-700"
        )}
        data-testid={`component-showcase-${component.id}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{component.name}</h3>
            <p className="text-sm text-gray-600 mt-1">{component.description}</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className={cn(
              "px-2 py-1 text-xs rounded-full",
              component.complexity === 'basic' && "bg-green-100 text-green-800",
              component.complexity === 'intermediate' && "bg-yellow-100 text-yellow-800",
              component.complexity === 'advanced' && "bg-red-100 text-red-800"
            )}>
              {component.complexity}
            </span>
            <span className={cn(
              "px-2 py-1 text-xs rounded-full",
              component.status === 'stable' && "bg-blue-100 text-blue-800",
              component.status === 'beta' && "bg-orange-100 text-orange-800",
              component.status === 'experimental' && "bg-purple-100 text-purple-800"
            )}>
              {component.status}
            </span>
          </div>
        </div>

        {/* Component Demo */}
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
          <div className="flex items-center justify-center min-h-[100px]">
            <Component {...component.props} />
          </div>
        </div>

        {/* Variants */}
        {component.variants && (
          <div className="mb-4">
            <h4 className="text-sm font-medium mb-2">Variants:</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {component.variants.map(variant => (
                <div
                  key={variant.name}
                  className="p-3 bg-gray-50 rounded border"
                >
                  <div className="text-xs font-medium text-gray-600 mb-2">
                    {variant.name}
                  </div>
                  <div className="flex items-center justify-center">
                    <Component {...variant.props} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>v{component.version}</span>
            {component.dependencies && (
              <span>• {component.dependencies.length} deps</span>
            )}
          </div>
          <div className="flex space-x-2">
            {showProps && (
              <button
                className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => setSelectedComponent(component.id)}
                data-testid={`view-props-${component.id}`}
              >
                Props
              </button>
            )}
            {showCode && (
              <button
                className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                onClick={() => {
                  setSelectedComponent(component.id);
                  setShowCodePanel(true);
                }}
                data-testid={`view-code-${component.id}`}
              >
                Code
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }, [theme, showProps, showCode]);

  // Render filters
  const renderFilters = () => {
    if (!filterable) return null;

    return (
      <div className="flex flex-wrap gap-4 mb-6" data-testid="catalog-filters">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm"
            data-testid="category-filter"
          >
            {CATEGORIES.map(category => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Complexity
          </label>
          <select
            value={selectedComplexity}
            onChange={(e) => setSelectedComplexity(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm"
            data-testid="complexity-filter"
          >
            {COMPLEXITY_LEVELS.map(level => (
              <option key={level} value={level}>
                {level === 'All' ? 'All' : level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm"
            data-testid="status-filter"
          >
            {STATUS_LEVELS.map(status => (
              <option key={status} value={status}>
                {status === 'All' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            className={cn(
              "px-3 py-2 text-sm border rounded transition-colors",
              currentLayout === 'grid'
                ? "bg-blue-500 text-white border-blue-500"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            )}
            onClick={() => setCurrentLayout('grid')}
            data-testid="grid-layout-button"
          >
            Grid
          </button>
          <button
            className={cn(
              "px-3 py-2 text-sm border rounded transition-colors ml-1",
              currentLayout === 'list'
                ? "bg-blue-500 text-white border-blue-500"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            )}
            onClick={() => setCurrentLayout('list')}
            data-testid="list-layout-button"
          >
            List
          </button>
        </div>
      </div>
    );
  };

  return (
    <div
      className={cn(
        "min-h-screen bg-gray-100 p-6",
        theme === 'dark' && "bg-gray-900 text-white",
        className
      )}
      data-testid={dataTestId}
    >
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Component Catalog</h1>
          <p className="text-gray-600">
            Interactive showcase of all UI components with live examples and documentation
          </p>
        </div>

        {/* Search */}
        {searchable && (
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="search-input"
            />
          </div>
        )}

        {/* Filters */}
        {renderFilters()}

        {/* Stats */}
        <div className="mb-6 flex items-center space-x-6 text-sm text-gray-600">
          <span>{filteredComponents.length} components</span>
          <span>{Object.keys(groupedComponents).length} categories</span>
          <span>{filteredComponents.filter(c => c.status === 'stable').length} stable</span>
        </div>

        {/* Components Grid/List */}
        <div className="space-y-8">
          {Object.entries(groupedComponents).map(([category, components]) => (
            <div key={category}>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">
                {category} ({components.length})
              </h2>
              <div className={cn(
                currentLayout === 'grid'
                  ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
                  : "space-y-4"
              )}>
                {components.map(renderComponentShowcase)}
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredComponents.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No components found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComponentCatalog;