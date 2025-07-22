import { render, screen, fireEvent } from '@testing-library/react';
import { LoginPage } from './Login';

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />);
    expect(screen.getByText('ITDO ERP')).toBeDefined();
    expect(screen.getByLabelText('メールアドレス')).toBeDefined();
    expect(screen.getByLabelText('パスワード')).toBeDefined();
  });

  it('updates input values', () => {
    render(<LoginPage />);
    const emailInput = screen.getByLabelText('メールアドレス') as HTMLInputElement;
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    expect(emailInput.value).toBe('test@example.com');
  });
});