from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class Organization(OrganizationBase):
    id: str
    level: int
    children: List[Dict[str, Any]]
    created_at: datetime

class OrganizationCreate(OrganizationBase):
    pass

# モックデータストア
organizations_db = {}

@router.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(org: OrganizationCreate):
    """組織を作成"""
    org_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # レベル計算
    level = 0
    if org.parent_id and org.parent_id in organizations_db:
        parent = organizations_db[org.parent_id]
        level = parent["level"] + 1
    
    new_org = {
        "id": org_id,
        "name": org.name,
        "description": org.description,
        "parent_id": org.parent_id,
        "level": level,
        "children": [],
        "created_at": now
    }
    
    organizations_db[org_id] = new_org
    
    # 親組織の子リストに追加
    if org.parent_id and org.parent_id in organizations_db:
        organizations_db[org.parent_id]["children"].append(new_org)
    
    return new_org

@router.get("/organizations", response_model=List[Organization])
async def list_organizations():
    """全組織を取得"""
    return list(organizations_db.values())

@router.get("/organizations/tree")
async def get_organization_tree():
    """組織階層ツリーを取得"""
    roots = [org for org in organizations_db.values() if org["parent_id"] is None]
    return {"tree": roots}

@router.get("/organizations/{org_id}/children")
async def get_organization_children(org_id: str):
    """子組織を取得"""
    if org_id not in organizations_db:
        raise HTTPException(status_code=404, detail="組織が見つかりません")
    
    return organizations_db[org_id]["children"]
EOF < /dev/null
