import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'

import TextInput from './TextInput'
import Select from './Select'
import Checkbox from './Checkbox'
import Radio from './Radio'

describe('Form Input Components', () => {
  describe('TextInput', () => {
    it('renders correctly with default props', () => {
      render(<TextInput />)
      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })

    it('displays label when provided', () => {
      render(<TextInput label="Email Address" />)
      expect(screen.getByText('Email Address')).toBeInTheDocument()
    })

    it('shows error state correctly', () => {
      render(<TextInput error errorMessage="This field is required" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(screen.getByText('This field is required')).toBeInTheDocument()
    })

    it('handles validation correctly', async () => {
      const user = userEvent.setup()
      render(
        <TextInput 
          validation={{ required: true, minLength: 3 }}
          label="Username"
        />
      )
      
      const input = screen.getByRole('textbox')
      
      // Trigger validation by focusing and blurring
      await user.click(input)
      await user.tab()
      
      await waitFor(() => {
        expect(screen.getByText('This field is required')).toBeInTheDocument()
      })
    })

    it('shows password toggle for password type', () => {
      render(<TextInput type="password" />)
      const toggleButton = screen.getByRole('button')
      expect(toggleButton).toBeInTheDocument()
    })

    it('handles clearable functionality', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      render(<TextInput clearable value="test" onChange={handleChange} />)
      
      const clearButton = screen.getByRole('button')
      await user.click(clearButton)
      
      expect(handleChange).toHaveBeenCalled()
    })
  })

  describe('Select', () => {
    const options = [
      { value: 'option1', label: 'Option 1' },
      { value: 'option2', label: 'Option 2' },
      { value: 'option3', label: 'Option 3' }
    ]

    it('renders correctly with options', () => {
      render(<Select options={options} />)
      const select = screen.getByRole('combobox')
      expect(select).toBeInTheDocument()
    })

    it('opens dropdown when clicked', async () => {
      const user = userEvent.setup()
      render(<Select options={options} />)
      
      const select = screen.getByRole('combobox')
      await user.click(select)
      
      expect(screen.getByText('Option 1')).toBeInTheDocument()
      expect(screen.getByText('Option 2')).toBeInTheDocument()
      expect(screen.getByText('Option 3')).toBeInTheDocument()
    })

    it('selects option when clicked', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      render(<Select options={options} onChange={handleChange} />)
      
      const select = screen.getByRole('combobox')
      await user.click(select)
      
      await user.click(screen.getByText('Option 2'))
      
      expect(handleChange).toHaveBeenCalledWith('option2')
    })

    it('handles multiple selection', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      render(<Select options={options} multiple onChange={handleChange} />)
      
      const select = screen.getByRole('combobox')
      await user.click(select)
      
      await user.click(screen.getByText('Option 1'))
      expect(handleChange).toHaveBeenCalledWith(['option1'])
    })

    it('shows search input when searchable', async () => {
      const user = userEvent.setup()
      render(<Select options={options} searchable />)
      
      const select = screen.getByRole('combobox')
      await user.click(select)
      
      expect(screen.getByPlaceholderText('Search options...')).toBeInTheDocument()
    })

    it('filters options when searching', async () => {
      const user = userEvent.setup()
      render(<Select options={options} searchable />)
      
      const select = screen.getByRole('combobox')
      await user.click(select)
      
      const searchInput = screen.getByPlaceholderText('Search options...')
      await user.type(searchInput, '1')
      
      expect(screen.getByText('Option 1')).toBeInTheDocument()
      expect(screen.queryByText('Option 2')).not.toBeInTheDocument()
    })
  })

  describe('Checkbox', () => {
    it('renders correctly', () => {
      render(<Checkbox label="Accept terms" />)
      const checkbox = screen.getByRole('checkbox')
      const label = screen.getByText('Accept terms')
      
      expect(checkbox).toBeInTheDocument()
      expect(label).toBeInTheDocument()
    })

    it('handles checked state', () => {
      render(<Checkbox label="Accept terms" checked />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeChecked()
    })

    it('handles click events', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      render(<Checkbox label="Accept terms" onChange={handleChange} />)
      
      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)
      
      expect(handleChange).toHaveBeenCalled()
    })

    it('shows description when provided', () => {
      render(
        <Checkbox 
          label="Accept terms" 
          description="I agree to the terms and conditions"
        />
      )
      
      expect(screen.getByText('I agree to the terms and conditions')).toBeInTheDocument()
    })

    it('handles indeterminate state', () => {
      render(<Checkbox label="Select all" indeterminate />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBePartiallyChecked()
    })

    it('shows error message when error is true', () => {
      render(
        <Checkbox 
          label="Accept terms" 
          error 
          errorMessage="You must accept the terms"
        />
      )
      
      expect(screen.getByText('You must accept the terms')).toBeInTheDocument()
    })
  })

  describe('Radio', () => {
    const options = [
      { value: 'small', label: 'Small', description: 'Perfect for personal use' },
      { value: 'medium', label: 'Medium', description: 'Great for small teams' },
      { value: 'large', label: 'Large', description: 'Best for enterprises' }
    ]

    it('renders all options', () => {
      render(<Radio name="size" options={options} />)
      
      expect(screen.getByLabelText('Small')).toBeInTheDocument()
      expect(screen.getByLabelText('Medium')).toBeInTheDocument()
      expect(screen.getByLabelText('Large')).toBeInTheDocument()
    })

    it('shows option descriptions', () => {
      render(<Radio name="size" options={options} />)
      
      expect(screen.getByText('Perfect for personal use')).toBeInTheDocument()
      expect(screen.getByText('Great for small teams')).toBeInTheDocument()
      expect(screen.getByText('Best for enterprises')).toBeInTheDocument()
    })

    it('handles selection', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      render(<Radio name="size" options={options} onChange={handleChange} />)
      
      const mediumRadio = screen.getByLabelText('Medium')
      await user.click(mediumRadio)
      
      expect(handleChange).toHaveBeenCalledWith('medium')
    })

    it('shows selected option', () => {
      render(<Radio name="size" options={options} value="large" />)
      
      const largeRadio = screen.getByLabelText('Large')
      expect(largeRadio).toBeChecked()
    })

    it('handles disabled options', () => {
      const disabledOptions = [
        ...options,
        { value: 'premium', label: 'Premium', disabled: true }
      ]
      
      render(<Radio name="size" options={disabledOptions} />)
      
      const premiumRadio = screen.getByLabelText('Premium')
      expect(premiumRadio).toBeDisabled()
    })

    it('displays group label when provided', () => {
      render(<Radio name="size" options={options} label="Choose your plan size" />)
      
      expect(screen.getByText('Choose your plan size')).toBeInTheDocument()
    })

    it('shows error message when error is true', () => {
      render(
        <Radio 
          name="size" 
          options={options} 
          error 
          errorMessage="Please select a size"
        />
      )
      
      expect(screen.getByText('Please select a size')).toBeInTheDocument()
    })

    it('handles horizontal orientation', () => {
      render(<Radio name="size" options={options} orientation="horizontal" />)
      
      const container = screen.getByRole('radiogroup')
      expect(container).toHaveClass('flex-row')
    })
  })
})