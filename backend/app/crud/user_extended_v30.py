from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
from passlib.context import CryptContext

from app.models.user_extended import User, UserActivity
from app.schemas.user_complete_v30 import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DuplicateError(Exception):
    pass

class NotFoundError(Exception):
    pass

class UserCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> tuple[List[User], int]:
        query = self.db.query(User)

        # フィルタリング
        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(User.is_active == filters["is_active"])
            if filters.get("department"):
                query = query.filter(User.department == filters["department"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        User.email.ilike(search),
                        User.username.ilike(search),
                        User.full_name.ilike(search)
                    )
                )

        # カウント
        total = query.count()

        # ソート
        order_by = getattr(User, sort_by)
        if sort_desc:
            order_by = order_by.desc()
        query = query.order_by(order_by)

        # ページネーション
        users = query.offset(skip).limit(limit).all()

        return users, total

    def create(self, user_in: UserCreate) -> User:
        # 重複チェック
        if self.get_by_email(user_in.email):
            raise DuplicateError("Email already registered")
        if self.get_by_username(user_in.username):
            raise DuplicateError("Username already taken")

        # パスワードハッシュ化
        password_hash = pwd_context.hash(user_in.password)

        # ユーザー作成
        db_user = User(
            id=str(uuid.uuid4()),
            email=user_in.email,
            username=user_in.username,
            password_hash=password_hash,
            full_name=user_in.full_name,
            phone_number=user_in.phone_number,
            department=user_in.department,
            position=user_in.position,
            employee_id=user_in.employee_id,
            password_changed_at=datetime.utcnow()
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        # アクティビティログ
        self.log_activity(db_user.id, "user_created", {"user_id": db_user.id})

        return db_user

    def update(self, user_id: str, user_in: UserUpdate) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        update_data = user_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        # アクティビティログ
        self.log_activity(user_id, "user_updated", update_data)

        return user

    def delete(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # ソフトデリート
        user.is_active = False
        user.updated_at = datetime.utcnow()

        self.db.commit()
        
        # アクティビティログ
        self.log_activity(user_id, "user_deleted", {"user_id": user_id})

        return True

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(username)
        if not user:
            user = self.get_by_email(username)

        if not user or not self.verify_password(password, user.password_hash):
            return None

        # 最終ログイン時刻更新
        user.last_login_at = datetime.utcnow()
        self.db.commit()

        # アクティビティログ
        self.log_activity(user.id, "user_login", {"login_time": user.last_login_at.isoformat()})

        return user

    def reset_password(self, user_id: str, new_password: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        user.password_hash = pwd_context.hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        self.db.commit()

        # アクティビティログ
        self.log_activity(user_id, "password_reset", {"reset_time": user.password_changed_at.isoformat()})

        return True

    def verify_user(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        user.is_verified = True
        user.updated_at = datetime.utcnow()

        self.db.commit()

        # アクティビティログ
        self.log_activity(user_id, "user_verified", {"verified_at": user.updated_at.isoformat()})

        return True

    def get_user_activities(self, user_id: str, limit: int = 50) -> List[UserActivity]:
        return (
            self.db.query(UserActivity)
            .filter(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_user_stats(self) -> Dict[str, Any]:
        """ユーザー統計情報を取得"""
        current_time = datetime.utcnow()
        month_ago = current_time - timedelta(days=30)

        total_users = self.db.query(func.count(User.id)).scalar()
        active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        verified_users = self.db.query(func.count(User.id)).filter(User.is_verified == True).scalar()
        new_users_this_month = (
            self.db.query(func.count(User.id))
            .filter(User.created_at >= month_ago)
            .scalar()
        )

        # 部署別統計
        departments = {}
        dept_stats = (
            self.db.query(User.department, func.count(User.id))
            .group_by(User.department)
            .all()
        )
        for dept, count in dept_stats:
            departments[dept or "未設定"] = count

        return {
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "verified_users": verified_users or 0,
            "new_users_this_month": new_users_this_month or 0,
            "departments": departments
        }

    def log_activity(self, user_id: str, action: str, details: Dict[str, Any], ip_address: str = None):
        """ユーザーアクティビティをログに記録"""
        activity = UserActivity(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        self.db.add(activity)
        # コミットは呼び出し元で行う