import React, { useState, useRef, useEffect } from 'react';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  placement?: 'left' | 'right' | 'top' | 'bottom';
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showOverlay?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  overlayClassName?: string;
  contentClassName?: string;
  onOpen?: () => void;
  onClosed?: () => void;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  placement = 'right',
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showOverlay = true,
  children,
  footer,
  className = '',
  overlayClassName = '',
  contentClassName = '',
  onOpen,
  onClosed
}) => {
  const [isAnimating, setIsAnimating] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  const getSizeClasses = () => {
    const isHorizontal = placement === 'left' || placement === 'right';
    const sizeMap = isHorizontal ? {
      sm: 'w-80',
      md: 'w-96',
      lg: 'w-[32rem]',
      xl: 'w-[40rem]',
      full: 'w-full'
    } : {
      sm: 'h-80',
      md: 'h-96',
      lg: 'h-[32rem]',
      xl: 'h-[40rem]',
      full: 'h-full'
    };
    return sizeMap[size];
  };

  const getPlacementClasses = () => {
    const placementMap = {
      left: 'left-0 top-0 h-full',
      right: 'right-0 top-0 h-full',
      top: 'top-0 left-0 w-full',
      bottom: 'bottom-0 left-0 w-full'
    };
    return placementMap[placement];
  };

  const getTransformClasses = () => {
    if (!mounted) return '';
    
    const isVisible = isOpen && !isAnimating;
    const transformMap = {
      left: isVisible ? 'translate-x-0' : '-translate-x-full',
      right: isVisible ? 'translate-x-0' : 'translate-x-full',
      top: isVisible ? 'translate-y-0' : '-translate-y-full',
      bottom: isVisible ? 'translate-y-0' : 'translate-y-full'
    };
    return transformMap[placement];
  };

  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlayClick && event.target === overlayRef.current) {
      handleClose();
    }
  };

  const handleClose = () => {
    if (isAnimating) return;
    
    setIsAnimating(true);
    setTimeout(() => {
      setIsAnimating(false);
      onClose();
      onClosed?.();
    }, 300);
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if (closeOnEscape && event.key === 'Escape') {
      handleClose();
    }
  };

  useEffect(() => {
    if (isOpen) {
      setMounted(true);
      onOpen?.();
      
      if (closeOnEscape) {
        document.addEventListener('keydown', handleKeyDown);
      }
      
      document.body.style.overflow = 'hidden';

      const focusableElements = drawerRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements && focusableElements.length > 0) {
        (focusableElements[0] as HTMLElement).focus();
      }
    } else {
      const timer = setTimeout(() => {
        setMounted(false);
      }, 300);
      
      return () => clearTimeout(timer);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, closeOnEscape, onOpen, onClosed]);

  useEffect(() => {
    const handleFocusTrap = (event: KeyboardEvent) => {
      if (!isOpen || !drawerRef.current) return;

      const focusableElements = drawerRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleFocusTrap);
    }

    return () => {
      document.removeEventListener('keydown', handleFocusTrap);
    };
  }, [isOpen]);

  if (!isOpen && !isAnimating && !mounted) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50">
      {showOverlay && (
        <div
          ref={overlayRef}
          className={`
            absolute inset-0 bg-black transition-opacity duration-300
            ${isOpen && !isAnimating ? 'bg-opacity-50' : 'bg-opacity-0'}
            ${overlayClassName}
          `}
          onClick={handleOverlayClick}
        />
      )}
      
      <div
        ref={drawerRef}
        className={`
          absolute bg-white shadow-xl flex flex-col
          transition-transform duration-300 ease-in-out
          ${getPlacementClasses()}
          ${getSizeClasses()}
          ${getTransformClasses()}
          ${contentClassName}
          ${className}
        `}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "drawer-title" : undefined}
      >
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200 shrink-0">
            {title && (
              <h2 id="drawer-title" className="text-lg font-semibold text-gray-900">
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600 transition-colors ml-auto"
                type="button"
                aria-label="Close drawer"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4">
          {children}
        </div>

        {footer && (
          <div className="border-t border-gray-200 p-4 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default Drawer;