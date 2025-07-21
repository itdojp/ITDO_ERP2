import React from 'react'
import { createPortal } from 'react-dom'
import { cn } from '../../../lib/utils'
import { X } from 'lucide-react'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  className?: string
  overlayClassName?: string
  animation?: 'fade' | 'slide' | 'scale' | 'none'
  preventScroll?: boolean
}

const Modal = React.memo(React.forwardRef<HTMLDivElement, ModalProps>(
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
    overlayClassName,
    animation = 'fade',
    preventScroll = true,
  }, ref) => {
    const [mounted, setMounted] = React.useState(false)
    const [isAnimating, setIsAnimating] = React.useState(false)
    const modalRef = React.useRef<HTMLDivElement>(null)
    const previousActiveElement = React.useRef<HTMLElement | null>(null)

    React.useImperativeHandle(ref, () => modalRef.current!)

    // Handle mounting for SSR compatibility
    React.useEffect(() => {
      setMounted(true)
      return () => setMounted(false)
    }, [])

    // Handle scroll prevention
    React.useEffect(() => {
      if (!preventScroll || !isOpen) return

      const originalStyle = window.getComputedStyle(document.body).overflow
      document.body.style.overflow = 'hidden'

      return () => {
        document.body.style.overflow = originalStyle
      }
    }, [isOpen, preventScroll])

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

    // Focus management
    React.useEffect(() => {
      if (isOpen) {
        previousActiveElement.current = document.activeElement as HTMLElement
        
        // Focus the modal after a small delay to ensure it's rendered
        setTimeout(() => {
          const modal = modalRef.current
          if (modal) {
            const firstFocusableElement = modal.querySelector(
              'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            ) as HTMLElement
            
            if (firstFocusableElement) {
              firstFocusableElement.focus()
            } else {
              modal.focus()
            }
          }
        }, 100)
      } else {
        // Return focus to previous element when modal closes
        if (previousActiveElement.current) {
          previousActiveElement.current.focus()
        }
      }
    }, [isOpen])

    // Focus trap
    React.useEffect(() => {
      if (!isOpen) return

      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return

        const modal = modalRef.current
        if (!modal) return

        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        
        const firstElement = focusableElements[0] as HTMLElement
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

        if (focusableElements.length === 0) {
          e.preventDefault()
          return
        }

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus()
            e.preventDefault()
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus()
            e.preventDefault()
          }
        }
      }

      document.addEventListener('keydown', handleTabKey)
      return () => document.removeEventListener('keydown', handleTabKey)
    }, [isOpen])

    // Animation handling
    React.useEffect(() => {
      if (isOpen) {
        setIsAnimating(true)
        const timer = setTimeout(() => setIsAnimating(false), 300)
        return () => clearTimeout(timer)
      }
    }, [isOpen])

    const handleOverlayClick = (e: React.MouseEvent) => {
      if (closeOnOverlayClick && e.target === e.currentTarget) {
        onClose()
      }
    }

    if (!mounted || !isOpen) return null

    const sizes = {
      xs: 'max-w-xs',
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-xl',
      full: 'max-w-full mx-4'
    }

    const animations = {
      fade: {
        overlay: isAnimating ? 'opacity-0' : 'opacity-100',
        modal: isAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
      },
      slide: {
        overlay: isAnimating ? 'opacity-0' : 'opacity-100',
        modal: isAnimating ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
      },
      scale: {
        overlay: isAnimating ? 'opacity-0' : 'opacity-100',
        modal: isAnimating ? 'opacity-0 scale-50' : 'opacity-100 scale-100'
      },
      none: {
        overlay: 'opacity-100',
        modal: 'opacity-100'
      }
    }

    const animationClasses = animations[animation] || animations.fade

    const modalContent = (
      <div
        className={cn(
          'fixed inset-0 z-50 flex items-center justify-center p-4',
          'bg-black/50 backdrop-blur-sm transition-all duration-300',
          animationClasses.overlay,
          overlayClassName
        )}
        onClick={handleOverlayClick}
      >
        <div
          ref={modalRef}
          className={cn(
            'relative w-full bg-white rounded-lg shadow-xl',
            'transform transition-all duration-300',
            'max-h-[90vh] overflow-hidden',
            sizes[size],
            animationClasses.modal,
            className
          )}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? 'modal-title' : undefined}
          aria-describedby={description ? 'modal-description' : undefined}
          tabIndex={-1}
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex-1 min-w-0">
                {title && (
                  <h2 
                    id="modal-title"
                    className="text-lg font-semibold text-gray-900 truncate"
                  >
                    {title}
                  </h2>
                )}
                {description && (
                  <p 
                    id="modal-description"
                    className="mt-1 text-sm text-gray-600"
                  >
                    {description}
                  </p>
                )}
              </div>
              
              {showCloseButton && (
                <button
                  type="button"
                  className={cn(
                    'ml-4 text-gray-400 hover:text-gray-600',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-sm',
                    'transition-colors duration-200'
                  )}
                  onClick={onClose}
                  aria-label="Close modal"
                >
                  <X className="h-6 w-6" />
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
))

Modal.displayName = 'Modal'

export default Modal