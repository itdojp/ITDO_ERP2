from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.schemas.organization_complete_v30 import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, OrganizationListResponse,
    OrganizationTreeNode, OrganizationHierarchyResponse, OrganizationStatsResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    AddressCreate, AddressResponse, ContactCreate, ContactResponse
)
from app.crud.organization_extended_v30 import (
    OrganizationCRUD, DepartmentCRUD, AddressCRUD, ContactCRUD,
    NotFoundError, DuplicateError
)
from app.models.user_extended import User

router = APIRouter()

# Mock security dependency
async def get_current_user() -> User:
    """Mock current user - replace with actual implementation"""
    user = User()
    user.id = "current-user-id"
    user.is_superuser = True
    return user

async def require_admin() -> User:
    """Mock admin requirement - replace with actual implementation"""
    return await get_current_user()

@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    organization_type: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織一覧取得（ページネーション、フィルタリング、ソート対応）
    
    - **page**: ページ番号 (1から開始)
    - **per_page**: 1ページあたりの件数 (1-100)
    - **search**: 検索キーワード (名前、コード、説明)
    - **is_active**: アクティブ組織フィルター
    - **organization_type**: 組織タイプフィルター
    - **industry**: 業界フィルター
    - **country**: 国フィルター
    - **parent_id**: 親組織IDフィルター
    """
    crud = OrganizationCRUD(db)

    filters = {}
    if search:
        filters["search"] = search
    if is_active is not None:
        filters["is_active"] = is_active
    if organization_type:
        filters["organization_type"] = organization_type
    if industry:
        filters["industry"] = industry
    if country:
        filters["country"] = country
    if parent_id:
        filters["parent_id"] = parent_id

    skip = (page - 1) * per_page
    organizations, total = crud.get_multi(
        skip=skip,
        limit=per_page,
        filters=filters,
        sort_by=sort_by,
        sort_desc=sort_desc
    )

    return OrganizationListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
        items=organizations
    )

@router.post("/organizations", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    org_in: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    新規組織作成（管理者のみ）
    
    - **code**: 組織コード（英数字、ハイフン、アンダースコアのみ）
    - **name**: 組織名
    - **parent_id**: 親組織ID（階層構造用）
    - **organization_type**: 組織タイプ (corporation, division, department, team)
    """
    crud = OrganizationCRUD(db)
    try:
        organization = crud.create(org_in)
        return organization
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織詳細取得
    
    - **org_id**: 組織ID
    """
    crud = OrganizationCRUD(db)
    organization = crud.get_by_id(org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_in: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織情報更新（管理者のみ）
    
    - **org_id**: 更新対象組織ID
    """
    crud = OrganizationCRUD(db)
    try:
        organization = crud.update(org_id, org_in)
        return organization
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")

@router.delete("/organizations/{org_id}", status_code=204)
async def delete_organization(
    org_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織削除（ソフトデリート、管理者のみ）
    
    - **org_id**: 削除対象組織ID
    - 子組織がある場合は削除不可
    """
    crud = OrganizationCRUD(db)
    try:
        crud.delete(org_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/organizations/{org_id}/hierarchy", response_model=OrganizationHierarchyResponse)
async def get_organization_hierarchy(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織階層構造取得
    
    - **org_id**: 組織ID
    - 子組織と部署を含む階層構造を返す
    """
    crud = OrganizationCRUD(db)
    organization = crud.get_hierarchy(org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # レスポンス構築（実際の実装ではより詳細な変換が必要）
    return {
        "organization": organization,
        "departments": organization.departments or [],
        "children": []
    }

@router.get("/organizations/tree", response_model=List[OrganizationTreeNode])
async def get_organization_tree(
    parent_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織ツリー構造取得
    
    - **parent_id**: 親組織ID（指定がない場合はルート組織を返す）
    """
    crud = OrganizationCRUD(db)
    organizations = crud.get_tree(parent_id)
    
    # ツリー構造に変換
    tree_nodes = []
    for org in organizations:
        tree_nodes.append(OrganizationTreeNode(
            id=org.id,
            name=org.name,
            code=org.code,
            level=org.level,
            is_active=org.is_active,
            children=[]  # 実際の実装では再帰的に子要素を取得
        ))
    
    return tree_nodes

@router.get("/organizations/stats/summary", response_model=OrganizationStatsResponse)
async def get_organization_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織統計情報（管理者のみ）
    
    統計情報:
    - 総組織数
    - アクティブ組織数
    - 本社数
    - タイプ別組織数
    - 業界別組織数
    - 国別組織数
    - 総従業員数
    - 総部署数
    """
    crud = OrganizationCRUD(db)
    stats = crud.get_statistics()
    return OrganizationStatsResponse(**stats)

# Department Management Endpoints

@router.get("/organizations/{org_id}/departments", response_model=List[DepartmentResponse])
async def list_departments(
    org_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    department_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織の部署一覧取得
    
    - **org_id**: 組織ID
    - **is_active**: アクティブ部署フィルター
    - **department_type**: 部署タイプフィルター
    - **search**: 検索キーワード
    """
    crud = DepartmentCRUD(db)
    
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if department_type:
        filters["department_type"] = department_type
    if search:
        filters["search"] = search

    skip = (page - 1) * per_page
    departments, total = crud.get_multi(
        skip=skip,
        limit=per_page,
        organization_id=org_id,
        filters=filters
    )

    return departments

@router.post("/organizations/{org_id}/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(
    org_id: str,
    dept_in: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    部署作成（管理者のみ）
    
    - **org_id**: 組織ID
    - **code**: 部署コード
    - **name**: 部署名
    - **department_type**: 部署タイプ (operational, support, management)
    """
    # 組織IDを設定
    dept_in.organization_id = org_id
    
    crud = DepartmentCRUD(db)
    try:
        department = crud.create(dept_in)
        return department
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Address Management Endpoints

@router.get("/organizations/{org_id}/addresses", response_model=List[AddressResponse])
async def list_organization_addresses(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織の住所一覧取得
    
    - **org_id**: 組織ID
    """
    crud = AddressCRUD(db)
    addresses = crud.get_by_organization(org_id)
    return addresses

@router.post("/organizations/{org_id}/addresses", response_model=AddressResponse, status_code=201)
async def create_organization_address(
    org_id: str,
    address_in: AddressCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織住所作成（管理者のみ）
    
    - **org_id**: 組織ID
    - **address_type**: 住所タイプ (headquarters, branch, warehouse等)
    - **is_primary**: プライマリ住所フラグ
    """
    # 組織IDを設定
    address_in.organization_id = org_id
    
    crud = AddressCRUD(db)
    address = crud.create(address_in)
    return address

# Contact Management Endpoints

@router.get("/organizations/{org_id}/contacts", response_model=List[ContactResponse])
async def list_organization_contacts(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    組織の連絡先一覧取得
    
    - **org_id**: 組織ID
    """
    crud = ContactCRUD(db)
    contacts = crud.get_by_organization(org_id)
    return contacts

@router.post("/organizations/{org_id}/contacts", response_model=ContactResponse, status_code=201)
async def create_organization_contact(
    org_id: str,
    contact_in: ContactCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織連絡先作成（管理者のみ）
    
    - **org_id**: 組織ID
    - **name**: 連絡先担当者名
    - **contact_type**: 連絡先タイプ (primary, billing, technical, emergency)
    - **is_primary**: プライマリ連絡先フラグ
    """
    # 組織IDを設定
    contact_in.organization_id = org_id
    
    crud = ContactCRUD(db)
    contact = crud.create(contact_in)
    return contact