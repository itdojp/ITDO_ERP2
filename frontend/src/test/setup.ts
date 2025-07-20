import '@testing-library/jest-dom'

// Configure React Testing Library to use React.act instead of ReactDOMTestUtils.act
// This resolves deprecation warnings in test output
import { configure } from '@testing-library/react'

configure({
  // Enable React 18+ concurrent features support
  reactStrictMode: true,
  // Use modern React.act by default
  unstable_advanceTimersWrapper: (cb) => {
    return cb()
  }
})