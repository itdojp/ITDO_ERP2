"""Password security API endpoints for Issue #41."""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.password_security import (
    AccountLockoutInfo,
    ForcePasswordChangeRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordExpiryInfo,
    PasswordPolicySchema,
    PasswordStrengthRequest,
    PasswordStrengthResponse,
    PasswordValidationRequest,
    PasswordValidationResponse,
    SecurityStatusResponse,
    UnlockAccountRequest,
)
from app.services.password_policy_service import PasswordPolicyService

router = APIRouter()


@router.get("/policy")
async def get_password_policy(
    organization_id: Optional[int] = Query(None, description="Organization ID (null for global policy)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordPolicySchema:
    """
    Get password policy configuration.
    パスワードポリシー設定の取得
    """
    service = PasswordPolicyService(db)
    
    # If organization_id is specified, get that policy; otherwise get for current user
    if organization_id is not None:
        # Check if user has permission to view organization policy
        if not (current_user.is_superuser or current_user.organization_id == organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Cannot view this organization's policy."
            )
        
        # Create a temporary user context for the organization
        temp_user_id = current_user.id
        policy = await service.get_policy_for_user(temp_user_id)
    else:
        policy = await service.get_policy_for_user(current_user.id)
    
    return PasswordPolicySchema.from_orm(policy)


@router.post("/validate")
async def validate_password(
    request: PasswordValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordValidationResponse:
    """
    Validate password against policy and history.
    パスワードのポリシーと履歴に対する検証
    """
    # Check permissions - users can only validate for themselves unless admin
    if request.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only validate password for yourself."
        )
    
    service = PasswordPolicyService(db)
    
    try:
        result = await service.validate_password(
            password=request.password,
            user_id=request.user_id,
            check_history=request.check_history
        )
        
        return PasswordValidationResponse(
            is_valid=result["is_valid"],
            errors=result["errors"],
            strength_score=result["strength_score"],
            policy_name=result["policy_name"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate password: {str(e)}"
        )


@router.post("/change")
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordChangeResponse:
    """
    Change user password with validation.
    パスワード変更（検証付き）
    """
    service = PasswordPolicyService(db)
    
    try:
        result = await service.change_password(
            user_id=current_user.id,
            new_password=request.new_password,
            current_password=request.current_password or "",
            force_change=request.force_change and current_user.is_superuser  # Only admins can force
        )
        
        return PasswordChangeResponse(
            success=result["success"],
            message=result.get("message"),
            errors=result.get("errors", []),
            strength_score=result.get("strength_score")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.post("/strength-check")
async def check_password_strength(
    request: PasswordStrengthRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordStrengthResponse:
    """
    Check password strength without validation.
    パスワード強度チェック（検証なし）
    """
    # Use current user ID if not specified
    user_id = request.user_id or current_user.id
    
    # Check permissions
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only check strength for yourself."
        )
    
    service = PasswordPolicyService(db)
    
    try:
        policy = await service.get_policy_for_user(user_id)
        strength_score = policy.get_password_strength_score(request.password)
        
        # Generate feedback based on score
        feedback = []
        if strength_score < 25:
            feedback.extend([
                "Password is too weak",
                "Consider using a longer password",
                "Add different types of characters (uppercase, numbers, symbols)"
            ])
        elif strength_score < 50:
            feedback.extend([
                "Password strength is fair",
                "Consider adding more character variety",
                "Increase length for better security"
            ])
        elif strength_score < 75:
            feedback.extend([
                "Good password strength",
                "Consider adding more unique characters"
            ])
        else:
            feedback.append("Excellent password strength!")
        
        return PasswordStrengthResponse(
            strength_score=strength_score,
            strength_level="",  # Will be set by validator
            feedback=feedback
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check password strength: {str(e)}"
        )


@router.get("/users/{user_id}/security-status")
async def get_user_security_status(
    user_id: int = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SecurityStatusResponse:
    """
    Get comprehensive security status for a user.
    ユーザーの包括的なセキュリティステータス取得
    """
    # Check permissions
    if user_id != current_user.id and not (
        current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view own security status or require admin privileges."
        )
    
    service = PasswordPolicyService(db)
    
    try:
        # Get user info
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get security status components
        is_locked = await service.is_account_locked(user_id)
        expiry_info = await service.check_password_expiry(user_id)
        policy = await service.get_policy_for_user(user_id)
        
        return SecurityStatusResponse(
            user_id=user_id,
            account_locked=is_locked,
            password_expired=expiry_info["is_expired"],
            password_expiry_warning=expiry_info["warning"],
            days_until_expiry=expiry_info["days_until_expiry"],
            failed_login_attempts=user.failed_login_attempts,
            must_change_password=user.password_must_change,
            last_login=user.last_login_at,
            password_last_changed=user.password_changed_at,
            policy_name=policy.name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security status: {str(e)}"
        )


@router.post("/users/{user_id}/unlock")
async def unlock_user_account(
    user_id: int = Path(..., description="User ID"),
    *,
    request: UnlockAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Unlock a user account (admin only).
    ユーザーアカウントのロック解除（管理者のみ）
    """
    # Check admin permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required to unlock accounts."
        )
    
    service = PasswordPolicyService(db)
    
    try:
        success = await service.unlock_account(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log the unlock event
        # TODO: Add to audit log
        
        return {
            "success": True,
            "message": f"Account {user_id} unlocked successfully",
            "unlocked_by": current_user.id,
            "unlocked_at": datetime.utcnow().isoformat(),
            "reason": request.reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock account: {str(e)}"
        )


@router.post("/users/{user_id}/force-password-change")
async def force_password_change(
    user_id: int = Path(..., description="User ID"),
    request: ForcePasswordChangeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Force a user to change password on next login (admin only).
    次回ログイン時のパスワード変更強制（管理者のみ）
    """
    # Check admin permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required to force password changes."
        )
    
    try:
        from sqlalchemy import select
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Set force password change flag
        user.password_must_change = True
        await db.commit()
        
        # TODO: Add to audit log
        
        return {
            "success": True,
            "message": f"User {user_id} will be required to change password on next login",
            "forced_by": current_user.id,
            "forced_at": datetime.utcnow().isoformat(),
            "reason": request.reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force password change: {str(e)}"
        )


@router.get("/users/{user_id}/password-expiry")
async def get_password_expiry_info(
    user_id: int = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PasswordExpiryInfo:
    """
    Get password expiry information for a user.
    ユーザーのパスワード有効期限情報取得
    """
    # Check permissions
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view own password expiry information."
        )
    
    service = PasswordPolicyService(db)
    
    try:
        expiry_info = await service.check_password_expiry(user_id)
        
        return PasswordExpiryInfo(
            is_expired=expiry_info["is_expired"],
            days_until_expiry=expiry_info["days_until_expiry"],
            warning=expiry_info["warning"],
            password_age_days=expiry_info["password_age_days"],
            policy_expiry_days=expiry_info["policy_expiry_days"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get password expiry information: {str(e)}"
        )