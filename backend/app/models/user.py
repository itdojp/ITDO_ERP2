"""User model."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, or_
from sqlalchemy.orm import Session, relationship

from app.core.database import Base
from app.core.security import hash_password, verify_password
from app.core.exceptions import BusinessLogicError, PermissionDenied

if TYPE_CHECKING:
    from app.models.organization import Organization  # type: ignore
    from app.models.department import Department  # type: ignore
    from app.models.role import Role, UserRole  # type: ignore
    from app.models.password_history import PasswordHistory  # type: ignore
    from app.models.user_session import UserSession  # type: ignore
    from app.models.user_activity_log import UserActivityLog  # type: ignore


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    full_name: str = Column(String(100), nullable=False)
    phone: Optional[str] = Column(String(20))
    profile_image_url: Optional[str] = Column(String(500))
    is_active: bool = Column(Boolean, default=True)
    is_superuser: bool = Column(Boolean, default=False)
    
    # Security fields
    last_login_at: Optional[datetime] = Column(DateTime(timezone=True))
    password_changed_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    failed_login_attempts: int = Column(Integer, default=0)
    locked_until: Optional[datetime] = Column(DateTime(timezone=True))
    password_must_change: bool = Column(Boolean, default=False)
    
    # Audit fields
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Optional[datetime] = Column(DateTime(timezone=True))
    deleted_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    created_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="user", foreign_keys="UserRole.user_id")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    @classmethod
    def create(
        cls,
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        is_active: bool = True,
        is_superuser: bool = False
    ) -> "User":
        """Create a new user."""
        # Validate password strength
        cls._validate_password_strength(password)
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create user instance
        user = cls(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            phone=phone,
            is_active=is_active,
            is_superuser=is_superuser,
            password_changed_at=datetime.utcnow()
        )
        
        # Add to database
        db.add(user)
        db.flush()
        
        return user
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Get user by email."""
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional["User"]:
        """Authenticate user by email and password."""
        # Get user by email
        user = cls.get_by_email(db, email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def update(self, db: Session, **kwargs: Any) -> None:
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at"]:
                # Hash password if updating
                if key == "password":
                    self._validate_password_strength(value)
                    value = hash_password(value)
                    key = "hashed_password"
                    self.password_changed_at = datetime.utcnow()
                setattr(self, key, value)
        
        db.add(self)
        db.flush()
    
    def change_password(self, db: Session, current_password: str, new_password: str) -> None:
        """Change user password with validation."""
        # Verify current password
        if not verify_password(current_password, self.hashed_password):
            raise BusinessLogicError("現在のパスワードが正しくありません")
        
        # Validate new password
        self._validate_password_strength(new_password)
        
        # Check password history
        if self._is_password_in_history(db, new_password):
            raise BusinessLogicError("直近3回使用したパスワードは再利用できません")
        
        # Save current password to history
        from app.models.password_history import PasswordHistory
        history = PasswordHistory(
            user_id=self.id,
            password_hash=self.hashed_password
        )
        db.add(history)
        
        # Update password
        self.hashed_password = hash_password(new_password)
        self.password_changed_at = datetime.utcnow()
        self.password_must_change = False
        self.failed_login_attempts = 0
        self.locked_until = None
        
        db.add(self)
        db.flush()
    
    def record_failed_login(self, db: Session) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        db.add(self)
        db.flush()
    
    def record_successful_login(self, db: Session) -> None:
        """Record successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
        
        db.add(self)
        db.flush()
    
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def is_password_expired(self) -> bool:
        """Check if password has expired (90 days)."""
        expiry_date = self.password_changed_at + timedelta(days=90)
        return datetime.utcnow() > expiry_date
    
    def create_session(
        self,
        db: Session,
        session_token: str,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> "UserSession":
        """Create a new user session."""
        from app.models.user_session import UserSession
        
        # Check concurrent session limit (5 sessions)
        active_sessions = db.query(UserSession).filter(
            UserSession.user_id == self.id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.created_at).all()
        
        if len(active_sessions) >= 5:
            # Invalidate oldest session
            active_sessions[0].invalidate()
            db.add(active_sessions[0])
        
        # Create new session
        if not expires_at:
            expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession(
            user_id=self.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        db.flush()
        
        return session
    
    def validate_session(
        self,
        session_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "UserSession":
        """Validate session with security checks."""
        from app.models.user_session import UserSession
        
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.user_id == self.id
        ).first()
        
        if not session or not session.is_valid():
            raise BusinessLogicError("無効なセッションです")
        
        # Security checks
        if ip_address and session.ip_address != ip_address:
            session.requires_verification = True
            session.security_alert = "IP_MISMATCH"
        
        return session
    
    @property
    def active_sessions(self) -> List["UserSession"]:
        """Get active sessions."""
        from app.models.user_session import UserSession
        return [s for s in self.sessions if s.is_valid()]
    
    def assign_to_organization(
        self,
        db: Session,
        organization: "Organization",
        role: "Role",
        assigned_by: int
    ) -> "UserRole":
        """Assign user to organization with role."""
        from app.models.role import UserRole
        
        user_role = UserRole(
            user_id=self.id,
            role_id=role.id,
            organization_id=organization.id,
            assigned_by=assigned_by
        )
        
        db.add(user_role)
        db.flush()
        
        return user_role
    
    def assign_to_department(
        self,
        db: Session,
        organization: "Organization",
        department: "Department",
        role: "Role",
        assigned_by: int
    ) -> "UserRole":
        """Assign user to department with role."""
        from app.models.role import UserRole
        
        user_role = UserRole(
            user_id=self.id,
            role_id=role.id,
            organization_id=organization.id,
            department_id=department.id,
            assigned_by=assigned_by
        )
        
        db.add(user_role)
        db.flush()
        
        return user_role
    
    def get_organizations(self) -> List["Organization"]:
        """Get user's organizations."""
        return list(set(ur.organization for ur in self.user_roles if ur.organization))
    
    def get_departments(self, organization_id: int) -> List["Department"]:
        """Get user's departments in organization."""
        return [
            ur.department for ur in self.user_roles
            if ur.organization_id == organization_id and ur.department
        ]
    
    def get_roles_in_organization(self, organization_id: int) -> List["Role"]:
        """Get user's roles in organization."""
        return [
            ur.role for ur in self.user_roles
            if ur.organization_id == organization_id and ur.role
        ]
    
    def get_effective_permissions(self, organization_id: int) -> List[str]:
        """Get user's effective permissions in organization."""
        permissions = set()
        
        for user_role in self.user_roles:
            if user_role.organization_id == organization_id and not user_role.is_expired():
                if user_role.role.permissions:
                    permissions.update(user_role.role.permissions)
        
        return list(permissions)
    
    def has_permission(self, permission: str, organization_id: int) -> bool:
        """Check if user has specific permission in organization."""
        return permission in self.get_effective_permissions(organization_id)
    
    def has_role_in_department(self, role_code: str, department_id: int) -> bool:
        """Check if user has role in department."""
        for user_role in self.user_roles:
            if (user_role.department_id == department_id and 
                user_role.role.code == role_code and 
                not user_role.is_expired()):
                return True
        return False
    
    def has_permission_in_department(self, permission: str, department_id: int) -> bool:
        """Check if user has permission in department."""
        for user_role in self.user_roles:
            if user_role.department_id == department_id and not user_role.is_expired():
                if user_role.role.has_permission(permission):
                    return True
        return False
    
    def can_access_user(self, target_user: "User") -> bool:
        """Check if user can access another user's data."""
        # Self access
        if self.id == target_user.id:
            return True
        
        # System admin
        if self.is_superuser:
            return True
        
        # Check organization overlap
        user_orgs = set(o.id for o in self.get_organizations())
        target_orgs = set(o.id for o in target_user.get_organizations())
        
        return bool(user_orgs & target_orgs)
    
    def soft_delete(self, db: Session, deleted_by: int) -> None:
        """Soft delete user."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        
        # Invalidate all sessions
        for session in self.sessions:
            session.invalidate()
            db.add(session)
        
        db.add(self)
        db.flush()
    
    def log_activity(
        self,
        db: Session,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log user activity."""
        from app.models.user_activity_log import UserActivityLog
        
        log = UserActivityLog(
            user_id=self.id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(log)
        db.flush()
    
    def to_dict_safe(self) -> Dict[str, Any]:
        """Convert to dictionary with masked sensitive data."""
        return {
            "id": self.id,
            "email": self._mask_email(self.email),
            "full_name": self.full_name,
            "phone": self._mask_phone(self.phone) if self.phone else None,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at
        }
    
    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email for privacy."""
        parts = email.split("@")
        if len(parts) != 2:
            return email
        
        local = parts[0]
        if len(local) > 3:
            local = local[:3] + "*" * 6
        
        return f"{local}@{parts[1]}"
    
    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone number for privacy."""
        if len(phone) < 8:
            return phone
        
        # Keep area code and last 4 digits
        parts = phone.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-****-{parts[2]}"
        
        return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]
    
    @staticmethod
    def _validate_password_strength(password: str) -> None:
        """Validate password meets security requirements."""
        if len(password) < 8:
            raise BusinessLogicError("パスワードは8文字以上である必要があります")
        
        # Check for at least 3 of: uppercase, lowercase, digit, special char
        import re
        checks = [
            bool(re.search(r"[A-Z]", password)),  # Has uppercase
            bool(re.search(r"[a-z]", password)),  # Has lowercase
            bool(re.search(r"\d", password)),     # Has digit
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))  # Has special char
        ]
        
        if sum(checks) < 3:
            raise BusinessLogicError(
                "パスワードは大文字・小文字・数字・特殊文字のうち3種類以上を含む必要があります"
            )
        
        # Check for common patterns
        if password.lower() in ["password", "12345678", "qwertyui"]:
            raise BusinessLogicError("一般的なパスワードは使用できません")
    
    def _is_password_in_history(self, db: Session, password: str) -> bool:
        """Check if password was recently used."""
        from app.models.password_history import PasswordHistory
        
        # Get last 3 passwords
        recent_passwords = db.query(PasswordHistory).filter(
            PasswordHistory.user_id == self.id
        ).order_by(PasswordHistory.created_at.desc()).limit(3).all()
        
        # Check against history
        for history in recent_passwords:
            if verify_password(password, history.password_hash):
                return True
        
        # Check current password
        if verify_password(password, self.hashed_password):
            return True
        
        return False
    
    def is_password_in_history(self, password_hash: str) -> bool:
        """Check if password hash is in history (for testing)."""
        # This is a test helper method
        recent_hashes = [h.password_hash for h in self.password_history[:3]]
        return password_hash in recent_hashes
    
    def assign_role_to_self(self, role: "Role", organization: "Organization") -> None:
        """Attempt to assign role to self (should fail for security)."""
        raise PermissionDenied("ユーザーは自分自身にロールを割り当てることはできません")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"