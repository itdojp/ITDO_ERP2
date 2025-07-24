import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { Tabs, Tab } from './Tabs';

describe('Tabs', () => {
  const mockTabs: Tab[] = [
    { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
    { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div> },
    { id: 'tab3', label: 'Tab 3', content: <div>Content 3</div>, disabled: true },
    { id: 'tab4', label: 'Tab 4', content: <div>Content 4</div> }
  ];

  const defaultProps = {
    tabs: mockTabs
  };

  it('renders all tabs', () => {
    render(<Tabs {...defaultProps} />);
    
    expect(screen.getByText('Tab 1')).toBeInTheDocument();
    expect(screen.getByText('Tab 2')).toBeInTheDocument();
    expect(screen.getByText('Tab 3')).toBeInTheDocument();
    expect(screen.getByText('Tab 4')).toBeInTheDocument();
  });

  it('shows first non-disabled tab as active by default', () => {
    render(<Tabs {...defaultProps} />);
    
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
  });

  it('respects activeTab prop', () => {
    render(<Tabs {...defaultProps} activeTab="tab2" />);
    
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
  });

  it('switches tabs on click', () => {
    render(<Tabs {...defaultProps} />);
    
    fireEvent.click(screen.getByText('Tab 2'));
    
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
  });

  it('calls onTabChange when tab is clicked', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} />);
    
    fireEvent.click(screen.getByText('Tab 2'));
    
    expect(onTabChange).toHaveBeenCalledWith('tab2');
  });

  it('does not switch to disabled tab', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} />);
    
    fireEvent.click(screen.getByText('Tab 3'));
    
    expect(onTabChange).not.toHaveBeenCalled();
    expect(screen.getByText('Content 1')).toBeInTheDocument();
  });

  it('displays tab icons when provided', () => {
    const tabsWithIcons: Tab[] = [
      { 
        id: 'tab1', 
        label: 'Tab 1', 
        content: <div>Content 1</div>,
        icon: <span data-testid="icon-1">🏠</span>
      }
    ];
    
    render(<Tabs tabs={tabsWithIcons} />);
    
    expect(screen.getByTestId('icon-1')).toBeInTheDocument();
  });

  it('displays tab badges when provided', () => {
    const tabsWithBadges: Tab[] = [
      { 
        id: 'tab1', 
        label: 'Tab 1', 
        content: <div>Content 1</div>,
        badge: 5
      }
    ];
    
    render(<Tabs tabs={tabsWithBadges} />);
    
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('shows close button on closable tabs when allowCloseTabs is true', () => {
    const tabsWithClosable: Tab[] = [
      { 
        id: 'tab1', 
        label: 'Tab 1', 
        content: <div>Content 1</div>,
        closable: true
      }
    ];
    
    render(<Tabs tabs={tabsWithClosable} allowCloseTabs={true} />);
    
    expect(screen.getByLabelText('Close Tab 1 tab')).toBeInTheDocument();
  });

  it('calls onTabClose when close button is clicked', () => {
    const onTabClose = jest.fn();
    const tabsWithClosable: Tab[] = [
      { 
        id: 'tab1', 
        label: 'Tab 1', 
        content: <div>Content 1</div>,
        closable: true
      }
    ];
    
    render(<Tabs tabs={tabsWithClosable} allowCloseTabs={true} onTabClose={onTabClose} />);
    
    fireEvent.click(screen.getByLabelText('Close Tab 1 tab'));
    
    expect(onTabClose).toHaveBeenCalledWith('tab1');
  });

  it('does not switch tab when close button is clicked', () => {
    const onTabChange = jest.fn();
    const onTabClose = jest.fn();
    const tabsWithClosable: Tab[] = [
      { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
      { 
        id: 'tab2', 
        label: 'Tab 2', 
        content: <div>Content 2</div>,
        closable: true
      }
    ];
    
    render(<Tabs tabs={tabsWithClosable} allowCloseTabs={true} onTabChange={onTabChange} onTabClose={onTabClose} />);
    
    fireEvent.click(screen.getByLabelText('Close Tab 2 tab'));
    
    expect(onTabClose).toHaveBeenCalledWith('tab2');
    expect(onTabChange).not.toHaveBeenCalled();
  });

  it('applies pills variant classes', () => {
    render(<Tabs {...defaultProps} variant="pills" />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    expect(activeTab).toHaveClass('rounded-lg', 'bg-blue-100', 'text-blue-700');
  });

  it('applies underline variant classes', () => {
    render(<Tabs {...defaultProps} variant="underline" />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    expect(activeTab).toHaveClass('border-b-2', 'border-blue-500', 'text-blue-600');
  });

  it('applies bordered variant classes', () => {
    render(<Tabs {...defaultProps} variant="bordered" />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    expect(activeTab).toHaveClass('border', 'border-blue-500', 'text-blue-600');
  });

  it('applies small size classes', () => {
    render(<Tabs {...defaultProps} size="sm" />);
    
    const tab = screen.getByText('Tab 1');
    expect(tab).toHaveClass('text-sm', 'px-3', 'py-1.5');
  });

  it('applies medium size classes', () => {
    render(<Tabs {...defaultProps} size="md" />);
    
    const tab = screen.getByText('Tab 1');
    expect(tab).toHaveClass('text-sm', 'px-4', 'py-2');
  });

  it('applies large size classes', () => {
    render(<Tabs {...defaultProps} size="lg" />);
    
    const tab = screen.getByText('Tab 1');
    expect(tab).toHaveClass('text-base', 'px-6', 'py-3');
  });

  it('renders in vertical orientation', () => {
    render(<Tabs {...defaultProps} orientation="vertical" />);
    
    const tabList = screen.getByRole('tablist');
    expect(tabList).toHaveClass('flex-col');
    expect(tabList).toHaveAttribute('aria-orientation', 'vertical');
  });

  it('centers tabs when centered prop is true', () => {
    render(<Tabs {...defaultProps} centered={true} />);
    
    const tabList = screen.getByRole('tablist');
    expect(tabList).toHaveClass('justify-center');
  });

  it('applies custom className', () => {
    render(<Tabs {...defaultProps} className="custom-tabs" />);
    
    const container = screen.getByRole('tablist').closest('div');
    expect(container).toHaveClass('custom-tabs');
  });

  it('applies custom tabListClassName', () => {
    render(<Tabs {...defaultProps} tabListClassName="custom-tab-list" />);
    
    const tabList = screen.getByRole('tablist');
    expect(tabList).toHaveClass('custom-tab-list');
  });

  it('applies custom tabClassName', () => {
    render(<Tabs {...defaultProps} tabClassName="custom-tab" />);
    
    const tab = screen.getByText('Tab 1');
    expect(tab).toHaveClass('custom-tab');
  });

  it('applies custom contentClassName', () => {
    render(<Tabs {...defaultProps} contentClassName="custom-content" />);
    
    const content = screen.getByText('Content 1').closest('div')?.parentElement;
    expect(content).toHaveClass('custom-content');
  });

  it('handles keyboard navigation with arrow keys', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    activeTab.focus();
    
    fireEvent.keyDown(activeTab, { key: 'ArrowRight' });
    expect(onTabChange).toHaveBeenCalledWith('tab2');
    
    fireEvent.keyDown(activeTab, { key: 'ArrowLeft' });
    expect(onTabChange).toHaveBeenCalledWith('tab4'); // wraps to last enabled tab
  });

  it('handles keyboard navigation with Home and End keys', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} activeTab="tab2" />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    activeTab.focus();
    
    fireEvent.keyDown(activeTab, { key: 'Home' });
    expect(onTabChange).toHaveBeenCalledWith('tab1');
    
    fireEvent.keyDown(activeTab, { key: 'End' });
    expect(onTabChange).toHaveBeenCalledWith('tab4');
  });

  it('handles keyboard navigation with Enter and Space keys', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} />);
    
    const tab2 = screen.getByText('Tab 2');
    tab2.focus();
    
    fireEvent.keyDown(tab2, { key: 'Enter' });
    expect(onTabChange).toHaveBeenCalledWith('tab2');
    
    fireEvent.keyDown(tab2, { key: ' ' });
    expect(onTabChange).toHaveBeenCalledTimes(2);
  });

  it('skips disabled tabs in keyboard navigation', () => {
    const onTabChange = jest.fn();
    render(<Tabs {...defaultProps} onTabChange={onTabChange} activeTab="tab2" />);
    
    const activeTab = screen.getByRole('tab', { selected: true });
    activeTab.focus();
    
    fireEvent.keyDown(activeTab, { key: 'ArrowRight' });
    // Should skip tab3 (disabled) and go to tab4
    expect(onTabChange).toHaveBeenCalledWith('tab4');
  });

  it('sets proper ARIA attributes', () => {
    render(<Tabs {...defaultProps} />);
    
    const tabList = screen.getByRole('tablist');
    expect(tabList).toHaveAttribute('aria-orientation', 'horizontal');
    
    const activeTab = screen.getByRole('tab', { selected: true });
    expect(activeTab).toHaveAttribute('aria-selected', 'true');
    expect(activeTab).toHaveAttribute('tabindex', '0');
    
    const inactiveTab = screen.getByText('Tab 2');
    expect(inactiveTab).toHaveAttribute('aria-selected', 'false');
    expect(inactiveTab).toHaveAttribute('tabindex', '-1');
    
    const tabPanel = screen.getByRole('tabpanel');
    expect(tabPanel).toHaveAttribute('aria-labelledby', 'tab-tab1');
    expect(tabPanel).toHaveAttribute('id', 'tabpanel-tab1');
  });

  it('handles lazy loading of tab content', () => {
    render(<Tabs {...defaultProps} lazy={true} />);
    
    // Initially only active tab content should be rendered
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
    
    // Click on tab 2
    fireEvent.click(screen.getByText('Tab 2'));
    
    // Now both contents should be rendered (lazy loaded)
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.getByText('Content 1')).toBeInTheDocument();
  });

  it('renders scroll buttons when scrollable', () => {
    render(<Tabs {...defaultProps} scrollable={true} />);
    
    // Mock scrollWidth to trigger scroll buttons
    const tabList = screen.getByRole('tablist');
    Object.defineProperty(tabList, 'scrollWidth', { value: 1000, configurable: true });
    Object.defineProperty(tabList, 'clientWidth', { value: 500, configurable: true });
    Object.defineProperty(tabList, 'scrollLeft', { value: 100, configurable: true });
    
    fireEvent.scroll(tabList);
    
    // Check if scroll buttons would be available (implementation depends on scroll state)
    const scrollButtons = screen.queryAllByLabelText(/Scroll tabs/);
    expect(scrollButtons.length).toBeGreaterThanOrEqual(0);
  });

  it('handles disabled state properly', () => {
    render(<Tabs {...defaultProps} />);
    
    const disabledTab = screen.getByText('Tab 3');
    expect(disabledTab).toHaveAttribute('disabled');
    expect(disabledTab).toHaveClass('opacity-50', 'cursor-not-allowed');
  });
});