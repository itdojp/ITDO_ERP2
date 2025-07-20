import React from 'react'
import Modal from './Modal'
import Button from './Button'
import { AlertTriangle, Info, CheckCircle } from 'lucide-react'

export interface DialogProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  type?: 'confirm' | 'alert' | 'success' | 'danger'
  confirmText?: string
  cancelText?: string
  onConfirm?: () => void
  onCancel?: () => void
  loading?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
}

const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
  ({
    isOpen,
    onClose,
    title,
    description,
    type = 'confirm',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    onConfirm,
    onCancel,
    loading = false,
    closeOnOverlayClick = true,
    closeOnEscape = true,
  }, ref) => {
    const handleConfirm = () => {
      onConfirm?.()
    }

    const handleCancel = () => {
      onCancel?.()
      onClose()
    }

    const getIcon = () => {
      const iconClass = "h-6 w-6"
      
      switch (type) {
        case 'success':
          return <CheckCircle className={`${iconClass} text-green-600`} />
        case 'danger':
          return <AlertTriangle className={`${iconClass} text-red-600`} />
        case 'alert':
          return <AlertTriangle className={`${iconClass} text-yellow-600`} />
        case 'confirm':
        default:
          return <Info className={`${iconClass} text-blue-600`} />
      }
    }

    const getConfirmButtonVariant = () => {
      switch (type) {
        case 'danger':
          return 'destructive'
        case 'success':
          return 'primary'
        default:
          return 'primary'
      }
    }

    return (
      <Modal
        ref={ref}
        isOpen={isOpen}
        onClose={onClose}
        size="sm"
        closeOnOverlayClick={closeOnOverlayClick}
        closeOnEscape={closeOnEscape}
        showCloseButton={false}
      >
        <div className="sm:flex sm:items-start">
          <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 sm:mx-0 sm:h-10 sm:w-10">
            {getIcon()}
          </div>
          
          <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
            <h3 className="text-lg font-medium text-gray-900">
              {title}
            </h3>
            {description && (
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  {description}
                </p>
              </div>
            )}
          </div>
        </div>
        
        <div className="mt-6 sm:flex sm:flex-row-reverse sm:gap-3">
          <Button
            variant={getConfirmButtonVariant()}
            onClick={handleConfirm}
            loading={loading}
            disabled={loading}
            className="w-full sm:w-auto"
          >
            {confirmText}
          </Button>
          
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={loading}
            className="mt-3 w-full sm:mt-0 sm:w-auto"
          >
            {cancelText}
          </Button>
        </div>
      </Modal>
    )
  }
)

Dialog.displayName = 'Dialog'

export default Dialog