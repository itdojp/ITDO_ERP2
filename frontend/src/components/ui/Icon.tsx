import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface IconProps {
  name?: string;
  svg?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | number;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | string;
  rotation?: number;
  spin?: boolean;
  pulse?: boolean;
  bounce?: boolean;
  iconSet?: 'heroicons' | 'lucide' | 'feather' | 'material';
  variant?: 'solid' | 'outline';
  strokeWidth?: number;
  gradient?: { from: string; to: string };
  shadow?: boolean;
  outline?: boolean;
  badge?: string | number;
  dot?: boolean;
  disabled?: boolean;
  loading?: boolean;
  interactive?: boolean;
  flip?: 'horizontal' | 'vertical' | 'both';
  viewBox?: string;
  title?: string;
  renderIcon?: (name: string) => React.ReactNode;
  children?: React.ReactNode;
  responsive?: {
    sm?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
    md?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
    lg?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  };
  theme?: 'light' | 'dark' | 'auto';
  animationDelay?: number;
  animationDuration?: number;
  className?: string;
  style?: React.CSSProperties;
  onClick?: (e: React.MouseEvent) => void;
  onMouseEnter?: (e: React.MouseEvent) => void;
  onMouseLeave?: (e: React.MouseEvent) => void;
  'aria-label'?: string;
  'data-testid'?: string;
  'data-category'?: string;
  'data-id'?: string;
}

// Basic icon SVG paths for common icons
const ICON_PATHS: Record<string, string> = {
  home: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z',
  bell: 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0',
  heart: 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z',
  loading: 'M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83',
  arrow: 'M5 12h14m-7-7l7 7-7 7',
  plus: 'M12 5v14m-7-7h14',
  minus: 'M5 12h14',
  check: 'M20 6L9 17l-5-5',
  close: 'M18 6L6 18M6 6l12 12',
  search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  star: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
  user: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z',
  mail: 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6',
  phone: 'M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z'
};

export const Icon: React.FC<IconProps> = ({
  name,
  svg,
  size = 'md',
  color,
  rotation,
  spin = false,
  pulse = false,
  bounce = false,
  iconSet = 'heroicons',
  variant = 'outline',
  strokeWidth = 2,
  gradient,
  shadow = false,
  outline = false,
  badge,
  dot = false,
  disabled = false,
  loading = false,
  interactive = false,
  flip,
  viewBox = '0 0 24 24',
  title,
  renderIcon,
  children,
  responsive,
  theme = 'auto',
  animationDelay,
  animationDuration,
  className,
  style,
  onClick,
  onMouseEnter,
  onMouseLeave,
  'aria-label': ariaLabel,
  'data-testid': dataTestId = 'icon',
  'data-category': dataCategory,
  'data-id': dataId,
  ...props
}) => {
  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8',
    '2xl': 'w-10 h-10'
  };

  const colorClasses = {
    primary: 'text-blue-600',
    secondary: 'text-gray-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
    info: 'text-blue-500'
  };

  const responsiveClasses = useMemo(() => {
    if (!responsive) return '';
    
    let classes = '';
    if (responsive.sm) classes += ` sm:${sizeClasses[responsive.sm]}`;
    if (responsive.md) classes += ` md:${sizeClasses[responsive.md]}`;
    if (responsive.lg) classes += ` lg:${sizeClasses[responsive.lg]}`;
    
    return classes;
  }, [responsive]);

  const getIconPath = (iconName?: string): string => {
    if (svg) return svg;
    if (!iconName) return ICON_PATHS.home;
    return ICON_PATHS[iconName] || ICON_PATHS.home;
  };

  const getTransform = (): string => {
    const transforms: string[] = [];
    
    if (rotation) {
      transforms.push(`rotate(${rotation}deg)`);
    }
    
    if (flip === 'horizontal') {
      transforms.push('scaleX(-1)');
    } else if (flip === 'vertical') {
      transforms.push('scaleY(-1)');
    } else if (flip === 'both') {
      transforms.push('scaleX(-1) scaleY(-1)');
    }
    
    return transforms.join(' ');
  };

  const iconStyle: React.CSSProperties = {
    ...style,
    ...(typeof color === 'string' && !colorClasses[color as keyof typeof colorClasses] && { color }),
    ...(getTransform() && { transform: getTransform() }),
    ...(animationDelay && { animationDelay: `${animationDelay}ms` }),
    ...(animationDuration && { animationDuration: `${animationDuration}ms` }),
    ...(typeof size === 'number' && { width: size, height: size })
  };

  const gradientId = useMemo(() => 
    gradient ? `gradient-${Math.random().toString(36).substr(2, 9)}` : undefined,
    [gradient]
  );

  if (loading) {
    return (
      <div
        data-testid="loading-icon"
        className={cn(
          typeof size === 'string' ? sizeClasses[size] : '',
          'animate-spin',
          className
        )}
        style={iconStyle}
      >
        <svg
          viewBox={viewBox}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="w-full h-full"
        >
          <path d={ICON_PATHS.loading} />
        </svg>
      </div>
    );
  }

  if (renderIcon && name) {
    return <>{renderIcon(name)}</>;
  }

  const iconElement = (
    <div
      className={cn(
        'relative inline-flex items-center justify-center',
        typeof size === 'string' ? sizeClasses[size] : '',
        typeof color === 'string' && colorClasses[color as keyof typeof colorClasses] ? colorClasses[color as keyof typeof colorClasses] : '',
        spin && 'animate-spin',
        pulse && 'animate-pulse',
        bounce && 'animate-bounce',
        shadow && 'drop-shadow-md',
        disabled && 'opacity-50 cursor-not-allowed',
        interactive && 'hover:scale-110 transition-transform cursor-pointer',
        responsiveClasses,
        className
      )}
      style={iconStyle}
      onClick={!disabled ? onClick : undefined}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      aria-label={ariaLabel}
      {...props}
    >
      <svg
        viewBox={viewBox}
        fill={variant === 'solid' ? 'currentColor' : 'none'}
        stroke={variant === 'outline' || outline ? 'currentColor' : 'none'}
        strokeWidth={strokeWidth}
        className={cn(
          'w-full h-full',
          outline && 'stroke-current'
        )}
        title={title}
      >
        {gradient && (
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={gradient.from} />
              <stop offset="100%" stopColor={gradient.to} />
            </linearGradient>
          </defs>
        )}
        <path
          d={getIconPath(name)}
          fill={gradient ? `url(#${gradientId})` : undefined}
        />
      </svg>
      
      {badge && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
          {badge}
        </span>
      )}
      
      {dot && (
        <span className="icon-dot absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
      )}
      
      {children}
    </div>
  );

  return iconElement;
};

export default Icon;