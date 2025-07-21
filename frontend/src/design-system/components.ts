import { designTokens } from './tokens'

export const componentStyles = {
  button: {
    base: [
      'inline-flex items-center justify-center',
      'font-medium rounded-md transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'gap-2'
    ].join(' '),
    
    variants: {
      default: [
        'bg-white text-gray-900 border border-gray-300',
        'hover:bg-gray-50 focus:ring-blue-500'
      ].join(' '),
      
      primary: [
        'bg-blue-600 text-white border border-transparent',
        'hover:bg-blue-700 focus:ring-blue-500'
      ].join(' '),
      
      secondary: [
        'bg-gray-600 text-white border border-transparent',
        'hover:bg-gray-700 focus:ring-gray-500'
      ].join(' '),
      
      outline: [
        'bg-transparent text-blue-600 border border-blue-600',
        'hover:bg-blue-50 focus:ring-blue-500'
      ].join(' '),
      
      ghost: [
        'bg-transparent text-gray-700 border border-transparent',
        'hover:bg-gray-100 focus:ring-gray-500'
      ].join(' '),
      
      destructive: [
        'bg-red-600 text-white border border-transparent',
        'hover:bg-red-700 focus:ring-red-500'
      ].join(' '),
      
      danger: [
        'bg-red-600 text-white border border-transparent',
        'hover:bg-red-700 focus:ring-red-500'
      ].join(' ')
    },
    
    sizes: {
      xs: 'px-2 py-1 text-xs',
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
      xl: 'px-8 py-4 text-lg'
    }
  },

  input: {
    base: [
      'block w-full border border-gray-300 rounded-md',
      'px-3 py-2 text-sm placeholder-gray-400',
      'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
      'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
      'transition-colors duration-200'
    ].join(' '),
    
    states: {
      error: 'border-red-500 focus:ring-red-500',
      success: 'border-green-500 focus:ring-green-500',
      disabled: 'bg-gray-50 border-gray-200 text-gray-500'
    }
  },

  card: {
    base: [
      'bg-white rounded-lg border border-gray-200',
      'shadow-sm overflow-hidden'
    ].join(' '),
    
    variants: {
      default: 'shadow-sm',
      elevated: 'shadow-md',
      flat: 'shadow-none border-0 bg-gray-50'
    },
    
    header: [
      'px-6 py-4 border-b border-gray-200',
      'bg-gray-50/50'
    ].join(' '),
    
    body: 'px-6 py-4',
    
    footer: [
      'px-6 py-4 border-t border-gray-200',
      'bg-gray-50/50 flex justify-end gap-3'
    ].join(' ')
  },

  modal: {
    overlay: [
      'fixed inset-0 z-50 flex items-center justify-center p-4',
      'bg-black/50 backdrop-blur-sm transition-all duration-300'
    ].join(' '),
    
    content: [
      'relative w-full bg-white rounded-lg shadow-xl',
      'transform transition-all duration-300 max-h-[90vh] overflow-hidden'
    ].join(' '),
    
    sizes: {
      xs: 'max-w-xs',
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-xl',
      full: 'max-w-full mx-4'
    }
  },

  badge: {
    base: [
      'inline-flex items-center px-2.5 py-0.5 rounded-full',
      'text-xs font-medium'
    ].join(' '),
    
    variants: {
      default: 'bg-gray-100 text-gray-800',
      primary: 'bg-blue-100 text-blue-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      secondary: 'bg-gray-100 text-gray-800'
    }
  },

  alert: {
    base: [
      'p-4 rounded-md border-l-4'
    ].join(' '),
    
    variants: {
      info: 'bg-blue-50 border-blue-400 text-blue-700',
      success: 'bg-green-50 border-green-400 text-green-700',
      warning: 'bg-yellow-50 border-yellow-400 text-yellow-700',
      error: 'bg-red-50 border-red-400 text-red-700'
    }
  },

  grid: {
    base: 'grid gap-4',
    
    responsive: {
      1: 'grid-cols-1',
      2: 'grid-cols-1 md:grid-cols-2',
      3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
      4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
      5: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5',
      6: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6'
    }
  },

  stack: {
    base: 'flex',
    
    directions: {
      row: 'flex-row',
      column: 'flex-col',
      'row-reverse': 'flex-row-reverse',
      'column-reverse': 'flex-col-reverse'
    },
    
    align: {
      start: 'items-start',
      center: 'items-center',
      end: 'items-end',
      stretch: 'items-stretch',
      baseline: 'items-baseline'
    },
    
    justify: {
      start: 'justify-start',
      center: 'justify-center',
      end: 'justify-end',
      between: 'justify-between',
      around: 'justify-around',
      evenly: 'justify-evenly'
    },
    
    spacing: {
      1: 'gap-1',
      2: 'gap-2',
      3: 'gap-3',
      4: 'gap-4',
      5: 'gap-5',
      6: 'gap-6',
      8: 'gap-8'
    }
  }
} as const

export type ComponentVariants = typeof componentStyles
export type ButtonVariant = keyof typeof componentStyles.button.variants
export type ButtonSize = keyof typeof componentStyles.button.sizes
export type CardVariant = keyof typeof componentStyles.card.variants
export type BadgeVariant = keyof typeof componentStyles.badge.variants
export type AlertVariant = keyof typeof componentStyles.alert.variants