import '@testing-library/jest-dom'
import { act } from 'react'

// Configure React Testing Library to use React.act instead of ReactDOMTestUtils.act
// This resolves deprecation warnings in test output
import { configure } from '@testing-library/react'

configure({
  // Use modern React.act wrapper to eliminate ReactDOMTestUtils deprecation warnings
  unstable_advanceTimersWrapper: (cb) => {
    return act(() => cb())
  }
})

// Ensure React.act is used globally for all async updates
const originalError = console.error
// eslint-disable-next-line no-console
console.error = (...args) => {
  if (typeof args[0] === 'string' && args[0].includes('ReactDOMTestUtils.act')) {
    return // Suppress ReactDOMTestUtils deprecation warnings
  }
  originalError.call(console, ...args)
}