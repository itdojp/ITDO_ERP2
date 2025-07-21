import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

import Grid from './Grid'
import Stack from './Stack'
import Divider from './Divider'
import Card, { CardHeader, CardBody, CardFooter } from './Card'

describe('Layout Components', () => {
  describe('Grid', () => {
    it('renders correctly with default props', () => {
      render(
        <Grid data-testid="grid">
          <div>Item 1</div>
          <div>Item 2</div>
        </Grid>
      )
      
      const grid = screen.getByTestId('grid')
      expect(grid).toHaveClass('grid', 'grid-cols-1', 'gap-4')
    })

    it('applies correct column classes', () => {
      render(
        <Grid cols={3} data-testid="grid">
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Grid>
      )
      
      expect(screen.getByTestId('grid')).toHaveClass('grid-cols-3')
    })

    it('applies responsive classes correctly', () => {
      render(
        <Grid 
          cols={1} 
          responsive={{ sm: 2, md: 3, lg: 4 }}
          data-testid="grid"
        >
          <div>Item 1</div>
        </Grid>
      )
      
      const grid = screen.getByTestId('grid')
      expect(grid).toHaveClass('sm:grid-cols-2', 'md:grid-cols-3', 'lg:grid-cols-4')
    })

    it('applies gap classes correctly', () => {
      render(
        <Grid gap="lg" data-testid="grid">
          <div>Item 1</div>
        </Grid>
      )
      
      expect(screen.getByTestId('grid')).toHaveClass('gap-6')
    })

    it('handles auto-fit layout', () => {
      render(
        <Grid autoFit minColWidth="300px" data-testid="grid">
          <div>Item 1</div>
        </Grid>
      )
      
      const grid = screen.getByTestId('grid')
      expect(grid).toHaveStyle('grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))')
      expect(grid).not.toHaveClass('grid-cols-1')
    })
  })

  describe('Stack', () => {
    it('renders vertically by default', () => {
      render(
        <Stack data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('flex', 'flex-col', 'gap-4')
    })

    it('renders horizontally when specified', () => {
      render(
        <Stack direction="horizontal" data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('flex', 'flex-row')
    })

    it('applies spacing correctly', () => {
      render(
        <Stack spacing="xl" data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('gap-8')
    })

    it('applies alignment correctly', () => {
      render(
        <Stack align="center" data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('items-center')
    })

    it('applies justification correctly', () => {
      render(
        <Stack justify="between" data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('justify-between')
    })

    it('handles wrapping', () => {
      render(
        <Stack wrap data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      )
      
      expect(screen.getByTestId('stack')).toHaveClass('flex-wrap')
    })

    it('renders dividers between children', () => {
      render(
        <Stack divider={<hr data-testid="divider" />}>
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Stack>
      )
      
      const dividers = screen.getAllByTestId('divider')
      expect(dividers).toHaveLength(2) // Between 3 items, should have 2 dividers
    })
  })

  describe('Divider', () => {
    it('renders horizontal divider by default', () => {
      render(<Divider data-testid="divider" />)
      
      const divider = screen.getByTestId('divider')
      expect(divider).toHaveAttribute('role', 'separator')
      expect(divider).toHaveAttribute('aria-orientation', 'horizontal')
      expect(divider).toHaveClass('w-full', 'border-t')
    })

    it('renders vertical divider when specified', () => {
      render(<Divider orientation="vertical" data-testid="divider" />)
      
      const divider = screen.getByTestId('divider')
      expect(divider).toHaveAttribute('aria-orientation', 'vertical')
      expect(divider).toHaveClass('h-full', 'border-l')
    })

    it('applies variant classes correctly', () => {
      render(<Divider variant="dashed" data-testid="divider" />)
      
      expect(screen.getByTestId('divider')).toHaveClass('border-dashed')
    })

    it('applies size classes correctly', () => {
      render(<Divider size="lg" data-testid="divider" />)
      
      expect(screen.getByTestId('divider')).toHaveClass('h-1')
    })

    it('applies color classes correctly', () => {
      render(<Divider color="blue" data-testid="divider" />)
      
      expect(screen.getByTestId('divider')).toHaveClass('border-blue-300')
    })

    it('renders with label', () => {
      render(<Divider label="Section Break" />)
      
      expect(screen.getByText('Section Break')).toBeInTheDocument()
    })

    it('positions label correctly', () => {
      render(<Divider label="Left Label" labelPosition="left" data-testid="divider-container" />)
      
      const container = screen.getByTestId('divider-container')
      expect(container).toHaveClass('justify-start')
    })
  })

  describe('Card', () => {
    it('renders correctly with default props', () => {
      render(
        <Card data-testid="card">
          <div>Card content</div>
        </Card>
      )
      
      const card = screen.getByTestId('card')
      expect(card).toHaveClass('border', 'rounded-lg', 'bg-white', 'border-gray-200')
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies variant classes correctly', () => {
      render(
        <Card variant="primary" data-testid="card">
          Content
        </Card>
      )
      
      expect(screen.getByTestId('card')).toHaveClass('bg-blue-50', 'border-blue-200')
    })

    it('applies size classes correctly', () => {
      render(
        <Card size="lg" data-testid="card">
          Content
        </Card>
      )
      
      expect(screen.getByTestId('card')).toHaveClass('p-6')
    })

    it('applies shadow classes correctly', () => {
      render(
        <Card shadow="lg" data-testid="card">
          Content
        </Card>
      )
      
      expect(screen.getByTestId('card')).toHaveClass('shadow-lg')
    })

    it('applies hover effects when enabled', () => {
      render(
        <Card hover data-testid="card">
          Content
        </Card>
      )
      
      expect(screen.getByTestId('card')).toHaveClass('hover:shadow-lg', 'hover:-translate-y-0.5')
    })

    it('handles interactive state correctly', () => {
      render(
        <Card interactive data-testid="card">
          Content
        </Card>
      )
      
      const card = screen.getByTestId('card')
      expect(card).toHaveClass('cursor-pointer')
      expect(card).toHaveAttribute('role', 'button')
      expect(card).toHaveAttribute('tabIndex', '0')
    })
  })

  describe('CardHeader', () => {
    it('renders with title and subtitle', () => {
      render(
        <CardHeader 
          title="Card Title" 
          subtitle="Card Subtitle"
        />
      )
      
      expect(screen.getByText('Card Title')).toBeInTheDocument()
      expect(screen.getByText('Card Subtitle')).toBeInTheDocument()
    })

    it('renders with actions', () => {
      render(
        <CardHeader 
          title="Card Title"
          actions={<button>Action</button>}
        />
      )
      
      expect(screen.getByText('Card Title')).toBeInTheDocument()
      expect(screen.getByText('Action')).toBeInTheDocument()
    })

    it('renders custom children', () => {
      render(
        <CardHeader>
          <div>Custom Header Content</div>
        </CardHeader>
      )
      
      expect(screen.getByText('Custom Header Content')).toBeInTheDocument()
    })
  })

  describe('CardBody', () => {
    it('renders children correctly', () => {
      render(
        <CardBody>
          <p>Body content</p>
        </CardBody>
      )
      
      expect(screen.getByText('Body content')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    it('renders children correctly', () => {
      render(
        <CardFooter>
          <div>Footer content</div>
        </CardFooter>
      )
      
      expect(screen.getByText('Footer content')).toBeInTheDocument()
    })
  })

  describe('Card Compound Component', () => {
    it('renders complete card with all sections', () => {
      render(
        <Card>
          <Card.Header title="Test Card" subtitle="Test subtitle" />
          <Card.Body>
            <p>This is the card body content.</p>
          </Card.Body>
          <Card.Footer>
            <button>Footer Action</button>
          </Card.Footer>
        </Card>
      )
      
      expect(screen.getByText('Test Card')).toBeInTheDocument()
      expect(screen.getByText('Test subtitle')).toBeInTheDocument()
      expect(screen.getByText('This is the card body content.')).toBeInTheDocument()
      expect(screen.getByText('Footer Action')).toBeInTheDocument()
    })
  })
})