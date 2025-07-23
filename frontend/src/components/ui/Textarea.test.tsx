import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { Textarea } from './Textarea';

describe('Textarea', () => {
  it('renders basic textarea', () => {
    render(<Textarea />);
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Textarea label="Message" />);
    
    expect(screen.getByText('Message')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with placeholder', () => {
    render(<Textarea placeholder="Enter your message..." />);
    
    expect(screen.getByPlaceholderText('Enter your message...')).toBeInTheDocument();
  });

  it('handles value changes', () => {
    const onChange = vi.fn();
    render(<Textarea onChange={onChange} />);
    
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    
    expect(onChange).toHaveBeenCalledWith('Hello world');
  });

  it('renders as controlled component', () => {
    const onChange = vi.fn();
    const { rerender } = render(<Textarea value="" onChange={onChange} />);
    
    let textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toBe('');
    
    rerender(<Textarea value="Hello" onChange={onChange} />);
    textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toBe('Hello');
  });

  it('renders in different sizes', () => {
    const { rerender } = render(<Textarea size="sm" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('text-sm', 'px-3', 'py-2');
    
    rerender(<Textarea size="md" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('text-base', 'px-4', 'py-3');
    
    rerender(<Textarea size="lg" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('text-lg', 'px-5', 'py-4');
  });

  it('applies different variants', () => {
    const { rerender } = render(<Textarea variant="primary" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-gray-300', 'focus:border-blue-500', 'focus:ring-blue-500');
    
    rerender(<Textarea variant="secondary" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-gray-300', 'focus:border-gray-500', 'focus:ring-gray-500');
    
    rerender(<Textarea variant="success" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-green-300', 'focus:border-green-500', 'focus:ring-green-500');
  });

  it('renders as disabled', () => {
    render(<Textarea disabled />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveClass('opacity-50', 'cursor-not-allowed', 'bg-gray-50');
  });

  it('renders as readonly', () => {
    render(<Textarea readonly />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('readonly');
    expect(textarea).toHaveClass('bg-gray-50');
  });

  it('renders as required', () => {
    render(<Textarea required />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeRequired();
  });

  it('renders with custom rows and columns', () => {
    render(<Textarea rows={5} cols={40} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '5');
    expect(textarea).toHaveAttribute('cols', '40');
  });

  it('handles resize options', () => {
    const { rerender } = render(<Textarea resize="none" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('resize-none');
    
    rerender(<Textarea resize="vertical" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('resize-y');
    
    rerender(<Textarea resize="horizontal" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('resize-x');
    
    rerender(<Textarea resize="both" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('resize');
  });

  it('renders with character count', () => {
    render(<Textarea maxLength={100} showCount />);
    
    expect(screen.getByText('0/100')).toBeInTheDocument();
    
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    
    expect(screen.getByText('5/100')).toBeInTheDocument();
  });

  it('renders with error state', () => {
    render(<Textarea error="This field is required" />);
    
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
  });

  it('renders with success state', () => {
    render(<Textarea success="Valid input" />);
    
    expect(screen.getByText('Valid input')).toBeInTheDocument();
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-green-500', 'focus:border-green-500', 'focus:ring-green-500');
  });

  it('renders with warning state', () => {
    render(<Textarea warning="Check this field" />);
    
    expect(screen.getByText('Check this field')).toBeInTheDocument();
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-yellow-500', 'focus:border-yellow-500', 'focus:ring-yellow-500');
  });

  it('renders with description', () => {
    render(<Textarea label="Message" description="Enter your message here" />);
    
    expect(screen.getByText('Enter your message here')).toBeInTheDocument();
  });

  it('renders with custom className', () => {
    render(<Textarea className="custom-textarea" />);
    
    const container = screen.getByRole('textbox').closest('.custom-textarea');
    expect(container).toHaveClass('custom-textarea');
  });

  it('handles auto-resize functionality', () => {
    render(<Textarea autoResize />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('style');
  });

  it('renders with loading state', () => {
    render(<Textarea loading />);
    
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('handles focus and blur events', () => {
    const onFocus = vi.fn();
    const onBlur = vi.fn();
    render(<Textarea onFocus={onFocus} onBlur={onBlur} />);
    
    const textarea = screen.getByRole('textbox');
    fireEvent.focus(textarea);
    expect(onFocus).toHaveBeenCalled();
    
    fireEvent.blur(textarea);
    expect(onBlur).toHaveBeenCalled();
  });

  it('handles keyboard events', () => {
    const onKeyDown = vi.fn();
    const onKeyUp = vi.fn();
    render(<Textarea onKeyDown={onKeyDown} onKeyUp={onKeyUp} />);
    
    const textarea = screen.getByRole('textbox');
    fireEvent.keyDown(textarea, { key: 'Enter' });
    expect(onKeyDown).toHaveBeenCalled();
    
    fireEvent.keyUp(textarea, { key: 'Enter' });
    expect(onKeyUp).toHaveBeenCalled();
  });

  it('renders with icon', () => {
    const icon = <span data-testid="test-icon">📝</span>;
    render(<Textarea icon={icon} />);
    
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('handles paste events', () => {
    const onPaste = vi.fn();
    render(<Textarea onPaste={onPaste} />);
    
    const textarea = screen.getByRole('textbox');
    fireEvent.paste(textarea);
    
    expect(onPaste).toHaveBeenCalled();
  });

  it('validates minimum and maximum length', () => {
    const { rerender } = render(<Textarea minLength={5} value="Hi" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('minlength', '5');
    
    rerender(<Textarea maxLength={10} value="Hello world!" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('maxlength', '10');
  });

  it('renders with tooltip', () => {
    render(<Textarea tooltip="Enter your message" />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('title', 'Enter your message');
  });

  it('handles spell check options', () => {
    const { rerender } = render(<Textarea spellCheck />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('spellcheck', 'true');
    
    rerender(<Textarea spellCheck={false} />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('spellcheck', 'false');
  });

  it('renders with different border radius options', () => {
    const { rerender } = render(<Textarea rounded="none" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('rounded-none');
    
    rerender(<Textarea rounded="sm" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('rounded-sm');
    
    rerender(<Textarea rounded="lg" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('rounded-lg');
  });

  it('renders with custom background', () => {
    const { container } = render(<Textarea background="bg-blue-50" />);
    
    const bgContainer = container.querySelector('.bg-blue-50');
    expect(bgContainer).toBeInTheDocument();
  });

  it('handles auto-complete options', () => {
    render(<Textarea autoComplete="off" />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('autocomplete', 'off');
  });

  it('renders with accessibility attributes', () => {
    render(
      <Textarea 
        aria-describedby="help-text"
        aria-label="Message input"
        role="textbox"
      />
    );
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('aria-describedby', 'help-text');
    expect(textarea).toHaveAttribute('aria-label', 'Message input');
  });

  it('handles word wrap options', () => {
    const { rerender } = render(<Textarea wrap="soft" />);
    let textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('wrap', 'soft');
    
    rerender(<Textarea wrap="hard" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('wrap', 'hard');
    
    rerender(<Textarea wrap="off" />);
    textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('wrap', 'off');
  });
});