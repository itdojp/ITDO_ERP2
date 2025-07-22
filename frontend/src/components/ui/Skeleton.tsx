import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular';
  animation?: 'pulse' | 'wave' | 'none';
  lines?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  className = '',
  variant = 'text',
  animation = 'pulse',
  lines = 1,
}) => {
  // バリアントごとのスタイル
  const variantStyles = {
    text: 'rounded',
    rectangular: 'rounded-md',
    circular: 'rounded-full',
  };

  // アニメーションのスタイル
  const animationStyles = {
    pulse: 'animate-pulse',
    wave: 'animate-wave',
    none: '',
  };

  const getDefaultSize = () => {
    switch (variant) {
      case 'text':
        return { width: '100%', height: '1rem' };
      case 'rectangular':
        return { width: '100%', height: '4rem' };
      case 'circular':
        return { width: '2.5rem', height: '2.5rem' };
      default:
        return { width: '100%', height: '1rem' };
    }
  };

  const defaultSize = getDefaultSize();
  const finalWidth = width || defaultSize.width;
  const finalHeight = height || defaultSize.height;

  const skeletonClasses = `
    bg-gray-200
    ${variantStyles[variant]}
    ${animationStyles[animation]}
    ${className}
  `;

  const skeletonStyle = {
    width: typeof finalWidth === 'number' ? `${finalWidth}px` : finalWidth,
    height: typeof finalHeight === 'number' ? `${finalHeight}px` : finalHeight,
  };

  // 複数行のテキストスケルトン
  if (variant === 'text' && lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }, (_, index) => (
          <div
            key={index}
            className={skeletonClasses}
            style={{
              ...skeletonStyle,
              width: index === lines - 1 && lines > 1 ? '75%' : skeletonStyle.width,
            }}
          />
        ))}
      </div>
    );
  }

  return <div className={skeletonClasses} style={skeletonStyle} />;
};

// プリセットされたスケルトンコンポーネント
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`space-y-4 ${className}`}>
    <Skeleton variant="rectangular" height="12rem" />
    <div className="space-y-2">
      <Skeleton variant="text" width="60%" height="1.5rem" />
      <Skeleton variant="text" lines={2} />
    </div>
  </div>
);

export const SkeletonList: React.FC<{ 
  items?: number; 
  showAvatar?: boolean;
  className?: string;
}> = ({ items = 3, showAvatar = false, className = '' }) => (
  <div className={`space-y-4 ${className}`}>
    {Array.from({ length: items }, (_, index) => (
      <div key={index} className="flex items-start space-x-3">
        {showAvatar && <Skeleton variant="circular" width="2.5rem" height="2.5rem" />}
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="40%" height="1.25rem" />
          <Skeleton variant="text" lines={2} />
        </div>
      </div>
    ))}
  </div>
);

export const SkeletonTable: React.FC<{ 
  rows?: number;
  columns?: number;
  className?: string;
}> = ({ rows = 5, columns = 4, className = '' }) => (
  <div className={`space-y-3 ${className}`}>
    {/* ヘッダー */}
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {Array.from({ length: columns }, (_, index) => (
        <Skeleton key={index} variant="text" width="80%" height="1.25rem" />
      ))}
    </div>
    
    {/* 行 */}
    {Array.from({ length: rows }, (_, rowIndex) => (
      <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }, (_, colIndex) => (
          <Skeleton key={colIndex} variant="text" />
        ))}
      </div>
    ))}
  </div>
);