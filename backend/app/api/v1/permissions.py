import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class ResourceType(str, Enum):
    PRODUCTS = "products"
    INVENTORY = "inventory"
    SALES_ORDERS = "sales_orders"
    USERS = "users"
    REPORTS = "reports"
    SETTINGS = "settings"

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: str
    created_at: datetime

class RoleCreate(RoleBase):
    pass

# モックデータストア
roles_db = {}

@router.post("/roles", response_model=Role, status_code=201)
async def create_role(role: RoleCreate) -> dict:
    """ロールを作成"""
    role_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_role = {
        "id": role_id,
        "name": role.name,
        "description": role.description,
        "created_at": now
    }
    
    roles_db[role_id] = new_role
    return new_role

@router.get("/roles")
async def list_roles() -> None:
    """ロール一覧を取得"""
    return list(roles_db.values())

@router.post("/check-permission")
async def check_permission(user_id: str, resource: str, permission_type: str) -> dict:
    """ユーザーの権限チェック"""
    return {"has_permission": True, "user_id": user_id, "resource": resource, "permission_type": permission_type}
EOF < /dev/null
