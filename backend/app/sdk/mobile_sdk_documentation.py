"""Mobile SDK Documentation & Code Samples Generator - CC02 v72.0 Day 17."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentationType(str, Enum):
    """Documentation types."""

    API_REFERENCE = "api_reference"
    QUICK_START = "quick_start"
    TUTORIAL = "tutorial"
    INTEGRATION_GUIDE = "integration_guide"
    CODE_SAMPLE = "code_sample"
    TROUBLESHOOTING = "troubleshooting"
    CHANGELOG = "changelog"


class PlatformType(str, Enum):
    """Supported platforms."""

    IOS = "ios"
    ANDROID = "android"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    WEB = "web"


class CodeSample(BaseModel):
    """Code sample definition."""

    sample_id: str
    title: str
    description: str
    platform: PlatformType
    language: str  # swift, kotlin, javascript, dart, python
    code: str
    imports: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DocumentationSection(BaseModel):
    """Documentation section."""

    section_id: str
    title: str
    content: str
    subsections: List["DocumentationSection"] = Field(default_factory=list)
    code_samples: List[CodeSample] = Field(default_factory=list)
    links: List[Dict[str, str]] = Field(default_factory=list)
    order: int = 0


class APIEndpoint(BaseModel):
    """API endpoint documentation."""

    endpoint: str
    method: str
    description: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    error_codes: List[Dict[str, Any]] = Field(default_factory=list)


class SDKDocumentationGenerator:
    """Generate comprehensive SDK documentation."""

    def __init__(self, output_dir: str = "docs/sdk") -> dict:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sections: Dict[str, DocumentationSection] = {}
        self.code_samples: Dict[str, List[CodeSample]] = {}
        self.api_endpoints: List[APIEndpoint] = []

    def generate_quick_start_guide(self) -> DocumentationSection:
        """Generate quick start guide."""
        ios_sample = CodeSample(
            sample_id="ios_quick_start",
            title="iOS Quick Start",
            description="Initialize and authenticate with the ITDO ERP SDK on iOS",
            platform=PlatformType.IOS,
            language="swift",
            imports=["import Foundation", "import ITDOERPMobileSDK"],
            code="""
// 1. Configure the SDK
let config = SDKConfig(
    apiBaseUrl: "https://api.your-org.com",
    organizationId: "your-org-id",
    appId: "your-app-id",
    apiKey: "your-api-key"
)

// 2. Initialize the SDK
let sdk = MobileERPSDK(config: config)

// 3. Set device information
let deviceInfo = DeviceInfo(
    deviceId: UIDevice.current.identifierForVendor?.uuidString ?? "",
    platform: "ios",
    osVersion: UIDevice.current.systemVersion,
    appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "",
    deviceModel: UIDevice.current.model,
    screenResolution: "\\(UIScreen.main.bounds.width)x\\(UIScreen.main.bounds.height)",
    timezone: TimeZone.current.identifier,
    locale: Locale.current.identifier
)

// 4. Initialize SDK with device info
try await sdk.initialize(deviceInfo: deviceInfo)

// 5. Authenticate user
do {
    let token = try await sdk.authenticate(
        username: "user@example.com",
        password: "password123"
    )
    print("Authentication successful: \\(token.accessToken)")
} catch {
    print("Authentication failed: \\(error)")
}

// 6. Make authenticated API calls
do {
    let profile = try await sdk.httpClient.get(endpoint: "auth/profile")
    print("User profile: \\(profile)")
} catch {
    print("API call failed: \\(error)")
}
""",
            prerequisites=["iOS 13.0+", "Xcode 12.0+", "Valid ITDO ERP account"],
            notes=[
                "Replace placeholder values with your actual credentials",
                "Store API keys securely using Keychain",
                "Handle authentication errors gracefully",
            ],
            tags=["quickstart", "ios", "authentication"],
        )

        android_sample = CodeSample(
            sample_id="android_quick_start",
            title="Android Quick Start",
            description="Initialize and authenticate with the ITDO ERP SDK on Android",
            platform=PlatformType.ANDROID,
            language="kotlin",
            imports=["import com.itdo.erp.mobile.sdk.*", "import kotlinx.coroutines.*"],
            code="""
// 1. Configure the SDK
val config = SDKConfig(
    apiBaseUrl = "https://api.your-org.com",
    organizationId = "your-org-id",
    appId = "your-app-id",
    apiKey = "your-api-key"
)

// 2. Initialize the SDK
val sdk = MobileERPSDK(config)

// 3. Set device information
val deviceInfo = DeviceInfo(
    deviceId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID),
    platform = "android",
    osVersion = Build.VERSION.RELEASE,
    appVersion = BuildConfig.VERSION_NAME,
    deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}",
    screenResolution = "${resources.displayMetrics.widthPixels}x${resources.displayMetrics.heightPixels}",
    timezone = TimeZone.getDefault().id,
    locale = Locale.getDefault().toString()
)

// 4. Initialize SDK with device info (in coroutine)
lifecycleScope.launch {
    try {
        sdk.initialize(deviceInfo)

        // 5. Authenticate user
        val token = sdk.authenticate(
            username = "user@example.com",
            password = "password123"
        )
        println("Authentication successful: ${token.accessToken}")

        // 6. Make authenticated API calls
        val profile = sdk.httpClient.get("auth/profile")
        println("User profile: $profile")

    } catch (e: Exception) {
        println("SDK operation failed: ${e.message}")
    }
}
""",
            prerequisites=["Android API 21+", "Kotlin 1.7+", "Valid ITDO ERP account"],
            notes=[
                "Add required permissions to AndroidManifest.xml",
                "Use lifecycle-aware coroutines for async operations",
                "Store sensitive data in Android Keystore",
            ],
            tags=["quickstart", "android", "authentication"],
        )

        return DocumentationSection(
            section_id="quick_start",
            title="Quick Start Guide",
            content="""
# Quick Start Guide

Get up and running with the ITDO ERP Mobile SDK in minutes.

## Installation

### iOS (Swift Package Manager)
```swift
dependencies: [
    .package(url: "https://github.com/itdo-io/erp-mobile-sdk-ios", from: "1.0.0")
]
```

### Android (Gradle)
```kotlin
implementation 'com.itdo.erp:mobile-sdk:1.0.0'
```

### React Native
```bash
npm install @itdo/erp-mobile-sdk
```

## Basic Usage

The SDK provides a simple, consistent API across all platforms. Follow these steps to get started:

1. **Configure the SDK** with your organization credentials
2. **Initialize** with device information
3. **Authenticate** your users
4. **Make API calls** to access ERP data

## Platform-Specific Examples

Choose your platform to see detailed implementation examples:
""",
            code_samples=[ios_sample, android_sample],
            order=1,
        )

    def generate_authentication_guide(self) -> DocumentationSection:
        """Generate authentication guide."""
        credential_auth_sample = CodeSample(
            sample_id="credential_auth",
            title="Username/Password Authentication",
            description="Authenticate users with username and password",
            platform=PlatformType.IOS,
            language="swift",
            code="""
// Basic authentication
do {
    let token = try await sdk.authenticate(
        username: "user@company.com",
        password: "securePassword123"
    )

    // Token is automatically stored and managed by SDK
    print("Access token: \\(token.accessToken)")
    print("Expires at: \\(token.expiresAt)")

} catch AuthenticationError.invalidCredentials {
    // Handle invalid credentials
    showAlert("Invalid username or password")
} catch AuthenticationError.accountLocked {
    // Handle locked account
    showAlert("Account is locked. Contact administrator.")
} catch {
    // Handle other authentication errors
    showAlert("Authentication failed: \\(error.localizedDescription)")
}

// Check authentication status
if sdk.isAuthenticated() {
    // User is authenticated and ready to use SDK
    proceedToMainApp()
} else {
    // Show login screen
    showLoginScreen()
}
""",
            tags=["authentication", "credentials"],
        )

        biometric_auth_sample = CodeSample(
            sample_id="biometric_auth",
            title="Biometric Authentication",
            description="Authenticate users with biometric data (Face ID, Touch ID, Fingerprint)",
            platform=PlatformType.IOS,
            language="swift",
            code="""
import LocalAuthentication

// Check biometric availability
let context = LAContext()
var error: NSError?

if context.canEvaluatePolicy(.biometricAuthentication, error: &error) {

    // Collect biometric data (simplified - actual implementation would use proper biometric APIs)
    let biometricData: [String: Any] = [
        "type": "face_id", // or "touch_id", "fingerprint"
        "quality_score": 0.95,
        "liveness_score": 0.88,
        "template_data": "encrypted_biometric_template"
    ]

    do {
        let token = try await sdk.authenticateBiometric(
            deviceId: deviceInfo.deviceId,
            biometricData: biometricData
        )

        print("Biometric authentication successful")

        // Optional: Set up biometric for future quick access
        try await sdk.authSecurityModule.biometricManager.enrollBiometric(
            biometricType: "face_id",
            biometricData: biometricData,
            userId: token.userId,
            deviceId: deviceInfo.deviceId
        )

    } catch {
        print("Biometric authentication failed: \\(error)")
        // Fall back to credential authentication
        showCredentialLogin()
    }
} else {
    // Biometric not available, use credential authentication
    showCredentialLogin()
}
""",
            prerequisites=[
                "Biometric hardware (Face ID, Touch ID, Fingerprint sensor)",
                "User enrolled biometrics on device",
                "App permissions for biometric access",
            ],
            tags=["authentication", "biometric", "security"],
        )

        mfa_sample = CodeSample(
            sample_id="mfa_auth",
            title="Multi-Factor Authentication",
            description="Implement multi-factor authentication with TOTP",
            platform=PlatformType.IOS,
            language="swift",
            code="""
// Step 1: Initiate MFA after successful primary authentication
do {
    let primaryToken = try await sdk.authenticate(
        username: "user@company.com",
        password: "password123"
    )

    // Step 2: Initiate MFA challenge
    let mfaChallenge = try await sdk.authSecurityModule.mfaManager.initiateMFA(
        userId: primaryToken.userId,
        primaryAuthToken: primaryToken.accessToken,
        requestedFactors: ["totp", "sms"] // Request TOTP and SMS backup
    )

    print("MFA Challenge ID: \\(mfaChallenge.challengeId)")
    print("Send code to: \\(mfaChallenge.maskedDestination)")

    // Step 3: Show MFA input UI
    showMFACodeInput { code in
        Task {
            do {
                // Step 4: Verify MFA code
                let result = try await sdk.authSecurityModule.mfaManager.verifyMFAFactor(
                    challengeId: mfaChallenge.challengeId,
                    factorType: "totp",
                    factorValue: code
                )

                if result.verificationSuccessful {
                    print("MFA verification successful")
                    // Update SDK with final authentication token
                    sdk.authManager.currentToken = result.finalToken
                    proceedToMainApp()
                } else {
                    showAlert("Invalid verification code. Please try again.")
                }

            } catch {
                showAlert("MFA verification failed: \\(error.localizedDescription)")
            }
        }
    }

} catch {
    showAlert("Primary authentication failed: \\(error.localizedDescription)")
}
""",
            prerequisites=[
                "MFA enabled for organization",
                "User has configured TOTP app (Google Authenticator, Authy, etc.)",
                "Valid phone number for SMS backup",
            ],
            notes=[
                "Always provide backup MFA methods",
                "Handle MFA challenge expiration gracefully",
                "Store MFA preferences securely",
            ],
            tags=["authentication", "mfa", "security", "totp"],
        )

        return DocumentationSection(
            section_id="authentication",
            title="Authentication Guide",
            content="""
# Authentication Guide

The ITDO ERP Mobile SDK supports multiple authentication methods to ensure secure access to your ERP system.

## Authentication Methods

1. **Username/Password** - Traditional credential-based authentication
2. **Biometric** - Face ID, Touch ID, or Fingerprint authentication
3. **Multi-Factor Authentication (MFA)** - TOTP, SMS, or Email verification
4. **Device Trust** - Device-based authentication for trusted devices

## Security Features

- **Automatic token refresh** - SDK handles token expiration automatically
- **Secure token storage** - Tokens stored in device keychain/keystore
- **Device fingerprinting** - Enhanced security through device identification
- **Session management** - Automatic session cleanup and security monitoring

## Best Practices

- Always handle authentication errors gracefully
- Implement biometric authentication where supported
- Use MFA for high-privilege operations
- Monitor authentication events for security
- Implement proper logout and session cleanup
""",
            code_samples=[credential_auth_sample, biometric_auth_sample, mfa_sample],
            order=2,
        )

    def generate_data_sync_guide(self) -> DocumentationSection:
        """Generate data synchronization guide."""
        sync_sample = CodeSample(
            sample_id="data_sync",
            title="Data Synchronization",
            description="Sync data between local storage and server",
            platform=PlatformType.IOS,
            language="swift",
            code="""
// Initialize sync module
let syncModule = sdk.getModule("sync") as! DataSyncModule

// Configure sync settings
let syncConfig = SyncConfiguration(
    batchSize: 100,
    maxRetries: 3,
    conflictResolution: .clientWins, // or .serverWins, .merge, .manual
    enableBackgroundSync: true,
    syncIntervalMinutes: 15
)

// Start initial synchronization
do {
    let syncSession = try await syncModule.syncNow(
        entityTypes: ["users", "projects", "tasks", "documents"],
        forceFULLSync: false
    )

    print("Sync started - Session ID: \\(syncSession.sessionId)")

    // Monitor sync progress
    syncModule.onSyncProgress { progress in
        DispatchQueue.main.async {
            updateProgressBar(progress.completedEntities / progress.totalEntities)
            updateStatusLabel("Syncing \\(progress.currentEntity)...")
        }
    }

    // Handle sync completion
    syncModule.onSyncComplete { result in
        DispatchQueue.main.async {
            if result.success {
                showAlert("Sync completed successfully")
                print("Synced \\(result.entitiesSynced) entities in \\(result.durationMs)ms")
            } else {
                showAlert("Sync failed: \\(result.error?.localizedDescription ?? "Unknown error")")
            }
        }
    }

} catch {
    showAlert("Failed to start sync: \\(error.localizedDescription)")
}

// Query local data (works offline)
let localData = try await syncModule.queryLocal(
    entityType: "projects",
    filters: ["status": "active"],
    orderBy: "updated_at",
    limit: 50
)

print("Found \\(localData.count) local projects")

// Create new data (queued for sync)
let newProject = Project(
    name: "New Mobile Project",
    description: "Created offline",
    status: "active"
)

try await syncModule.createLocal(
    entityType: "projects",
    data: newProject.toDictionary()
)

print("Project created locally, will sync when online")
""",
            prerequisites=[
                "Network connectivity for initial sync",
                "Sufficient local storage space",
                "Proper data access permissions",
            ],
            notes=[
                "Sync works automatically in background",
                "Data remains accessible offline",
                "Conflicts are resolved based on configuration",
            ],
            tags=["sync", "offline", "data"],
        )

        return DocumentationSection(
            section_id="data_sync",
            title="Data Synchronization",
            content="""
# Data Synchronization

Keep your mobile app data in sync with the ERP server, even when offline.

## Key Features

- **Offline-first architecture** - App works without internet connection
- **Automatic background sync** - Data syncs automatically when online
- **Conflict resolution** - Handles data conflicts intelligently
- **Selective sync** - Choose which data to sync
- **Progress monitoring** - Track sync progress in real-time

## Sync Strategies

1. **Full Sync** - Downloads all data (initial setup)
2. **Incremental Sync** - Only syncs changes since last sync
3. **Selective Sync** - Sync specific entity types or filters
4. **Background Sync** - Automatic sync in background

## Conflict Resolution

When the same data is modified both locally and on server:

- **Client Wins** - Local changes take precedence
- **Server Wins** - Server changes take precedence
- **Merge** - Attempt to merge changes automatically
- **Manual** - Prompt user to resolve conflicts
""",
            code_samples=[sync_sample],
            order=3,
        )

    def generate_api_reference(self) -> DocumentationSection:
        """Generate comprehensive API reference."""
        # Core SDK APIs
        self.api_endpoints.extend(
            [
                APIEndpoint(
                    endpoint="/api/v1/auth/token",
                    method="POST",
                    description="Authenticate user and obtain access token",
                    parameters=[
                        {
                            "name": "grant_type",
                            "type": "string",
                            "required": True,
                            "description": "Authentication grant type",
                        },
                        {
                            "name": "username",
                            "type": "string",
                            "required": True,
                            "description": "User's username or email",
                        },
                        {
                            "name": "password",
                            "type": "string",
                            "required": True,
                            "description": "User's password",
                        },
                        {
                            "name": "organization_id",
                            "type": "string",
                            "required": True,
                            "description": "Organization identifier",
                        },
                        {
                            "name": "app_id",
                            "type": "string",
                            "required": True,
                            "description": "Application identifier",
                        },
                    ],
                    request_body={
                        "type": "object",
                        "properties": {
                            "grant_type": {"type": "string", "example": "password"},
                            "username": {
                                "type": "string",
                                "example": "user@company.com",
                            },
                            "password": {
                                "type": "string",
                                "example": "securePassword123",
                            },
                            "organization_id": {
                                "type": "string",
                                "example": "org_123456",
                            },
                            "app_id": {"type": "string", "example": "mobile_app_v1"},
                        },
                    },
                    response_schema={
                        "type": "object",
                        "properties": {
                            "access_token": {"type": "string"},
                            "refresh_token": {"type": "string"},
                            "token_type": {"type": "string", "example": "Bearer"},
                            "expires_at": {"type": "string", "format": "datetime"},
                            "scope": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    error_codes=[
                        {"code": 400, "description": "Invalid request parameters"},
                        {"code": 401, "description": "Invalid credentials"},
                        {"code": 403, "description": "Account locked or disabled"},
                        {
                            "code": 429,
                            "description": "Too many authentication attempts",
                        },
                    ],
                ),
                APIEndpoint(
                    endpoint="/api/v1/mobile-erp/security/biometric/authenticate",
                    method="POST",
                    description="Authenticate user with biometric data",
                    parameters=[
                        {
                            "name": "device_id",
                            "type": "string",
                            "required": True,
                            "description": "Device identifier",
                        },
                        {
                            "name": "biometric_type",
                            "type": "string",
                            "required": True,
                            "description": "Type of biometric (fingerprint, face, voice)",
                        },
                        {
                            "name": "biometric_template",
                            "type": "string",
                            "required": True,
                            "description": "Encrypted biometric template",
                        },
                        {
                            "name": "challenge_response",
                            "type": "string",
                            "required": True,
                            "description": "Challenge response",
                        },
                    ],
                    response_schema={
                        "type": "object",
                        "properties": {
                            "authentication_successful": {"type": "boolean"},
                            "session_token": {"type": "string"},
                            "expires_at": {"type": "string", "format": "datetime"},
                            "trust_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                    },
                ),
                APIEndpoint(
                    endpoint="/api/v1/data/sync",
                    method="POST",
                    description="Initiate data synchronization session",
                    parameters=[
                        {
                            "name": "entity_types",
                            "type": "array",
                            "required": False,
                            "description": "Entity types to sync",
                        },
                        {
                            "name": "force_full_sync",
                            "type": "boolean",
                            "required": False,
                            "description": "Force full synchronization",
                        },
                        {
                            "name": "batch_size",
                            "type": "integer",
                            "required": False,
                            "description": "Sync batch size",
                        },
                    ],
                    response_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "sync_url": {"type": "string"},
                            "estimated_duration_ms": {"type": "integer"},
                            "total_entities": {"type": "integer"},
                        },
                    },
                ),
            ]
        )

        api_content = """
# API Reference

Complete reference for all ITDO ERP Mobile SDK APIs.

## Base URL
```
https://api.your-organization.com/api/v1
```

## Authentication
All API requests require authentication using Bearer tokens:
```
Authorization: Bearer your_access_token_here
```

## Rate Limiting
- **Rate Limit**: 1000 requests per hour per user
- **Burst Limit**: 100 requests per minute
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Error Handling
All errors follow consistent format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  }
}
```

## Endpoints
"""

        for endpoint in self.api_endpoints:
            api_content += f"""
### {endpoint.method} {endpoint.endpoint}

{endpoint.description}

**Parameters:**
"""
            for param in endpoint.parameters:
                required = "✅" if param.get("required") else "⚪"
                api_content += f"- {required} `{param['name']}` ({param['type']}): {param['description']}\n"

            if endpoint.request_body:
                api_content += f"""
**Request Body:**
```json
{json.dumps(endpoint.request_body.get("properties", {}), indent=2)}
```
"""

            if endpoint.response_schema:
                api_content += f"""
**Response Schema:**
```json
{json.dumps(endpoint.response_schema.get("properties", {}), indent=2)}
```
"""

            if endpoint.error_codes:
                api_content += "\n**Error Codes:**\n"
                for error in endpoint.error_codes:
                    api_content += f"- `{error['code']}`: {error['description']}\n"

            api_content += "\n---\n"

        return DocumentationSection(
            section_id="api_reference",
            title="API Reference",
            content=api_content,
            order=4,
        )

    def generate_integration_examples(self) -> DocumentationSection:
        """Generate platform integration examples."""
        react_native_sample = CodeSample(
            sample_id="react_native_integration",
            title="React Native Integration",
            description="Complete React Native integration example",
            platform=PlatformType.REACT_NATIVE,
            language="javascript",
            imports=[
                "import { MobileERPSDK, SDKConfig, DeviceInfo } from '@itdo/erp-mobile-sdk';",
                "import AsyncStorage from '@react-native-async-storage/async-storage';",
                "import DeviceInfo from 'react-native-device-info';",
            ],
            code="""
import React, { useEffect, useState, useContext, createContext } from 'react';
import { Alert, ActivityIndicator } from 'react-native';

// Create SDK Context
const SDKContext = createContext(null);

// SDK Provider Component
export const SDKProvider = ({ children }) => {
  const [sdk, setSdk] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    initializeSDK();
  }, []);

  const initializeSDK = async () => {
    try {
      // 1. Configure SDK
      const config = new SDKConfig({
        apiBaseUrl: 'https://api.your-org.com',
        organizationId: 'your-org-id',
        appId: 'your-react-native-app',
        apiKey: 'your-api-key',
        logLevel: __DEV__ ? 'DEBUG' : 'INFO'
      });

      // 2. Create SDK instance
      const sdkInstance = new MobileERPSDK(config);

      // 3. Gather device information
      const deviceInfo = new DeviceInfo({
        deviceId: await DeviceInfo.getUniqueId(),
        platform: 'react_native',
        osVersion: await DeviceInfo.getSystemVersion(),
        appVersion: await DeviceInfo.getVersion(),
        deviceModel: await DeviceInfo.getModel(),
        screenResolution: `${await DeviceInfo.getScreenWidth()}x${await DeviceInfo.getScreenHeight()}`,
        timezone: await DeviceInfo.getTimezone(),
        locale: await DeviceInfo.getLocale()
      });

      // 4. Initialize SDK
      await sdkInstance.initialize(deviceInfo);

      // 5. Check for existing authentication
      const storedToken = await AsyncStorage.getItem('auth_token');
      if (storedToken) {
        const token = JSON.parse(storedToken);
        if (new Date(token.expiresAt) > new Date()) {
          sdkInstance.authManager.currentToken = token;
          setIsAuthenticated(true);
        }
      }

      setSdk(sdkInstance);
      setIsInitialized(true);

    } catch (error) {
      Alert.alert('Initialization Error', error.message);
    }
  };

  const authenticate = async (username, password) => {
    try {
      const token = await sdk.authenticate(username, password);

      // Store token securely
      await AsyncStorage.setItem('auth_token', JSON.stringify(token));
      setIsAuthenticated(true);

      return token;
    } catch (error) {
      Alert.alert('Authentication Error', error.message);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await sdk.logout();
      await AsyncStorage.removeItem('auth_token');
      setIsAuthenticated(false);
    } catch (error) {
      Alert.alert('Logout Error', error.message);
    }
  };

  if (!isInitialized) {
    return <ActivityIndicator size="large" />;
  }

  return (
    <SDKContext.Provider value={{
      sdk,
      isAuthenticated,
      authenticate,
      logout
    }}>
      {children}
    </SDKContext.Provider>
  );
};

// Hook to use SDK
export const useSDK = () => {
  const context = useContext(SDKContext);
  if (!context) {
    throw new Error('useSDK must be used within SDKProvider');
  }
  return context;
};

// Example usage in a component
const LoginScreen = () => {
  const { authenticate, isAuthenticated } = useSDK();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      await authenticate(username, password);
      // Navigation handled by parent based on isAuthenticated state
    } catch (error) {
      // Error already shown by authenticate function
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) {
    return <MainApp />;
  }

  return (
    <View style={styles.container}>
      <TextInput
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        style={styles.input}
      />
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        style={styles.input}
      />
      <Button
        title={loading ? "Logging in..." : "Login"}
        onPress={handleLogin}
        disabled={loading}
      />
    </View>
  );
};
""",
            prerequisites=[
                "React Native 0.66+",
                "@react-native-async-storage/async-storage",
                "react-native-device-info",
            ],
            tags=["integration", "react-native", "authentication"],
        )

        flutter_sample = CodeSample(
            sample_id="flutter_integration",
            title="Flutter Integration",
            description="Flutter integration with state management",
            platform=PlatformType.FLUTTER,
            language="dart",
            code="""
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:itdo_erp_mobile_sdk/itdo_erp_mobile_sdk.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

// SDK Service Class
class SDKService extends ChangeNotifier {
  MobileERPSDK? _sdk;
  bool _isInitialized = false;
  bool _isAuthenticated = false;
  String? _error;

  MobileERPSDK? get sdk => _sdk;
  bool get isInitialized => _isInitialized;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  Future<void> initialize() async {
    try {
      // 1. Configure SDK
      final config = SDKConfig(
        apiBaseUrl: 'https://api.your-org.com',
        organizationId: 'your-org-id',
        appId: 'your-flutter-app',
        apiKey: 'your-api-key',
      );

      // 2. Create SDK instance
      _sdk = MobileERPSDK(config);

      // 3. Get device info
      final deviceInfoPlugin = DeviceInfoPlugin();
      final deviceInfo = await deviceInfoPlugin.deviceInfo;

      final sdkDeviceInfo = DeviceInfo(
        deviceId: deviceInfo.identifierForVendor ?? '',
        platform: 'flutter',
        osVersion: deviceInfo.systemVersion,
        appVersion: '1.0.0', // Get from pubspec.yaml
        deviceModel: deviceInfo.model,
        screenResolution: '${MediaQuery.of(context).size.width}x${MediaQuery.of(context).size.height}',
        timezone: DateTime.now().timeZoneName,
        locale: Platform.localeName,
      );

      // 4. Initialize SDK
      await _sdk!.initialize(deviceInfo: sdkDeviceInfo);

      // 5. Check existing auth
      final prefs = await SharedPreferences.getInstance();
      final tokenJson = prefs.getString('auth_token');
      if (tokenJson != null) {
        final token = AuthToken.fromJson(jsonDecode(tokenJson));
        if (token.expiresAt.isAfter(DateTime.now())) {
          _sdk!.authManager.currentToken = token;
          _isAuthenticated = true;
        }
      }

      _isInitialized = true;
      _error = null;
      notifyListeners();

    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<AuthToken> authenticate(String username, String password) async {
    try {
      final token = await _sdk!.authenticate(
        username: username,
        password: password,
      );

      // Store token
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', jsonEncode(token.toJson()));

      _isAuthenticated = true;
      _error = null;
      notifyListeners();

      return token;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      await _sdk!.logout();

      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('auth_token');

      _isAuthenticated = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }
}

// Main App with Provider
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => SDKService()..initialize(),
      child: MaterialApp(
        title: 'ITDO ERP Mobile',
        home: Consumer<SDKService>(
          builder: (context, sdkService, child) {
            if (!sdkService.isInitialized) {
              return const SplashScreen();
            }

            if (sdkService.error != null) {
              return ErrorScreen(error: sdkService.error!);
            }

            return sdkService.isAuthenticated
                ? const MainScreen()
                : const LoginScreen();
          },
        ),
      ),
    );
  }
}

// Login Screen
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final sdkService = Provider.of<SDKService>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(labelText: 'Username'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : () => _handleLogin(sdkService),
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('Login'),
            ),
            if (sdkService.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Text(
                  sdkService.error!,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogin(SDKService sdkService) async {
    setState(() => _isLoading = true);

    try {
      await sdkService.authenticate(
        _usernameController.text,
        _passwordController.text,
      );
    } catch (e) {
      // Error handled by SDKService
    } finally {
      setState(() => _isLoading = false);
    }
  }
}
""",
            prerequisites=[
                "Flutter 3.0+",
                "provider package",
                "device_info_plus package",
                "shared_preferences package",
            ],
            tags=["integration", "flutter", "state-management"],
        )

        return DocumentationSection(
            section_id="integration_examples",
            title="Platform Integration Examples",
            content="""
# Platform Integration Examples

Complete integration examples for popular mobile development frameworks.

## React Native

React Native integration with context providers and AsyncStorage for token persistence.

## Flutter

Flutter integration with Provider state management and SharedPreferences.

## Native iOS

Native iOS integration with Swift and proper Keychain storage.

## Native Android

Native Android integration with Kotlin and Android Keystore.

## Best Practices

- Use proper state management patterns
- Store tokens securely (Keychain/Keystore)
- Handle network errors gracefully
- Implement proper loading states
- Follow platform UI guidelines
""",
            code_samples=[react_native_sample, flutter_sample],
            order=5,
        )

    def generate_troubleshooting_guide(self) -> DocumentationSection:
        """Generate troubleshooting guide."""
        return DocumentationSection(
            section_id="troubleshooting",
            title="Troubleshooting Guide",
            content="""
# Troubleshooting Guide

Common issues and solutions when using the ITDO ERP Mobile SDK.

## Authentication Issues

### "Invalid credentials" Error
**Problem**: Authentication fails with invalid credentials error.

**Solutions**:
1. Verify username/email and password are correct
2. Check if account is locked or disabled
3. Ensure organization_id and app_id are correct
4. Check if MFA is required but not provided

### "Network timeout" During Authentication
**Problem**: Authentication requests timeout.

**Solutions**:
1. Check network connectivity
2. Verify API base URL is correct
3. Check if firewall is blocking requests
4. Increase timeout in SDK configuration

### Token Refresh Failures
**Problem**: Automatic token refresh fails.

**Solutions**:
1. Ensure refresh token is stored correctly
2. Check token expiration times
3. Verify refresh endpoint is accessible
4. Handle refresh failures with re-authentication

## Data Synchronization Issues

### Sync Fails to Start
**Problem**: Data synchronization doesn't initiate.

**Solutions**:
1. Verify user is authenticated
2. Check network connectivity
3. Ensure sufficient local storage space
4. Check sync permissions for user role

### Slow Sync Performance
**Problem**: Data synchronization is very slow.

**Solutions**:
1. Reduce sync batch size
2. Use incremental sync instead of full sync
3. Sync during off-peak hours
4. Optimize network connection

### Sync Conflicts
**Problem**: Data conflicts during synchronization.

**Solutions**:
1. Configure appropriate conflict resolution strategy
2. Implement manual conflict resolution UI
3. Provide clear conflict information to users
4. Consider last-write-wins for simple cases

## Biometric Authentication Issues

### Biometric Hardware Not Detected
**Problem**: SDK cannot detect biometric hardware.

**Solutions**:
1. Verify device has biometric sensors
2. Check app permissions for biometric access
3. Ensure user has enrolled biometrics on device
4. Fall back to credential authentication

### Low Biometric Quality Scores
**Problem**: Biometric authentication fails due to low quality.

**Solutions**:
1. Improve lighting conditions
2. Clean biometric sensors
3. Guide users on proper biometric positioning
4. Adjust quality thresholds if appropriate

## Network and Connectivity Issues

### SSL Certificate Errors
**Problem**: HTTPS requests fail with certificate errors.

**Solutions**:
1. Verify API server SSL certificate is valid
2. Check certificate pinning configuration
3. Update app if certificates have changed
4. Disable certificate pinning for testing (not production)

### API Rate Limiting
**Problem**: Requests fail with rate limit errors.

**Solutions**:
1. Implement exponential backoff retry logic
2. Cache responses to reduce API calls
3. Optimize API usage patterns
4. Contact support to increase rate limits

## Platform-Specific Issues

### iOS

#### App Transport Security (ATS) Issues
- Configure ATS exceptions in Info.plist
- Use HTTPS for all API endpoints
- Implement certificate pinning properly

#### Keychain Access Issues
- Check app entitlements for keychain access
- Handle keychain errors gracefully
- Use proper keychain sharing groups

### Android

#### Network Security Config Issues
- Configure network_security_config.xml properly
- Allow cleartext traffic for development only
- Implement certificate pinning correctly

#### Keystore Issues
- Handle keystore hardware availability
- Implement software fallback for keystore
- Check keystore authentication requirements

## Debugging Tips

### Enable Debug Logging
```javascript
const config = new SDKConfig({
  // ... other config
  logLevel: 'DEBUG',
  logRequests: true,
  logResponses: true
});
```

### Monitor Network Traffic
- Use network monitoring tools (Charles, Wireshark)
- Check request/response headers and bodies
- Verify API endpoints and parameters

### Check Local Storage
- Inspect stored tokens and cached data
- Verify database schema and migrations
- Check storage permissions and space

### Review Error Logs
- Enable detailed error reporting
- Check both client and server logs
- Look for patterns in error timing/frequency

## Getting Help

### Documentation Resources
- API Reference: Complete endpoint documentation
- Code Samples: Working examples for all platforms
- Integration Guides: Platform-specific setup instructions

### Support Channels
- GitHub Issues: Report bugs and feature requests
- Developer Portal: Access documentation and tools
- Email Support: Direct technical support
- Community Forum: Connect with other developers

### Diagnostic Information to Include

When reporting issues, please include:

1. **SDK Version**: Which version of the SDK you're using
2. **Platform**: iOS, Android, React Native, Flutter, etc.
3. **Device Info**: Device model, OS version, app version
4. **Error Messages**: Complete error messages and stack traces
5. **Reproduction Steps**: Clear steps to reproduce the issue
6. **Network Conditions**: Online/offline, connection type
7. **Configuration**: Relevant SDK configuration (without sensitive data)

### Sample Bug Report

```
**SDK Version**: 1.0.0
**Platform**: iOS 17.0 (iPhone 15 Pro)
**App Version**: 2.1.0

**Issue**: Biometric authentication fails with quality score error

**Steps to Reproduce**:
1. Initialize SDK with biometric authentication enabled
2. Attempt Face ID authentication
3. Authentication fails with "Low quality score" error

**Error Message**:
```
BiometricAuthenticationError: Quality score 0.65 below threshold 0.75
```

**Expected Behavior**: Authentication should succeed with good lighting

**Additional Context**: Issue occurs in bright lighting conditions
```
""",
            order=6,
        )

    def generate_changelog(self) -> DocumentationSection:
        """Generate changelog."""
        return DocumentationSection(
            section_id="changelog",
            title="Changelog",
            content="""
# Changelog

All notable changes to the ITDO ERP Mobile SDK will be documented here.

## [Unreleased]

### Added
- Performance optimization framework
- Enhanced error handling and reporting
- Improved offline synchronization

### Changed
- Updated authentication flow for better security
- Optimized network request caching

### Fixed
- Memory leaks in data synchronization
- Token refresh race conditions

## [1.0.0] - 2024-01-15

### Added
- 🎉 **Initial release of ITDO ERP Mobile SDK**
- Complete authentication system with multiple methods
- Biometric authentication (Face ID, Touch ID, Fingerprint)
- Multi-factor authentication (TOTP, SMS, Email)
- Device trust and fingerprinting
- Offline-first data synchronization
- Comprehensive analytics and monitoring
- UI component library for all platforms
- Testing framework with mocking capabilities
- Complete documentation and code samples

### Authentication Features
- Username/password authentication
- Biometric authentication with liveness detection
- Multi-factor authentication (MFA) support
- Automatic token refresh and management
- Device registration and trust scoring
- Security event logging and monitoring

### Data Synchronization
- Offline-first architecture
- Automatic background synchronization
- Conflict resolution strategies
- SQLite local storage with encryption
- Incremental and full sync modes
- Progress monitoring and reporting

### Platform Support
- Native iOS (Swift)
- Native Android (Kotlin)
- React Native (JavaScript/TypeScript)
- Flutter (Dart)
- Web (JavaScript/TypeScript)

### Security Features
- End-to-end encryption for sensitive data
- Certificate pinning for API communications
- Secure token storage (Keychain/Keystore)
- Device fingerprinting and risk assessment
- Comprehensive audit logging

### Developer Experience
- Complete API documentation
- Interactive code samples
- Testing framework with mocks
- Performance benchmarking tools
- Comprehensive error handling
- Debug logging and monitoring

### Breaking Changes
- None (initial release)

### Migration Guide
- None (initial release)

## Version Support

| Version | Status | Support End |
|---------|--------|-------------|
| 1.0.x   | Active | TBD |

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new backwards-compatible functionality
- **PATCH** version for backwards-compatible bug fixes

## Support Policy

- **Latest Version**: Full support with new features and bug fixes
- **Previous Major**: Security fixes and critical bug fixes only
- **End of Life**: No support, users encouraged to upgrade

## Upgrade Guide

### From Pre-release to 1.0.0

This is the initial stable release. No migration required.

### Future Upgrades

Detailed upgrade guides will be provided for each major version release.
""",
            order=7,
        )

    def add_section(self, section: DocumentationSection) -> None:
        """Add documentation section."""
        self.sections[section.section_id] = section

    def generate_all_documentation(self) -> Dict[str, DocumentationSection]:
        """Generate complete documentation suite."""
        # Generate all sections
        self.add_section(self.generate_quick_start_guide())
        self.add_section(self.generate_authentication_guide())
        self.add_section(self.generate_data_sync_guide())
        self.add_section(self.generate_api_reference())
        self.add_section(self.generate_integration_examples())
        self.add_section(self.generate_troubleshooting_guide())
        self.add_section(self.generate_changelog())

        return self.sections

    def export_to_files(self) -> Dict[str, str]:
        """Export documentation to files."""
        generated_files = {}

        for section_id, section in self.sections.items():
            # Create markdown file for each section
            filename = f"{section_id}.md"
            filepath = self.output_dir / filename

            # Write section content
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {section.title}\n\n")
                f.write(section.content)

                # Add code samples
                for sample in section.code_samples:
                    f.write(f"\n\n## {sample.title}\n\n")
                    f.write(f"{sample.description}\n\n")

                    if sample.prerequisites:
                        f.write("**Prerequisites:**\n")
                        for prereq in sample.prerequisites:
                            f.write(f"- {prereq}\n")
                        f.write("\n")

                    if sample.imports:
                        f.write("**Imports:**\n")
                        f.write("```" + sample.language + "\n")
                        for imp in sample.imports:
                            f.write(f"{imp}\n")
                        f.write("```\n\n")

                    f.write("**Code:**\n")
                    f.write("```" + sample.language + "\n")
                    f.write(sample.code)
                    f.write("\n```\n")

                    if sample.notes:
                        f.write("\n**Notes:**\n")
                        for note in sample.notes:
                            f.write(f"- {note}\n")

            generated_files[filename] = str(filepath)

        # Generate main README
        readme_path = self.output_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# ITDO ERP Mobile SDK Documentation\n\n")
            f.write("Complete documentation for the ITDO ERP Mobile SDK.\n\n")
            f.write("## Table of Contents\n\n")

            # Sort sections by order
            sorted_sections = sorted(self.sections.values(), key=lambda x: x.order)
            for section in sorted_sections:
                f.write(f"- [{section.title}]({section.section_id}.md)\n")

            f.write(f"\n---\n\nGenerated on {datetime.now().isoformat()}\n")

        generated_files["README.md"] = str(readme_path)

        # Generate JSON API reference
        api_json_path = self.output_dir / "api_reference.json"
        with open(api_json_path, "w", encoding="utf-8") as f:
            api_data = {
                "version": "1.0.0",
                "title": "ITDO ERP Mobile SDK API",
                "description": "Complete API reference for ITDO ERP Mobile SDK",
                "base_url": "https://api.your-organization.com/api/v1",
                "endpoints": [endpoint.dict() for endpoint in self.api_endpoints],
                "generated_at": datetime.now().isoformat(),
            }
            json.dump(api_data, f, indent=2)

        generated_files["api_reference.json"] = str(api_json_path)

        return generated_files

    def generate_sample_project(self, platform: PlatformType) -> Dict[str, str]:
        """Generate complete sample project for platform."""
        sample_files = {}

        if platform == PlatformType.REACT_NATIVE:
            # Package.json
            package_json = {
                "name": "itdo-erp-mobile-sample",
                "version": "1.0.0",
                "private": True,
                "scripts": {
                    "android": "react-native run-android",
                    "ios": "react-native run-ios",
                    "start": "react-native start",
                },
                "dependencies": {
                    "react": "18.2.0",
                    "react-native": "0.72.0",
                    "@itdo/erp-mobile-sdk": "^1.0.0",
                    "@react-native-async-storage/async-storage": "^1.19.0",
                    "react-native-device-info": "^10.9.0",
                },
            }
            sample_files["package.json"] = json.dumps(package_json, indent=2)

        elif platform == PlatformType.FLUTTER:
            # pubspec.yaml
            pubspec_yaml = """
name: itdo_erp_mobile_sample
description: Sample Flutter app with ITDO ERP SDK
version: 1.0.0+1

environment:
  sdk: '>=2.19.0 <4.0.0'
  flutter: ">=3.0.0"

dependencies:
  flutter:
    sdk: flutter
  itdo_erp_mobile_sdk: ^1.0.0
  provider: ^6.0.5
  device_info_plus: ^9.1.0
  shared_preferences: ^2.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""
            sample_files["pubspec.yaml"] = pubspec_yaml.strip()

        return sample_files
