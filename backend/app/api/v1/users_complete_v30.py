from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.user_extended_v30 import DuplicateError, NotFoundError, UserCRUD
from app.models.user_extended import User
from app.schemas.user_complete_v30 import (
    PasswordReset,
    UserActivityResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
)

router = APIRouter()


# Mock security dependencies
async def get_current_user() -> User:
    """Mock current user - replace with actual implementation"""
    user = User()
    user.id = "current-user-id"
    user.is_superuser = True
    return user


async def require_admin() -> User:
    """Mock admin requirement - replace with actual implementation"""
    user = await get_current_user()
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    department: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ユーザー一覧取得（ページネーション、フィルタリング、ソート対応）

    - **page**: ページ番号 (1から開始)
    - **per_page**: 1ページあたりの件数 (1-100)
    - **search**: 検索キーワード (名前、メール、ユーザー名)
    - **is_active**: アクティブユーザーフィルター
    - **department**: 部署フィルター
    - **sort_by**: ソートフィールド
    - **sort_desc**: 降順ソート
    """
    crud = UserCRUD(db)

    filters = {}
    if search:
        filters["search"] = search
    if is_active is not None:
        filters["is_active"] = is_active
    if department:
        filters["department"] = department

    skip = (page - 1) * per_page
    users, total = crud.get_multi(
        skip=skip, limit=per_page, filters=filters, sort_by=sort_by, sort_desc=sort_desc
    )

    return UserListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
        items=users,
    )


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    新規ユーザー作成（管理者のみ）

    強力なパスワード要件:
    - 最低8文字
    - 大文字、小文字、数字を含む
    """
    crud = UserCRUD(db)
    try:
        user = crud.create(user_in)

        # 作成ログ
        crud.log_activity(
            current_user.id,
            "user_created_by_admin",
            {"created_user_id": user.id},
            request.client.host if request.client else None,
        )

        return user
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報取得"""
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ユーザー詳細取得

    - **user_id**: ユーザーID
    """
    crud = UserCRUD(db)
    user = crud.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ユーザー情報更新

    - 自分自身または管理者のみ更新可能
    - **user_id**: 更新対象ユーザーID
    """
    # 自分自身または管理者のみ更新可能
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud = UserCRUD(db)
    try:
        user = crud.update(user_id, user_in)

        # 更新ログ
        crud.log_activity(
            current_user.id,
            "user_updated",
            {
                "updated_user_id": user_id,
                "fields": list(user_in.dict(exclude_unset=True).keys()),
            },
            request.client.host if request.client else None,
        )

        return user
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    ユーザー削除（ソフトデリート、管理者のみ）

    - **user_id**: 削除対象ユーザーID
    """
    crud = UserCRUD(db)
    try:
        crud.delete(user_id)

        # 削除ログ
        crud.log_activity(
            current_user.id,
            "user_deleted_by_admin",
            {"deleted_user_id": user_id},
            request.client.host if request.client else None,
        )

    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    password_reset: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    パスワードリセット（管理者のみ）

    - **user_id**: 対象ユーザーID
    - **new_password**: 新しいパスワード (強力なパスワード要件あり)
    """
    crud = UserCRUD(db)
    try:
        crud.reset_password(user_id, password_reset.new_password)

        # パスワードリセットログ
        crud.log_activity(
            current_user.id,
            "password_reset_by_admin",
            {"target_user_id": user_id},
            request.client.host if request.client else None,
        )

        return {"message": "Password reset successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/users/{user_id}/verify")
async def verify_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    ユーザー検証（管理者のみ）

    - **user_id**: 検証対象ユーザーID
    """
    crud = UserCRUD(db)
    try:
        crud.verify_user(user_id)

        # 検証ログ
        crud.log_activity(
            current_user.id,
            "user_verified_by_admin",
            {"verified_user_id": user_id},
            request.client.host if request.client else None,
        )

        return {"message": "User verified successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/users/{user_id}/activities", response_model=List[UserActivityResponse])
async def get_user_activities(
    user_id: str,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ユーザーアクティビティ履歴取得

    - 自分自身または管理者のみアクセス可能
    - **user_id**: 対象ユーザーID
    - **limit**: 取得件数上限
    """
    # 自分自身または管理者のみアクセス可能
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud = UserCRUD(db)
    activities = crud.get_user_activities(user_id, limit)
    return activities


@router.get("/users/stats/summary", response_model=UserStatsResponse)
async def get_users_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    ユーザー統計情報（管理者のみ）

    統計情報:
    - 総ユーザー数
    - アクティブユーザー数
    - 検証済みユーザー数
    - 今月の新規ユーザー数
    - 部署別ユーザー数
    """
    crud = UserCRUD(db)
    stats = crud.get_user_stats()

    return UserStatsResponse(
        total_users=stats["total_users"],
        active_users=stats["active_users"],
        verified_users=stats["verified_users"],
        new_users_this_month=stats["new_users_this_month"],
        departments=stats["departments"],
        roles={},  # ロール統計は後で実装
    )
