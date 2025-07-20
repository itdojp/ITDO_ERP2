import React from 'react'
import { createPortal } from 'react-dom'
import { cn } from '../../lib/utils'
import { X } from 'lucide-react'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  className?: string
}

const Modal = React.forwardRef<HTMLDivElement, ModalProps>(
  ({
    isOpen,
    onClose,
    title,
    description,
    children,
    size = 'md',
    closeOnOverlayClick = true,
    closeOnEscape = true,
    showCloseButton = true,
    className,
  }, ref) => {
    const [mounted, setMounted] = React.useState(false)

    // Handle mounting for SSR compatibility
    React.useEffect(() => {
      setMounted(true)
      return () => setMounted(false)
    }, [])

    // Handle escape key
    React.useEffect(() => {
      if (!isOpen || !closeOnEscape) return

      const handleEscape = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          onClose()
        }
      }

      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }, [isOpen, closeOnEscape, onClose])

    // Handle body scroll lock
    React.useEffect(() => {
      if (!isOpen) return

      const originalStyle = window.getComputedStyle(document.body).overflow
      document.body.style.overflow = 'hidden'

      return () => {
        document.body.style.overflow = originalStyle
      }
    }, [isOpen])

    // Focus management
    React.useEffect(() => {
      if (!isOpen) return

      const focusableElements = document.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
      )
      const firstElement = focusableElements[0] as HTMLElement
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

      const handleTabKey = (event: KeyboardEvent) => {
        if (event.key !== 'Tab') return

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement?.focus()
            event.preventDefault()
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement?.focus()
            event.preventDefault()
          }
        }
      }

      document.addEventListener('keydown', handleTabKey)
      firstElement?.focus()

      return () => document.removeEventListener('keydown', handleTabKey)
    }, [isOpen])

    const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
      if (closeOnOverlayClick && event.target === event.currentTarget) {
        onClose()
      }
    }

    const sizeClasses = {
      sm: 'max-w-md',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      xl: 'max-w-4xl',
      full: 'max-w-7xl mx-4'
    }

    if (!mounted || !isOpen) {
      return null
    }

    const modalContent = (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        aria-describedby={description ? 'modal-description' : undefined}
      >
        {/* Overlay */}
        <div
          className="fixed inset-0 bg-black/50 transition-opacity"
          onClick={handleOverlayClick}
        />
        
        {/* Modal */}
        <div
          ref={ref}
          className={cn(
            'relative w-full bg-white rounded-lg shadow-xl transition-all',
            'max-h-[90vh] overflow-hidden flex flex-col',
            sizeClasses[size],
            className
          )}
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex-1">
                {title && (
                  <h2 
                    id="modal-title"
                    className="text-lg font-semibold text-gray-900"
                  >
                    {title}
                  </h2>
                )}
                {description && (
                  <p 
                    id="modal-description"
                    className="mt-1 text-sm text-gray-500"
                  >
                    {description}
                  </p>
                )}
              </div>
              
              {showCloseButton && (
                <button
                  type="button"
                  className={cn(
                    'ml-4 p-2 text-gray-400 hover:text-gray-500',
                    'hover:bg-gray-100 rounded-md transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500'
                  )}
                  onClick={onClose}
                  aria-label="Close modal"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
          )}
          
          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {children}
          </div>
        </div>
      </div>
    )

    return createPortal(modalContent, document.body)
  }
)

Modal.displayName = 'Modal'

export default Modal