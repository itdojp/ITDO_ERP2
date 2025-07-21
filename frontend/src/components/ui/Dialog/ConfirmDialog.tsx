import React from 'react'
import { cn } from '../../../lib/utils'
import { createPortal } from 'react-dom'
import { AlertTriangle, CheckCircle, XCircle, Info, X } from 'lucide-react'
import Button from '../Button'

export interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'info'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  className?: string
}

const ConfirmDialog = React.memo(({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  description = 'Are you sure you want to proceed?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  size = 'md',
  loading = false,
  disabled = false,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className,
}: ConfirmDialogProps) => {
  const [mounted, setMounted] = React.useState(false)
  const modalRef = React.useRef<HTMLDivElement>(null)
  const confirmButtonRef = React.useRef<HTMLButtonElement>(null)

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

  // Focus management
  React.useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus()
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

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleConfirm = async () => {
    if (disabled || loading) return
    onConfirm()
  }

  if (!mounted || !isOpen) return null

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg'
  }

  const icons = {
    default: Info,
    danger: XCircle,
    warning: AlertTriangle,
    success: CheckCircle,
    info: Info
  }

  const iconColors = {
    default: 'text-blue-500',
    danger: 'text-red-500',
    warning: 'text-yellow-500',
    success: 'text-green-500',
    info: 'text-blue-500'
  }

  const confirmButtonVariants = {
    default: 'primary' as const,
    danger: 'destructive' as const,
    warning: 'primary' as const,
    success: 'primary' as const,
    info: 'primary' as const
  }

  const IconComponent = icons[variant]

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleOverlayClick}
    >
      <div
        ref={modalRef}
        className={cn(
          'relative w-full rounded-lg bg-white shadow-xl transform transition-all',
          sizes[size],
          className
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description"
      >
        {/* Close button */}
        <button
          type="button"
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-sm"
          onClick={onClose}
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6">
          {/* Header with icon */}
          <div className="flex items-start gap-4">
            <div className={cn(
              'flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center',
              variant === 'danger' && 'bg-red-100',
              variant === 'warning' && 'bg-yellow-100',
              variant === 'success' && 'bg-green-100',
              (variant === 'default' || variant === 'info') && 'bg-blue-100'
            )}>
              <IconComponent className={cn('h-6 w-6', iconColors[variant])} />
            </div>

            <div className="flex-1 min-w-0">
              <h3
                id="dialog-title"
                className="text-lg font-semibold text-gray-900 mb-2"
              >
                {title}
              </h3>
              
              <p
                id="dialog-description"
                className="text-sm text-gray-600 mb-6"
              >
                {description}
              </p>

              {/* Actions */}
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={onClose}
                  disabled={loading}
                  className="sm:w-auto w-full"
                >
                  {cancelText}
                </Button>
                
                <Button
                  ref={confirmButtonRef}
                  variant={confirmButtonVariants[variant]}
                  onClick={handleConfirm}
                  loading={loading}
                  disabled={disabled}
                  className="sm:w-auto w-full"
                >
                  {confirmText}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
})

ConfirmDialog.displayName = 'ConfirmDialog'

export default ConfirmDialog