// ITDO ERP Component Library - Main Export
// This is the main entry point for the component library

// Core Components
export * from './components/ui'
export * from './components/auth'
export * from './components/user-management'

// Hooks
export * from './hooks'

// Utilities
export * from './lib'

// Design System
export * from './design-system'

// API Integration
export * from './services/api'

// Version info
export const version = '1.0.0'
export const buildDate = new Date().toISOString()

// Library metadata
export const libraryInfo = {
  name: 'ITDO ERP Components',
  version,
  buildDate,
  description: 'A comprehensive React component library for ERP systems',
  author: 'ITDO Team',
  license: 'MIT',
  repository: 'https://github.com/itdo/erp-components',
  homepage: 'https://erp-components.itdo.com',
  keywords: [
    'react',
    'typescript',
    'components',
    'ui',
    'erp',
    'enterprise',
    'dashboard',
    'forms',
    'charts',
    'tables',
  ],
}