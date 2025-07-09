# E2E Testing with Playwright

## Overview

This directory contains end-to-end tests using Playwright for the ITDO ERP system.

## Structure

```
tests/e2e/
├── auth/           # Authentication flow tests
├── fixtures/       # Test fixtures and helpers
├── pages/          # Page object models
└── README.md       # This file
```

## Running Tests

```bash
# Run all tests
npm run test:e2e

# Run tests with UI
npm run test:e2e:headed

# Run specific test file
npm run test:e2e auth/login.spec.ts

# Run tests for specific browser
npm run test:e2e -- --project=chromium
```

## Test Categories

### Authentication Tests (`auth/`)
- **login.spec.ts**: Login flow testing
- **logout.spec.ts**: Logout flow testing
- **session.spec.ts**: Session management testing

## Writing Tests

1. Use Page Object Model pattern
2. Keep tests independent
3. Use fixtures for common setup
4. Always clean up test data

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Daily scheduled runs

Test results and screenshots are uploaded as artifacts.