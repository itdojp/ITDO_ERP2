import { render, fireEvent, screen } from '@testing-library/react';
import { ColorPicker } from './ColorPicker';

describe('ColorPicker', () => {
  it('renders color button with initial color', () => {
    render(<ColorPicker value="#FF5733" />);
    const button = screen.getByRole('button');
    expect(button).toHaveStyle('background-color: #FF5733');
  });

  it('opens color picker when button is clicked', () => {
    render(<ColorPicker />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('カスタムカラー')).toBeInTheDocument();
  });

  it('shows preset colors when enabled', () => {
    render(<ColorPicker showPresets />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('プリセットカラー')).toBeInTheDocument();
  });

  it('hides preset colors when disabled', () => {
    render(<ColorPicker showPresets={false} />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.queryByText('プリセットカラー')).not.toBeInTheDocument();
  });

  it('calls onChange when preset color is selected', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    // Click on first preset color
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith('#FF5733');
    }
  });

  it('applies custom color when apply button is clicked', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const customColorInput = screen.getByPlaceholderText('#000000');
    fireEvent.change(customColorInput, { target: { value: '#123456' } });
    
    const applyButton = screen.getByText('適用');
    fireEvent.click(applyButton);
    
    expect(handleChange).toHaveBeenCalledWith('#123456');
  });

  it('formats color in RGB format', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} format="rgb" />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith('rgb(255, 87, 51)');
    }
  });

  it('formats color in HSL format', () => {
    const handleChange = jest.fn();
    render(<ColorPicker onChange={handleChange} format="hsl" />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    const presetButtons = screen.getAllByRole('button');
    const firstPreset = presetButtons.find(btn => btn.getAttribute('title') === '#FF5733');
    if (firstPreset) {
      fireEvent.click(firstPreset);
      expect(handleChange).toHaveBeenCalledWith(expect.stringMatching(/^hsl\(\d+, \d+%, \d+%\)$/));
    }
  });

  it('respects disabled state', () => {
    render(<ColorPicker disabled />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    
    fireEvent.click(button);
    expect(screen.queryByText('カスタムカラー')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<ColorPicker size="sm" />);
    expect(screen.getByRole('button')).toHaveClass('w-8', 'h-8');

    rerender(<ColorPicker size="lg" />);
    expect(screen.getByRole('button')).toHaveClass('w-12', 'h-12');
  });

  it('closes picker when clicking outside', () => {
    render(
      <div>
        <ColorPicker />
        <button>Outside button</button>
      </div>
    );
    
    const colorButton = screen.getAllByRole('button')[0];
    fireEvent.click(colorButton);
    expect(screen.getByText('カスタムカラー')).toBeInTheDocument();
    
    const outsideButton = screen.getByText('Outside button');
    fireEvent.mouseDown(outsideButton);
    
    expect(screen.queryByText('カスタムカラー')).not.toBeInTheDocument();
  });

  it('shows current color information', () => {
    render(<ColorPicker value="#FF5733" />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(screen.getByText('選択中:')).toBeInTheDocument();
    expect(screen.getByText('#FF5733')).toBeInTheDocument();
  });
});