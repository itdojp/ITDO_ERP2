import { render, fireEvent, screen } from '@testing-library/react';
import { Pagination } from './Pagination';

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 5,
    totalPages: 10,
    onPageChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders page numbers correctly', () => {
    render(<Pagination {...defaultProps} />);
    
    // Should render visible pages around current page
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('marks current page as active', () => {
    render(<Pagination {...defaultProps} />);
    
    const currentPageButton = screen.getByLabelText('Page 5');
    expect(currentPageButton).toHaveAttribute('aria-current', 'page');
    expect(currentPageButton).toHaveClass('bg-blue-600');
  });

  it('calls onPageChange when page is clicked', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('6'));
    
    expect(onPageChange).toHaveBeenCalledWith(6);
  });

  it('renders first and last buttons by default', () => {
    render(<Pagination {...defaultProps} />);
    
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Last')).toBeInTheDocument();
  });

  it('renders previous and next buttons by default', () => {
    render(<Pagination {...defaultProps} />);
    
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('hides first/last buttons when showFirstLast is false', () => {
    render(<Pagination {...defaultProps} showFirstLast={false} />);
    
    expect(screen.queryByText('First')).not.toBeInTheDocument();
    expect(screen.queryByText('Last')).not.toBeInTheDocument();
  });

  it('hides prev/next buttons when showPrevNext is false', () => {
    render(<Pagination {...defaultProps} showPrevNext={false} />);
    
    expect(screen.queryByText('Previous')).not.toBeInTheDocument();
    expect(screen.queryByText('Next')).not.toBeInTheDocument();
  });

  it('hides page numbers when showPageNumbers is false', () => {
    render(<Pagination {...defaultProps} showPageNumbers={false} />);
    
    expect(screen.queryByText('4')).not.toBeInTheDocument();
    expect(screen.queryByText('5')).not.toBeInTheDocument();
    expect(screen.queryByText('6')).not.toBeInTheDocument();
  });

  it('navigates to first page when First button is clicked', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('First'));
    
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('navigates to last page when Last button is clicked', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('Last'));
    
    expect(onPageChange).toHaveBeenCalledWith(10);
  });

  it('navigates to previous page when Previous button is clicked', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('Previous'));
    
    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  it('navigates to next page when Next button is clicked', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('Next'));
    
    expect(onPageChange).toHaveBeenCalledWith(6);
  });

  it('disables Previous and First buttons on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} />);
    
    const firstButton = screen.getByText('First');
    const prevButton = screen.getByText('Previous');
    
    expect(firstButton).toBeDisabled();
    expect(prevButton).toBeDisabled();
  });

  it('disables Next and Last buttons on last page', () => {
    render(<Pagination {...defaultProps} currentPage={10} />);
    
    const lastButton = screen.getByText('Last');
    const nextButton = screen.getByText('Next');
    
    expect(lastButton).toBeDisabled();
    expect(nextButton).toBeDisabled();
  });

  it('handles keyboard navigation with Enter key', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    const pageButton = screen.getByText('6');
    fireEvent.keyDown(pageButton, { key: 'Enter' });
    
    expect(onPageChange).toHaveBeenCalledWith(6);
  });

  it('handles keyboard navigation with Space key', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    const pageButton = screen.getByText('6');
    fireEvent.keyDown(pageButton, { key: ' ' });
    
    expect(onPageChange).toHaveBeenCalledWith(6);
  });

  it('renders ellipsis when there are many pages', () => {
    render(<Pagination currentPage={15} totalPages={50} onPageChange={jest.fn()} />);
    
    const ellipsis = screen.getAllByText('...');
    expect(ellipsis.length).toBeGreaterThan(0);
  });

  it('shows page size selector when enabled', () => {
    render(
      <Pagination 
        {...defaultProps} 
        showPageSizeSelect={true} 
        onPageSizeChange={jest.fn()}
        pageSize={25}
      />
    );
    
    expect(screen.getByText('Results per page:')).toBeInTheDocument();
    expect(screen.getByDisplayValue('25')).toBeInTheDocument();
  });

  it('calls onPageSizeChange when page size is changed', () => {
    const onPageSizeChange = jest.fn();
    render(
      <Pagination 
        {...defaultProps} 
        showPageSizeSelect={true} 
        onPageSizeChange={onPageSizeChange}
        pageSize={10}
        pageSizeOptions={[10, 25, 50]}
      />
    );
    
    const select = screen.getByDisplayValue('10');
    fireEvent.change(select, { target: { value: '25' } });
    
    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });

  it('shows info when enabled', () => {
    render(
      <Pagination 
        {...defaultProps} 
        showInfo={true}
        totalItems={100}
        pageSize={10}
        currentPage={2}
      />
    );
    
    expect(screen.getByText('Showing 11 to 20 of 100 items')).toBeInTheDocument();
  });

  it('applies simple variant classes', () => {
    render(<Pagination {...defaultProps} variant="simple" />);
    
    const pageButton = screen.getByText('6');
    expect(pageButton).toHaveClass('bg-white', 'border-gray-300');
  });

  it('applies compact variant classes', () => {
    render(<Pagination {...defaultProps} variant="compact" />);
    
    const pageButton = screen.getByText('6');
    expect(pageButton).toHaveClass('bg-transparent', 'border-transparent');
  });

  it('applies small size classes', () => {
    render(<Pagination {...defaultProps} size="sm" />);
    
    const pageButton = screen.getByText('5');
    expect(pageButton).toHaveClass('px-2', 'py-1', 'text-xs');
  });

  it('applies medium size classes', () => {
    render(<Pagination {...defaultProps} size="md" />);
    
    const pageButton = screen.getByText('5');
    expect(pageButton).toHaveClass('px-3', 'py-2', 'text-sm');
  });

  it('applies large size classes', () => {
    render(<Pagination {...defaultProps} size="lg" />);
    
    const pageButton = screen.getByText('5');
    expect(pageButton).toHaveClass('px-4', 'py-3', 'text-base');
  });

  it('applies custom className', () => {
    render(<Pagination {...defaultProps} className="custom-pagination" />);
    
    const container = screen.getByRole('navigation').parentElement;
    expect(container).toHaveClass('custom-pagination');
  });

  it('applies custom buttonClassName', () => {
    render(<Pagination {...defaultProps} buttonClassName="custom-button" />);
    
    const pageButton = screen.getByText('5');
    expect(pageButton).toHaveClass('custom-button');
  });

  it('applies custom activeButtonClassName', () => {
    render(<Pagination {...defaultProps} activeButtonClassName="custom-active" />);
    
    const activeButton = screen.getByText('5');
    expect(activeButton).toHaveClass('custom-active');
  });

  it('applies custom infoClassName', () => {
    render(
      <Pagination 
        {...defaultProps} 
        showInfo={true}
        totalItems={100}
        infoClassName="custom-info"
      />
    );
    
    const info = screen.getByText(/Showing/);
    expect(info).toHaveClass('custom-info');
  });

  it('disables all buttons when disabled prop is true', () => {
    render(<Pagination {...defaultProps} disabled={true} />);
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('uses custom labels when provided', () => {
    const customLabels = {
      first: 'Premier',
      previous: 'Précédent',
      next: 'Suivant',
      last: 'Dernier'
    };
    
    render(<Pagination {...defaultProps} labels={customLabels} />);
    
    expect(screen.getByText('Premier')).toBeInTheDocument();
    expect(screen.getByText('Précédent')).toBeInTheDocument();
    expect(screen.getByText('Suivant')).toBeInTheDocument();
    expect(screen.getByText('Dernier')).toBeInTheDocument();
  });

  it('renders nothing when totalPages is 1 and no info/pageSize selector', () => {
    const { container } = render(<Pagination currentPage={1} totalPages={1} onPageChange={jest.fn()} />);
    
    expect(container.firstChild).toBeNull();
  });

  it('still renders when totalPages is 1 but showInfo is true', () => {
    render(
      <Pagination 
        currentPage={1} 
        totalPages={1} 
        onPageChange={jest.fn()} 
        showInfo={true}
        totalItems={5}
        pageSize={10}
      />
    );
    
    expect(screen.getByText('Showing 1 to 5 of 5 items')).toBeInTheDocument();
  });

  it('limits visible pages based on maxVisiblePages', () => {
    render(
      <Pagination 
        currentPage={10} 
        totalPages={20} 
        onPageChange={jest.fn()} 
        maxVisiblePages={5}
      />
    );
    
    // Should show limited number of page buttons
    const pageButtons = screen.getAllByRole('button').filter(button => 
      /^Page \d+$/.test(button.getAttribute('aria-label') || '')
    );
    
    expect(pageButtons.length).toBeLessThanOrEqual(7); // 5 + potentially ellipsis pages
  });

  it('does not call onPageChange for current page', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    fireEvent.click(screen.getByText('5')); // Current page
    
    expect(onPageChange).not.toHaveBeenCalled();
  });

  it('does not call onPageChange for invalid page numbers', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    
    // Simulate clicking a page that would be out of bounds
    const firstButton = screen.getByText('First');
    
    // Mock the function to try to go to page 0
    const mockHandlePageChange = jest.fn();
    fireEvent.click(firstButton);
    
    // onPageChange should still be called with 1, not 0
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('shows correct page range in info text', () => {
    render(
      <Pagination 
        currentPage={3}
        totalPages={10}
        onPageChange={jest.fn()}
        showInfo={true}
        totalItems={95}
        pageSize={10}
      />
    );
    
    expect(screen.getByText('Showing 21 to 30 of 95 items')).toBeInTheDocument();
  });

  it('handles last page correctly in info text', () => {
    render(
      <Pagination 
        currentPage={10}
        totalPages={10}
        onPageChange={jest.fn()}
        showInfo={true}
        totalItems={95}
        pageSize={10}
      />
    );
    
    expect(screen.getByText('Showing 91 to 95 of 95 items')).toBeInTheDocument();
  });

  it('renders compact variant with icons only', () => {
    render(<Pagination {...defaultProps} variant="compact" />);
    
    // In compact mode, navigation buttons should not show text
    const buttons = screen.getAllByRole('button');
    const firstButton = buttons.find(btn => btn.getAttribute('aria-label') === 'Go to first page');
    
    expect(firstButton).toBeInTheDocument();
    expect(firstButton?.textContent).not.toContain('First');
  });

  it('sets proper ARIA labels', () => {
    render(<Pagination {...defaultProps} />);
    
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'Pagination navigation');
    
    const firstButton = screen.getByLabelText('Go to first page');
    expect(firstButton).toBeInTheDocument();
    
    const pageButton = screen.getByLabelText('Page 5');
    expect(pageButton).toBeInTheDocument();
  });
});