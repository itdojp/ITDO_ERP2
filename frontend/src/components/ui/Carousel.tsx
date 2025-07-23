import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';

export interface CarouselItem {
  id: string;
  content: React.ReactNode;
}

export interface CarouselImage {
  id: string;
  src: string;
  alt: string;
  caption?: string;
}

export interface ResponsiveConfig {
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
}

export interface CarouselProps {
  items?: CarouselItem[];
  images?: CarouselImage[];
  defaultIndex?: number;
  variant?: 'default' | 'card' | 'fade';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  theme?: 'light' | 'dark';
  orientation?: 'horizontal' | 'vertical';
  transition?: 'slide' | 'fade' | 'none';
  itemsPerView?: number;
  responsive?: ResponsiveConfig;
  spacing?: 'none' | 'small' | 'medium' | 'large';
  autoplay?: boolean;
  autoplayInterval?: number;
  pauseOnHover?: boolean;
  infinite?: boolean;
  centered?: boolean;
  showArrows?: boolean;
  showDots?: boolean;
  showThumbnails?: boolean;
  showProgress?: boolean;
  showCounter?: boolean;
  swipeable?: boolean;
  draggable?: boolean;
  keyboardNavigation?: boolean;
  zoomable?: boolean;
  lazyLoad?: boolean;
  autoHeight?: boolean;
  adaptiveHeight?: boolean;
  variableWidth?: boolean;
  focusOnSelect?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  slideDuration?: number;
  slidePadding?: string;
  prevArrow?: React.ReactNode;
  nextArrow?: React.ReactNode;
  renderDot?: (props: { active: boolean; onClick: () => void; index: number }) => React.ReactNode;
  counterFormat?: (current: number, total: number) => string;
  onSlideChange?: (index: number, item: CarouselItem | CarouselImage) => void;
  onAutoplayStart?: () => void;
  onAutoplayStop?: () => void;
  className?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

export const Carousel: React.FC<CarouselProps> = ({
  items = [],
  images = [],
  defaultIndex = 0,
  variant = 'default',
  size = 'md',
  theme = 'light',
  orientation = 'horizontal',
  transition = 'slide',
  itemsPerView = 1,
  responsive,
  spacing = 'medium',
  autoplay = false,
  autoplayInterval = 3000,
  pauseOnHover = true,
  infinite = false,
  centered = false,
  showArrows = false,
  showDots = false,
  showThumbnails = false,
  showProgress = false,
  showCounter = false,
  swipeable = false,
  draggable = false,
  keyboardNavigation = false,
  zoomable = false,
  lazyLoad = false,
  autoHeight = false,
  adaptiveHeight = false,
  variableWidth = false,
  focusOnSelect = false,
  loading = false,
  loadingComponent,
  slideDuration = 300,
  slidePadding,
  prevArrow,
  nextArrow,
  renderDot,
  counterFormat = (current, total) => `${current} / ${total}`,
  onSlideChange,
  onAutoplayStart,
  onAutoplayStop,
  className,
  'data-testid': dataTestId = 'carousel-container',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const [currentIndex, setCurrentIndex] = useState(defaultIndex);
  const [isZoomed, setIsZoomed] = useState(false);
  const [zoomedIndex, setZoomedIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(0);
  const [isAutoplayPaused, setIsAutoplayPaused] = useState(false);
  
  const carouselRef = useRef<HTMLDivElement>(null);
  const autoplayRef = useRef<NodeJS.Timeout>();
  const touchStartRef = useRef(0);

  const allItems = images.length > 0 ? images : items;
  const totalItems = allItems.length;

  const sizeClasses = {
    sm: 'h-48',
    md: 'h-64',
    lg: 'h-80',
    xl: 'h-96'
  };

  const variantClasses = {
    default: 'rounded-lg',
    card: 'rounded-xl shadow-lg',
    fade: 'rounded-lg'
  };

  const themeClasses = {
    light: 'bg-white border-gray-200',
    dark: 'bg-gray-900 border-gray-700'
  };

  const spacingClasses = {
    none: 'gap-0',
    small: 'gap-2',
    medium: 'gap-4',
    large: 'gap-6'
  };

  const transitionClasses = {
    slide: 'slide-transition',
    fade: 'fade-transition',
    none: 'no-transition'
  };

  // Auto-play functionality
  useEffect(() => {
    if (!autoplay || totalItems <= 1 || isAutoplayPaused) return;

    const startAutoplay = () => {
      autoplayRef.current = setInterval(() => {
        setCurrentIndex(prev => {
          const nextIndex = infinite ? (prev + 1) % totalItems : Math.min(prev + 1, totalItems - 1);
          return nextIndex;
        });
      }, autoplayInterval);
      onAutoplayStart?.();
    };

    startAutoplay();

    return () => {
      if (autoplayRef.current) {
        clearInterval(autoplayRef.current);
        onAutoplayStop?.();
      }
    };
  }, [autoplay, autoplayInterval, totalItems, infinite, isAutoplayPaused, onAutoplayStart, onAutoplayStop]);

  // Handle slide change
  useEffect(() => {
    if (onSlideChange && allItems[currentIndex]) {
      onSlideChange(currentIndex, allItems[currentIndex]);
    }
  }, [currentIndex, allItems, onSlideChange]);

  const goToSlide = useCallback((index: number) => {
    if (infinite) {
      setCurrentIndex(index < 0 ? totalItems - 1 : index % totalItems);
    } else {
      setCurrentIndex(Math.max(0, Math.min(index, totalItems - 1)));
    }
  }, [infinite, totalItems]);

  const nextSlide = useCallback(() => {
    goToSlide(currentIndex + 1);
  }, [currentIndex, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(currentIndex - 1);
  }, [currentIndex, goToSlide]);

  // Keyboard navigation
  useEffect(() => {
    if (!keyboardNavigation) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          if (orientation === 'horizontal') prevSlide();
          break;
        case 'ArrowRight':
          event.preventDefault();
          if (orientation === 'horizontal') nextSlide();
          break;
        case 'ArrowUp':
          event.preventDefault();
          if (orientation === 'vertical') prevSlide();
          break;
        case 'ArrowDown':
          event.preventDefault();
          if (orientation === 'vertical') nextSlide();
          break;
        case 'Escape':
          if (isZoomed) setIsZoomed(false);
          break;
      }
    };

    if (carouselRef.current) {
      carouselRef.current.addEventListener('keydown', handleKeyDown);
      return () => carouselRef.current?.removeEventListener('keydown', handleKeyDown);
    }
  }, [keyboardNavigation, orientation, prevSlide, nextSlide, isZoomed]);

  // Touch/Swipe handling
  const handleTouchStart = (e: React.TouchEvent) => {
    if (!swipeable) return;
    touchStartRef.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!swipeable) return;
    e.preventDefault();
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!swipeable || !e.changedTouches || e.changedTouches.length === 0) return;
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStartRef.current - touchEnd;
    
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }
  };

  // Mouse drag handling
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!draggable) return;
    setIsDragging(true);
    setDragStart(e.clientX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggable || !isDragging) return;
    e.preventDefault();
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (!draggable || !isDragging) return;
    setIsDragging(false);
    const diff = dragStart - e.clientX;
    
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }
  };

  // Hover pause functionality
  const handleMouseEnter = () => {
    if (pauseOnHover && autoplay) {
      setIsAutoplayPaused(true);
    }
  };

  const handleMouseLeave = () => {
    if (pauseOnHover && autoplay) {
      setIsAutoplayPaused(false);
    }
  };

  const handleZoom = (index: number) => {
    if (!zoomable) return;
    setZoomedIndex(index);
    setIsZoomed(true);
  };

  const renderSlide = (item: CarouselItem | CarouselImage, index: number) => {
    if (images.length > 0) {
      const image = item as CarouselImage;
      return (
        <div key={image.id} className="relative">
          <img
            src={image.src}
            alt={image.alt}
            loading={lazyLoad ? 'lazy' : 'eager'}
            className={cn(
              'w-full h-full object-cover',
              zoomable && 'cursor-zoom-in'
            )}
            onClick={() => handleZoom(index)}
          />
          {image.caption && (
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-4">
              {image.caption}
            </div>
          )}
        </div>
      );
    } else {
      const carouselItem = item as CarouselItem;
      return (
        <div key={carouselItem.id} className="w-full h-full">
          {carouselItem.content}
        </div>
      );
    }
  };

  const renderThumbnails = () => {
    if (!showThumbnails || images.length === 0) return null;

    return (
      <div data-testid="carousel-thumbnails" className="flex justify-center mt-4 space-x-2">
        {images.map((image, index) => (
          <button
            key={image.id}
            data-testid={`thumbnail-${index}`}
            onClick={() => goToSlide(index)}
            className={cn(
              'w-16 h-16 rounded-md overflow-hidden border-2 transition-colors',
              index === currentIndex
                ? 'border-blue-500'
                : 'border-gray-300 hover:border-gray-400'
            )}
          >
            <img
              src={image.src}
              alt={image.alt}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>
    );
  };

  const renderDots = () => {
    if (!showDots) return null;

    return (
      <div className="flex justify-center mt-4 space-x-2">
        {allItems.map((_, index) => {
          if (renderDot) {
            return (
              <div key={index}>
                {renderDot({
                  active: index === currentIndex,
                  onClick: () => goToSlide(index),
                  index
                })}
              </div>
            );
          }

          return (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={cn(
                'w-3 h-3 rounded-full transition-colors',
                index === currentIndex
                  ? 'bg-blue-500'
                  : 'bg-gray-300 hover:bg-gray-400'
              )}
            />
          );
        })}
      </div>
    );
  };

  const renderArrows = () => {
    if (!showArrows) return null;

    return (
      <>
        <button
          data-testid="carousel-prev"
          onClick={prevSlide}
          disabled={!infinite && currentIndex === 0}
          className={cn(
            'absolute left-4 top-1/2 -translate-y-1/2 z-10',
            'bg-white bg-opacity-80 hover:bg-opacity-100 rounded-full p-2',
            'text-gray-800 hover:text-black transition-all',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {prevArrow || <span>‹</span>}
        </button>
        <button
          data-testid="carousel-next"
          onClick={nextSlide}
          disabled={!infinite && currentIndex === totalItems - 1}
          className={cn(
            'absolute right-4 top-1/2 -translate-y-1/2 z-10',
            'bg-white bg-opacity-80 hover:bg-opacity-100 rounded-full p-2',
            'text-gray-800 hover:text-black transition-all',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {nextArrow || <span>›</span>}
        </button>
      </>
    );
  };

  const renderProgress = () => {
    if (!showProgress) return null;

    const progress = ((currentIndex + 1) / totalItems) * 100;

    return (
      <div data-testid="carousel-progress" className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  };

  const renderCounter = () => {
    if (!showCounter) return null;

    return (
      <div className="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
        {counterFormat(currentIndex + 1, totalItems)}
      </div>
    );
  };

  const renderZoomOverlay = () => {
    if (!isZoomed || images.length === 0) return null;

    const zoomedImage = images[zoomedIndex];

    return (
      <div
        data-testid="carousel-zoom-overlay"
        className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center"
        onClick={() => setIsZoomed(false)}
        onKeyDown={(e) => e.key === 'Escape' && setIsZoomed(false)}
        tabIndex={0}
      >
        <button
          onClick={() => setIsZoomed(false)}
          className="absolute top-4 right-4 text-white text-2xl hover:text-gray-300"
        >
          ×
        </button>
        <img
          src={zoomedImage.src}
          alt={zoomedImage.alt}
          className="max-w-full max-h-full object-contain"
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div
        data-testid="carousel-loading"
        className={cn(
          'flex items-center justify-center',
          sizeClasses[size],
          variantClasses[variant],
          themeClasses[theme],
          className
        )}
      >
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  if (totalItems === 0) {
    return (
      <div
        data-testid={dataTestId}
        className={cn(
          'flex items-center justify-center text-gray-500',
          sizeClasses[size],
          variantClasses[variant],
          themeClasses[theme],
          className
        )}
      >
        No items to display
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={carouselRef}
        className={cn(
          'relative overflow-hidden',
          sizeClasses[size],
          variantClasses[variant],
          themeClasses[theme],
          `theme-${theme}`,
          orientation === 'vertical' && 'vertical-carousel',
          responsive && 'responsive-carousel',
          `spacing-${spacing}`,
          transitionClasses[transition],
          centered && 'centered-mode',
          autoHeight && 'auto-height',
          adaptiveHeight && 'adaptive-height',
          variableWidth && 'variable-width',
          className
        )}
        style={{
          '--slide-duration': `${slideDuration}ms`,
          '--slide-padding': slidePadding,
        } as React.CSSProperties}
        data-testid={dataTestId}
        data-category={dataCategory}
        data-id={dataId}
        tabIndex={focusOnSelect ? 0 : undefined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        {...props}
      >
        {/* Slides */}
        <div
          className={cn(
            'flex transition-transform duration-300',
            orientation === 'vertical' ? 'flex-col' : 'flex-row'
          )}
          style={{
            transform: orientation === 'vertical'
              ? `translateY(-${currentIndex * 100}%)`
              : `translateX(-${currentIndex * 100}%)`
          }}
        >
          {allItems.map((item, index) => (
            <div
              key={item.id}
              className={cn(
                'flex-shrink-0',
                orientation === 'vertical' ? 'w-full h-full' : 'w-full h-full'
              )}
            >
              {renderSlide(item, index)}
            </div>
          ))}
        </div>

        {/* Navigation arrows */}
        {renderArrows()}

        {/* Counter */}
        {renderCounter()}
      </div>

      {/* Dots navigation */}
      {renderDots()}

      {/* Thumbnails */}
      {renderThumbnails()}

      {/* Progress indicator */}
      {renderProgress()}

      {/* Zoom overlay */}
      {renderZoomOverlay()}
    </div>
  );
};

export default Carousel;