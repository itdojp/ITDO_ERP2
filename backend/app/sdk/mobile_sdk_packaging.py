"""Mobile SDK Packaging & Distribution System - CC02 v72.0 Day 17."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PackageMetadata(BaseModel):
    """Package metadata information."""
    name: str
    version: str
    description: str
    author: str = "ITDO Development Team"
    license: str = "MIT"
    homepage: str = "https://github.com/itdo-io/erp-mobile-sdk"
    repository: str = "https://github.com/itdo-io/erp-mobile-sdk.git"
    
    keywords: List[str] = Field(default_factory=lambda: ["erp", "mobile", "sdk", "itdo"])
    platforms: List[str] = Field(default_factory=lambda: ["ios", "android", "react-native", "flutter"])
    
    dependencies: Dict[str, str] = Field(default_factory=dict)
    dev_dependencies: Dict[str, str] = Field(default_factory=dict)
    
    min_versions: Dict[str, str] = Field(default_factory=lambda: {
        "ios": "13.0",
        "android": "21",
        "react_native": "0.66.0",
        "flutter": "3.0.0"
    })


class BuildConfiguration(BaseModel):
    """Build configuration settings."""
    build_type: str = "release"  # debug, release
    target_platforms: List[str] = Field(default_factory=lambda: ["ios", "android", "react-native", "flutter"])
    optimization_level: str = "O2"
    include_debug_symbols: bool = False
    minify_code: bool = True
    enable_tree_shaking: bool = True
    
    # Output settings
    output_directory: str = "dist"
    package_formats: List[str] = Field(default_factory=lambda: ["tar.gz", "zip"])
    
    # Code signing
    code_signing_enabled: bool = False
    signing_certificate: Optional[str] = None
    signing_key: Optional[str] = None


class DistributionConfig(BaseModel):
    """Distribution configuration."""
    # Package registries
    npm_registry: str = "https://registry.npmjs.org"
    cocoapods_specs_repo: str = "https://github.com/CocoaPods/Specs.git"
    maven_repository: str = "https://repo1.maven.org/maven2"
    pub_dev_registry: str = "https://pub.dev"
    
    # Authentication
    npm_token: Optional[str] = None
    cocoapods_trunk_token: Optional[str] = None
    maven_credentials: Optional[Dict[str, str]] = None
    pub_dev_credentials: Optional[Dict[str, str]] = None
    
    # Release settings
    auto_publish: bool = False
    pre_release: bool = False
    release_notes: Optional[str] = None


class PackageBuilder:
    """Multi-platform package builder."""
    
    def __init__(self, metadata: PackageMetadata, build_config: BuildConfiguration) -> dict:
        self.metadata = metadata
        self.build_config = build_config
        self.build_artifacts: Dict[str, List[str]] = {}
        
        # Source paths
        self.source_root = Path("app/sdk")
        self.templates_dir = Path("templates/sdk")
        self.output_dir = Path(build_config.output_directory)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def build_all_packages(self) -> Dict[str, Any]:
        """Build packages for all target platforms."""
        build_results = {
            "build_id": f"build_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": self.metadata.dict(),
            "configuration": self.build_config.dict(),
            "platforms": {},
            "artifacts": [],
            "errors": [],
        }
        
        for platform in self.build_config.target_platforms:
            print(f"[Package Builder] Building {platform} package...")
            
            try:
                platform_result = await self._build_platform_package(platform)
                build_results["platforms"][platform] = platform_result
                
                if platform_result["success"]:
                    build_results["artifacts"].extend(platform_result["artifacts"])
                else:
                    build_results["errors"].extend(platform_result["errors"])
                    
            except Exception as e:
                error_msg = f"Failed to build {platform} package: {str(e)}"
                build_results["errors"].append(error_msg)
                print(f"[Package Builder] {error_msg}")
        
        # Generate build summary
        build_results["summary"] = {
            "total_platforms": len(self.build_config.target_platforms),
            "successful_builds": len([p for p in build_results["platforms"].values() if p["success"]]),
            "failed_builds": len([p for p in build_results["platforms"].values() if not p["success"]]),
            "total_artifacts": len(build_results["artifacts"]),
        }
        
        return build_results
    
    async def _build_platform_package(self, platform: str) -> Dict[str, Any]:
        """Build package for specific platform."""
        platform_result = {
            "platform": platform,
            "success": False,
            "artifacts": [],
            "errors": [],
            "build_time_ms": 0,
        }
        
        start_time = datetime.now()
        
        try:
            if platform == "ios":
                await self._build_ios_package(platform_result)
            elif platform == "android":
                await self._build_android_package(platform_result)
            elif platform == "react-native":
                await self._build_react_native_package(platform_result)
            elif platform == "flutter":
                await self._build_flutter_package(platform_result)
            else:
                platform_result["errors"].append(f"Unsupported platform: {platform}")
                return platform_result
            
            platform_result["success"] = len(platform_result["errors"]) == 0
            
        except Exception as e:
            platform_result["errors"].append(str(e))
        
        finally:
            end_time = datetime.now()
            platform_result["build_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        return platform_result
    
    async def _build_ios_package(self, result: Dict[str, Any]) -> None:
        """Build iOS Swift package."""
        platform_dir = self.output_dir / "ios"
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Package.swift
        package_swift_content = f'''
// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "{self.metadata.name}",
    platforms: [
        .iOS(.v{self.metadata.min_versions["ios"].replace(".", "_")})
    ],
    products: [
        .library(
            name: "{self.metadata.name}",
            targets: ["{self.metadata.name}"])
    ],
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.6.0"),
        .package(url: "https://github.com/apple/swift-crypto.git", from: "2.0.0"),
        .package(url: "https://github.com/realm/realm-swift.git", from: "10.40.0")
    ],
    targets: [
        .target(
            name: "{self.metadata.name}",
            dependencies: [
                "Alamofire",
                .product(name: "Crypto", package: "swift-crypto"),
                .product(name: "RealmSwift", package: "realm-swift")
            ],
            path: "Sources"
        ),
        .testTarget(
            name: "{self.metadata.name}Tests",
            dependencies: ["{self.metadata.name}"],
            path: "Tests"
        )
    ]
)
'''
        
        package_swift_file = platform_dir / "Package.swift"
        with open(package_swift_file, 'w') as f:
            f.write(package_swift_content.strip())
        
        # Generate iOS source files
        sources_dir = platform_dir / "Sources" / self.metadata.name
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        # Main SDK file
        main_swift_content = f'''
import Foundation
import Alamofire
import Crypto
import RealmSwift

/// ITDO ERP Mobile SDK for iOS
/// Version: {self.metadata.version}
public class ITDOERPMobileSDK {{
    
    public let version = "{self.metadata.version}"
    private let config: SDKConfig
    private let httpClient: HTTPClient
    private let authManager: AuthManager
    
    public init(config: SDKConfig) {{
        self.config = config
        self.httpClient = HTTPClient(config: config)
        self.authManager = AuthManager(config: config, httpClient: httpClient)
    }}
    
    public func initialize(deviceInfo: DeviceInfo) async throws {{
        try await httpClient.initialize()
        authManager.setDeviceInfo(deviceInfo)
    }}
    
    public func authenticate(username: String, password: String) async throws -> AuthToken {{
        return try await authManager.authenticateWithCredentials(
            username: username,
            password: password
        )
    }}
    
    public func authenticateBiometric(deviceId: String, biometricData: [String: Any]) async throws -> AuthToken {{
        return try await authManager.authenticateWithBiometric(
            deviceId: deviceId,
            biometricData: biometricData
        )
    }}
    
    public func logout() async throws {{
        try await authManager.logout()
    }}
    
    public var isAuthenticated: Bool {{
        return authManager.isAuthenticated()
    }}
}}

/// SDK Configuration
public struct SDKConfig {{
    public let apiBaseUrl: String
    public let organizationId: String
    public let appId: String
    public let apiKey: String
    public let timeoutSeconds: Int
    public let maxRetries: Int
    
    public init(
        apiBaseUrl: String,
        organizationId: String,
        appId: String,
        apiKey: String,
        timeoutSeconds: Int = 30,
        maxRetries: Int = 3
    ) {{
        self.apiBaseUrl = apiBaseUrl
        self.organizationId = organizationId
        self.appId = appId
        self.apiKey = apiKey
        self.timeoutSeconds = timeoutSeconds
        self.maxRetries = maxRetries
    }}
}}

/// Device Information
public struct DeviceInfo {{
    public let deviceId: String
    public let platform: String
    public let osVersion: String
    public let appVersion: String
    public let deviceModel: String
    public let screenResolution: String
    public let timezone: String
    public let locale: String
    
    public init(
        deviceId: String,
        platform: String = "ios",
        osVersion: String,
        appVersion: String,
        deviceModel: String,
        screenResolution: String,
        timezone: String,
        locale: String
    ) {{
        self.deviceId = deviceId
        self.platform = platform
        self.osVersion = osVersion
        self.appVersion = appVersion
        self.deviceModel = deviceModel
        self.screenResolution = screenResolution
        self.timezone = timezone
        self.locale = locale
    }}
}}

/// Authentication Token
public struct AuthToken {{
    public let accessToken: String
    public let refreshToken: String?
    public let tokenType: String
    public let expiresAt: Date
    public let scope: [String]
    
    public init(
        accessToken: String,
        refreshToken: String? = nil,
        tokenType: String = "Bearer",
        expiresAt: Date,
        scope: [String] = []
    ) {{
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.tokenType = tokenType
        self.expiresAt = expiresAt
        self.scope = scope
    }}
}}
'''
        
        main_swift_file = sources_dir / "ITDOERPMobileSDK.swift"
        with open(main_swift_file, 'w') as f:
            f.write(main_swift_content.strip())
        
        # Generate CocoaPods spec
        podspec_content = f'''
Pod::Spec.new do |spec|
  spec.name                  = "{self.metadata.name}"
  spec.version               = "{self.metadata.version}"
  spec.summary               = "{self.metadata.description}"
  spec.description           = <<-DESC
    {self.metadata.description}
    
    Complete mobile SDK for ITDO ERP system with:
    - Authentication (credentials, biometric, MFA)
    - Data synchronization and offline support
    - Analytics and performance monitoring
    - UI components and widgets
    DESC
  
  spec.homepage              = "{self.metadata.homepage}"
  spec.license               = {{ :type => "{self.metadata.license}" }}
  spec.author                = {{ "ITDO Team" => "sdk@itdo.io" }}
  spec.source                = {{ :git => "{self.metadata.repository}", :tag => "#{{{spec.version}}}}" }}
  
  spec.ios.deployment_target = "{self.metadata.min_versions["ios"]}"
  spec.swift_version         = "5.7"
  
  spec.source_files          = "Sources/**/*.swift"
  spec.frameworks            = "Foundation", "Security", "LocalAuthentication"
  
  spec.dependency "Alamofire", "~> 5.6"
  spec.dependency "RealmSwift", "~> 10.40"
  
  spec.test_spec "Tests" do |test_spec|
    test_spec.source_files = "Tests/**/*.swift"
  end
end
'''
        
        podspec_file = platform_dir / f"{self.metadata.name}.podspec"
        with open(podspec_file, 'w') as f:
            f.write(podspec_content.strip())
        
        # Create archive
        ios_archive = await self._create_archive(platform_dir, f"{self.metadata.name}-ios-{self.metadata.version}")
        result["artifacts"].append(str(ios_archive))
    
    async def _build_android_package(self, result: Dict[str, Any]) -> None:
        """Build Android package."""
        platform_dir = self.output_dir / "android"
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate build.gradle
        build_gradle_content = f'''
apply plugin: 'com.android.library'
apply plugin: 'kotlin-android'
apply plugin: 'maven-publish'

android {{
    compileSdkVersion 33
    
    defaultConfig {{
        minSdkVersion {self.metadata.min_versions["android"]}
        targetSdkVersion 33
        versionCode 1
        versionName "{self.metadata.version}"
        
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }}
    
    buildTypes {{
        release {{
            minifyEnabled {str(self.build_config.minify_code).lower()}
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
    
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
    
    kotlinOptions {{
        jvmTarget = '1.8'
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.10.1'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.1'
    implementation 'androidx.room:room-runtime:2.5.0'
    implementation 'androidx.room:room-ktx:2.5.0'
    implementation 'androidx.biometric:biometric:1.1.0'
    
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}}

publishing {{
    publications {{
        release(MavenPublication) {{
            from components.release
            groupId = 'com.itdo.erp'
            artifactId = '{self.metadata.name.lower()}'
            version = '{self.metadata.version}'
        }}
    }}
}}
'''
        
        build_gradle_file = platform_dir / "build.gradle"
        with open(build_gradle_file, 'w') as f:
            f.write(build_gradle_content.strip())
        
        # Generate main SDK class
        src_dir = platform_dir / "src" / "main" / "java" / "com" / "itdo" / "erp" / "sdk"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        main_kotlin_content = f'''
package com.itdo.erp.sdk

import android.content.Context
import kotlinx.coroutines.*
import okhttp3.*
import retrofit2.*
import retrofit2.converter.gson.GsonConverterFactory

/**
 * ITDO ERP Mobile SDK for Android
 * Version: {self.metadata.version}
 */
class ITDOERPMobileSDK(private val config: SDKConfig) {{
    
    companion object {{
        const val VERSION = "{self.metadata.version}"
    }}
    
    private val httpClient: OkHttpClient
    private val retrofit: Retrofit
    private val authManager: AuthManager
    
    init {{
        httpClient = OkHttpClient.Builder()
            .connectTimeout(config.timeoutSeconds.toLong(), java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(config.timeoutSeconds.toLong(), java.util.concurrent.TimeUnit.SECONDS)
            .build()
        
        retrofit = Retrofit.Builder()
            .baseUrl(config.apiBaseUrl)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        authManager = AuthManager(config, retrofit)
    }}
    
    suspend fun initialize(context: Context, deviceInfo: DeviceInfo) {{
        authManager.setDeviceInfo(deviceInfo)
    }}
    
    suspend fun authenticate(username: String, password: String): AuthToken {{
        return authManager.authenticateWithCredentials(username, password)
    }}
    
    suspend fun authenticateBiometric(
        context: Context,
        deviceId: String,
        biometricData: Map<String, Any>
    ): AuthToken {{
        return authManager.authenticateWithBiometric(context, deviceId, biometricData)
    }}
    
    suspend fun logout() {{
        authManager.logout()
    }}
    
    val isAuthenticated: Boolean
        get() = authManager.isAuthenticated()
}}

/**
 * SDK Configuration
 */
data class SDKConfig(
    val apiBaseUrl: String,
    val organizationId: String,
    val appId: String,
    val apiKey: String,
    val timeoutSeconds: Int = 30,
    val maxRetries: Int = 3
)

/**
 * Device Information
 */
data class DeviceInfo(
    val deviceId: String,
    val platform: String = "android",
    val osVersion: String,
    val appVersion: String,
    val deviceModel: String,
    val screenResolution: String,
    val timezone: String,
    val locale: String
)

/**
 * Authentication Token
 */
data class AuthToken(
    val accessToken: String,
    val refreshToken: String? = null,
    val tokenType: String = "Bearer",
    val expiresAt: Long,
    val scope: List<String> = emptyList()
)
'''
        
        main_kotlin_file = src_dir / "ITDOERPMobileSDK.kt"
        with open(main_kotlin_file, 'w') as f:
            f.write(main_kotlin_content.strip())
        
        # Generate AndroidManifest.xml
        manifest_dir = platform_dir / "src" / "main"
        manifest_content = f'''
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.itdo.erp.sdk">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />
    <uses-permission android:name="android.permission.USE_FINGERPRINT" />
    
</manifest>
'''
        
        manifest_file = manifest_dir / "AndroidManifest.xml"
        with open(manifest_file, 'w') as f:
            f.write(manifest_content.strip())
        
        # Create archive
        android_archive = await self._create_archive(platform_dir, f"{self.metadata.name}-android-{self.metadata.version}")
        result["artifacts"].append(str(android_archive))
    
    async def _build_react_native_package(self, result: Dict[str, Any]) -> None:
        """Build React Native package."""
        platform_dir = self.output_dir / "react-native"
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate package.json
        package_json = {
            "name": f"@itdo/{self.metadata.name.lower().replace('_', '-')}",
            "version": self.metadata.version,
            "description": self.metadata.description,
            "main": "lib/index.js",
            "types": "lib/index.d.ts",
            "scripts": {
                "build": "tsc",
                "prepare": "npm run build",
                "test": "jest"
            },
            "keywords": self.metadata.keywords,
            "author": self.metadata.author,
            "license": self.metadata.license,
            "homepage": self.metadata.homepage,
            "repository": {
                "type": "git",
                "url": self.metadata.repository
            },
            "peerDependencies": {
                "react": ">=16.8.0",
                "react-native": ">=0.66.0"
            },
            "dependencies": {
                "@react-native-async-storage/async-storage": "^1.19.0",
                "react-native-device-info": "^10.9.0",
                "react-native-keychain": "^8.1.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-native": "^0.72.0",
                "typescript": "^5.1.0",
                "jest": "^29.0.0",
                "@testing-library/react-native": "^12.0.0"
            },
            "engines": {
                "node": ">=16.0.0"
            }
        }
        
        package_json_file = platform_dir / "package.json"
        with open(package_json_file, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Generate TypeScript source
        src_dir = platform_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        index_ts_content = f'''
/**
 * ITDO ERP Mobile SDK for React Native
 * Version: {self.metadata.version}
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';
import * as Keychain from 'react-native-keychain';

export interface SDKConfig {{
  apiBaseUrl: string;
  organizationId: string;
  appId: string;
  apiKey: string;
  timeoutSeconds?: number;
  maxRetries?: number;
}}

export interface DeviceInfo {{
  deviceId: string;
  platform: string;
  osVersion: string;
  appVersion: string;
  deviceModel: string;
  screenResolution: string;
  timezone: string;
  locale: string;
}}

export interface AuthToken {{
  accessToken: string;
  refreshToken?: string;
  tokenType: string;
  expiresAt: Date;
  scope: string[];
}}

export class ITDOERPMobileSDK {{
  public static readonly VERSION = '{self.metadata.version}';
  
  private config: SDKConfig;
  private authToken: AuthToken | null = null;
  
  constructor(config: SDKConfig) {{
    this.config = {{
      timeoutSeconds: 30,
      maxRetries: 3,
      ...config
    }};
  }}
  
  async initialize(deviceInfo?: Partial<DeviceInfo>): Promise<void> {{
    const fullDeviceInfo: DeviceInfo = {{
      deviceId: await DeviceInfo.getUniqueId(),
      platform: 'react_native',
      osVersion: await DeviceInfo.getSystemVersion(),
      appVersion: await DeviceInfo.getVersion(),
      deviceModel: await DeviceInfo.getModel(),
      screenResolution: `${{await DeviceInfo.getScreenWidth()}}x${{await DeviceInfo.getScreenHeight()}}`,
      timezone: await DeviceInfo.getTimezone(),
      locale: await DeviceInfo.getLocale(),
      ...deviceInfo
    }};
    
    // Check for stored auth token
    try {{
      const storedToken = await AsyncStorage.getItem('itdo_auth_token');
      if (storedToken) {{
        const token = JSON.parse(storedToken);
        if (new Date(token.expiresAt) > new Date()) {{
          this.authToken = token;
        }}
      }}
    }} catch (error) {{
      console.warn('Failed to load stored auth token:', error);
    }}
  }}
  
  async authenticate(username: string, password: string): Promise<AuthToken> {{
    const response = await this.makeRequest('POST', 'auth/token', {{
      grant_type: 'password',
      username,
      password,
      organization_id: this.config.organizationId,
      app_id: this.config.appId
    }});
    
    if (response.status !== 200) {{
      throw new Error('Authentication failed');
    }}
    
    const tokenData = response.data;
    const token: AuthToken = {{
      accessToken: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      tokenType: tokenData.token_type || 'Bearer',
      expiresAt: new Date(tokenData.expires_at),
      scope: tokenData.scope || []
    }};
    
    this.authToken = token;
    
    // Store token securely
    try {{
      await AsyncStorage.setItem('itdo_auth_token', JSON.stringify(token));
      await Keychain.setInternetCredentials(
        'itdo_erp_sdk',
        username,
        token.accessToken
      );
    }} catch (error) {{
      console.warn('Failed to store auth token:', error);
    }}
    
    return token;
  }}
  
  async logout(): Promise<void> {{
    if (this.authToken) {{
      try {{
        await this.makeRequest('POST', 'auth/logout', {{
          token: this.authToken.accessToken
        }});
      }} catch (error) {{
        console.warn('Logout request failed:', error);
      }}
    }}
    
    this.authToken = null;
    
    // Clear stored tokens
    try {{
      await AsyncStorage.removeItem('itdo_auth_token');
      await Keychain.resetInternetCredentials('itdo_erp_sdk');
    }} catch (error) {{
      console.warn('Failed to clear stored tokens:', error);
    }}
  }}
  
  get isAuthenticated(): boolean {{
    return this.authToken !== null && new Date() < this.authToken.expiresAt;
  }}
  
  private async makeRequest(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<any> {{
    const url = `${{this.config.apiBaseUrl}}/api/v1/${{endpoint}}`;
    const headers: Record<string, string> = {{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': `ITDO-ERP-SDK-RN/{self.metadata.version}`
    }};
    
    if (this.authToken) {{
      headers.Authorization = `${{this.authToken.tokenType}} ${{this.authToken.accessToken}}`;
    }}
    
    const requestOptions: RequestInit = {{
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined
    }};
    
    const response = await fetch(url, requestOptions);
    const responseData = await response.json();
    
    return {{
      status: response.status,
      data: responseData,
      headers: response.headers
    }};
  }}
}}

export default ITDOERPMobileSDK;
'''
        
        index_ts_file = src_dir / "index.ts"
        with open(index_ts_file, 'w') as f:
            f.write(index_ts_content.strip())
        
        # Generate TypeScript config
        tsconfig_json = {
            "compilerOptions": {
                "target": "es2018",
                "module": "commonjs",
                "lib": ["es2018"],
                "declaration": True,
                "outDir": "./lib",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "resolveJsonModule": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "lib", "**/*.test.ts"]
        }
        
        tsconfig_file = platform_dir / "tsconfig.json"
        with open(tsconfig_file, 'w') as f:
            json.dump(tsconfig_json, f, indent=2)
        
        # Create archive
        rn_archive = await self._create_archive(platform_dir, f"{self.metadata.name}-react-native-{self.metadata.version}")
        result["artifacts"].append(str(rn_archive))
    
    async def _build_flutter_package(self, result: Dict[str, Any]) -> None:
        """Build Flutter package."""
        platform_dir = self.output_dir / "flutter"
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate pubspec.yaml
        pubspec_yaml = f'''
name: {self.metadata.name.lower()}
description: {self.metadata.description}
version: {self.metadata.version}
homepage: {self.metadata.homepage}
repository: {self.metadata.repository}

environment:
  sdk: '>={self.metadata.min_versions["flutter"]} <4.0.0'
  flutter: ">=3.0.0"

dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.0
  device_info_plus: ^9.1.0
  crypto: ^3.0.3
  local_auth: ^2.1.6

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  plugin:
    platforms:
      android:
        package: com.itdo.erp.sdk
        pluginClass: ITDOERPMobileSDKPlugin
      ios:
        pluginClass: ITDOERPMobileSDKPlugin
'''
        
        pubspec_file = platform_dir / "pubspec.yaml"
        with open(pubspec_file, 'w') as f:
            f.write(pubspec_yaml.strip())
        
        # Generate main Dart file
        lib_dir = platform_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        
        main_dart_content = f'''
/// ITDO ERP Mobile SDK for Flutter
/// Version: {self.metadata.version}
library {self.metadata.name.lower()};

import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:local_auth/local_auth.dart';

export 'src/sdk_config.dart';
export 'src/device_info.dart';
export 'src/auth_token.dart';

/// Main SDK class
class ITDOERPMobileSDK {{
  static const String version = '{self.metadata.version}';
  
  final SDKConfig _config;
  AuthToken? _authToken;
  
  ITDOERPMobileSDK(this._config);
  
  /// Initialize the SDK
  Future<void> initialize([DeviceInfo? deviceInfo]) async {{
    deviceInfo ??= await _getDeviceInfo();
    
    // Check for stored auth token
    final prefs = await SharedPreferences.getInstance();
    final tokenJson = prefs.getString('itdo_auth_token');
    if (tokenJson != null) {{
      try {{
        final tokenData = jsonDecode(tokenJson);
        final token = AuthToken.fromJson(tokenData);
        if (token.expiresAt.isAfter(DateTime.now())) {{
          _authToken = token;
        }}
      }} catch (e) {{
        debugPrint('Failed to load stored auth token: $e');
      }}
    }}
  }}
  
  /// Authenticate with username and password
  Future<AuthToken> authenticate(String username, String password) async {{
    final response = await _makeRequest('POST', 'auth/token', {{
      'grant_type': 'password',
      'username': username,
      'password': password,
      'organization_id': _config.organizationId,
      'app_id': _config.appId,
    }});
    
    if (response.statusCode != 200) {{
      throw Exception('Authentication failed');
    }}
    
    final data = jsonDecode(response.body);
    final token = AuthToken(
      accessToken: data['access_token'],
      refreshToken: data['refresh_token'],
      tokenType: data['token_type'] ?? 'Bearer',
      expiresAt: DateTime.parse(data['expires_at']),
      scope: List<String>.from(data['scope'] ?? []),
    );
    
    _authToken = token;
    
    // Store token
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('itdo_auth_token', jsonEncode(token.toJson()));
    
    return token;
  }}
  
  /// Logout
  Future<void> logout() async {{
    if (_authToken != null) {{
      try {{
        await _makeRequest('POST', 'auth/logout', {{
          'token': _authToken!.accessToken,
        }});
      }} catch (e) {{
        debugPrint('Logout request failed: $e');
      }}
    }}
    
    _authToken = null;
    
    // Clear stored token
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('itdo_auth_token');
  }}
  
  /// Check if authenticated
  bool get isAuthenticated {{
    return _authToken != null && DateTime.now().isBefore(_authToken!.expiresAt);
  }}
  
  /// Make HTTP request
  Future<http.Response> _makeRequest(
    String method,
    String endpoint,
    Map<String, dynamic>? data,
  ) async {{
    final url = Uri.parse('${{_config.apiBaseUrl}}/api/v1/$endpoint');
    final headers = <String, String>{{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'ITDO-ERP-SDK-Flutter/{self.metadata.version}',
    }};
    
    if (_authToken != null) {{
      headers['Authorization'] = '${{_authToken!.tokenType}} ${{_authToken!.accessToken}}';
    }}
    
    http.Response response;
    final body = data != null ? jsonEncode(data) : null;
    
    switch (method.toUpperCase()) {{
      case 'GET':
        response = await http.get(url, headers: headers);
        break;
      case 'POST':
        response = await http.post(url, headers: headers, body: body);
        break;
      case 'PUT':
        response = await http.put(url, headers: headers, body: body);
        break;
      case 'DELETE':
        response = await http.delete(url, headers: headers);
        break;
      default:
        throw ArgumentError('Unsupported HTTP method: $method');
    }}
    
    return response;
  }}
  
  /// Get device information
  Future<DeviceInfo> _getDeviceInfo() async {{
    final deviceInfoPlugin = DeviceInfoPlugin();
    
    if (Platform.isIOS) {{
      final iosInfo = await deviceInfoPlugin.iosInfo;
      return DeviceInfo(
        deviceId: iosInfo.identifierForVendor ?? '',
        platform: 'flutter_ios',
        osVersion: iosInfo.systemVersion,
        deviceModel: iosInfo.model,
      );
    }} else if (Platform.isAndroid) {{
      final androidInfo = await deviceInfoPlugin.androidInfo;
      return DeviceInfo(
        deviceId: androidInfo.id,
        platform: 'flutter_android',
        osVersion: androidInfo.version.release,
        deviceModel: androidInfo.model,
      );
    }} else {{
      return DeviceInfo(
        deviceId: 'unknown',
        platform: 'flutter_unknown',
        osVersion: 'unknown',
        deviceModel: 'unknown',
      );
    }}
  }}
}}
'''
        
        main_dart_file = lib_dir / f"{self.metadata.name.lower()}.dart"
        with open(main_dart_file, 'w') as f:
            f.write(main_dart_content.strip())
        
        # Create archive
        flutter_archive = await self._create_archive(platform_dir, f"{self.metadata.name}-flutter-{self.metadata.version}")
        result["artifacts"].append(str(flutter_archive))
    
    async def _create_archive(self, source_dir: Path, archive_name: str) -> Path:
        """Create archive from source directory."""
        archives = []
        
        for format_type in self.build_config.package_formats:
            if format_type == "tar.gz":
                archive_path = self.output_dir / f"{archive_name}.tar.gz"
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(source_dir, arcname=archive_name)
                archives.append(archive_path)
                
            elif format_type == "zip":
                archive_path = self.output_dir / f"{archive_name}.zip"
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in source_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = archive_name / file_path.relative_to(source_dir)
                            zip_file.write(file_path, arcname)
                archives.append(archive_path)
        
        return archives[0] if archives else source_dir


class DistributionManager:
    """Manage package distribution to various registries."""
    
    def __init__(self, distribution_config: DistributionConfig) -> dict:
        self.config = distribution_config
        self.publish_results: Dict[str, Dict[str, Any]] = {}
    
    async def publish_all_packages(self, build_results: Dict[str, Any]) -> Dict[str, Any]:
        """Publish packages to all configured registries."""
        publish_summary = {
            "started_at": datetime.now().isoformat(),
            "platforms": {},
            "total_published": 0,
            "failed_publications": 0,
            "errors": []
        }
        
        for platform, platform_result in build_results["platforms"].items():
            if not platform_result["success"]:
                continue
                
            try:
                publication_result = await self._publish_platform_package(platform, platform_result)
                publish_summary["platforms"][platform] = publication_result
                
                if publication_result["success"]:
                    publish_summary["total_published"] += 1
                else:
                    publish_summary["failed_publications"] += 1
                    publish_summary["errors"].extend(publication_result["errors"])
                    
            except Exception as e:
                error_msg = f"Failed to publish {platform} package: {str(e)}"
                publish_summary["errors"].append(error_msg)
                publish_summary["failed_publications"] += 1
        
        publish_summary["completed_at"] = datetime.now().isoformat()
        return publish_summary
    
    async def _publish_platform_package(self, platform: str, platform_result: Dict[str, Any]) -> Dict[str, Any]:
        """Publish platform-specific package."""
        result = {
            "platform": platform,
            "success": False,
            "published_to": [],
            "errors": []
        }
        
        if not self.config.auto_publish:
            result["errors"].append("Auto-publish is disabled")
            return result
        
        try:
            if platform == "react-native" and self.config.npm_token:
                await self._publish_to_npm(platform_result["artifacts"][0])
                result["published_to"].append("npm")
                
            elif platform == "ios" and self.config.cocoapods_trunk_token:
                await self._publish_to_cocoapods(platform_result["artifacts"][0])
                result["published_to"].append("cocoapods")
                
            elif platform == "android" and self.config.maven_credentials:
                await self._publish_to_maven(platform_result["artifacts"][0])
                result["published_to"].append("maven")
                
            elif platform == "flutter":
                await self._publish_to_pub_dev(platform_result["artifacts"][0])
                result["published_to"].append("pub.dev")
            
            result["success"] = len(result["published_to"]) > 0
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    async def _publish_to_npm(self, package_path: str) -> None:
        """Publish to NPM registry."""
        # Extract package to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            if package_path.endswith('.tar.gz'):
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
            elif package_path.endswith('.zip'):
                with zipfile.ZipFile(package_path, 'r') as zip_file:
                    zip_file.extractall(temp_dir)
            
            # Find package.json
            package_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if 'package.json' in files:
                    package_dir = root
                    break
            
            if not package_dir:
                raise Exception("package.json not found in archive")
            
            # Set NPM token
            npmrc_content = f"//registry.npmjs.org/:_authToken={self.config.npm_token}\n"
            npmrc_path = os.path.join(package_dir, '.npmrc')
            with open(npmrc_path, 'w') as f:
                f.write(npmrc_content)
            
            # Build TypeScript if needed
            if os.path.exists(os.path.join(package_dir, 'tsconfig.json')):
                subprocess.run(['npm', 'run', 'build'], cwd=package_dir, check=True)
            
            # Publish
            publish_cmd = ['npm', 'publish']
            if self.config.pre_release:
                publish_cmd.append('--tag=beta')
            
            subprocess.run(publish_cmd, cwd=package_dir, check=True)
    
    async def _publish_to_cocoapods(self, package_path: str) -> None:
        """Publish to CocoaPods trunk."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            if package_path.endswith('.tar.gz'):
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
            
            # Find podspec
            podspec_path = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.podspec'):
                        podspec_path = os.path.join(root, file)
                        break
                if podspec_path:
                    break
            
            if not podspec_path:
                raise Exception("Podspec file not found in archive")
            
            # Validate podspec
            subprocess.run(['pod', 'spec', 'lint', podspec_path], check=True)
            
            # Push to trunk
            subprocess.run(['pod', 'trunk', 'push', podspec_path], check=True)
    
    async def _publish_to_maven(self, package_path: str) -> None:
        """Publish to Maven repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            if package_path.endswith('.tar.gz'):
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
            
            # Find build.gradle
            gradle_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if 'build.gradle' in files:
                    gradle_dir = root
                    break
            
            if not gradle_dir:
                raise Exception("build.gradle not found in archive")
            
            # Publish using Gradle
            subprocess.run(['./gradlew', 'publish'], cwd=gradle_dir, check=True)
    
    async def _publish_to_pub_dev(self, package_path: str) -> None:
        """Publish to pub.dev."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            if package_path.endswith('.tar.gz'):
                with tarfile.open(package_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
            
            # Find pubspec.yaml
            pubspec_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if 'pubspec.yaml' in files:
                    pubspec_dir = root
                    break
            
            if not pubspec_dir:
                raise Exception("pubspec.yaml not found in archive")
            
            # Publish
            subprocess.run(['dart', 'pub', 'publish', '--force'], cwd=pubspec_dir, check=True)


class SDKPackagingManager:
    """Main SDK packaging and distribution manager."""
    
    def __init__(self) -> dict:
        self.metadata = PackageMetadata(
            name="ITDOERPMobileSDK",
            version="1.0.0",
            description="Production-grade mobile SDK for ITDO ERP system with authentication, data sync, and analytics"
        )
        
        self.build_config = BuildConfiguration()
        self.distribution_config = DistributionConfig()
        
        self.builder = PackageBuilder(self.metadata, self.build_config)
        self.distributor = DistributionManager(self.distribution_config)
    
    async def create_complete_distribution(self) -> Dict[str, Any]:
        """Create complete SDK distribution."""
        print("[SDK Packaging] Starting complete distribution build...")
        
        start_time = datetime.now()
        
        # Build all packages
        build_results = await self.builder.build_all_packages()
        
        # Publish packages (if enabled)
        publish_results = None
        if self.distribution_config.auto_publish:
            publish_results = await self.distributor.publish_all_packages(build_results)
        
        # Generate distribution summary
        end_time = datetime.now()
        distribution_summary = {
            "sdk_version": self.metadata.version,
            "build_started": start_time.isoformat(),
            "build_completed": end_time.isoformat(),
            "build_duration_seconds": (end_time - start_time).total_seconds(),
            "build_results": build_results,
            "publish_results": publish_results,
            "distribution_urls": self._generate_distribution_urls(),
            "installation_commands": self._generate_installation_commands(),
        }
        
        # Export build report
        report_path = Path(self.build_config.output_directory) / "distribution_report.json"
        with open(report_path, 'w') as f:
            json.dump(distribution_summary, f, indent=2)
        
        print(f"[SDK Packaging] Distribution completed in {(end_time - start_time).total_seconds():.1f}s")
        print(f"[SDK Packaging] Report saved to: {report_path}")
        
        return distribution_summary
    
    def _generate_distribution_urls(self) -> Dict[str, str]:
        """Generate distribution URLs for each platform."""
        base_name = self.metadata.name.lower().replace('_', '-')
        version = self.metadata.version
        
        return {
            "npm": f"https://www.npmjs.com/package/@itdo/{base_name}",
            "cocoapods": f"https://cocoapods.org/pods/{self.metadata.name}",
            "maven": f"https://repo1.maven.org/maven2/com/itdo/erp/{base_name}/{version}/",
            "pub_dev": f"https://pub.dev/packages/{base_name}",
            "github_releases": f"{self.metadata.homepage}/releases/tag/v{version}"
        }
    
    def _generate_installation_commands(self) -> Dict[str, str]:
        """Generate installation commands for each platform."""
        base_name = self.metadata.name.lower().replace('_', '-')
        
        return {
            "react_native": f"npm install @itdo/{base_name}",
            "ios_spm": f'.package(url: "{self.metadata.repository}", from: "{self.metadata.version}")',
            "ios_cocoapods": f'pod "{self.metadata.name}", "~> {self.metadata.version}"',
            "android": f'implementation "com.itdo.erp:{base_name}:{self.metadata.version}"',
            "flutter": f"flutter pub add {base_name}"
        }