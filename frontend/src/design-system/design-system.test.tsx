import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { designTokens, componentStyles, accessibilityGuidelines } from './index'
import DesignSystemPage from '../pages/DesignSystemPage'
import ComponentPlayground from '../pages/ComponentPlayground'

describe('Design System', () => {
  describe('Design Tokens', () => {
    it('should have complete color palettes', () => {
      expect(designTokens.colors.primary).toBeDefined()
      expect(designTokens.colors.secondary).toBeDefined()
      expect(designTokens.colors.success).toBeDefined()
      expect(designTokens.colors.warning).toBeDefined()
      expect(designTokens.colors.error).toBeDefined()
      expect(designTokens.colors.neutral).toBeDefined()

      // Each palette should have consistent shades
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']
      Object.values(designTokens.colors).forEach(palette => {
        expectedShades.forEach(shade => {
          expect(palette[shade]).toBeDefined()
          expect(palette[shade]).toMatch(/^rgb\(\d+ \d+ \d+\)$/)
        })
      })
    })

    it('should have consistent spacing scale', () => {
      expect(designTokens.spacing).toBeDefined()
      expect(Object.keys(designTokens.spacing).length).toBeGreaterThan(20)
      
      // Check common spacing tokens
      expect(designTokens.spacing['0']).toBe('0px')
      expect(designTokens.spacing['1']).toBe('0.25rem')
      expect(designTokens.spacing['4']).toBe('1rem')
      expect(designTokens.spacing['8']).toBe('2rem')
    })

    it('should have complete typography tokens', () => {
      expect(designTokens.typography.fontFamily).toBeDefined()
      expect(designTokens.typography.fontSize).toBeDefined()
      expect(designTokens.typography.fontWeight).toBeDefined()
      expect(designTokens.typography.lineHeight).toBeDefined()

      // Check font sizes have both size and line height
      Object.values(designTokens.typography.fontSize).forEach(([fontSize, { lineHeight }]) => {
        expect(fontSize).toMatch(/^\d+(\.\d+)?rem$/)
        expect(lineHeight).toMatch(/^\d+(\.\d+)?(rem)?$/)
      })
    })

    it('should have animation tokens', () => {
      expect(designTokens.animation.durations).toBeDefined()
      expect(designTokens.animation.easings).toBeDefined()
      
      // Check duration values
      Object.values(designTokens.animation.durations).forEach(duration => {
        expect(duration).toMatch(/^\d+ms$/)
      })
    })
  })

  describe('Component Styles', () => {
    it('should have button component styles', () => {
      expect(componentStyles.button).toBeDefined()
      expect(componentStyles.button.base).toBeTruthy()
      expect(componentStyles.button.variants).toBeDefined()
      expect(componentStyles.button.sizes).toBeDefined()

      // Check all variants exist
      const expectedVariants = ['default', 'primary', 'secondary', 'outline', 'ghost', 'destructive', 'danger']
      expectedVariants.forEach(variant => {
        expect(componentStyles.button.variants[variant]).toBeDefined()
      })

      // Check all sizes exist
      const expectedSizes = ['xs', 'sm', 'md', 'lg', 'xl']
      expectedSizes.forEach(size => {
        expect(componentStyles.button.sizes[size]).toBeDefined()
      })
    })

    it('should have input component styles', () => {
      expect(componentStyles.input).toBeDefined()
      expect(componentStyles.input.base).toBeTruthy()
      expect(componentStyles.input.states).toBeDefined()
      
      // Check error, success, and disabled states
      expect(componentStyles.input.states.error).toBeDefined()
      expect(componentStyles.input.states.success).toBeDefined()
      expect(componentStyles.input.states.disabled).toBeDefined()
    })

    it('should have modal component styles', () => {
      expect(componentStyles.modal).toBeDefined()
      expect(componentStyles.modal.overlay).toBeTruthy()
      expect(componentStyles.modal.content).toBeTruthy()
      expect(componentStyles.modal.sizes).toBeDefined()

      // Check all modal sizes
      const expectedSizes = ['xs', 'sm', 'md', 'lg', 'xl', 'full']
      expectedSizes.forEach(size => {
        expect(componentStyles.modal.sizes[size]).toBeDefined()
      })
    })

    it('should have layout component styles', () => {
      expect(componentStyles.grid).toBeDefined()
      expect(componentStyles.stack).toBeDefined()
      
      // Check grid responsive classes
      expect(componentStyles.grid.responsive).toBeDefined()
      for (let i = 1; i <= 6; i++) {
        expect(componentStyles.grid.responsive[i]).toBeDefined()
      }

      // Check stack properties
      expect(componentStyles.stack.directions).toBeDefined()
      expect(componentStyles.stack.align).toBeDefined()
      expect(componentStyles.stack.justify).toBeDefined()
      expect(componentStyles.stack.spacing).toBeDefined()
    })
  })

  describe('Accessibility Guidelines', () => {
    it('should have WCAG color contrast standards', () => {
      expect(accessibilityGuidelines.colorContrast).toBeDefined()
      expect(accessibilityGuidelines.colorContrast.wcag).toBeDefined()
      
      // Check AA standards
      expect(accessibilityGuidelines.colorContrast.wcag.aa.normal).toBe(4.5)
      expect(accessibilityGuidelines.colorContrast.wcag.aa.large).toBe(3)
      
      // Check AAA standards
      expect(accessibilityGuidelines.colorContrast.wcag.aaa.normal).toBe(7)
      expect(accessibilityGuidelines.colorContrast.wcag.aaa.large).toBe(4.5)
    })

    it('should have keyboard navigation requirements', () => {
      expect(accessibilityGuidelines.keyboardNavigation).toBeDefined()
      expect(accessibilityGuidelines.keyboardNavigation.requirements).toBeInstanceOf(Array)
      expect(accessibilityGuidelines.keyboardNavigation.requirements.length).toBeGreaterThan(0)
      
      // Check implementation guidelines
      expect(accessibilityGuidelines.keyboardNavigation.implementation).toBeDefined()
      expect(accessibilityGuidelines.keyboardNavigation.implementation.tabIndex).toBeDefined()
    })

    it('should have screen reader guidelines', () => {
      expect(accessibilityGuidelines.screenReaders).toBeDefined()
      expect(accessibilityGuidelines.screenReaders.ariaLabels).toBeDefined()
      expect(accessibilityGuidelines.screenReaders.landmarks).toBeDefined()
      
      // Check landmark definitions
      const landmarks = accessibilityGuidelines.screenReaders.landmarks
      expect(landmarks.banner).toBeDefined()
      expect(landmarks.navigation).toBeDefined()
      expect(landmarks.main).toBeDefined()
      expect(landmarks.contentinfo).toBeDefined()
    })

    it('should have comprehensive testing checklists', () => {
      expect(accessibilityGuidelines.checklist).toBeDefined()
      expect(accessibilityGuidelines.checklist.development).toBeInstanceOf(Array)
      expect(accessibilityGuidelines.checklist.testing).toBeInstanceOf(Array)
      
      // Ensure checklists are not empty
      expect(accessibilityGuidelines.checklist.development.length).toBeGreaterThan(5)
      expect(accessibilityGuidelines.checklist.testing.length).toBeGreaterThan(5)
    })

    it('should have focus management patterns', () => {
      expect(accessibilityGuidelines.focusManagement).toBeDefined()
      expect(accessibilityGuidelines.focusManagement.patterns).toBeDefined()
      
      // Check specific patterns
      expect(accessibilityGuidelines.focusManagement.patterns.modal).toBeInstanceOf(Array)
      expect(accessibilityGuidelines.focusManagement.patterns.dropdown).toBeInstanceOf(Array)
      expect(accessibilityGuidelines.focusManagement.patterns.tabs).toBeInstanceOf(Array)
    })
  })

  describe('Design System Page', () => {
    it('should render without crashing', () => {
      render(<DesignSystemPage />)
      expect(screen.getByText('Design System')).toBeInTheDocument()
    })

    it('should display table of contents', () => {
      render(<DesignSystemPage />)
      expect(screen.getByText('Table of Contents')).toBeInTheDocument()
      expect(screen.getByText('Colors')).toBeInTheDocument()
      expect(screen.getAllByText('Typography')).toHaveLength(2) // Once in TOC, once as section header
      expect(screen.getByText('Components')).toBeInTheDocument()
      expect(screen.getByText('Accessibility')).toBeInTheDocument()
    })

    it('should display color palettes', () => {
      render(<DesignSystemPage />)
      expect(screen.getByText('Color Palette')).toBeInTheDocument()
      
      // Should display different color categories
      expect(screen.getByText(/primary/i)).toBeInTheDocument()
      expect(screen.getByText(/secondary/i)).toBeInTheDocument()
      expect(screen.getByText(/success/i)).toBeInTheDocument()
    })

    it('should display component showcase', () => {
      render(<DesignSystemPage />)
      expect(screen.getByText('Components')).toBeInTheDocument()
      
      // Should show button examples
      expect(screen.getByText('Buttons')).toBeInTheDocument()
      expect(screen.getByText('Form Inputs')).toBeInTheDocument()
      expect(screen.getByText('Cards')).toBeInTheDocument()
    })

    it('should display accessibility section', () => {
      render(<DesignSystemPage />)
      expect(screen.getByText('Accessibility Guidelines')).toBeInTheDocument()
      expect(screen.getByText('WCAG Color Contrast')).toBeInTheDocument()
      expect(screen.getByText('Keyboard Navigation')).toBeInTheDocument()
      expect(screen.getByText('Development Checklist')).toBeInTheDocument()
    })
  })

  describe('Component Playground', () => {
    it('should render without crashing', () => {
      render(<ComponentPlayground />)
      expect(screen.getByText('Component Playground')).toBeInTheDocument()
    })

    it('should have component selection interface', () => {
      render(<ComponentPlayground />)
      expect(screen.getByText('Components')).toBeInTheDocument()
      expect(screen.getByText('Category')).toBeInTheDocument()
      expect(screen.getByText('Component')).toBeInTheDocument()
    })

    it('should display props panel', () => {
      render(<ComponentPlayground />)
      expect(screen.getByText('Props')).toBeInTheDocument()
    })

    it('should show generated code', () => {
      render(<ComponentPlayground />)
      expect(screen.getByText('Generated Code')).toBeInTheDocument()
      expect(screen.getByText('Copy Code')).toBeInTheDocument()
    })

    it('should display API documentation table', () => {
      render(<ComponentPlayground />)
      expect(screen.getByText('API Documentation')).toBeInTheDocument()
      
      // Should have table headers
      expect(screen.getByText('Prop')).toBeInTheDocument()
      expect(screen.getByText('Type')).toBeInTheDocument()
      expect(screen.getByText('Required')).toBeInTheDocument()
      expect(screen.getByText('Default')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
    })
  })

  describe('Design System Integration', () => {
    it('should have consistent naming conventions', () => {
      // Check that all component style keys use consistent naming
      Object.keys(componentStyles).forEach(componentName => {
        expect(componentName).toMatch(/^[a-z][a-zA-Z]*$/) // camelCase
      })
      
      // Check design token structure
      Object.keys(designTokens).forEach(category => {
        expect(category).toMatch(/^[a-z][a-zA-Z]*$/) // camelCase
      })
    })

    it('should have type-safe exports', () => {
      // Ensure all main exports are available
      expect(designTokens).toBeDefined()
      expect(componentStyles).toBeDefined()
      expect(accessibilityGuidelines).toBeDefined()
      
      // Check that types can be imported (TypeScript will catch this)
      expect(typeof designTokens).toBe('object')
      expect(typeof componentStyles).toBe('object')
      expect(typeof accessibilityGuidelines).toBe('object')
    })

    it('should provide comprehensive component coverage', () => {
      // Ensure we have styles for all major component categories
      const expectedComponents = ['button', 'input', 'card', 'modal', 'badge', 'alert', 'grid', 'stack']
      expectedComponents.forEach(component => {
        expect(componentStyles[component]).toBeDefined()
      })
    })
  })
})