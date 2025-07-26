"""Mobile SDK Authentication & Security Module - CC02 v72.0 Day 17."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field

from .mobile_sdk_core import MobileERPSDK, SDKError, AuthenticationError, ValidationError


class BiometricAuthRequest(BaseModel):
    """Biometric authentication request."""
    biometric_type: str = Field(..., description="Type of biometric (fingerprint, face, voice)")
    biometric_template: str = Field(..., description="Biometric template data")
    challenge_response: str = Field(..., description="Challenge response")
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    liveness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Liveness detection score")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Biometric quality score")


class MFAChallenge(BaseModel):
    """Multi-factor authentication challenge."""
    challenge_id: str
    challenge_type: str  # sms, email, totp, push
    masked_destination: str  # Masked phone/email
    expires_at: datetime
    required_factors: List[str]
    attempt_count: int = 0
    max_attempts: int = 3


class SecurityPolicy(BaseModel):
    """Security policy configuration."""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    password_expiry_days: int = 90
    
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    
    mfa_required: bool = True
    mfa_methods: List[str] = Field(default_factory=lambda: ["totp", "sms"])
    
    biometric_enabled: bool = True
    biometric_fallback_required: bool = True
    
    device_registration_required: bool = True
    device_trust_duration_days: int = 30
    
    geofencing_enabled: bool = False
    allowed_countries: List[str] = Field(default_factory=list)
    
    security_questions_required: int = 3
    lockout_threshold: int = 5
    lockout_duration_minutes: int = 15


class DeviceFingerprint(BaseModel):
    """Device fingerprinting data."""
    device_id: str
    hardware_fingerprint: str
    software_fingerprint: str
    network_fingerprint: str
    behavioral_fingerprint: str
    trust_score: float = Field(ge=0.0, le=1.0)
    last_seen: datetime
    risk_indicators: List[str] = Field(default_factory=list)


class SecurityEvent(BaseModel):
    """Security event for logging."""
    event_id: str
    event_type: str
    severity: str  # low, medium, high, critical
    user_id: Optional[str]
    device_id: Optional[str]
    ip_address: str
    location: Optional[Dict[str, Any]]
    user_agent: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CryptoUtils:
    """Cryptographic utilities for SDK."""
    
    @staticmethod
    def generate_key_pair() -> Tuple[bytes, bytes]:
        """Generate RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def encrypt_rsa(data: bytes, public_key_pem: bytes) -> bytes:
        """Encrypt data with RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted
    
    @staticmethod
    def decrypt_rsa(encrypted_data: bytes, private_key_pem: bytes) -> bytes:
        """Decrypt data with RSA private key."""
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted
    
    @staticmethod
    def encrypt_aes(data: bytes, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Encrypt data with AES using password-based key derivation."""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # Generate IV
        iv = secrets.token_bytes(16)
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        
        # Pad data to AES block size
        pad_length = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_length] * pad_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'salt': base64.b64encode(salt).decode(),
            'iv': base64.b64encode(iv).decode(),
        }
    
    @staticmethod
    def decrypt_aes(encrypted_dict: Dict[str, str], password: str) -> bytes:
        """Decrypt AES encrypted data."""
        encrypted_data = base64.b64decode(encrypted_dict['encrypted_data'])
        salt = base64.b64decode(encrypted_dict['salt'])
        iv = base64.b64decode(encrypted_dict['iv'])
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # Decrypt data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove padding
        pad_length = padded_data[-1]
        data = padded_data[:-pad_length]
        
        return data
    
    @staticmethod
    def generate_hmac(data: str, secret: str) -> str:
        """Generate HMAC signature."""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_hmac(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature."""
        expected_signature = CryptoUtils.generate_hmac(data, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        hashed = kdf.derive(password.encode())
        
        return {
            'hash': base64.b64encode(hashed).decode(),
            'salt': salt,
        }
    
    @staticmethod
    def verify_password(password: str, hash_dict: Dict[str, str]) -> bool:
        """Verify password against hash."""
        expected_hash = CryptoUtils.hash_password(password, hash_dict['salt'])
        return hmac.compare_digest(hash_dict['hash'], expected_hash['hash'])


class BiometricManager:
    """Biometric authentication manager."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self._biometric_templates: Dict[str, Dict[str, Any]] = {}
        self._challenges: Dict[str, str] = {}
    
    async def enroll_biometric(
        self,
        biometric_type: str,
        biometric_data: Dict[str, Any],
        user_id: str,
        device_id: str
    ) -> Dict[str, Any]:
        """Enroll biometric template."""
        try:
            # Generate biometric template (simplified)
            template_id = f"{user_id}_{biometric_type}_{device_id}"
            template_data = self._process_biometric_data(biometric_data)
            
            enrollment_data = {
                'template_id': template_id,
                'biometric_type': biometric_type,
                'template_data': template_data,
                'quality_score': biometric_data.get('quality_score', 0.0),
                'device_id': device_id,
                'enrolled_at': datetime.now().isoformat(),
            }
            
            # Store template securely
            self._biometric_templates[template_id] = enrollment_data
            
            # Register with server
            response = await self.sdk.http_client.post(
                'mobile-erp/security/biometric/enroll',
                enrollment_data,
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 201:
                raise AuthenticationError("Biometric enrollment failed")
            
            return response['data']
            
        except Exception as e:
            raise AuthenticationError(f"Biometric enrollment failed: {str(e)}")
    
    async def authenticate_biometric(
        self,
        biometric_type: str,
        biometric_data: Dict[str, Any],
        device_id: str
    ) -> Dict[str, Any]:
        """Authenticate using biometrics."""
        try:
            # Generate authentication challenge
            challenge = self._generate_biometric_challenge()
            
            # Process biometric data
            processed_data = self._process_biometric_data(biometric_data)
            
            # Create authentication request
            auth_request = BiometricAuthRequest(
                biometric_type=biometric_type,
                biometric_template=processed_data,
                challenge_response=challenge,
                device_id=device_id,
                liveness_score=biometric_data.get('liveness_score', 0.0),
                quality_score=biometric_data.get('quality_score', 0.0),
            )
            
            # Authenticate with server
            response = await self.sdk.http_client.post(
                'mobile-erp/security/biometric/authenticate',
                auth_request.dict(),
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 200:
                raise AuthenticationError("Biometric authentication failed")
            
            return response['data']
            
        except Exception as e:
            raise AuthenticationError(f"Biometric authentication failed: {str(e)}")
    
    def _process_biometric_data(self, biometric_data: Dict[str, Any]) -> str:
        """Process and normalize biometric data."""
        # In a real implementation, this would involve complex biometric processing
        # For now, we'll create a simplified template
        template_data = {
            'features': biometric_data.get('features', []),
            'quality_metrics': biometric_data.get('quality_metrics', {}),
            'processed_at': time.time(),
        }
        
        # Encrypt template data
        encrypted = CryptoUtils.encrypt_aes(
            json.dumps(template_data).encode(),
            self.sdk.config.api_key
        )
        
        return base64.b64encode(json.dumps(encrypted).encode()).decode()
    
    def _generate_biometric_challenge(self) -> str:
        """Generate biometric authentication challenge."""
        challenge_data = {
            'timestamp': time.time(),
            'nonce': secrets.token_hex(16),
            'device_info': True,
        }
        
        challenge_json = json.dumps(challenge_data, sort_keys=True)
        signature = CryptoUtils.generate_hmac(challenge_json, self.sdk.config.api_key)
        
        return base64.b64encode(f"{challenge_json}.{signature}".encode()).decode()


class MFAManager:
    """Multi-factor authentication manager."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self._active_challenges: Dict[str, MFAChallenge] = {}
    
    async def initiate_mfa(
        self,
        user_id: str,
        primary_auth_token: str,
        requested_factors: List[str]
    ) -> MFAChallenge:
        """Initiate multi-factor authentication."""
        try:
            challenge_data = {
                'user_id': user_id,
                'primary_token': primary_auth_token,
                'requested_factors': requested_factors,
                'device_id': self.sdk.auth_manager.device_info.device_id if self.sdk.auth_manager.device_info else None,
            }
            
            response = await self.sdk.http_client.post(
                'auth/mfa/initiate',
                challenge_data,
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 200:
                raise AuthenticationError("MFA initiation failed")
            
            challenge_info = response['data']
            challenge = MFAChallenge(
                challenge_id=challenge_info['challenge_id'],
                challenge_type=challenge_info['challenge_type'],
                masked_destination=challenge_info['masked_destination'],
                expires_at=datetime.fromisoformat(challenge_info['expires_at']),
                required_factors=challenge_info['required_factors'],
            )
            
            self._active_challenges[challenge.challenge_id] = challenge
            return challenge
            
        except Exception as e:
            raise AuthenticationError(f"MFA initiation failed: {str(e)}")
    
    async def verify_mfa_factor(
        self,
        challenge_id: str,
        factor_type: str,
        factor_value: str
    ) -> Dict[str, Any]:
        """Verify MFA factor."""
        try:
            challenge = self._active_challenges.get(challenge_id)
            if not challenge:
                raise ValidationError("Invalid or expired challenge")
            
            if datetime.now() > challenge.expires_at:
                del self._active_challenges[challenge_id]
                raise ValidationError("Challenge expired")
            
            if challenge.attempt_count >= challenge.max_attempts:
                del self._active_challenges[challenge_id]
                raise ValidationError("Too many attempts")
            
            challenge.attempt_count += 1
            
            verification_data = {
                'challenge_id': challenge_id,
                'factor_type': factor_type,
                'factor_value': factor_value,
                'attempt_count': challenge.attempt_count,
            }
            
            response = await self.sdk.http_client.post(
                'auth/mfa/verify',
                verification_data,
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 200:
                raise AuthenticationError("MFA verification failed")
            
            result = response['data']
            
            if result.get('verification_successful'):
                # Clean up successful challenge
                del self._active_challenges[challenge_id]
            
            return result
            
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError)):
                raise
            else:
                raise AuthenticationError(f"MFA verification failed: {str(e)}")
    
    async def generate_totp_secret(self, user_id: str) -> Dict[str, Any]:
        """Generate TOTP secret for user."""
        try:
            response = await self.sdk.http_client.post(
                'auth/mfa/totp/generate',
                {'user_id': user_id},
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 200:
                raise AuthenticationError("TOTP secret generation failed")
            
            return response['data']
            
        except Exception as e:
            raise AuthenticationError(f"TOTP secret generation failed: {str(e)}")
    
    def generate_totp_code(self, secret: str, timestamp: Optional[int] = None) -> str:
        """Generate TOTP code from secret."""
        if timestamp is None:
            timestamp = int(time.time())
        
        # TOTP algorithm (simplified)
        time_step = timestamp // 30
        time_bytes = time_step.to_bytes(8, byteorder='big')
        
        hmac_hash = hmac.new(
            base64.b32decode(secret.upper()),
            time_bytes,
            hashlib.sha1
        ).digest()
        
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        
        return str(code % 1000000).zfill(6)


class DeviceTrustManager:
    """Device trust and fingerprinting manager."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self._device_fingerprints: Dict[str, DeviceFingerprint] = {}
    
    async def register_device(
        self,
        device_info: Dict[str, Any],
        trust_factors: Dict[str, Any]
    ) -> DeviceFingerprint:
        """Register and fingerprint device."""
        try:
            # Generate device fingerprint
            fingerprint = self._generate_device_fingerprint(device_info, trust_factors)
            
            registration_data = {
                'device_fingerprint': fingerprint.dict(),
                'device_info': device_info,
                'trust_factors': trust_factors,
            }
            
            response = await self.sdk.http_client.post(
                'mobile-erp/devices/register',
                registration_data,
                params={
                    'organization_id': self.sdk.config.organization_id,
                    'user_id': trust_factors.get('user_id'),
                }
            )
            
            if response['status'] != 201:
                raise ValidationError("Device registration failed")
            
            self._device_fingerprints[fingerprint.device_id] = fingerprint
            return fingerprint
            
        except Exception as e:
            raise ValidationError(f"Device registration failed: {str(e)}")
    
    async def verify_device_trust(
        self,
        device_id: str,
        current_fingerprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify device trust based on fingerprint."""
        try:
            stored_fingerprint = self._device_fingerprints.get(device_id)
            if not stored_fingerprint:
                raise ValidationError("Device not registered")
            
            # Compare fingerprints
            trust_score = self._calculate_trust_score(
                stored_fingerprint,
                current_fingerprint
            )
            
            verification_data = {
                'device_id': device_id,
                'current_fingerprint': current_fingerprint,
                'trust_score': trust_score,
                'risk_assessment': self._assess_risk(trust_score, current_fingerprint),
            }
            
            response = await self.sdk.http_client.post(
                'mobile-erp/devices/verify-trust',
                verification_data,
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] != 200:
                raise ValidationError("Device trust verification failed")
            
            return response['data']
            
        except Exception as e:
            raise ValidationError(f"Device trust verification failed: {str(e)}")
    
    def _generate_device_fingerprint(
        self,
        device_info: Dict[str, Any],
        trust_factors: Dict[str, Any]
    ) -> DeviceFingerprint:
        """Generate comprehensive device fingerprint."""
        # Hardware fingerprint
        hardware_data = {
            'device_model': device_info.get('device_model', ''),
            'cpu_info': device_info.get('cpu_info', ''),
            'memory_size': device_info.get('memory_size', 0),
            'storage_size': device_info.get('storage_size', 0),
            'screen_resolution': device_info.get('screen_resolution', ''),
        }
        hardware_fingerprint = hashlib.sha256(
            json.dumps(hardware_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Software fingerprint
        software_data = {
            'os_version': device_info.get('os_version', ''),
            'app_version': device_info.get('app_version', ''),
            'installed_apps': sorted(device_info.get('installed_apps', [])),
            'system_settings': device_info.get('system_settings', {}),
        }
        software_fingerprint = hashlib.sha256(
            json.dumps(software_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Network fingerprint
        network_data = {
            'ip_address': trust_factors.get('ip_address', ''),
            'network_type': trust_factors.get('network_type', ''),
            'carrier': trust_factors.get('carrier', ''),
            'wifi_networks': sorted(trust_factors.get('wifi_networks', [])),
        }
        network_fingerprint = hashlib.sha256(
            json.dumps(network_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Behavioral fingerprint (simplified)
        behavioral_data = {
            'usage_patterns': trust_factors.get('usage_patterns', {}),
            'interaction_timing': trust_factors.get('interaction_timing', {}),
            'app_preferences': trust_factors.get('app_preferences', {}),
        }
        behavioral_fingerprint = hashlib.sha256(
            json.dumps(behavioral_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Calculate initial trust score
        trust_score = self._calculate_initial_trust_score(trust_factors)
        
        return DeviceFingerprint(
            device_id=device_info.get('device_id', ''),
            hardware_fingerprint=hardware_fingerprint,
            software_fingerprint=software_fingerprint,
            network_fingerprint=network_fingerprint,
            behavioral_fingerprint=behavioral_fingerprint,
            trust_score=trust_score,
            last_seen=datetime.now(),
            risk_indicators=self._identify_risk_indicators(device_info, trust_factors),
        )
    
    def _calculate_trust_score(
        self,
        stored_fingerprint: DeviceFingerprint,
        current_fingerprint: Dict[str, Any]
    ) -> float:
        """Calculate trust score based on fingerprint comparison."""
        score = 1.0
        
        # Compare hardware fingerprint (should be stable)
        if stored_fingerprint.hardware_fingerprint != current_fingerprint.get('hardware_fingerprint', ''):
            score *= 0.3  # Major trust reduction for hardware changes
        
        # Compare software fingerprint (can change)
        if stored_fingerprint.software_fingerprint != current_fingerprint.get('software_fingerprint', ''):
            score *= 0.8  # Minor trust reduction for software changes
        
        # Compare network fingerprint (frequently changes)
        if stored_fingerprint.network_fingerprint != current_fingerprint.get('network_fingerprint', ''):
            score *= 0.9  # Minimal trust reduction for network changes
        
        # Compare behavioral fingerprint
        if stored_fingerprint.behavioral_fingerprint != current_fingerprint.get('behavioral_fingerprint', ''):
            score *= 0.7  # Moderate trust reduction for behavioral changes
        
        # Time-based trust decay
        days_since_last_seen = (datetime.now() - stored_fingerprint.last_seen).days
        if days_since_last_seen > 30:
            score *= max(0.5, 1.0 - (days_since_last_seen - 30) * 0.01)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_initial_trust_score(self, trust_factors: Dict[str, Any]) -> float:
        """Calculate initial trust score for new device."""
        score = 0.5  # Start with neutral trust
        
        # Known user factors
        if trust_factors.get('user_verified'):
            score += 0.2
        
        # Device security factors
        if trust_factors.get('device_encrypted'):
            score += 0.1
        if trust_factors.get('screen_lock_enabled'):
            score += 0.1
        if trust_factors.get('biometric_enabled'):
            score += 0.1
        
        # Network factors
        if trust_factors.get('secure_network'):
            score += 0.05
        if trust_factors.get('known_location'):
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _identify_risk_indicators(
        self,
        device_info: Dict[str, Any],
        trust_factors: Dict[str, Any]
    ) -> List[str]:
        """Identify potential risk indicators."""
        risk_indicators = []
        
        # Device risks
        if device_info.get('rooted') or device_info.get('jailbroken'):
            risk_indicators.append('device_compromised')
        
        if not device_info.get('device_encrypted', True):
            risk_indicators.append('device_not_encrypted')
        
        if not device_info.get('screen_lock_enabled', True):
            risk_indicators.append('no_screen_lock')
        
        # Network risks
        if trust_factors.get('vpn_detected'):
            risk_indicators.append('vpn_usage')
        
        if trust_factors.get('suspicious_network'):
            risk_indicators.append('suspicious_network')
        
        # Location risks
        if trust_factors.get('unusual_location'):
            risk_indicators.append('unusual_location')
        
        # Behavioral risks
        if trust_factors.get('unusual_usage_pattern'):
            risk_indicators.append('unusual_behavior')
        
        return risk_indicators
    
    def _assess_risk(self, trust_score: float, current_fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk based on trust score and other factors."""
        if trust_score >= 0.8:
            risk_level = 'low'
        elif trust_score >= 0.6:
            risk_level = 'medium'
        elif trust_score >= 0.4:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return {
            'risk_level': risk_level,
            'trust_score': trust_score,
            'recommended_actions': self._get_risk_recommendations(risk_level),
            'monitoring_required': risk_level in ['high', 'critical'],
        }
    
    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level."""
        if risk_level == 'low':
            return ['continue_normal_operation']
        elif risk_level == 'medium':
            return ['increase_monitoring', 'request_additional_verification']
        elif risk_level == 'high':
            return ['require_mfa', 'limit_sensitive_operations', 'notify_security_team']
        else:  # critical
            return ['block_access', 'require_device_re_registration', 'alert_security_team']


class SecurityEventLogger:
    """Security event logging and monitoring."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self._event_buffer: List[SecurityEvent] = []
        self._buffer_size = 100
    
    async def log_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """Log security event."""
        event = SecurityEvent(
            event_id=CryptoUtils.generate_secure_token(16),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            device_id=device_id,
            ip_address=metadata.get('ip_address', 'unknown') if metadata else 'unknown',
            location=metadata.get('location') if metadata else None,
            user_agent=metadata.get('user_agent', 'unknown') if metadata else 'unknown',
            description=description,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        self._event_buffer.append(event)
        
        # Flush buffer if full
        if len(self._event_buffer) >= self._buffer_size:
            await self._flush_events()
        
        # Send critical events immediately
        if severity == 'critical':
            await self._send_event(event)
        
        return event
    
    async def _flush_events(self) -> None:
        """Flush event buffer to server."""
        if not self._event_buffer:
            return
        
        try:
            events_data = [event.dict() for event in self._event_buffer]
            
            response = await self.sdk.http_client.post(
                'mobile-erp/security/events/batch',
                {'events': events_data},
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] == 201:
                self._event_buffer.clear()
            
        except Exception as e:
            print(f"[SDK] Failed to flush security events: {e}")
    
    async def _send_event(self, event: SecurityEvent) -> None:
        """Send individual event to server."""
        try:
            await self.sdk.http_client.post(
                'mobile-erp/security/events',
                event.dict(),
                params={
                    'organization_id': self.sdk.config.organization_id,
                    'user_id': event.user_id,
                    'device_id': event.device_id,
                }
            )
        except Exception as e:
            print(f"[SDK] Failed to send security event: {e}")


class AuthSecurityModule:
    """Main authentication and security module for SDK."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self.biometric_manager = BiometricManager(sdk)
        self.mfa_manager = MFAManager(sdk)
        self.device_trust_manager = DeviceTrustManager(sdk)
        self.security_logger = SecurityEventLogger(sdk)
        self.security_policy: Optional[SecurityPolicy] = None
    
    async def initialize(self) -> None:
        """Initialize security module."""
        # Load security policy
        await self._load_security_policy()
        
        # Register event handlers
        self.sdk.events.on('auth.login_attempt', self._on_login_attempt)
        self.sdk.events.on('auth.success', self._on_auth_success)
        self.sdk.events.on('auth.failure', self._on_auth_failure)
        self.sdk.events.on('device.suspicious_activity', self._on_suspicious_activity)
    
    async def _load_security_policy(self) -> None:
        """Load security policy from server."""
        try:
            response = await self.sdk.http_client.get(
                'security/policy',
                params={'organization_id': self.sdk.config.organization_id}
            )
            
            if response['status'] == 200:
                self.security_policy = SecurityPolicy(**response['data'])
            else:
                # Use default policy
                self.security_policy = SecurityPolicy()
        except Exception:
            # Use default policy on error
            self.security_policy = SecurityPolicy()
    
    async def _on_login_attempt(self, user_id: str, device_id: str, metadata: Dict[str, Any]) -> None:
        """Handle login attempt event."""
        await self.security_logger.log_event(
            event_type='login_attempt',
            severity='low',
            description=f'Login attempt for user {user_id}',
            user_id=user_id,
            device_id=device_id,
            metadata=metadata,
        )
    
    async def _on_auth_success(self, token: Any) -> None:
        """Handle successful authentication event."""
        device_id = self.sdk.auth_manager.device_info.device_id if self.sdk.auth_manager.device_info else None
        
        await self.security_logger.log_event(
            event_type='authentication_success',
            severity='low',
            description='User successfully authenticated',
            device_id=device_id,
        )
    
    async def _on_auth_failure(self, error: str, metadata: Dict[str, Any]) -> None:
        """Handle authentication failure event."""
        await self.security_logger.log_event(
            event_type='authentication_failure',
            severity='medium',
            description=f'Authentication failed: {error}',
            metadata=metadata,
        )
    
    async def _on_suspicious_activity(self, activity_type: str, metadata: Dict[str, Any]) -> None:
        """Handle suspicious activity event."""
        await self.security_logger.log_event(
            event_type='suspicious_activity',
            severity='high',
            description=f'Suspicious activity detected: {activity_type}',
            metadata=metadata,
        )
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength against policy."""
        if not self.security_policy:
            return {'valid': True, 'score': 100, 'feedback': []}
        
        feedback = []
        score = 0
        
        # Length check
        if len(password) >= self.security_policy.password_min_length:
            score += 20
        else:
            feedback.append(f'Password must be at least {self.security_policy.password_min_length} characters')
        
        # Character type checks
        if self.security_policy.password_require_uppercase:
            if any(c.isupper() for c in password):
                score += 20
            else:
                feedback.append('Password must contain uppercase letters')
        
        if self.security_policy.password_require_lowercase:
            if any(c.islower() for c in password):
                score += 20
            else:
                feedback.append('Password must contain lowercase letters')
        
        if self.security_policy.password_require_numbers:
            if any(c.isdigit() for c in password):
                score += 20
            else:
                feedback.append('Password must contain numbers')
        
        if self.security_policy.password_require_symbols:
            if any(not c.isalnum() for c in password):
                score += 20
            else:
                feedback.append('Password must contain special characters')
        
        return {
            'valid': len(feedback) == 0,
            'score': score,
            'feedback': feedback,
        }
    
    async def check_device_compliance(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check device compliance against security policy."""
        if not self.security_policy:
            return {'compliant': True, 'violations': []}
        
        violations = []
        
        # Device encryption check
        if not device_info.get('device_encrypted', True):
            violations.append('Device is not encrypted')
        
        # Screen lock check
        if not device_info.get('screen_lock_enabled', True):
            violations.append('Screen lock is not enabled')
        
        # Root/jailbreak check
        if device_info.get('rooted') or device_info.get('jailbroken'):
            violations.append('Device is rooted or jailbroken')
        
        # OS version check (simplified)
        os_version = device_info.get('os_version', '')
        if 'old' in os_version.lower():
            violations.append('Operating system is outdated')
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'policy_version': '1.0',
        }