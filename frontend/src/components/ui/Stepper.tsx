import React from 'react';

interface Step {
  id: string;
  title: string;
  description?: string;
  icon?: React.ReactNode;
  status?: 'completed' | 'current' | 'pending' | 'error';
}

interface StepperProps {
  steps: Step[];
  currentStep?: string;
  orientation?: 'horizontal' | 'vertical';
  variant?: 'default' | 'compact' | 'numbered';
  onStepClick?: (stepId: string) => void;
  allowClickableSteps?: boolean;
  showStepNumbers?: boolean;
  className?: string;
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  orientation = 'horizontal',
  variant = 'default',
  onStepClick,
  allowClickableSteps = false,
  showStepNumbers = true,
  className = ''
}) => {
  const getStepStatus = (step: Step, index: number): 'completed' | 'current' | 'pending' | 'error' => {
    if (step.status) return step.status;
    
    if (!currentStep) {
      return index === 0 ? 'current' : 'pending';
    }
    
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    if (currentIndex === -1) return 'pending';
    
    if (index < currentIndex) return 'completed';
    if (index === currentIndex) return 'current';
    return 'pending';
  };

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          circle: 'bg-green-600 text-white border-green-600',
          title: 'text-green-600',
          description: 'text-gray-600'
        };
      case 'current':
        return {
          circle: 'bg-blue-600 text-white border-blue-600',
          title: 'text-blue-600 font-semibold',
          description: 'text-gray-700'
        };
      case 'error':
        return {
          circle: 'bg-red-600 text-white border-red-600',
          title: 'text-red-600',
          description: 'text-gray-600'
        };
      default: // pending
        return {
          circle: 'bg-gray-200 text-gray-500 border-gray-300',
          title: 'text-gray-500',
          description: 'text-gray-400'
        };
    }
  };

  const getConnectorStyles = (fromStatus: string, toStatus: string) => {
    if (fromStatus === 'completed') {
      return 'border-green-600';
    }
    if (fromStatus === 'current' && (toStatus === 'pending' || toStatus === 'error')) {
      return 'border-gray-300';
    }
    return 'border-gray-300';
  };

  const handleStepClick = (stepId: string) => {
    if (allowClickableSteps && onStepClick) {
      onStepClick(stepId);
    }
  };

  const renderStepIcon = (step: Step, status: string, index: number) => {
    if (step.icon) {
      return step.icon;
    }
    
    if (status === 'completed') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (status === 'error') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (showStepNumbers || variant === 'numbered') {
      return <span className="text-sm font-semibold">{index + 1}</span>;
    }
    
    return null;
  };

  if (orientation === 'vertical') {
    return (
      <div className={`flex flex-col ${className}`}>
        {steps.map((step, index) => {
          const status = getStepStatus(step, index);
          const styles = getStatusStyles(status);
          const isClickable = allowClickableSteps && onStepClick;
          const isLastStep = index === steps.length - 1;

          return (
            <div key={step.id} className="flex">
              <div className="flex flex-col items-center">
                <button
                  onClick={() => handleStepClick(step.id)}
                  disabled={!isClickable}
                  className={`
                    w-10 h-10 rounded-full border-2 flex items-center justify-center transition-colors
                    ${styles.circle}
                    ${isClickable ? 'cursor-pointer hover:shadow-md' : 'cursor-default'}
                    ${variant === 'compact' ? 'w-8 h-8' : ''}
                  `}
                  type="button"
                >
                  {renderStepIcon(step, status, index)}
                </button>
                
                {!isLastStep && (
                  <div 
                    className={`w-0.5 h-12 border-l-2 mt-2 ${getConnectorStyles(status, getStepStatus(steps[index + 1], index + 1))}`}
                  />
                )}
              </div>
              
              <div className={`ml-4 pb-8 ${variant === 'compact' ? 'pb-4' : ''}`}>
                <h3 className={`text-sm ${styles.title} ${variant === 'compact' ? 'text-xs' : ''}`}>
                  {step.title}
                </h3>
                {step.description && variant !== 'compact' && (
                  <p className={`text-xs mt-1 ${styles.description}`}>
                    {step.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Horizontal orientation
  return (
    <div className={`flex items-center ${className}`}>
      {steps.map((step, index) => {
        const status = getStepStatus(step, index);
        const styles = getStatusStyles(status);
        const isClickable = allowClickableSteps && onStepClick;
        const isLastStep = index === steps.length - 1;

        return (
          <React.Fragment key={step.id}>
            <div className="flex flex-col items-center">
              <button
                onClick={() => handleStepClick(step.id)}
                disabled={!isClickable}
                className={`
                  w-10 h-10 rounded-full border-2 flex items-center justify-center transition-colors mb-2
                  ${styles.circle}
                  ${isClickable ? 'cursor-pointer hover:shadow-md' : 'cursor-default'}
                  ${variant === 'compact' ? 'w-8 h-8 mb-1' : ''}
                `}
                type="button"
              >
                {renderStepIcon(step, status, index)}
              </button>
              
              <div className="text-center">
                <h3 className={`text-sm ${styles.title} ${variant === 'compact' ? 'text-xs' : ''}`}>
                  {step.title}
                </h3>
                {step.description && variant !== 'compact' && (
                  <p className={`text-xs mt-1 ${styles.description} max-w-24`}>
                    {step.description}
                  </p>
                )}
              </div>
            </div>
            
            {!isLastStep && (
              <div className={`flex-1 mx-4 mb-8 ${variant === 'compact' ? 'mb-4' : ''}`}>
                <div 
                  className={`h-0.5 border-t-2 ${getConnectorStyles(status, getStepStatus(steps[index + 1], index + 1))}`}
                />
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default Stepper;