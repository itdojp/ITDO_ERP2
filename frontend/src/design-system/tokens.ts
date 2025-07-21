export const designTokens = {
  colors: {
    primary: {
      50: 'rgb(239 246 255)', // blue-50
      100: 'rgb(219 234 254)', // blue-100
      200: 'rgb(191 219 254)', // blue-200
      300: 'rgb(147 197 253)', // blue-300
      400: 'rgb(96 165 250)', // blue-400
      500: 'rgb(59 130 246)', // blue-500 - primary
      600: 'rgb(37 99 235)', // blue-600
      700: 'rgb(29 78 216)', // blue-700
      800: 'rgb(30 64 175)', // blue-800
      900: 'rgb(30 58 138)', // blue-900
      950: 'rgb(23 37 84)', // blue-950
    },
    secondary: {
      50: 'rgb(248 250 252)', // slate-50
      100: 'rgb(241 245 249)', // slate-100
      200: 'rgb(226 232 240)', // slate-200
      300: 'rgb(203 213 225)', // slate-300
      400: 'rgb(148 163 184)', // slate-400
      500: 'rgb(100 116 139)', // slate-500
      600: 'rgb(71 85 105)', // slate-600
      700: 'rgb(51 65 85)', // slate-700
      800: 'rgb(30 41 59)', // slate-800
      900: 'rgb(15 23 42)', // slate-900
      950: 'rgb(2 6 23)', // slate-950
    },
    success: {
      50: 'rgb(240 253 244)', // green-50
      100: 'rgb(220 252 231)', // green-100
      200: 'rgb(187 247 208)', // green-200
      300: 'rgb(134 239 172)', // green-300
      400: 'rgb(74 222 128)', // green-400
      500: 'rgb(34 197 94)', // green-500
      600: 'rgb(22 163 74)', // green-600
      700: 'rgb(21 128 61)', // green-700
      800: 'rgb(22 101 52)', // green-800
      900: 'rgb(20 83 45)', // green-900
      950: 'rgb(5 46 22)', // green-950
    },
    warning: {
      50: 'rgb(255 251 235)', // yellow-50
      100: 'rgb(254 243 199)', // yellow-100
      200: 'rgb(253 230 138)', // yellow-200
      300: 'rgb(252 211 77)', // yellow-300
      400: 'rgb(251 191 36)', // yellow-400
      500: 'rgb(245 158 11)', // yellow-500
      600: 'rgb(217 119 6)', // yellow-600
      700: 'rgb(180 83 9)', // yellow-700
      800: 'rgb(146 64 14)', // yellow-800
      900: 'rgb(120 53 15)', // yellow-900
      950: 'rgb(69 26 3)', // yellow-950
    },
    error: {
      50: 'rgb(254 242 242)', // red-50
      100: 'rgb(254 226 226)', // red-100
      200: 'rgb(254 202 202)', // red-200
      300: 'rgb(252 165 165)', // red-300
      400: 'rgb(248 113 113)', // red-400
      500: 'rgb(239 68 68)', // red-500
      600: 'rgb(220 38 38)', // red-600
      700: 'rgb(185 28 28)', // red-700
      800: 'rgb(153 27 27)', // red-800
      900: 'rgb(127 29 29)', // red-900
      950: 'rgb(69 10 10)', // red-950
    },
    neutral: {
      50: 'rgb(249 250 251)', // gray-50
      100: 'rgb(243 244 246)', // gray-100
      200: 'rgb(229 231 235)', // gray-200
      300: 'rgb(209 213 219)', // gray-300
      400: 'rgb(156 163 175)', // gray-400
      500: 'rgb(107 114 128)', // gray-500
      600: 'rgb(75 85 99)', // gray-600
      700: 'rgb(55 65 81)', // gray-700
      800: 'rgb(31 41 55)', // gray-800
      900: 'rgb(17 24 39)', // gray-900
      950: 'rgb(3 7 18)', // gray-950
    },
  },

  spacing: {
    px: '1px',
    0: '0px',
    0.5: '0.125rem', // 2px
    1: '0.25rem', // 4px
    1.5: '0.375rem', // 6px
    2: '0.5rem', // 8px
    2.5: '0.625rem', // 10px
    3: '0.75rem', // 12px
    3.5: '0.875rem', // 14px
    4: '1rem', // 16px
    5: '1.25rem', // 20px
    6: '1.5rem', // 24px
    7: '1.75rem', // 28px
    8: '2rem', // 32px
    9: '2.25rem', // 36px
    10: '2.5rem', // 40px
    11: '2.75rem', // 44px
    12: '3rem', // 48px
    14: '3.5rem', // 56px
    16: '4rem', // 64px
    20: '5rem', // 80px
    24: '6rem', // 96px
    28: '7rem', // 112px
    32: '8rem', // 128px
    36: '9rem', // 144px
    40: '10rem', // 160px
    44: '11rem', // 176px
    48: '12rem', // 192px
    52: '13rem', // 208px
    56: '14rem', // 224px
    60: '15rem', // 240px
    64: '16rem', // 256px
    72: '18rem', // 288px
    80: '20rem', // 320px
    96: '24rem', // 384px
  },

  typography: {
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      serif: ['ui-serif', 'Georgia', 'serif'],
      mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
    },
    fontSize: {
      xs: ['0.75rem', { lineHeight: '1rem' }], // 12px
      sm: ['0.875rem', { lineHeight: '1.25rem' }], // 14px
      base: ['1rem', { lineHeight: '1.5rem' }], // 16px
      lg: ['1.125rem', { lineHeight: '1.75rem' }], // 18px
      xl: ['1.25rem', { lineHeight: '1.75rem' }], // 20px
      '2xl': ['1.5rem', { lineHeight: '2rem' }], // 24px
      '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
      '4xl': ['2.25rem', { lineHeight: '2.5rem' }], // 36px
      '5xl': ['3rem', { lineHeight: '1' }], // 48px
      '6xl': ['3.75rem', { lineHeight: '1' }], // 60px
      '7xl': ['4.5rem', { lineHeight: '1' }], // 72px
      '8xl': ['6rem', { lineHeight: '1' }], // 96px
      '9xl': ['8rem', { lineHeight: '1' }], // 128px
    },
    fontWeight: {
      thin: '100',
      extralight: '200',
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
      black: '900',
    },
    lineHeight: {
      none: '1',
      tight: '1.25',
      snug: '1.375',
      normal: '1.5',
      relaxed: '1.625',
      loose: '2',
    },
  },

  borderRadius: {
    none: '0px',
    sm: '0.125rem', // 2px
    DEFAULT: '0.25rem', // 4px
    md: '0.375rem', // 6px
    lg: '0.5rem', // 8px
    xl: '0.75rem', // 12px
    '2xl': '1rem', // 16px
    '3xl': '1.5rem', // 24px
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: '0 0 #0000',
  },

  animation: {
    durations: {
      fastest: '100ms',
      fast: '200ms',
      normal: '300ms',
      slow: '500ms',
      slowest: '1000ms',
    },
    easings: {
      linear: 'linear',
      ease: 'ease',
      easeIn: 'ease-in',
      easeOut: 'ease-out',
      easeInOut: 'ease-in-out',
      cubic: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },

  zIndex: {
    auto: 'auto',
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
  },
} as const

export type DesignTokens = typeof designTokens
export type ColorScale = keyof typeof designTokens.colors.primary
export type SpacingToken = keyof typeof designTokens.spacing
export type FontSize = keyof typeof designTokens.typography.fontSize
export type FontWeight = keyof typeof designTokens.typography.fontWeight