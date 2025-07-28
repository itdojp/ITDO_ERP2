"""Multi-Factor Authentication (MFA) API endpoints."""

import io

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.mfa import (
    BackupCodesResponse,
    MFADeviceResponse,
    MFADisableRequest,
    MFASetupResponse,
    MFAStatusResponse,
    MFAVerifySetupRequest,
)
from app.services.mfa_service import MFAService

router = APIRouter(prefix="/mfa", tags=["mfa"])


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFAStatusResponse:
    """
    Get current user's MFA status.
    """
    mfa_service = MFAService(db)

    devices = mfa_service.get_user_devices(current_user)
    active_devices = [d for d in devices if d.is_active]

    # Count backup codes
    backup_codes_count = mfa_service.count_active_backup_codes(current_user)

    return MFAStatusResponse(
        mfa_enabled=current_user.mfa_required,
        mfa_setup_at=current_user.mfa_enabled_at,
        devices=[
            MFADeviceResponse(
                id=device.id,
                device_name=device.device_name,
                device_type=device.device_type,
                is_primary=device.is_primary,
                created_at=device.created_at,
                last_used_at=device.last_used_at,
            )
            for device in active_devices
        ],
        backup_codes_count=backup_codes_count,
    )


@router.post("/setup/totp", response_model=MFASetupResponse)
async def setup_totp_mfa(
    device_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFASetupResponse:
    """
    Start TOTP MFA setup process.

    Returns a secret and QR code URL for setting up authenticator app.
    """
    if current_user.mfa_required and current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAは既に有効化されています",
        )

    # Generate secret
    secret = pyotp.random_base32()

    # Create provisional URI for QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ITDO ERP System",
    )

    # Store secret temporarily (not enabled yet)
    current_user.mfa_secret = secret
    db.commit()

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=provisioning_uri,
        manual_entry_key=secret,
        manual_entry_setup={
            "issuer": "ITDO ERP System",
            "account": current_user.email,
            "algorithm": "SHA1",
            "digits": 6,
            "period": 30,
        },
    )


@router.get("/setup/qrcode")
async def get_mfa_qrcode(
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Get QR code image for MFA setup.

    Returns a PNG image of the QR code.
    """
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAセットアップが開始されていません",
        )

    if current_user.mfa_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAは既に有効化されています",
        )

    # Generate QR code
    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ITDO ERP System",
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return StreamingResponse(
        img_byte_arr,
        media_type="image/png",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.post("/setup/verify")
async def verify_mfa_setup(
    request: MFAVerifySetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackupCodesResponse:
    """
    Verify TOTP code and complete MFA setup.

    Returns backup codes on successful verification.
    """
    if current_user.mfa_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAは既に有効化されています",
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAセットアップが開始されていません",
        )

    mfa_service = MFAService(db)

    try:
        # Verify the code
        if not mfa_service.verify_totp(current_user, request.code):
            raise BusinessLogicError("無効な認証コードです")

        # Enable MFA
        backup_codes = mfa_service.enable_mfa(
            current_user,
            device_name=request.device_name,
            device_type="totp",
        )

        # Log activity
        current_user.log_activity(
            db,
            action="mfa_enabled",
            details={"device_type": "totp", "device_name": request.device_name},
        )

        return BackupCodesResponse(
            backup_codes=backup_codes,
            warning="これらのバックアップコードを安全な場所に保管してください。各コードは一度だけ使用できます。",
        )

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Disable MFA for the current user.

    Requires password confirmation.
    """
    if not current_user.mfa_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAは有効化されていません",
        )

    mfa_service = MFAService(db)

    try:
        # Verify password
        from app.core.security import verify_password

        if not verify_password(request.password, current_user.hashed_password):
            raise BusinessLogicError("パスワードが正しくありません")

        # Disable MFA
        mfa_service.disable_mfa(current_user)

        # Log activity
        current_user.log_activity(
            db,
            action="mfa_disabled",
            details={"reason": request.reason},
        )

        return {"message": "MFAを無効化しました"}

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackupCodesResponse:
    """
    Regenerate backup codes for the current user.

    This will invalidate all existing backup codes.
    """
    if not current_user.mfa_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAが有効化されていません",
        )

    mfa_service = MFAService(db)

    # Regenerate codes
    new_codes = mfa_service.regenerate_backup_codes(current_user)

    # Log activity
    current_user.log_activity(
        db,
        action="backup_codes_regenerated",
        details={"count": len(new_codes)},
    )

    return BackupCodesResponse(
        backup_codes=new_codes,
        warning="古いバックアップコードは無効になりました。新しいコードを安全な場所に保管してください。",
    )


@router.post("/backup-codes/verify")
async def verify_backup_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Verify a backup code (for testing purposes).

    Note: In production, backup codes should only be used during login.
    """
    if not current_user.mfa_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFAが有効化されていません",
        )

    mfa_service = MFAService(db)

    # Verify code (without using it)
    is_valid = mfa_service.verify_backup_code(current_user, code, use_code=False)

    return {
        "valid": is_valid,
        "message": "バックアップコードは有効です"
        if is_valid
        else "バックアップコードが無効です",
    }


@router.get("/devices", response_model=list[MFADeviceResponse])
async def list_mfa_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MFADeviceResponse]:
    """
    List all MFA devices for the current user.
    """
    mfa_service = MFAService(db)
    devices = mfa_service.get_user_devices(current_user)

    return [
        MFADeviceResponse(
            id=device.id,
            device_name=device.device_name,
            device_type=device.device_type,
            is_primary=device.is_primary,
            is_active=device.is_active,
            created_at=device.created_at,
            last_used_at=device.last_used_at,
        )
        for device in devices
    ]


@router.delete("/devices/{device_id}")
async def remove_mfa_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Remove an MFA device.

    Cannot remove the last active device.
    """
    mfa_service = MFAService(db)

    try:
        mfa_service.remove_device(current_user, device_id)

        # Log activity
        current_user.log_activity(
            db,
            action="mfa_device_removed",
            details={"device_id": device_id},
        )

        return {"message": "MFAデバイスを削除しました"}

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/devices/{device_id}/primary")
async def set_primary_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Set an MFA device as primary.
    """
    mfa_service = MFAService(db)

    try:
        mfa_service.set_primary_device(current_user, device_id)

        return {"message": "プライマリデバイスを設定しました"}

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
