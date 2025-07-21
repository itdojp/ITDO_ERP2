import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

import Form from './Form'
import { ValidationRules } from '../../../hooks/useFormValidation'

describe('Form Components', () => {
  describe('Form', () => {
    it('renders form with children', () => {
      const validationConfig = {
        email: {
          required: true,
          rules: [ValidationRules.email()],
        },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="email" label="Email" />
          <Form.Submit>Submit</Form.Submit>
        </Form>
      )

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument()
    })

    it('validates fields on submit', async () => {
      const user = userEvent.setup()
      const handleSubmit = vi.fn()
      
      const validationConfig = {
        email: {
          required: true,
          rules: [ValidationRules.email()],
        },
      }

      render(
        <Form validationConfig={validationConfig} onSubmit={handleSubmit}>
          <Form.Input name="email" label="Email" />
          <Form.Submit>Submit</Form.Submit>
        </Form>
      )

      const submitButton = screen.getByRole('button', { name: 'Submit' })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('email is required')).toBeInTheDocument()
      })

      expect(handleSubmit).not.toHaveBeenCalled()
    })

    it('submits valid form data', async () => {
      const user = userEvent.setup()
      const handleSubmit = vi.fn()
      
      const validationConfig = {
        email: {
          required: true,
          rules: [ValidationRules.email()],
        },
      }

      render(
        <Form validationConfig={validationConfig} onSubmit={handleSubmit} initialValues={{ email: '' }}>
          <Form.Input name="email" label="Email" />
          <Form.Submit>Submit</Form.Submit>
        </Form>
      )

      const emailInput = screen.getByLabelText('Email')
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: 'Submit' })
      await user.click(submitButton)

      await waitFor(() => {
        expect(handleSubmit).toHaveBeenCalledWith({ email: 'test@example.com' })
      })
    })

    it('uses render prop pattern', () => {
      const validationConfig = {
        email: { required: true },
      }

      render(
        <Form validationConfig={validationConfig}>
          {({ values, errors, setValue }) => (
            <>
              <input
                value={values.email || ''}
                onChange={(e) => setValue('email', e.target.value)}
                data-testid="email-input"
              />
              {errors.email && <div data-testid="email-error">{errors.email}</div>}
              <button type="submit">Submit</button>
            </>
          )}
        </Form>
      )

      expect(screen.getByTestId('email-input')).toBeInTheDocument()
    })
  })

  describe('Form.Input', () => {
    it('renders input with label', () => {
      const validationConfig = {
        username: { required: true },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="username" label="Username" placeholder="Enter username" />
        </Form>
      )

      expect(screen.getByLabelText('Username')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
    })

    it('shows required indicator', () => {
      const validationConfig = {
        username: { required: true },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="username" label="Username" required />
        </Form>
      )

      expect(screen.getByText('*')).toBeInTheDocument()
    })

    it('shows validation errors', async () => {
      const user = userEvent.setup()
      
      const validationConfig = {
        email: {
          required: true,
          rules: [ValidationRules.email()],
          validateOnBlur: true,
        },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="email" label="Email" />
        </Form>
      )

      const emailInput = screen.getByLabelText('Email')
      await user.type(emailInput, 'invalid-email')
      await user.tab() // Trigger blur

      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
      })
    })

    it('shows help text', () => {
      const validationConfig = {
        username: {},
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="username" label="Username" helpText="Choose a unique username" />
        </Form>
      )

      expect(screen.getByText('Choose a unique username')).toBeInTheDocument()
    })
  })

  describe('Form.Textarea', () => {
    it('renders textarea with label', () => {
      const validationConfig = {
        description: { required: true },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Textarea name="description" label="Description" placeholder="Enter description" />
        </Form>
      )

      expect(screen.getByLabelText('Description')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Enter description')).toBeInTheDocument()
    })

    it('handles value changes', async () => {
      const user = userEvent.setup()
      
      const validationConfig = {
        description: {},
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Textarea name="description" label="Description" />
        </Form>
      )

      const textarea = screen.getByLabelText('Description')
      await user.type(textarea, 'This is a test description')

      expect(textarea).toHaveValue('This is a test description')
    })
  })

  describe('Form.Submit', () => {
    it('is disabled when form is invalid', () => {
      const validationConfig = {
        email: { required: true },
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="email" label="Email" />
          <Form.Submit>Submit</Form.Submit>
        </Form>
      )

      const submitButton = screen.getByRole('button', { name: 'Submit' })
      expect(submitButton).toBeDisabled()
    })

    it('shows loading state', () => {
      const validationConfig = {
        email: {},
      }

      render(
        <Form validationConfig={validationConfig}>
          <Form.Input name="email" label="Email" />
          <Form.Submit loading loadingText="Processing...">Submit</Form.Submit>
        </Form>
      )

      expect(screen.getByText('Processing...')).toBeInTheDocument()
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('applies different variants', () => {
      const validationConfig = {
        email: {},
      }

      const { rerender } = render(
        <Form validationConfig={validationConfig}>
          <Form.Submit variant="primary">Primary</Form.Submit>
        </Form>
      )

      let submitButton = screen.getByRole('button')
      expect(submitButton).toHaveClass('bg-blue-600')

      rerender(
        <Form validationConfig={validationConfig}>
          <Form.Submit variant="outline">Outline</Form.Submit>
        </Form>
      )

      submitButton = screen.getByRole('button')
      expect(submitButton).toHaveClass('bg-transparent')
    })
  })

  describe('Form.Field', () => {
    it('renders field with label and error', () => {
      render(
        <Form.Field name="test" label="Test Field" error="This field has an error">
          <input data-testid="test-input" />
        </Form.Field>
      )

      expect(screen.getByText('Test Field')).toBeInTheDocument()
      expect(screen.getByText('This field has an error')).toBeInTheDocument()
      expect(screen.getByTestId('test-input')).toBeInTheDocument()
    })

    it('shows required indicator', () => {
      render(
        <Form.Field name="test" label="Test Field" required>
          <input />
        </Form.Field>
      )

      expect(screen.getByText('*')).toBeInTheDocument()
    })

    it('shows help text when no error', () => {
      render(
        <Form.Field name="test" label="Test Field" helpText="This is help text">
          <input />
        </Form.Field>
      )

      expect(screen.getByText('This is help text')).toBeInTheDocument()
    })

    it('prioritizes error over help text', () => {
      render(
        <Form.Field 
          name="test" 
          label="Test Field" 
          error="Error message"
          helpText="Help text"
        >
          <input />
        </Form.Field>
      )

      expect(screen.getByText('Error message')).toBeInTheDocument()
      expect(screen.queryByText('Help text')).not.toBeInTheDocument()
    })

    it('sets appropriate ARIA attributes', () => {
      render(
        <Form.Field name="test" label="Test Field" error="Error message">
          <input data-testid="test-input" />
        </Form.Field>
      )

      const input = screen.getByTestId('test-input')
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(input).toHaveAttribute('id', 'field-test')
      expect(input).toHaveAttribute('aria-describedby', 'field-test-error')
    })
  })

  describe('Form.Error', () => {
    it('renders error message', () => {
      render(<Form.Error message="This is an error" />)
      
      expect(screen.getByText('This is an error')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('does not render when no message', () => {
      const { container } = render(<Form.Error message={null} />)
      expect(container.firstChild).toBeNull()
    })

    it('has proper accessibility attributes', () => {
      render(<Form.Error message="Error message" />)
      
      const errorElement = screen.getByRole('alert')
      expect(errorElement).toHaveAttribute('aria-live', 'polite')
    })
  })

  describe('Form.Group', () => {
    it('renders children', () => {
      render(
        <Form.Group>
          <div data-testid="child">Child content</div>
        </Form.Group>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
    })

    it('applies error styling', () => {
      render(
        <Form.Group error>
          <div>Content</div>
        </Form.Group>
      )

      const group = screen.getByText('Content').parentElement
      expect(group).toHaveClass('space-y-1')
    })
  })

  describe('Form Integration', () => {
    it('handles complex validation scenarios', async () => {
      const user = userEvent.setup()
      
      const validationConfig = {
        password: {
          required: true,
          rules: [ValidationRules.minLength(8, 'Password must be at least 8 characters')],
        },
        confirmPassword: {
          required: true,
          rules: [ValidationRules.matches('password', 'Passwords must match')],
        },
      }

      render(
        <Form validationConfig={validationConfig} initialValues={{ password: '', confirmPassword: '' }}>
          <Form.Input name="password" type="password" label="Password" />
          <Form.Input name="confirmPassword" type="password" label="Confirm Password" />
          <Form.Submit>Create Account</Form.Submit>
        </Form>
      )

      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: 'Create Account' })

      // Test short password
      await user.type(passwordInput, '123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
      })

      // Test valid password but mismatched confirmation
      await user.clear(passwordInput)
      await user.type(passwordInput, 'validpassword123')
      await user.type(confirmPasswordInput, 'differentpassword')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Passwords must match')).toBeInTheDocument()
      })

      // Test valid matching passwords
      await user.clear(confirmPasswordInput)
      await user.type(confirmPasswordInput, 'validpassword123')

      // Submit button should be enabled now
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })
    })

    it('resets form correctly', async () => {
      const user = userEvent.setup()
      
      const validationConfig = {
        email: { required: true },
      }

      render(
        <Form validationConfig={validationConfig} initialValues={{ email: '' }}>
          {({ values, resetForm }) => (
            <>
              <Form.Input name="email" label="Email" />
              <button type="button" onClick={resetForm}>Reset</button>
              <div data-testid="email-value">{values.email}</div>
            </>
          )}
        </Form>
      )

      const emailInput = screen.getByLabelText('Email')
      const resetButton = screen.getByText('Reset')

      await user.type(emailInput, 'test@example.com')
      expect(screen.getByTestId('email-value')).toHaveTextContent('test@example.com')

      await user.click(resetButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('email-value')).toHaveTextContent('')
      })
      expect(emailInput).toHaveValue('')
    })
  })
})