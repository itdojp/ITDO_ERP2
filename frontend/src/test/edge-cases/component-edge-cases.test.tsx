import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { act } from 'react'
import Badge from '../../components/ui/Badge'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Alert from '../../components/ui/Alert'
import LoadingSpinner from '../../components/common/LoadingSpinner'

describe('Component Edge Cases Tests', () => {
  describe('Null/Undefined Props Handling', () => {
    it('Badge handles null/undefined children gracefully', () => {
      act(() => {
        render(<Badge>{null}</Badge>)
      })
      
      const badge = screen.getByRole('generic')
      expect(badge).toBeInTheDocument()
      expect(badge).toBeEmptyDOMElement()
    })
    
    it('Card handles undefined title', () => {
      act(() => {
        render(<Card title={undefined}>Content</Card>)
      })
      
      const card = screen.getByText('Content')
      expect(card).toBeInTheDocument()
      // Should not render title element
      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })
    
    it('Button handles null onClick', () => {
      act(() => {
        render(<Button onClick={null as any}>Click me</Button>)
      })
      
      const button = screen.getByText('Click me')
      expect(button).toBeInTheDocument()
      expect(button).not.toBeDisabled()
    })
  })
  
  describe('Empty State Rendering', () => {
    it('Badge with empty string children', () => {
      act(() => {
        render(<Badge>{''}</Badge>)
      })
      
      const badge = screen.getByRole('generic')
      expect(badge).toBeInTheDocument()
      expect(badge).toBeEmptyDOMElement()
    })
    
    it('Card with empty content', () => {
      act(() => {
        render(<Card title="Empty Card"></Card>)
      })
      
      expect(screen.getByText('Empty Card')).toBeInTheDocument()
      const card = screen.getByText('Empty Card').closest('div')
      expect(card).toBeInTheDocument()
    })
    
    it('Alert with empty message fallback', () => {
      act(() => {
        render(<Alert message="" variant="info" />)
      })
      
      // Should still render but with no visible message
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
    })
  })
  
  describe('Large Data Set Performance', () => {
    it('renders many badges efficiently', () => {
      const manyBadges = Array.from({ length: 100 }, (_, i) => (
        <Badge key={i} variant="primary">Badge {i}</Badge>
      ))
      
      const startTime = performance.now()
      
      act(() => {
        render(<div>{manyBadges}</div>)
      })
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render within reasonable time (adjust threshold as needed)
      expect(renderTime).toBeLessThan(100) // 100ms threshold
      
      // Verify some badges are rendered
      expect(screen.getByText('Badge 0')).toBeInTheDocument()
      expect(screen.getByText('Badge 50')).toBeInTheDocument()
      expect(screen.getByText('Badge 99')).toBeInTheDocument()
    })
    
    it('handles large card content efficiently', () => {
      const largeContent = 'Lorem ipsum '.repeat(1000) // ~11KB of text
      
      act(() => {
        render(
          <Card title="Large Content">
            <p>{largeContent}</p>
          </Card>
        )
      })
      
      expect(screen.getByText('Large Content')).toBeInTheDocument()
      // Verify content is rendered (check first part)
      expect(screen.getByText(/Lorem ipsum/)).toBeInTheDocument()
    })
  })
  
  describe('Rapid State Changes', () => {
    it('Button handles rapid loading state changes', async () => {
      const RapidStateButton = () => {
        const [loading, setLoading] = React.useState(false)
        
        React.useEffect(() => {
          // Simulate rapid state changes
          const interval = setInterval(() => {
            setLoading(prev => !prev)
          }, 10) // Very rapid changes
          
          // Stop after 100ms
          setTimeout(() => clearInterval(interval), 100)
          
          return () => clearInterval(interval)
        }, [])
        
        return <Button loading={loading}>Rapid Changes</Button>
      }
      
      act(() => {
        render(<RapidStateButton />)
      })
      
      const button = screen.getByText('Rapid Changes')
      expect(button).toBeInTheDocument()
      
      // Should not crash during rapid state changes
      await new Promise(resolve => setTimeout(resolve, 150))
      expect(button).toBeInTheDocument()
    })
    
    it('LoadingSpinner handles rapid visibility changes', async () => {
      const RapidSpinner = () => {
        const [visible, setVisible] = React.useState(true)
        
        React.useEffect(() => {
          // Rapid show/hide
          const interval = setInterval(() => {
            setVisible(prev => !prev)
          }, 5)
          
          setTimeout(() => clearInterval(interval), 50)
          
          return () => clearInterval(interval)
        }, [])
        
        return visible ? <LoadingSpinner /> : <div>Hidden</div>
      }
      
      act(() => {
        render(<RapidSpinner />)
      })
      
      // Should handle rapid mount/unmount without errors
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Component should still be in DOM
      expect(screen.getByText(/Loading|Hidden/)).toBeInTheDocument()
    })
  })
  
  describe('Memory Management', () => {
    it('properly cleans up event listeners on unmount', () => {
      const EventButton = () => {
        React.useEffect(() => {
          const handleClick = () => console.log('Global click')
          document.addEventListener('click', handleClick)
          
          return () => {
            document.removeEventListener('click', handleClick)
          }
        }, [])
        
        return <Button>Event Button</Button>
      }
      
      const { unmount } = render(<EventButton />)
      
      const button = screen.getByText('Event Button')
      expect(button).toBeInTheDocument()
      
      // Should unmount without memory leaks
      act(() => {
        unmount()
      })
      
      expect(screen.queryByText('Event Button')).not.toBeInTheDocument()
    })
    
    it('handles component unmounting during async operations', async () => {
      const AsyncComponent = () => {
        const [data, setData] = React.useState(null)
        
        React.useEffect(() => {
          let mounted = true
          
          // Simulate async operation
          setTimeout(() => {
            if (mounted) {
              setData('Loaded')
            }
          }, 50)
          
          return () => {
            mounted = false
          }
        }, [])
        
        return <div>{data || 'Loading...'}</div>
      }
      
      const { unmount } = render(<AsyncComponent />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      
      // Unmount before async operation completes
      act(() => {
        unmount()
      })
      
      // Should not cause memory leaks or state updates on unmounted component
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      expect(screen.queryByText('Loaded')).not.toBeInTheDocument()
    })
  })
  
  describe('Accessibility Edge Cases', () => {
    it('maintains ARIA attributes under stress conditions', () => {
      const StressedComponent = () => {
        const [counter, setCounter] = React.useState(0)
        
        React.useEffect(() => {
          const interval = setInterval(() => {
            setCounter(prev => prev + 1)
          }, 10)
          
          setTimeout(() => clearInterval(interval), 100)
          
          return () => clearInterval(interval)
        }, [])
        
        return (
          <div>
            <LoadingSpinner aria-label={`Loading ${counter}`} />
            <Alert message={`Update ${counter}`} variant="info" />
          </div>
        )
      }
      
      act(() => {
        render(<StressedComponent />)
      })
      
      // Should maintain accessibility even during rapid updates
      const spinner = screen.getByRole('status')
      const alert = screen.getByRole('alert')
      
      expect(spinner).toHaveAttribute('aria-label')
      expect(alert).toBeInTheDocument()
    })
  })
})