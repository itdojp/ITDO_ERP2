import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { act } from 'react'
import userEvent from '@testing-library/user-event'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import Alert from '../../components/ui/Alert'
import Toast from '../../components/ui/Toast'

describe('Form Components Integration Tests', () => {
  it('handles form validation with input, button, and alert integration', async () => {
    const user = userEvent.setup()
    
    const TestForm = () => {
      const [email, setEmail] = React.useState('')
      const [error, setError] = React.useState('')
      const [isSubmitting, setIsSubmitting] = React.useState(false)
      
      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError('')
        
        // Simulate validation
        if (!email.includes('@')) {
          setError('Invalid email address')
          setIsSubmitting(false)
          return
        }
        
        // Simulate async submission
        await new Promise(resolve => setTimeout(resolve, 100))
        setIsSubmitting(false)
      }
      
      return (
        <form onSubmit={handleSubmit}>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter email"
            error={!!error}
            errorMessage={error}
          />
          {error && (
            <Alert
              variant="error"
              message={error}
              data-testid="form-error"
            />
          )}
          <Button
            type="submit"
            loading={isSubmitting}
            disabled={!email || isSubmitting}
          >
            Submit
          </Button>
        </form>
      )
    }
    
    act(() => {
      render(<TestForm />)
    })
    
    const emailInput = screen.getByPlaceholderText('Enter email')
    const submitButton = screen.getByText('Submit')
    
    // Initially button should be disabled
    expect(submitButton).toBeDisabled()
    
    // Enter invalid email
    await user.type(emailInput, 'invalid-email')
    expect(submitButton).not.toBeDisabled()
    
    // Submit invalid email
    await user.click(submitButton)
    
    // Verify error alert appears
    await waitFor(() => {
      expect(screen.getByTestId('form-error')).toBeInTheDocument()
      expect(screen.getByText('Invalid email address')).toBeInTheDocument()
    })
    
    // Clear input and enter valid email
    await user.clear(emailInput)
    await user.type(emailInput, 'valid@email.com')
    
    // Error should disappear when typing
    expect(screen.queryByTestId('form-error')).not.toBeInTheDocument()
    
    // Submit valid email
    await user.click(submitButton)
    
    // Button should show loading state
    expect(screen.getByText('Submit')).toBeDisabled()
    
    // Wait for submission to complete
    await waitFor(() => {
      expect(screen.getByText('Submit')).not.toBeDisabled()
    }, { timeout: 200 })
  })
  
  it('integrates multiple inputs with shared validation state', async () => {
    const user = userEvent.setup()
    
    const MultiInputForm = () => {
      const [formData, setFormData] = React.useState({
        firstName: '',
        lastName: '',
        email: ''
      })
      const [errors, setErrors] = React.useState<Record<string, string>>({})
      
      const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        // Clear error when user starts typing
        if (errors[field]) {
          setErrors(prev => ({ ...prev, [field]: '' }))
        }
      }
      
      const validateForm = () => {
        const newErrors: Record<string, string> = {}
        
        if (!formData.firstName) newErrors.firstName = 'First name is required'
        if (!formData.lastName) newErrors.lastName = 'Last name is required'
        if (!formData.email.includes('@')) newErrors.email = 'Valid email is required'
        
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
      }
      
      const isFormValid = formData.firstName && formData.lastName && formData.email.includes('@')
      
      return (
        <form>
          <Input
            value={formData.firstName}
            onChange={(e) => handleInputChange('firstName', e.target.value)}
            placeholder="First Name"
            error={!!errors.firstName}
            errorMessage={errors.firstName}
          />
          
          <Input
            value={formData.lastName}
            onChange={(e) => handleInputChange('lastName', e.target.value)}
            placeholder="Last Name"
            error={!!errors.lastName}
            errorMessage={errors.lastName}
          />
          
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="Email"
            error={!!errors.email}
            errorMessage={errors.email}
          />
          
          <Button
            onClick={validateForm}
            disabled={!isFormValid}
            variant={isFormValid ? 'primary' : 'secondary'}
          >
            Validate
          </Button>
        </form>
      )
    }
    
    act(() => {
      render(<MultiInputForm />)
    })
    
    const firstNameInput = screen.getByPlaceholderText('First Name')
    const lastNameInput = screen.getByPlaceholderText('Last Name')
    const emailInput = screen.getByPlaceholderText('Email')
    const validateButton = screen.getByText('Validate')
    
    // Initially button should be disabled and secondary
    expect(validateButton).toBeDisabled()
    expect(validateButton).toHaveClass('bg-gray-600')
    
    // Fill form partially
    await user.type(firstNameInput, 'John')
    await user.type(lastNameInput, 'Doe')
    
    // Button still disabled without valid email
    expect(validateButton).toBeDisabled()
    
    // Add valid email
    await user.type(emailInput, 'john@doe.com')
    
    // Button should now be enabled and primary
    expect(validateButton).not.toBeDisabled()
    expect(validateButton).toHaveClass('bg-blue-600')
    
    // Clear an input to test error state
    await user.clear(firstNameInput)
    
    // Click validate to trigger errors
    await user.click(validateButton)
    
    // Should show error for empty first name
    expect(screen.getByText('First name is required')).toBeInTheDocument()
    
    // Type in first name to clear error
    await user.type(firstNameInput, 'John')
    
    // Error should disappear
    expect(screen.queryByText('First name is required')).not.toBeInTheDocument()
  })
  
  it('integrates toast notifications with form submission', async () => {
    const user = userEvent.setup()
    
    const FormWithToast = () => {
      const [message, setMessage] = React.useState('')
      const [toast, setToast] = React.useState<{ message: string; type: 'success' | 'error' } | null>(null)
      
      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        
        if (message.length < 3) {
          setToast({ message: 'Message too short', type: 'error' })
          return
        }
        
        // Simulate success
        setToast({ message: 'Message sent successfully!', type: 'success' })
        setMessage('')
      }
      
      return (
        <div>
          <form onSubmit={handleSubmit}>
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter message"
            />
            <Button type="submit">Send Message</Button>
          </form>
          
          {toast && (
            <Toast
              message={toast.message}
              type={toast.type}
              onClose={() => setToast(null)}
            />
          )}
        </div>
      )
    }
    
    act(() => {
      render(<FormWithToast />)
    })
    
    const messageInput = screen.getByPlaceholderText('Enter message')
    const sendButton = screen.getByText('Send Message')
    
    // Submit with short message
    await user.type(messageInput, 'Hi')
    await user.click(sendButton)
    
    // Should show error toast
    expect(screen.getByText('Message too short')).toBeInTheDocument()
    
    // Close toast
    await user.click(screen.getByLabelText('Close toast'))
    expect(screen.queryByText('Message too short')).not.toBeInTheDocument()
    
    // Submit with valid message
    await user.clear(messageInput)
    await user.type(messageInput, 'Hello World!')
    await user.click(sendButton)
    
    // Should show success toast and clear input
    expect(screen.getByText('Message sent successfully!')).toBeInTheDocument()
    expect(messageInput).toHaveValue('')
  })
})