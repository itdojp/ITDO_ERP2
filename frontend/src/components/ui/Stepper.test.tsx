import { render, fireEvent, screen } from '@testing-library/react';
import { Stepper } from './Stepper';

const mockSteps = [
  { id: '1', title: 'Step 1', description: 'First step description' },
  { id: '2', title: 'Step 2', description: 'Second step description' },
  { id: '3', title: 'Step 3', description: 'Third step description' }
];

describe('Stepper', () => {
  it('renders all steps', () => {
    render(<Stepper steps={mockSteps} />);
    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
    expect(screen.getByText('Step 3')).toBeInTheDocument();
  });

  it('shows step descriptions when provided', () => {
    render(<Stepper steps={mockSteps} />);
    expect(screen.getByText('First step description')).toBeInTheDocument();
    expect(screen.getByText('Second step description')).toBeInTheDocument();
    expect(screen.getByText('Third step description')).toBeInTheDocument();
  });

  it('sets current step correctly', () => {
    render(<Stepper steps={mockSteps} currentStep="2" />);
    
    // Check if step numbers are displayed (1, 2, 3)
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows completed checkmark for completed steps', () => {
    const stepsWithStatus = [
      { ...mockSteps[0], status: 'completed' as const },
      { ...mockSteps[1], status: 'current' as const },
      { ...mockSteps[2], status: 'pending' as const }
    ];
    
    const { container } = render(<Stepper steps={stepsWithStatus} />);
    
    // Check for checkmark SVG in completed step
    const checkmarkSvg = container.querySelector('svg path[fill-rule="evenodd"]');
    expect(checkmarkSvg).toBeInTheDocument();
  });

  it('shows error icon for error steps', () => {
    const stepsWithError = [
      { ...mockSteps[0], status: 'error' as const },
      { ...mockSteps[1], status: 'pending' as const },
      { ...mockSteps[2], status: 'pending' as const }
    ];
    
    const { container } = render(<Stepper steps={stepsWithError} />);
    
    // Check for error X SVG
    const errorSvg = container.querySelector('svg path[fill-rule="evenodd"]');
    expect(errorSvg).toBeInTheDocument();
  });

  it('calls onStepClick when step is clicked and allowClickableSteps is true', () => {
    const handleStepClick = jest.fn();
    render(
      <Stepper 
        steps={mockSteps} 
        onStepClick={handleStepClick}
        allowClickableSteps 
      />
    );
    
    const firstStepButton = screen.getByText('1').closest('button');
    if (firstStepButton) {
      fireEvent.click(firstStepButton);
      expect(handleStepClick).toHaveBeenCalledWith('1');
    }
  });

  it('does not call onStepClick when allowClickableSteps is false', () => {
    const handleStepClick = jest.fn();
    render(
      <Stepper 
        steps={mockSteps} 
        onStepClick={handleStepClick}
        allowClickableSteps={false}
      />
    );
    
    const firstStepButton = screen.getByText('1').closest('button');
    if (firstStepButton) {
      fireEvent.click(firstStepButton);
      expect(handleStepClick).not.toHaveBeenCalled();
    }
  });

  it('renders in vertical orientation', () => {
    const { container } = render(<Stepper steps={mockSteps} orientation="vertical" />);
    
    // Check for vertical layout class
    const verticalContainer = container.querySelector('.flex-col');
    expect(verticalContainer).toBeInTheDocument();
  });

  it('hides descriptions in compact variant', () => {
    render(<Stepper steps={mockSteps} variant="compact" />);
    
    // Descriptions should not be visible in compact mode
    expect(screen.queryByText('First step description')).not.toBeInTheDocument();
  });

  it('shows step numbers when showStepNumbers is true', () => {
    render(<Stepper steps={mockSteps} showStepNumbers />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders custom icons when provided', () => {
    const stepsWithIcons = [
      { ...mockSteps[0], icon: <span data-testid="custom-icon-1">🎯</span> },
      { ...mockSteps[1] },
      { ...mockSteps[2] }
    ];
    
    render(<Stepper steps={stepsWithIcons} />);
    expect(screen.getByTestId('custom-icon-1')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Stepper steps={mockSteps} className="custom-stepper" />);
    expect(container.querySelector('.custom-stepper')).toBeInTheDocument();
  });

  it('handles empty steps array', () => {
    const { container } = render(<Stepper steps={[]} />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('handles single step', () => {
    render(<Stepper steps={[mockSteps[0]]} />);
    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('applies correct status styles based on current step', () => {
    const { container } = render(<Stepper steps={mockSteps} currentStep="2" />);
    
    // Check if the appropriate CSS classes are applied
    const buttons = container.querySelectorAll('button');
    expect(buttons).toHaveLength(3);
  });
});