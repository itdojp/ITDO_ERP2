import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import LoginForm from './LoginForm'

describe('LoginForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnForgotPassword = vi.fn()
  const mockOnSocialLogin = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const defaultProps = {
    onSubmit: mockOnSubmit,
  }

  it('renders login form with email and password fields', () => {
    render(<LoginForm {...defaultProps} />)
    
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows and hides password when toggle button is clicked', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const passwordInput = screen.getByLabelText(/^password$/i)
    const toggleButton = screen.getByRole('button', { name: '' }) // Eye icon button
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('validates email field on blur', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const emailInput = screen.getByLabelText(/email address/i)
    
    // Test empty email
    await user.click(emailInput)
    await user.tab()
    expect(screen.getByText('Email is required')).toBeInTheDocument()
    
    // Test invalid email
    await user.type(emailInput, 'invalid-email')
    await user.tab()
    expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    
    // Test valid email
    await user.clear(emailInput)
    await user.type(emailInput, 'test@example.com')
    await user.tab()
    expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument()
  })

  it('validates password field on blur', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const passwordInput = screen.getByLabelText(/^password$/i)
    
    // Test empty password
    await user.click(passwordInput)
    await user.tab()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
    
    // Test short password
    await user.type(passwordInput, '1234567')
    await user.tab()
    expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    
    // Test valid password
    await user.clear(passwordInput)
    await user.type(passwordInput, 'validpassword123')
    await user.tab()
    expect(screen.queryByText('Password must be at least 8 characters')).not.toBeInTheDocument()
  })

  it('clears validation errors when user starts typing', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const emailInput = screen.getByLabelText(/email address/i)
    
    // Trigger validation error
    await user.click(emailInput)
    await user.tab()
    expect(screen.getByText('Email is required')).toBeInTheDocument()
    
    // Start typing
    await user.type(emailInput, 't')
    expect(screen.queryByText('Email is required')).not.toBeInTheDocument()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'validpassword123')
    await user.click(submitButton)
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'validpassword123',
      rememberMe: false,
    })
  })

  it('does not submit form with validation errors', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} />)
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.click(submitButton)
    
    expect(screen.getByText('Email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('handles remember me checkbox', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} showRememberMe={true} />)
    
    const rememberMeCheckbox = screen.getByLabelText(/remember me/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    expect(rememberMeCheckbox).not.toBeChecked()
    
    await user.click(rememberMeCheckbox)
    expect(rememberMeCheckbox).toBeChecked()
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'validpassword123')
    await user.click(submitButton)
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'validpassword123',
      rememberMe: true,
    })
  })

  it('shows forgot password link when enabled', () => {
    render(
      <LoginForm
        {...defaultProps}
        showForgotPassword={true}
        onForgotPassword={mockOnForgotPassword}
      />
    )
    
    const forgotPasswordLink = screen.getByRole('button', { name: /forgot password/i })
    expect(forgotPasswordLink).toBeInTheDocument()
    
    fireEvent.click(forgotPasswordLink)
    expect(mockOnForgotPassword).toHaveBeenCalled()
  })

  it('hides forgot password link when disabled', () => {
    render(<LoginForm {...defaultProps} showForgotPassword={false} />)
    
    expect(screen.queryByRole('button', { name: /forgot password/i })).not.toBeInTheDocument()
  })

  it('shows social login when enabled', () => {
    render(
      <LoginForm
        {...defaultProps}
        showSocialLogin={true}
        onSocialLogin={mockOnSocialLogin}
      />
    )
    
    expect(screen.getByText(/or continue with/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /google/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /github/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /microsoft/i })).toBeInTheDocument()
  })

  it('handles social login clicks', async () => {
    const user = userEvent.setup()
    render(
      <LoginForm
        {...defaultProps}
        showSocialLogin={true}
        onSocialLogin={mockOnSocialLogin}
      />
    )
    
    const googleButton = screen.getByRole('button', { name: /google/i })
    await user.click(googleButton)
    
    expect(mockOnSocialLogin).toHaveBeenCalledWith('google')
  })

  it('displays error message when provided', () => {
    const errorMessage = 'Invalid credentials'
    render(<LoginForm {...defaultProps} error={errorMessage} />)
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('shows loading state during submission', () => {
    render(<LoginForm {...defaultProps} loading={true} />)
    
    expect(screen.getByText(/signing in.../i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in.../i })).toBeDisabled()
    
    // Check that form fields are disabled
    expect(screen.getByLabelText(/email address/i)).toBeDisabled()
    expect(screen.getByLabelText(/^password$/i)).toBeDisabled()
  })

  it('disables form during loading', async () => {
    const user = userEvent.setup()
    render(<LoginForm {...defaultProps} loading={true} />)
    
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const submitButton = screen.getByRole('button')
    
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
    expect(submitButton).toBeDisabled()
  })

  it('handles async submit errors gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const erroringOnSubmit = vi.fn().mockRejectedValue(new Error('Submit failed'))
    const user = userEvent.setup()
    
    render(<LoginForm onSubmit={erroringOnSubmit} />)
    
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'validpassword123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Login error:', expect.any(Error))
    })
    
    consoleErrorSpy.mockRestore()
  })

  it('applies custom className', () => {
    const { container } = render(<LoginForm {...defaultProps} className="custom-class" />)
    
    const form = container.querySelector('form')
    expect(form).toHaveClass('custom-class')
  })
})