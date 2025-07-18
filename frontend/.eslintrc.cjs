module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:react/jsx-runtime'
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  plugins: ['react-refresh', '@typescript-eslint'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': 'error',
    'no-unused-vars': 'off',
    'no-console': 'warn',
  },
  overrides: [
    {
      files: ['tests/e2e/**/*.ts', 'tests/e2e/**/*.tsx'],
      rules: {
        'no-console': 'off', // Allow console in E2E tests for debugging
      },
    },
  ],
  settings: {
    react: {
      version: 'detect'
    }
  }
}