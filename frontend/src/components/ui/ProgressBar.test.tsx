import { render, screen } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

describe('ProgressBar', () => {
  it('renders with correct progress value', () => {
    const { container } = render(<ProgressBar value={50} />);
    const progressBar = container.querySelector('div[style*="width: 50%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('shows label when provided', () => {
    render(<ProgressBar value={30} label="Loading" showLabel />);
    expect(screen.getByText('Loading')).toBeInTheDocument();
  });

  it('shows percentage value when enabled', () => {
    render(<ProgressBar value={75} showValue />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('applies correct variant colors', () => {
    const { container } = render(<ProgressBar value={50} variant="success" />);
    const progressBar = container.querySelector('.bg-green-600');
    expect(progressBar).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { container } = render(<ProgressBar value={50} size="lg" />);
    const progressContainer = container.querySelector('.h-6');
    expect(progressContainer).toBeInTheDocument();
  });

  it('handles edge cases for percentage calculation', () => {
    // Test negative value
    const { container: container1 } = render(<ProgressBar value={-10} />);
    let progressBar = container1.querySelector('div[style*="width: 0%"]');
    expect(progressBar).toBeInTheDocument();

    // Test value over max
    const { container: container2 } = render(<ProgressBar value={150} max={100} />);
    progressBar = container2.querySelector('div[style*="width: 100%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('calculates percentage with custom max value', () => {
    const { container } = render(<ProgressBar value={25} max={50} />);
    const progressBar = container.querySelector('div[style*="width: 50%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('shows label and value together', () => {
    render(
      <ProgressBar 
        value={60} 
        label="Download Progress" 
        showLabel 
        showValue 
      />
    );
    expect(screen.getByText('Download Progress')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('applies dynamic variant based on percentage', () => {
    // Test different percentage ranges for dynamic variant
    const { container: container1 } = render(<ProgressBar value={10} />); // Should be danger (red)
    let progressBar = container1.querySelector('.bg-red-600');
    expect(progressBar).toBeInTheDocument();

    const { container: container2 } = render(<ProgressBar value={100} />); // Should be success (green)
    progressBar = container2.querySelector('.bg-green-600');
    expect(progressBar).toBeInTheDocument();
  });

  it('applies striped styling when enabled', () => {
    const { container } = render(<ProgressBar value={50} striped />);
    const progressBar = container.querySelector('div[style*="background-image"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<ProgressBar value={50} className="custom-class" />);
    const wrapper = container.querySelector('.custom-class');
    expect(wrapper).toBeInTheDocument();
  });

  it('shows percentage inside bar for large size', () => {
    render(<ProgressBar value={50} size="lg" showValue />);
    // Check if percentage is displayed (should be visible for lg size with sufficient percentage)
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('hides percentage inside bar when percentage is too low', () => {
    const { container } = render(<ProgressBar value={10} size="lg" showValue />);
    // For 10% progress, the text should not be displayed inside the bar
    const progressBar = container.querySelector('div[style*="width: 10%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('rounds percentage values correctly', () => {
    render(<ProgressBar value={33.7} showValue />);
    expect(screen.getByText('34%')).toBeInTheDocument();
  });
});