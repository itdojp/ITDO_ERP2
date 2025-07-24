import React, { useState, useEffect, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface NotificationAction {
  label: string;
  onClick: () => void;
}

export interface NotificationProps {
  message?: string;
  content?: React.ReactNode;
  title?: string;
  type?: "success" | "error" | "warning" | "info";
  position?:
    | "top-right"
    | "top-left"
    | "bottom-right"
    | "bottom-left"
    | "top-center"
    | "bottom-center";
  size?: "sm" | "md" | "lg";
  theme?: "light" | "dark";
  priority?: "low" | "normal" | "high" | "urgent";
  duration?: number;
  closable?: boolean;
  persistent?: boolean;
  showProgress?: boolean;
  pauseOnHover?: boolean;
  animate?: boolean;
  multiline?: boolean;
  rtl?: boolean;
  stackable?: boolean;
  queueable?: boolean;
  dismissOnClickOutside?: boolean;
  swipeToDismiss?: boolean;
  draggable?: boolean;
  loading?: boolean;
  showLoadingSpinner?: boolean;
  showTimestamp?: boolean;
  showDefaultIcon?: boolean;
  autoFocus?: boolean;
  playSound?: boolean;
  visible?: boolean;
  icon?: React.ReactNode;
  action?: NotificationAction;
  closeButton?: React.ReactNode;
  timestamp?: string;
  soundUrl?: string;
  stackIndex?: number;
  maxQueue?: number;
  ariaLabel?: string;
  ariaLive?: "polite" | "assertive" | "off";
  onClose?: () => void;
  onDrag?: (e: React.DragEvent) => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const Notification: React.FC<NotificationProps> = ({
  message,
  content,
  title,
  type = "info",
  position = "top-right",
  size = "md",
  theme = "light",
  priority = "normal",
  duration = 4000,
  closable = false,
  persistent = false,
  showProgress = false,
  pauseOnHover = false,
  animate = false,
  multiline = false,
  rtl = false,
  stackable = false,
  queueable = false,
  dismissOnClickOutside = false,
  swipeToDismiss = false,
  draggable = false,
  loading = false,
  showLoadingSpinner = false,
  showTimestamp = false,
  showDefaultIcon = false,
  autoFocus = false,
  playSound = false,
  visible = true,
  icon,
  action,
  closeButton,
  timestamp,
  soundUrl = "/notification.mp3",
  stackIndex,
  maxQueue,
  ariaLabel,
  ariaLive = "polite",
  onClose,
  onDrag,
  className,
  "data-testid": dataTestId = "notification-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(visible);
  const [progress, setProgress] = useState(100);
  const [isPaused, setIsPaused] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const timerRef = useRef<NodeJS.Timeout>();
  const progressTimerRef = useRef<NodeJS.Timeout>();
  const containerRef = useRef<HTMLDivElement>(null);
  const startTimeRef = useRef<number>();
  const remainingTimeRef = useRef<number>(duration);

  const sizeClasses = {
    sm: "size-sm p-3 text-sm",
    md: "size-md p-4 text-base",
    lg: "size-lg p-6 text-lg",
  };

  const themeClasses = {
    light: "theme-light bg-white border-gray-300 text-gray-900 shadow-lg",
    dark: "theme-dark bg-gray-800 border-gray-600 text-white shadow-lg",
  };

  const typeClasses = {
    success:
      "type-success border-l-4 border-green-500 bg-green-50 text-green-800",
    error: "type-error border-l-4 border-red-500 bg-red-50 text-red-800",
    warning:
      "type-warning border-l-4 border-yellow-500 bg-yellow-50 text-yellow-800",
    info: "type-info border-l-4 border-blue-500 bg-blue-50 text-blue-800",
  };

  const positionClasses = {
    "top-right": "position-top-right fixed top-4 right-4",
    "top-left": "position-top-left fixed top-4 left-4",
    "bottom-right": "position-bottom-right fixed bottom-4 right-4",
    "bottom-left": "position-bottom-left fixed bottom-4 left-4",
    "top-center":
      "position-top-center fixed top-4 left-1/2 transform -translate-x-1/2",
    "bottom-center":
      "position-bottom-center fixed bottom-4 left-1/2 transform -translate-x-1/2",
  };

  const priorityClasses = {
    low: "priority-low",
    normal: "priority-normal",
    high: "priority-high z-50",
    urgent: "priority-urgent z-60 ring-2 ring-red-500",
  };

  // Auto close functionality
  useEffect(() => {
    if (!persistent && duration && duration > 0 && isVisible) {
      startTimer();
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    };
  }, [duration, persistent, isVisible, isPaused]);

  // Visibility effect
  useEffect(() => {
    setIsVisible(visible);
  }, [visible]);

  // Play sound effect
  useEffect(() => {
    if (playSound && isVisible && soundUrl) {
      try {
        const audio = new Audio(soundUrl);
        audio.play().catch(() => {
          // Ignore audio play errors
        });
      } catch (error) {
        // Ignore audio creation errors
      }
    }
  }, [playSound, isVisible, soundUrl]);

  // Auto focus effect
  useEffect(() => {
    if (autoFocus && isVisible && containerRef.current) {
      containerRef.current.focus();
    }
  }, [autoFocus, isVisible]);

  // Click outside handler
  useEffect(() => {
    if (!dismissOnClickOutside) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        handleClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dismissOnClickOutside]);

  const startTimer = useCallback(() => {
    if (isPaused || !duration) return;

    startTimeRef.current = Date.now();

    timerRef.current = setTimeout(() => {
      handleClose();
    }, remainingTimeRef.current);

    if (showProgress) {
      startProgressTimer();
    }
  }, [isPaused, duration, showProgress]);

  const startProgressTimer = useCallback(() => {
    const startTime = Date.now();
    const totalDuration = remainingTimeRef.current;

    progressTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, totalDuration - elapsed);
      const progressPercent = (remaining / totalDuration) * 100;

      setProgress(progressPercent);

      if (remaining <= 0) {
        if (progressTimerRef.current) {
          clearInterval(progressTimerRef.current);
        }
      }
    }, 50);
  }, []);

  const pauseTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }

    if (startTimeRef.current) {
      const elapsed = Date.now() - startTimeRef.current;
      remainingTimeRef.current = Math.max(
        0,
        remainingTimeRef.current - elapsed,
      );
    }

    setIsPaused(true);
  }, []);

  const resumeTimer = useCallback(() => {
    setIsPaused(false);
    if (remainingTimeRef.current > 0) {
      startTimer();
    }
  }, [startTimer]);

  const handleClose = useCallback(() => {
    if (animate) {
      setIsAnimating(true);
      setTimeout(() => {
        setIsVisible(false);
        onClose?.();
        setIsAnimating(false);
      }, 200);
    } else {
      setIsVisible(false);
      onClose?.();
    }
  }, [animate, onClose]);

  const handleMouseEnter = useCallback(() => {
    if (pauseOnHover && !persistent) {
      pauseTimer();
    }
  }, [pauseOnHover, persistent, pauseTimer]);

  const handleMouseLeave = useCallback(() => {
    if (pauseOnHover && !persistent && isPaused) {
      resumeTimer();
    }
  }, [pauseOnHover, persistent, isPaused, resumeTimer]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClose();
      }
    },
    [handleClose],
  );

  const handleActionClick = useCallback(() => {
    try {
      action?.onClick();
    } catch (error) {
      console.error("Notification action failed:", error);
    }
  }, [action]);

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (!swipeToDismiss) return;

      const touch = e.touches[0];
      containerRef.current?.setAttribute(
        "data-start-x",
        touch.clientX.toString(),
      );
    },
    [swipeToDismiss],
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!swipeToDismiss) return;

      const touch = e.touches[0];
      const startX = parseFloat(
        containerRef.current?.getAttribute("data-start-x") || "0",
      );
      const deltaX = touch.clientX - startX;

      if (Math.abs(deltaX) > 50) {
        containerRef.current?.style.setProperty(
          "transform",
          `translateX(${deltaX}px)`,
        );
      }
    },
    [swipeToDismiss],
  );

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!swipeToDismiss) return;

      const startX = parseFloat(
        containerRef.current?.getAttribute("data-start-x") || "0",
      );
      const endX = e.changedTouches?.[0]?.clientX || 0;
      const deltaX = endX - startX;

      if (Math.abs(deltaX) > 100) {
        handleClose();
      } else {
        containerRef.current?.style.setProperty("transform", "translateX(0)");
      }
    },
    [swipeToDismiss, handleClose],
  );

  const getDefaultIcon = () => {
    switch (type) {
      case "success":
        return (
          <div className="flex-shrink-0 mr-3" data-testid="notification-icon">
            <div className="w-5 h-5 flex-shrink-0 icon-success text-green-500">
              ✓
            </div>
          </div>
        );
      case "error":
        return (
          <div className="flex-shrink-0 mr-3" data-testid="notification-icon">
            <div className="w-5 h-5 flex-shrink-0 icon-error text-red-500">
              ✕
            </div>
          </div>
        );
      case "warning":
        return (
          <div className="flex-shrink-0 mr-3" data-testid="notification-icon">
            <div className="w-5 h-5 flex-shrink-0 icon-warning text-yellow-500">
              ⚠
            </div>
          </div>
        );
      case "info":
        return (
          <div className="flex-shrink-0 mr-3" data-testid="notification-icon">
            <div className="w-5 h-5 flex-shrink-0 icon-info text-blue-500">
              ℹ
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const renderIcon = () => {
    if (loading && showLoadingSpinner) {
      return (
        <div className="flex-shrink-0 mr-3" data-testid="loading-spinner">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-current rounded-full animate-spin"></div>
        </div>
      );
    }

    if (icon) {
      return (
        <div className="flex-shrink-0 mr-3" data-testid="notification-icon">
          {icon}
        </div>
      );
    }

    if (showDefaultIcon) {
      return getDefaultIcon();
    }

    return null;
  };

  const renderCloseButton = () => {
    if (closeButton) {
      return closeButton;
    }

    if (closable) {
      return (
        <button
          type="button"
          className="ml-auto pl-3 flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          onClick={handleClose}
          onKeyDown={handleKeyDown}
          tabIndex={0}
          data-testid="notification-close"
        >
          ✕
        </button>
      );
    }

    return null;
  };

  const renderProgress = () => {
    if (!showProgress || !duration || persistent) return null;

    return (
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 rounded-b">
        <div
          className="h-full bg-current rounded-b transition-all duration-100 ease-linear"
          style={{ width: `${progress}%` }}
          data-testid="notification-progress"
        />
      </div>
    );
  };

  const renderTimestamp = () => {
    if (!showTimestamp) return null;

    const displayTimestamp = timestamp || new Date().toLocaleTimeString();

    return (
      <div
        className="text-xs text-gray-500 mt-1"
        data-testid="notification-timestamp"
      >
        {displayTimestamp}
      </div>
    );
  };

  const renderContent = () => {
    if (content) {
      return <div className="flex-1">{content}</div>;
    }

    return (
      <div className="flex-1">
        {title && (
          <div className="font-semibold mb-1" data-testid="notification-title">
            {title}
          </div>
        )}
        {message && (
          <div
            className={cn(
              "notification-message",
              multiline && "whitespace-pre-wrap",
            )}
          >
            {message}
          </div>
        )}
        {renderTimestamp()}
      </div>
    );
  };

  const renderAction = () => {
    if (!action) return null;

    return (
      <button
        type="button"
        className="ml-3 px-3 py-1 text-sm font-medium bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-colors"
        onClick={handleActionClick}
        data-testid="notification-action"
      >
        {action.label}
      </button>
    );
  };

  if (!isVisible && !isAnimating) return null;

  return (
    <div
      ref={containerRef}
      className={cn(
        "notification-container relative rounded-lg border max-w-sm transition-all duration-200",
        sizeClasses[size],
        themeClasses[theme],
        typeClasses[type],
        positionClasses[position],
        priorityClasses[priority],
        multiline && "multiline",
        rtl && "rtl",
        stackable && "stackable",
        queueable && "queueable",
        animate && "animate-enter",
        isAnimating && "animate-exit",
        !isVisible && "hidden",
        loading && "loading",
        className,
      )}
      tabIndex={autoFocus ? 0 : -1}
      draggable={draggable}
      aria-label={ariaLabel}
      aria-live={ariaLive}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      data-stack-index={stackIndex}
      data-max-queue={maxQueue}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onDragStart={onDrag}
      {...props}
    >
      {loading && (
        <div
          className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg"
          data-testid="notification-loading"
        >
          <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
        </div>
      )}

      <div className="flex items-start">
        {renderIcon()}
        {renderContent()}
        {renderAction()}
        {renderCloseButton()}
      </div>

      {renderProgress()}
    </div>
  );
};

export default Notification;
