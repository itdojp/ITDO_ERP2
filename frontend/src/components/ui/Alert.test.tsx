import { render } from '@testing-library/react';
import { Alert } from './Alert';

describe('Alert', () => {
  it('renders with default info type', () => {
    const { getByText } = render(<Alert message="Test message" />);
    const alert = getByText('Test message');
    expect(alert).toBeDefined();
    expect(alert.className).toContain('bg-blue-50');
  });

  it('renders error type correctly', () => {
    const { getByText } = render(<Alert type="error" message="Error message" />);
    const alert = getByText('Error message');
    expect(alert.className).toContain('bg-red-50');
  });
});