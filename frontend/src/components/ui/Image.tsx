import React, { useState, useEffect, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface ImageProps {
  src: string;
  alt: string;
  className?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "full";
  width?: number | string;
  height?: number | string;
  objectFit?: "contain" | "cover" | "fill" | "none" | "scale-down";
  radius?: "none" | "sm" | "md" | "lg" | "full";
  shadow?: "none" | "sm" | "md" | "lg" | "xl";
  border?: {
    width?: number;
    color?: string;
  };
  loading?: "lazy" | "eager";
  lazy?: boolean;
  placeholder?: string;
  fallback?: string;
  blur?: boolean;
  grayscale?: boolean;
  sepia?: boolean;
  opacity?: number;
  hoverEffect?: "zoom" | "brightness" | "opacity" | "none";
  aspectRatio?: "1/1" | "4/3" | "16/9" | "3/2" | string;
  srcSet?: string;
  sizes?: string;
  draggable?: boolean;
  caption?: string;
  preview?: boolean;
  overlay?: React.ReactNode;
  showProgress?: boolean;
  zoomOnHover?: boolean;
  retina?: string;
  webp?: string;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  onLoad?: () => void;
  onError?: () => void;
  onClick?: (e: React.MouseEvent) => void;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const Image: React.FC<ImageProps> = ({
  src,
  alt,
  className,
  size = "md",
  width,
  height,
  objectFit = "cover",
  radius = "none",
  shadow = "none",
  border,
  loading = "lazy",
  lazy = false,
  placeholder,
  fallback,
  blur = false,
  grayscale = false,
  sepia = false,
  opacity,
  hoverEffect = "none",
  aspectRatio,
  srcSet,
  sizes,
  draggable = true,
  caption,
  preview = false,
  overlay,
  showProgress = false,
  zoomOnHover = false,
  retina,
  webp,
  loadingComponent,
  errorComponent,
  onLoad,
  onError,
  onClick,
  "data-testid": dataTestId = "image-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(() => {
    if (placeholder) return placeholder;
    return lazy ? "" : src;
  });
  const [loadProgress, setLoadProgress] = useState(0);
  const [isIntersecting, setIsIntersecting] = useState(!lazy);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    xs: "w-16 h-16",
    sm: "w-24 h-24",
    md: "w-32 h-32",
    lg: "w-48 h-48",
    xl: "w-64 h-64",
    full: "w-full h-full",
  };

  const radiusClasses = {
    none: "",
    sm: "rounded-sm",
    md: "rounded-md",
    lg: "rounded-lg",
    full: "rounded-full",
  };

  const shadowClasses = {
    none: "",
    sm: "shadow-sm",
    md: "shadow-md",
    lg: "shadow-lg",
    xl: "shadow-xl",
  };

  const aspectRatioClasses = {
    "1/1": "aspect-square",
    "4/3": "aspect-4/3",
    "16/9": "aspect-video",
    "3/2": "aspect-3/2",
  };

  const hoverEffectClasses = {
    zoom: "hover:scale-110 transition-transform duration-300",
    brightness: "hover:brightness-110 transition-all duration-300",
    opacity: "hover:opacity-80 transition-opacity duration-300",
    none: "",
  };

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!lazy || !containerRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsIntersecting(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 },
    );

    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, [lazy]);

  // Load actual image when in viewport (for lazy loading)
  useEffect(() => {
    if (isIntersecting && lazy) {
      if (placeholder && currentSrc === placeholder) {
        setCurrentSrc(src);
      } else if (!placeholder && currentSrc === "") {
        setCurrentSrc(src);
      }
    }
  }, [isIntersecting, lazy, placeholder, currentSrc, src]);

  // Load actual image after placeholder is shown (for non-lazy loading)
  useEffect(() => {
    if (!lazy && placeholder && currentSrc === placeholder) {
      const timer = setTimeout(() => {
        setCurrentSrc(src);
      }, 100); // Small delay to show placeholder briefly

      return () => clearTimeout(timer);
    }
  }, [lazy, placeholder, currentSrc, src]);

  const handleImageLoad = useCallback(() => {
    setIsLoading(false);
    setLoadProgress(100);
    if (onLoad) onLoad();
  }, [onLoad]);

  const handleImageError = useCallback(() => {
    setHasError(true);
    setIsLoading(false);
    if (fallback) {
      setCurrentSrc(fallback);
      setHasError(false);
    }
    if (onError) onError();
  }, [fallback, onError]);

  const handleImageProgress = useCallback((e: ProgressEvent) => {
    if (e.lengthComputable) {
      const progress = (e.loaded / e.total) * 100;
      setLoadProgress(progress);
    }
  }, []);

  const getBorderClasses = () => {
    if (!border) return "";
    const widthClass = `border-${border.width || 1}`;
    const colorClass = border.color
      ? `border-${border.color}-500`
      : "border-gray-300";
    return `${widthClass} ${colorClass}`;
  };

  const getImageSrcSet = () => {
    if (srcSet) return srcSet;
    if (retina) return `${src} 1x, ${retina} 2x`;
    return undefined;
  };

  const imageElement = (
    <img
      ref={imgRef}
      src={currentSrc}
      alt={alt}
      width={width}
      height={height}
      srcSet={getImageSrcSet()}
      sizes={sizes}
      loading={lazy ? "lazy" : loading}
      draggable={draggable}
      className={cn(
        "transition-all duration-300",
        `object-${objectFit}`,
        radiusClasses[radius],
        shadowClasses[shadow],
        getBorderClasses(),
        blur && isLoading && "blur-sm",
        grayscale && "grayscale",
        sepia && "sepia",
        hoverEffectClasses[hoverEffect],
        zoomOnHover && "hover:scale-110 transition-transform duration-300",
        preview && "cursor-pointer",
        !width && !height && sizeClasses[size],
      )}
      style={{
        ...(opacity !== undefined && { opacity }),
        ...(width && typeof width === "string" && { width }),
        ...(height && typeof height === "string" && { height }),
      }}
      onLoad={handleImageLoad}
      onError={handleImageError}
      onClick={onClick}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    />
  );

  const pictureElement = webp ? (
    <picture>
      <source srcSet={webp} type="image/webp" />
      {imageElement}
    </picture>
  ) : (
    imageElement
  );

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative inline-block",
        aspectRatio &&
          (aspectRatioClasses[aspectRatio as keyof typeof aspectRatioClasses] ||
            `aspect-[${aspectRatio}]`),
        className,
      )}
      data-testid={dataTestId}
    >
      {pictureElement}

      {/* Loading state */}
      {isLoading && !hasError && (
        <>
          {loadingComponent || (
            <div
              data-testid="image-loading"
              className="absolute inset-0 flex items-center justify-center bg-gray-200 animate-pulse"
            >
              <div className="w-8 h-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}

          {/* Progress bar */}
          {showProgress && (
            <div
              data-testid="image-progress"
              className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200"
            >
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${loadProgress}%` }}
              />
            </div>
          )}
        </>
      )}

      {/* Error state */}
      {hasError && !fallback && (
        <div data-testid="image-error">
          {errorComponent || (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500">
              <div className="text-center">
                <div className="text-2xl mb-2">⚠️</div>
                <div className="text-sm">Failed to load image</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Overlay content */}
      {overlay && (
        <div className="absolute inset-0 flex items-center justify-center">
          {overlay}
        </div>
      )}

      {/* Caption */}
      {caption && (
        <div className="mt-2 text-sm text-gray-600 text-center">{caption}</div>
      )}
    </div>
  );
};

export default Image;
