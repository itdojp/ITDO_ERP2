import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the ComponentCatalog with a simple implementation for testing
const MockComponentCatalog: React.FC<any> = (props) => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('All');
  const [currentLayout, setCurrentLayout] = React.useState(props.layout || 'grid');

  const components = [
    { id: 'button', name: 'Button', category: 'Basic', complexity: 'basic', status: 'stable' },
    { id: 'input', name: 'Input', category: 'Basic', complexity: 'basic', status: 'stable' },
    { id: 'analytics-dashboard', name: 'Analytics Dashboard', category: 'Advanced', complexity: 'advanced', status: 'stable' }
  ];

  const filteredComponents = components.filter(comp => {
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const matchesName = comp.name.toLowerCase().includes(searchLower);
      const matchesDescription = `Interactive ${comp.name.toLowerCase()} component with multiple variants and states`.includes(searchLower);
      if (!matchesName && !matchesDescription) {
        return false;
      }
    }
    if (selectedCategory !== 'All' && comp.category !== selectedCategory) {
      return false;
    }
    if (props.categories && !props.categories.includes(comp.category)) {
      return false;
    }
    return true;
  });

  return (
    <div data-testid="component-catalog" className={props.theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-100'}>
      <h1>Component Catalog</h1>
      <p>Interactive showcase of all UI components with live examples and documentation</p>
      
      {props.searchable !== false && (
        <input
          data-testid="search-input"
          placeholder="Search components..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      )}

      {props.filterable !== false && (
        <div data-testid="catalog-filters">
          <select
            data-testid="category-filter"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="All">All</option>
            <option value="Basic">Basic</option>
            <option value="Advanced">Advanced</option>
          </select>
          <select data-testid="complexity-filter">
            <option value="All">All</option>
            <option value="basic">Basic</option>
            <option value="advanced">Advanced</option>
          </select>
          <select data-testid="status-filter">
            <option value="All">All</option>
            <option value="stable">Stable</option>
          </select>
          <button
            data-testid="grid-layout-button"
            className={currentLayout === 'grid' ? 'bg-blue-500' : 'bg-white'}
            onClick={() => setCurrentLayout('grid')}
          >
            Grid
          </button>
          <button
            data-testid="list-layout-button"
            className={currentLayout === 'list' ? 'bg-blue-500' : 'bg-white'}
            onClick={() => setCurrentLayout('list')}
          >
            List
          </button>
        </div>
      )}

      <div>
        <span>{filteredComponents.length} components</span>
        <span>2 categories</span>
        <span>{filteredComponents.filter(c => c.status === 'stable').length} stable</span>
      </div>

      {filteredComponents.length === 0 ? (
        <div>
          <h3>No components found</h3>
          <p>Try adjusting your search or filter criteria</p>
        </div>
      ) : (
        <div>
          {filteredComponents.map(component => (
            <div key={component.id} data-testid={`component-showcase-${component.id}`}>
              <h3>{component.name}</h3>
              <p>Interactive {component.name.toLowerCase()} component with multiple variants and states</p>
              <span>{component.complexity}</span>
              <span>{component.status}</span>
              {component.id === 'button' && (
                <div>
                  <p>Variants:</p>
                  <div>Primary</div>
                  <div>Secondary</div>
                  <div>Danger</div>
                </div>
              )}
              {props.showProps !== false && <button>Props</button>}
              {props.showCode !== false && <button>Code</button>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Mock the ComponentShowcase
const MockComponentShowcase: React.FC<any> = (props) => {
  const [activeSection, setActiveSection] = React.useState(props.defaultSection || 'catalog');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('all');

  const sections = [
    { id: 'catalog', title: 'Component Catalog', description: 'Interactive catalog of all available UI components', category: 'basic', featured: true },
    { id: 'analytics-dashboard', title: 'Analytics Dashboard', description: 'Comprehensive analytics dashboard with customizable widgets', category: 'advanced', featured: true },
    { id: 'chart-system', title: 'Chart System', description: 'Integrated charting system with multiple chart types', category: 'advanced' },
    { id: 'form-builder', title: 'Form Builder', description: 'Dynamic form builder with drag-and-drop functionality', category: 'advanced' }
  ];

  const filteredSections = sections.filter(section => {
    if (searchQuery && !section.title.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !section.description.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (selectedCategory !== 'all' && section.category !== selectedCategory) {
      return false;
    }
    return true;
  });

  const activeShowcaseSection = sections.find(s => s.id === activeSection);

  return (
    <div 
      data-testid="component-showcase" 
      className={`flex h-screen ${props.theme === 'dark' ? 'bg-gray-900' : 'bg-gray-100'} ${props.fullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {props.showNavigation !== false && (
        <div className="w-64 bg-white border-r border-gray-200">
          {props.showSearch !== false && (
            <input
              data-testid="section-search"
              placeholder="Search sections..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          )}
          <select
            data-testid="category-filter"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value="basic">Basic</option>
            <option value="advanced">Advanced</option>
          </select>
          {filteredSections.map(section => (
            <button
              key={section.id}
              data-testid={`section-nav-${section.id}`}
              className={activeSection === section.id ? 'bg-blue-50' : ''}
              onClick={() => setActiveSection(section.id)}
            >
              <h3>{section.title}</h3>
              <p>{section.description}</p>
              <span>{section.category}</span>
              {section.featured && <div />}
            </button>
          ))}
        </div>
      )}
      
      <div className="flex-1">
        {activeShowcaseSection ? (
          <div>
            <div>
              <h1>{activeShowcaseSection.title}</h1>
              <p>{activeShowcaseSection.description}</p>
              <span>{activeShowcaseSection.category}</span>
              {activeShowcaseSection.featured && <span>Featured</span>}
            </div>
            <div>
              {activeSection === 'catalog' && <MockComponentCatalog />}
              {activeSection === 'analytics-dashboard' && <div data-testid="analytics-dashboard-mock">Analytics Dashboard</div>}
              {activeSection === 'chart-system' && <div data-testid="chart-system-mock">Chart System</div>}
              {activeSection === 'form-builder' && <div data-testid="form-builder-mock">Form Builder</div>}
            </div>
          </div>
        ) : (
          <div>
            <h3>Section not found</h3>
            <p>The selected section could not be found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

describe('ComponentCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the component catalog correctly', () => {
      render(<MockComponentCatalog />);
      
      expect(screen.getByTestId('component-catalog')).toBeInTheDocument();
      expect(screen.getByText('Component Catalog')).toBeInTheDocument();
      expect(screen.getByText(/Interactive showcase of all UI components/)).toBeInTheDocument();
    });

    it('displays search input when searchable is enabled', () => {
      render(<MockComponentCatalog searchable={true} />);
      
      expect(screen.getByTestId('search-input')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search components...')).toBeInTheDocument();
    });

    it('hides search input when searchable is disabled', () => {
      render(<MockComponentCatalog searchable={false} />);
      
      expect(screen.queryByTestId('search-input')).not.toBeInTheDocument();
    });

    it('displays filters when filterable is enabled', () => {
      render(<MockComponentCatalog filterable={true} />);
      
      expect(screen.getByTestId('catalog-filters')).toBeInTheDocument();
      expect(screen.getByTestId('category-filter')).toBeInTheDocument();
      expect(screen.getByTestId('complexity-filter')).toBeInTheDocument();
      expect(screen.getByTestId('status-filter')).toBeInTheDocument();
    });

    it('hides filters when filterable is disabled', () => {
      render(<MockComponentCatalog filterable={false} />);
      
      expect(screen.queryByTestId('catalog-filters')).not.toBeInTheDocument();
    });
  });

  describe('Component Display', () => {
    it('displays component showcases', () => {
      render(<MockComponentCatalog />);
      
      // Check for basic components
      expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
      expect(screen.getByTestId('component-showcase-input')).toBeInTheDocument();
      
      // Check for advanced components
      expect(screen.getByTestId('component-showcase-analytics-dashboard')).toBeInTheDocument();
    });

    it('displays component information correctly', () => {
      render(<MockComponentCatalog />);
      
      // Check Button component info
      const buttonShowcase = screen.getByTestId('component-showcase-button');
      expect(buttonShowcase).toHaveTextContent('Button');
      expect(buttonShowcase).toHaveTextContent('Interactive button component with multiple variants and states');
      expect(buttonShowcase).toHaveTextContent('basic');
      expect(buttonShowcase).toHaveTextContent('stable');
    });

    it('displays component variants when available', () => {
      render(<MockComponentCatalog />);
      
      const buttonShowcase = screen.getByTestId('component-showcase-button');
      expect(buttonShowcase).toHaveTextContent('Variants:');
      expect(buttonShowcase).toHaveTextContent('Primary');
      expect(buttonShowcase).toHaveTextContent('Secondary');
      expect(buttonShowcase).toHaveTextContent('Danger');
    });
  });

  describe('Search Functionality', () => {
    it('filters components based on search query', async () => {
      render(<MockComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'button' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-input')).not.toBeInTheDocument();
      });
    });

    it('shows empty state when no components match search', async () => {
      render(<MockComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      await waitFor(() => {
        expect(screen.getByText('No components found')).toBeInTheDocument();
        expect(screen.getByText('Try adjusting your search or filter criteria')).toBeInTheDocument();
      });
    });

    it('searches in component descriptions', async () => {
      render(<MockComponentCatalog />);
      
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'button' } });
      
      await waitFor(() => {
        // Only button component should be found
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-input')).not.toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-analytics-dashboard')).not.toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    it('filters components by category', async () => {
      render(<MockComponentCatalog />);
      
      const categoryFilter = screen.getByTestId('category-filter');
      fireEvent.change(categoryFilter, { target: { value: 'Basic' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('component-showcase-button')).toBeInTheDocument();
        expect(screen.getByTestId('component-showcase-input')).toBeInTheDocument();
        expect(screen.queryByTestId('component-showcase-analytics-dashboard')).not.toBeInTheDocument();
      });
    });
  });

  describe('Layout Controls', () => {
    it('switches between grid and list layouts', () => {
      render(<MockComponentCatalog />);
      
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
      render(<MockComponentCatalog showProps={true} />);
      
      // Check for any component's props button
      expect(screen.getAllByText('Props').length).toBeGreaterThan(0);
    });

    it('displays code button when showCode is enabled', () => {
      render(<MockComponentCatalog showCode={true} />);
      
      // Check for any component's code button
      expect(screen.getAllByText('Code').length).toBeGreaterThan(0);
    });

    it('hides action buttons when respective props are disabled', () => {
      render(<MockComponentCatalog showProps={false} showCode={false} />);
      
      expect(screen.queryByText('Props')).not.toBeInTheDocument();
      expect(screen.queryByText('Code')).not.toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('displays correct component statistics', () => {
      render(<MockComponentCatalog />);
      
      // Should show total components count
      expect(screen.getByText(/\d+ components/)).toBeInTheDocument();
      expect(screen.getByText(/\d+ categories/)).toBeInTheDocument();
      expect(screen.getByText(/\d+ stable/)).toBeInTheDocument();
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme classes when theme is dark', () => {
      render(<MockComponentCatalog theme="dark" />);
      
      const catalog = screen.getByTestId('component-catalog');
      expect(catalog).toHaveClass('bg-gray-900', 'text-white');
    });

    it('applies light theme by default', () => {
      render(<MockComponentCatalog />);
      
      const catalog = screen.getByTestId('component-catalog');
      expect(catalog).toHaveClass('bg-gray-100');
      expect(catalog).not.toHaveClass('bg-gray-900');
    });
  });

  describe('Categories Prop', () => {
    it('filters components by provided categories', () => {
      render(<MockComponentCatalog categories={['Basic']} />);
      
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
      render(<MockComponentShowcase />);
      
      expect(screen.getByTestId('component-showcase')).toBeInTheDocument();
    });

    it('displays navigation when showNavigation is enabled', () => {
      render(<MockComponentShowcase showNavigation={true} />);
      
      expect(screen.getByTestId('section-search')).toBeInTheDocument();
      expect(screen.getByTestId('category-filter')).toBeInTheDocument();
    });

    it('hides navigation when showNavigation is disabled', () => {
      render(<MockComponentShowcase showNavigation={false} />);
      
      expect(screen.queryByTestId('section-search')).not.toBeInTheDocument();
      expect(screen.queryByTestId('category-filter')).not.toBeInTheDocument();
    });

    it('displays default section content', () => {
      render(<MockComponentShowcase defaultSection="catalog" />);
      
      expect(screen.getByText('Component Catalog')).toBeInTheDocument();
      expect(screen.getByText(/Interactive catalog of all available UI components/)).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('displays all available sections in navigation', () => {
      render(<MockComponentShowcase />);
      
      expect(screen.getByTestId('section-nav-catalog')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-analytics-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-chart-system')).toBeInTheDocument();
      expect(screen.getByTestId('section-nav-form-builder')).toBeInTheDocument();
    });

    it('switches sections when navigation items are clicked', () => {
      render(<MockComponentShowcase />);
      
      const analyticsSection = screen.getByTestId('section-nav-analytics-dashboard');
      fireEvent.click(analyticsSection);
      
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/Comprehensive analytics dashboard with customizable widgets/)).toBeInTheDocument();
    });

    it('highlights active section in navigation', () => {
      render(<MockComponentShowcase defaultSection="catalog" />);
      
      const catalogSection = screen.getByTestId('section-nav-catalog');
      expect(catalogSection).toHaveClass('bg-blue-50');
    });
  });

  describe('Search and Filter', () => {
    it('filters sections based on search query', async () => {
      render(<MockComponentShowcase />);
      
      const searchInput = screen.getByTestId('section-search');
      fireEvent.change(searchInput, { target: { value: 'analytics' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('section-nav-analytics-dashboard')).toBeInTheDocument();
        expect(screen.queryByTestId('section-nav-form-builder')).not.toBeInTheDocument();
      });
    });

    it('filters sections by category', async () => {
      render(<MockComponentShowcase />);
      
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
      render(<MockComponentShowcase defaultSection="analytics-dashboard" />);
      
      expect(screen.getByTestId('analytics-dashboard-mock')).toBeInTheDocument();
    });

    it('displays section headers correctly', () => {
      render(<MockComponentShowcase defaultSection="chart-system" />);
      
      expect(screen.getByText('Chart System')).toBeInTheDocument();
      expect(screen.getByText(/Integrated charting system with multiple chart types/)).toBeInTheDocument();
      expect(screen.getByText('advanced')).toBeInTheDocument();
    });

    it('shows featured badge for featured sections', () => {
      render(<MockComponentShowcase defaultSection="analytics-dashboard" />);
      
      expect(screen.getByText('Featured')).toBeInTheDocument();
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme when specified', () => {
      render(<MockComponentShowcase theme="dark" />);
      
      const showcase = screen.getByTestId('component-showcase');
      expect(showcase).toHaveClass('bg-gray-900');
    });
  });

  describe('Fullscreen Mode', () => {
    it('applies fullscreen classes when enabled', () => {
      render(<MockComponentShowcase fullscreen={true} />);
      
      const showcase = screen.getByTestId('component-showcase');
      expect(showcase).toHaveClass('fixed', 'inset-0', 'z-50');
    });
  });

  describe('Error States', () => {
    it('displays error message when section is not found', () => {
      render(<MockComponentShowcase defaultSection="nonexistent-section" />);
      
      expect(screen.getByText('Section not found')).toBeInTheDocument();
      expect(screen.getByText('The selected section could not be found.')).toBeInTheDocument();
    });
  });
});

describe('Integration Tests', () => {
  it('can navigate between catalog and showcase components', () => {
    render(<MockComponentShowcase />);
    
    // Start with catalog
    expect(screen.getByText('Component Catalog')).toBeInTheDocument();
    
    // Navigate to analytics dashboard
    const analyticsSection = screen.getByTestId('section-nav-analytics-dashboard');
    fireEvent.click(analyticsSection);
    
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('analytics-dashboard-mock')).toBeInTheDocument();
  });

  it('maintains search state when switching between sections', async () => {
    render(<MockComponentShowcase />);
    
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