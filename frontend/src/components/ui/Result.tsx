import React, { useState } from 'react';

interface ResultProps {
  status?: 'success' | 'error' | 'info' | 'warning' | '404' | '403' | '500';
  title?: React.ReactNode;
  subTitle?: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode | false;
  iconSize?: 'small' | 'medium' | 'large';
  iconColor?: string;
  action?: React.ReactNode;
  actions?: React.ReactNode[];
  extra?: React.ReactNode;
  footer?: React.ReactNode;
  children?: React.ReactNode;
  size?: 'small' | 'medium' | 'large';
  layout?: 'vertical' | 'horizontal';
  color?: string;
  background?: boolean;
  bordered?: boolean;
  centered?: boolean;
  inline?: boolean;
  overlay?: boolean;
  animated?: boolean;
  responsive?: boolean;
  collapsible?: boolean;
  loading?: boolean;
  progress?: number;
  timestamp?: Date;
  helpText?: string;
  showDetails?: boolean;
  onRetry?: () => void;
  className?: string;
  style?: React.CSSProperties;
  [key: string]: any;
}

const Result: React.FC<ResultProps> = ({
  status = 'success',
  title,
  subTitle,
  description,
  icon,
  iconSize = 'medium',
  iconColor,
  action,
  actions,
  extra,
  footer,
  children,
  size = 'medium',
  layout = 'vertical',
  color,
  background = false,
  bordered = false,
  centered = false,
  inline = false,
  overlay = false,
  animated = false,
  responsive = false,
  collapsible = false,
  loading = false,
  progress,
  timestamp,
  helpText,
  showDetails = false,
  onRetry,
  className = '',
  style,
  ...props
}) => {
  const [isCollapsed, setIsCollapsed] = useState(collapsible);

  const getDefaultContent = () => {
    const contentMap = {
      success: { title: 'Success', subTitle: 'Your operation completed successfully.' },
      error: { title: 'Error', subTitle: 'Something went wrong. Please try again.' },
      info: { title: 'Information', subTitle: 'Here is some important information.' },
      warning: { title: 'Warning', subTitle: 'Please check the following warnings.' },
      '404': { title: '404', subTitle: 'Sorry, the page you visited does not exist.' },
      '403': { title: '403', subTitle: 'Sorry, you are not authorized to access this page.' },
      '500': { title: '500', subTitle: 'Sorry, something went wrong.' }
    };
    return contentMap[status];
  };

  const getSizeClasses = () => {
    const sizeMap = {
      small: {
        container: 'p-4',
        icon: 'w-8 h-8',
        title: 'text-lg',
        subtitle: 'text-sm'
      },
      medium: {
        container: 'p-6',
        icon: 'w-12 h-12',
        title: 'text-xl',
        subtitle: 'text-base'
      },
      large: {
        container: 'p-8',
        icon: 'w-16 h-16',
        title: 'text-2xl',
        subtitle: 'text-lg'
      }
    };
    return sizeMap[size];
  };

  const getIconSizeClasses = () => {
    const iconSizeMap = {
      small: 'w-8 h-8',
      medium: 'w-12 h-12',
      large: 'w-16 h-16'
    };
    return iconSizeMap[iconSize];
  };

  const getStatusColor = () => {
    const colorMap = {
      success: 'text-green-500',
      error: 'text-red-500',
      info: 'text-blue-500',
      warning: 'text-yellow-500',
      '404': 'text-gray-500',
      '403': 'text-red-500',
      '500': 'text-red-500'
    };
    return iconColor ? { color: iconColor } : colorMap[status];
  };

  const renderIcon = () => {
    if (icon === false) return null;
    if (loading) {
      return (
        <svg
          className={`${getIconSizeClasses()} text-blue-500 animate-spin`}
          fill="none"
          viewBox="0 0 24 24"
          role="img"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      );
    }

    if (icon) return icon;

    const iconClasses = `${getIconSizeClasses()} ${typeof getStatusColor() === 'string' ? getStatusColor() : ''}`;
    const iconStyle = typeof getStatusColor() === 'object' ? getStatusColor() : {};

    switch (status) {
      case 'success':
        return (
          <svg className={iconClasses} style={iconStyle} fill="currentColor" viewBox="0 0 20 20" role="img" aria-hidden="true">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
      case '403':
      case '500':
        return (
          <svg className={iconClasses} style={iconStyle} fill="currentColor" viewBox="0 0 20 20" role="img" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={iconClasses} style={iconStyle} fill="currentColor" viewBox="0 0 20 20" role="img" aria-hidden="true">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className={iconClasses} style={iconStyle} fill="currentColor" viewBox="0 0 20 20" role="img" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case '404':
        return (
          <svg className={iconClasses} style={iconStyle} fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const renderProgress = () => {
    if (typeof progress !== 'number') return null;

    return (
      <div className="mt-4 w-full max-w-md">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>
    );
  };

  const renderActions = () => {
    const allActions = [];
    
    if (status === 'error' && onRetry) {
      allActions.push(
        <button
          key="retry"
          onClick={onRetry}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      );
    }
    
    if (action) allActions.push(action);
    if (actions) allActions.push(...actions);

    if (allActions.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-3 justify-center mt-6">
        {allActions.map((actionItem, index) => (
          <React.Fragment key={index}>{actionItem}</React.Fragment>
        ))}
      </div>
    );
  };

  const renderTimestamp = () => {
    if (!timestamp) return null;
    
    return (
      <div className="text-xs text-gray-500 mt-2">
        {timestamp.toLocaleString()}
      </div>
    );
  };

  const renderContent = () => {
    const sizeClasses = getSizeClasses();
    const defaultContent = getDefaultContent();
    const displayTitle = title || defaultContent.title;
    const displaySubTitle = subTitle || (showDetails ? defaultContent.subTitle : subTitle);

    return (
      <div className={layout === 'horizontal' ? 'ml-4' : 'mt-4'}>
        {displayTitle && (
          <div className={`${sizeClasses.title} font-semibold text-gray-900 mb-2`}>
            {displayTitle}
          </div>
        )}
        
        {displaySubTitle && (
          <div className={`${sizeClasses.subtitle} text-gray-600 mb-4`}>
            {displaySubTitle}
          </div>
        )}
        
        {description && (
          <div className="text-gray-600 mb-4">
            {description}
          </div>
        )}
        
        {renderProgress()}
        {renderTimestamp()}
        {renderActions()}
        
        {extra && (
          <div className="mt-6">
            {extra}
          </div>
        )}
        
        {helpText && (
          <div className="text-sm text-gray-500 mt-4">
            {helpText}
          </div>
        )}
      </div>
    );
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const containerClasses = [
    'result-component',
    layout === 'horizontal' ? 'flex items-start' : 'flex flex-col items-center text-center',
    centered ? 'justify-center' : '',
    inline ? 'inline-flex' : '',
    getSizeClasses().container,
    background ? 'bg-gray-50' : '',
    bordered ? 'border border-gray-200 rounded-lg' : '',
    animated ? 'transition-all duration-300' : '',
    responsive ? 'responsive-result' : '',
    overlay ? 'absolute inset-0 z-10 bg-white bg-opacity-90' : '',
    className
  ].filter(Boolean).join(' ');

  const contentStyle: React.CSSProperties = {
    ...style,
    ...(color && { color })
  };

  return (
    <div
      className={containerClasses}
      style={contentStyle}
      data-testid="result-container"
      {...props}
    >
      {layout === 'vertical' && renderIcon()}
      
      <div className={layout === 'horizontal' ? 'flex items-start' : ''}>
        {layout === 'horizontal' && renderIcon()}
        {renderContent()}
      </div>
      
      {collapsible && (
        <button
          onClick={toggleCollapse}
          className="mt-4 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          {isCollapsed ? 'Show Details' : 'Hide Details'}
        </button>
      )}
      
      {!isCollapsed && children && (
        <div className="mt-6 w-full">
          {children}
        </div>
      )}
      
      {footer && (
        <div className="mt-8 w-full">
          {footer}
        </div>
      )}
    </div>
  );
};

export { Result };
export default Result;