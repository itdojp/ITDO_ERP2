export const accessibilityGuidelines = {
  colorContrast: {
    wcag: {
      aa: {
        normal: 4.5, // 4.5:1 ratio for normal text
        large: 3, // 3:1 ratio for large text (18pt+ or 14pt+ bold)
      },
      aaa: {
        normal: 7, // 7:1 ratio for normal text
        large: 4.5, // 4.5:1 ratio for large text
      },
    },
    guidelines: [
      'Ensure text has sufficient contrast against its background',
      'Large text (18pt+ or 14pt+ bold) requires lower contrast ratios',
      'Interactive elements should meet minimum contrast requirements',
      'Consider color-blind users - do not rely solely on color',
    ],
    tools: [
      'WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/',
      'Colour Contrast Analyser: https://www.tpgi.com/color-contrast-checker/',
      'Browser DevTools accessibility features',
    ],
  },

  keyboardNavigation: {
    requirements: [
      'All interactive elements must be keyboard accessible',
      'Tab order should be logical and meaningful',
      'Focus indicators must be clearly visible',
      'Escape key should close modals and dropdowns',
      'Arrow keys should navigate within component groups',
    ],
    implementation: {
      tabIndex: {
        '0': 'Include in natural tab order',
        '-1': 'Remove from tab order, but focusable programmatically',
        positive: 'Avoid - disrupts natural tab order',
      },
      focusManagement: [
        'Trap focus within modals',
        'Return focus to trigger element when closing modals',
        'Provide skip links for main content areas',
        'Ensure custom components handle focus correctly',
      ],
    },
  },

  screenReaders: {
    ariaLabels: {
      required: [
        'Interactive elements without visible text (buttons with only icons)',
        'Form inputs (via aria-label or associated labels)',
        'Landmark regions (navigation, main, aside, etc.)',
        'Complex widgets (comboboxes, tree views, etc.)',
      ],
      guidelines: [
        'Keep labels concise but descriptive',
        'Use aria-labelledby to reference existing text',
        'Prefer visible labels over aria-label when possible',
        'Update labels when content changes dynamically',
      ],
    },
    ariaDescribedby: [
      'Link to help text or error messages',
      'Provide additional context for complex interactions',
      'Reference instructions or format requirements',
    ],
    landmarks: {
      banner: 'Site header/masthead (usually <header> tag)',
      navigation: 'Navigation menus and links',
      main: 'Primary content area (only one per page)',
      contentinfo: 'Site footer information',
      complementary: 'Supporting content (<aside> tag)',
      search: 'Search functionality',
      form: 'Form regions',
      region: 'Generic landmark with accessible name',
    },
  },

  semanticHTML: {
    principles: [
      'Use appropriate HTML elements for their semantic meaning',
      'Headings should follow hierarchical order (h1 → h2 → h3)',
      'Lists should use <ul>, <ol>, or <dl> elements',
      'Form controls should be properly labeled',
      'Tables should have proper headers and captions',
    ],
    elements: {
      buttons: 'For actions and interactions',
      links: 'For navigation and external references',
      headings: 'For content hierarchy and structure',
      lists: 'For grouped related items',
      forms: 'For data input and submission',
      tables: 'For tabular data presentation',
    },
  },

  focusManagement: {
    patterns: {
      modal: [
        '1. Save reference to element that opened modal',
        '2. Move focus to modal (first focusable element or modal itself)',
        '3. Trap focus within modal boundaries',
        '4. Return focus to opening element when closed',
      ],
      dropdown: [
        '1. Focus trigger element on open',
        '2. Use arrow keys to navigate options',
        '3. Enter/Space to select',
        '4. Escape to close and return focus',
      ],
      tabs: [
        '1. Arrow keys to navigate between tabs',
        '2. Tab to move focus to tab panel',
        '3. Home/End to jump to first/last tab',
      ],
    },
    implementation: {
      focusTrap: `
// Focus trap implementation
const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
const firstFocusable = modal.querySelector(focusableElements)
const focusables = modal.querySelectorAll(focusableElements)
const lastFocusable = focusables[focusables.length - 1]

const handleTabKey = (e) => {
  if (e.key !== 'Tab') return
  
  if (e.shiftKey) {
    if (document.activeElement === firstFocusable) {
      lastFocusable.focus()
      e.preventDefault()
    }
  } else {
    if (document.activeElement === lastFocusable) {
      firstFocusable.focus()
      e.preventDefault()
    }
  }
}
      `,
    },
  },

  testing: {
    automated: [
      'axe-core for accessibility violations',
      'Jest/Vitest with @testing-library/jest-dom',
      'Lighthouse accessibility audits',
      'Pa11y command-line accessibility testing',
    ],
    manual: [
      'Keyboard-only navigation testing',
      'Screen reader testing (NVDA, JAWS, VoiceOver)',
      'High contrast mode testing',
      'Zoom testing up to 200%',
      'Color vision simulation',
    ],
    tools: {
      browser: [
        'Chrome DevTools Accessibility panel',
        'Firefox Accessibility Inspector',
        'Safari VoiceOver utility',
      ],
      extensions: [
        'axe DevTools browser extension',
        'WAVE Web Accessibility Evaluator',
        'Lighthouse accessibility audit',
        'Colour Contrast Analyser',
      ],
      screenReaders: [
        'NVDA (free, Windows)',
        'JAWS (commercial, Windows)',
        'VoiceOver (built-in, macOS/iOS)',
        'Orca (Linux)',
        'TalkBack (Android)',
      ],
    },
  },

  checklist: {
    development: [
      '☐ All interactive elements are keyboard accessible',
      '☐ Focus indicators are clearly visible',
      '☐ Color contrast meets WCAG AA standards',
      '☐ All images have appropriate alt text',
      '☐ Form inputs have associated labels',
      '☐ Headings follow logical hierarchy',
      '☐ ARIA labels are provided where needed',
      '☐ Error messages are descriptive and accessible',
      '☐ Loading states are announced to screen readers',
      '☐ Focus management works correctly in modals',
    ],
    testing: [
      '☐ Navigate entire interface using only keyboard',
      '☐ Test with screen reader (at least VoiceOver/NVDA)',
      '☐ Verify color contrast with automated tools',
      '☐ Run axe-core accessibility tests',
      '☐ Test zoom functionality up to 200%',
      '☐ Verify high contrast mode compatibility',
      '☐ Test with CSS disabled',
      '☐ Validate HTML semantics',
      '☐ Check mobile accessibility',
      '☐ Test with users who have disabilities',
    ],
  },
} as const

export type AccessibilityGuidelines = typeof accessibilityGuidelines