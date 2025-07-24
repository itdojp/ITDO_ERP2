import React, { useState, useRef, useEffect } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  preventScroll?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  overlayClassName?: string;
  contentClassName?: string;
  centered?: boolean;
  animation?: "fade" | "slide" | "zoom" | "none";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = "md",
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  preventScroll = true,
  children,
  footer,
  className = "",
  overlayClassName = "",
  contentClassName = "",
  centered = true,
  animation = "fade",
}) => {
  const [isAnimating, setIsAnimating] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const getSizeClasses = () => {
    const sizeMap = {
      sm: "max-w-md",
      md: "max-w-lg",
      lg: "max-w-2xl",
      xl: "max-w-4xl",
      full: "max-w-full w-full h-full",
    };
    return sizeMap[size];
  };

  const getAnimationClasses = () => {
    if (animation === "none") return "";

    const baseTransition = "transition-all duration-300 ease-in-out";

    switch (animation) {
      case "slide":
        return `${baseTransition} ${isOpen && !isAnimating ? "translate-y-0" : "-translate-y-full"}`;
      case "zoom":
        return `${baseTransition} ${isOpen && !isAnimating ? "scale-100" : "scale-95"}`;
      case "fade":
      default:
        return `${baseTransition} ${isOpen && !isAnimating ? "opacity-100" : "opacity-0"}`;
    }
  };

  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlayClick && event.target === overlayRef.current) {
      handleClose();
    }
  };

  const handleClose = () => {
    if (animation !== "none") {
      setIsAnimating(true);
      setTimeout(() => {
        setIsAnimating(false);
        onClose();
      }, 300);
    } else {
      onClose();
    }
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if (closeOnEscape && event.key === "Escape") {
      handleClose();
    }
  };

  useEffect(() => {
    if (isOpen) {
      if (closeOnEscape) {
        document.addEventListener("keydown", handleKeyDown);
      }

      if (preventScroll) {
        document.body.style.overflow = "hidden";
      }

      const focusableElements = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );

      if (focusableElements && focusableElements.length > 0) {
        (focusableElements[0] as HTMLElement).focus();
      }
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (preventScroll) {
        document.body.style.overflow = "unset";
      }
    };
  }, [isOpen, closeOnEscape, preventScroll]);

  useEffect(() => {
    const handleFocusTrap = (event: KeyboardEvent) => {
      if (!isOpen || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[
        focusableElements.length - 1
      ] as HTMLElement;

      if (event.key === "Tab") {
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
      document.addEventListener("keydown", handleFocusTrap);
    }

    return () => {
      document.removeEventListener("keydown", handleFocusTrap);
    };
  }, [isOpen]);

  if (!isOpen && !isAnimating) {
    return null;
  }

  return (
    <div
      ref={overlayRef}
      className={`
        fixed inset-0 z-50 flex items-center justify-center p-4
        bg-black bg-opacity-50 transition-opacity duration-300
        ${isOpen && !isAnimating ? "opacity-100" : "opacity-0"}
        ${centered ? "items-center" : "items-start pt-20"}
        ${overlayClassName}
      `}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      <div
        ref={modalRef}
        className={`
          relative bg-white rounded-lg shadow-xl w-full
          ${getSizeClasses()}
          ${getAnimationClasses()}
          ${contentClassName}
          ${className}
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            {title && (
              <h2
                id="modal-title"
                className="text-lg font-semibold text-gray-900"
              >
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                type="button"
                aria-label="Close modal"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        <div className="p-6">{children}</div>

        {footer && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;
