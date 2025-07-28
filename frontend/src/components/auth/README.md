# Authentication Components

This directory contains all authentication-related React components for the ITDO ERP system.

## Components

### Core Authentication Components

1. **LoginForm** - User login with email/password and Google SSO
2. **RegisterForm** - New user registration with password strength indicator
3. **MFAVerification** - Two-factor authentication code verification
4. **ForgotPassword** - Password reset request form
5. **ResetPassword** - Password reset form with token verification
6. **MFASetup** - Multi-factor authentication setup wizard

### Security Management Components

1. **ProtectedRoute** - Route wrapper for authentication-required pages
2. **SessionManager** - Active session management and configuration
3. **SecuritySettings** - Comprehensive security settings dashboard

## Features

### Authentication Features
- Email/password login
- Google SSO integration
- Two-factor authentication (TOTP)
- Remember me functionality
- Password reset flow
- Session management

### Security Features
- Password strength validation
- MFA setup and management
- Session timeout configuration
- Concurrent session limits
- Device trust management
- Security recommendations

### UI/UX Features
- Real-time password strength indicator
- Error handling and user feedback
- Loading states
- Responsive design
- Japanese localization

## Usage Example

```tsx
import { LoginForm, ProtectedRoute } from '@/components/auth';

// Public route
<Route path="/auth/login" element={<LoginForm />} />

// Protected route
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />

// MFA-required route
<Route path="/admin" element={
  <ProtectedRoute requireMFA={true}>
    <AdminPanel />
  </ProtectedRoute>
} />
```

## Testing

All components include comprehensive test coverage:
- Unit tests for individual components
- Integration tests for authentication flows
- Mock implementations for API calls