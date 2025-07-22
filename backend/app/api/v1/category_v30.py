from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.crud.category_v30 import (
    CategoryCRUD, CategoryAttributeCRUD, CategoryPricingRuleCRUD,
    NotFoundError, DuplicateError, InvalidOperationError
)
from app.schemas.category_v30 import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse,
    CategoryAttributeCreate, CategoryAttributeUpdate, CategoryAttributeResponse, CategoryAttributeListResponse,
    CategoryPricingRuleCreate, CategoryPricingRuleUpdate, CategoryPricingRuleResponse, CategoryPricingRuleListResponse,
    CategoryAnalyticsResponse, CategoryMoveRequest, CategoryBulkOperationRequest,
    CategoryImportRequest, CategoryExportRequest, CategoryHierarchyListResponse, CategoryHierarchyResponse
)

router = APIRouter(prefix="/categories", tags=["categories"])


# =============================================================================
# Category Management Endpoints
# =============================================================================

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ作成"""
    try:
        category_crud = CategoryCRUD(db)
        return category_crud.create(category, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ詳細取得"""
    category_crud = CategoryCRUD(db)
    category = category_crud.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("/", response_model=CategoryListResponse)
def list_categories(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    parent_id: Optional[str] = None,
    category_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    level: Optional[int] = Query(None, ge=1),
    industry_vertical: Optional[str] = None,
    business_unit: Optional[str] = None,
    tax_category: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    profitability_rating: Optional[str] = None,
    abc_analysis_class: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: Optional[str] = "category_name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    
    # Build filters dictionary
    filter_params = {
        "parent_id": parent_id,
        "category_type": category_type,
        "is_active": is_active,
        "level": level,
        "industry_vertical": industry_vertical,
        "business_unit": business_unit,
        "tax_category": tax_category,
        "lifecycle_stage": lifecycle_stage,
        "profitability_rating": profitability_rating,
        "abc_analysis_class": abc_analysis_class,
        "search": search,
        "tags": tags,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    
    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    category_crud = CategoryCRUD(db)
    categories, total = category_crud.get_multi(skip=skip, limit=per_page, filters=filters)
    
    pages = (total + per_page - 1) // per_page
    
    return CategoryListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=categories
    )


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ更新"""
    try:
        category_crud = CategoryCRUD(db)
        return category_crud.update(category_id, category_update, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{category_id}/activate", response_model=CategoryResponse)
def activate_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリアクティブ化"""
    try:
        category_crud = CategoryCRUD(db)
        return category_crud.activate(category_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{category_id}/deactivate", response_model=CategoryResponse)
def deactivate_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ非アクティブ化"""
    try:
        category_crud = CategoryCRUD(db)
        return category_crud.deactivate(category_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{category_id}/move", response_model=CategoryResponse)
def move_category(
    category_id: str,
    move_request: CategoryMoveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ移動"""
    try:
        category_crud = CategoryCRUD(db)
        return category_crud.move_category(
            move_request.category_id, 
            move_request.new_parent_id, 
            current_user["sub"]
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ削除"""
    try:
        category_crud = CategoryCRUD(db)
        success = category_crud.delete(category_id, current_user["sub"])
        return {"message": "Category deleted successfully"} if success else {"message": "Failed to delete category"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
def get_category_children(
    category_id: str,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """子カテゴリ取得"""
    category_crud = CategoryCRUD(db)
    
    # 親カテゴリの存在確認
    parent = category_crud.get_by_id(category_id)
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found")
    
    children = category_crud.get_by_parent(category_id)
    
    if not include_inactive:
        children = [c for c in children if c.is_active]
    
    return children


@router.get("/{category_id}/descendants", response_model=List[CategoryResponse])
def get_category_descendants(
    category_id: str,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """子孫カテゴリ取得（全階層）"""
    try:
        category_crud = CategoryCRUD(db)
        descendants = category_crud.get_descendants(category_id, include_inactive)
        return descendants
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{category_id}/hierarchy-path", response_model=List[CategoryResponse])
def get_category_hierarchy_path(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ階層パス取得（ルートから現在まで）"""
    category_crud = CategoryCRUD(db)
    path = category_crud.get_hierarchy_path(category_id)
    
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    return path


# =============================================================================
# Category Attributes Management
# =============================================================================

@router.post("/{category_id}/attributes", response_model=CategoryAttributeResponse, status_code=status.HTTP_201_CREATED)
def create_category_attribute(
    category_id: str,
    attribute: CategoryAttributeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ属性作成"""
    # カテゴリ存在確認
    category_crud = CategoryCRUD(db)
    if not category_crud.get_by_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # 属性のcategory_idを設定
    attribute.category_id = category_id
    
    try:
        attribute_crud = CategoryAttributeCRUD(db)
        return attribute_crud.create(attribute, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{category_id}/attributes", response_model=List[CategoryAttributeResponse])
def list_category_attributes(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ属性一覧取得"""
    # カテゴリ存在確認
    category_crud = CategoryCRUD(db)
    if not category_crud.get_by_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    attribute_crud = CategoryAttributeCRUD(db)
    return attribute_crud.get_by_category(category_id)


@router.get("/attributes/{attribute_id}", response_model=CategoryAttributeResponse)
def get_category_attribute(
    attribute_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ属性詳細取得"""
    attribute_crud = CategoryAttributeCRUD(db)
    attribute = attribute_crud.get_by_id(attribute_id)
    if not attribute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found")
    return attribute


@router.put("/attributes/{attribute_id}", response_model=CategoryAttributeResponse)
def update_category_attribute(
    attribute_id: str,
    attribute_update: CategoryAttributeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ属性更新"""
    try:
        attribute_crud = CategoryAttributeCRUD(db)
        return attribute_crud.update(attribute_id, attribute_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/attributes/{attribute_id}")
def delete_category_attribute(
    attribute_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ属性削除"""
    try:
        attribute_crud = CategoryAttributeCRUD(db)
        success = attribute_crud.delete(attribute_id)
        return {"message": "Attribute deleted successfully"} if success else {"message": "Failed to delete attribute"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Category Pricing Rules Management
# =============================================================================

@router.post("/{category_id}/pricing-rules", response_model=CategoryPricingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_pricing_rule(
    category_id: str,
    rule: CategoryPricingRuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルール作成"""
    # カテゴリ存在確認
    category_crud = CategoryCRUD(db)
    if not category_crud.get_by_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # ルールのcategory_idを設定
    rule.category_id = category_id
    
    rule_crud = CategoryPricingRuleCRUD(db)
    return rule_crud.create(rule, current_user["sub"])


@router.get("/{category_id}/pricing-rules", response_model=List[CategoryPricingRuleResponse])
def list_category_pricing_rules(
    category_id: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ価格ルール一覧取得"""
    # カテゴリ存在確認
    category_crud = CategoryCRUD(db)
    if not category_crud.get_by_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    rule_crud = CategoryPricingRuleCRUD(db)
    return rule_crud.get_by_category(category_id, active_only)


@router.get("/pricing-rules", response_model=CategoryPricingRuleListResponse)
def list_all_pricing_rules(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    rule_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """全価格ルール一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    
    filter_params = {
        "category_id": category_id,
        "rule_type": rule_type,
        "is_active": is_active,
        "currency": currency
    }
    
    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    rule_crud = CategoryPricingRuleCRUD(db)
    rules, total = rule_crud.get_multi(skip=skip, limit=per_page, filters=filters)
    
    pages = (total + per_page - 1) // per_page
    
    return CategoryPricingRuleListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=rules
    )


@router.get("/pricing-rules/{rule_id}", response_model=CategoryPricingRuleResponse)
def get_pricing_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルール詳細取得"""
    rule_crud = CategoryPricingRuleCRUD(db)
    rule = rule_crud.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")
    return rule


@router.put("/pricing-rules/{rule_id}", response_model=CategoryPricingRuleResponse)
def update_pricing_rule(
    rule_id: str,
    rule_update: CategoryPricingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルール更新"""
    try:
        rule_crud = CategoryPricingRuleCRUD(db)
        return rule_crud.update(rule_id, rule_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/pricing-rules/{rule_id}/activate", response_model=CategoryPricingRuleResponse)
def activate_pricing_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルールアクティブ化"""
    try:
        rule_crud = CategoryPricingRuleCRUD(db)
        return rule_crud.activate(rule_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/pricing-rules/{rule_id}/deactivate", response_model=CategoryPricingRuleResponse)
def deactivate_pricing_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルール非アクティブ化"""
    try:
        rule_crud = CategoryPricingRuleCRUD(db)
        return rule_crud.deactivate(rule_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/pricing-rules/{rule_id}")
def delete_pricing_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """価格ルール削除"""
    try:
        rule_crud = CategoryPricingRuleCRUD(db)
        success = rule_crud.delete(rule_id)
        return {"message": "Pricing rule deleted successfully"} if success else {"message": "Failed to delete pricing rule"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Category Analytics and Reporting
# =============================================================================

@router.get("/analytics", response_model=CategoryAnalyticsResponse)
def get_category_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    category_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ分析データ取得"""
    filters = {}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if category_type:
        filters["category_type"] = category_type
    
    category_crud = CategoryCRUD(db)
    analytics = category_crud.get_analytics(filters)
    
    return CategoryAnalyticsResponse(**analytics)


@router.get("/tree", response_model=List[Dict[str, Any]])
def get_category_tree(
    root_id: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリツリー構造取得"""
    category_crud = CategoryCRUD(db)
    tree = category_crud.get_tree_structure(root_id, include_inactive)
    return tree


@router.get("/hierarchy-view", response_model=CategoryHierarchyListResponse)
def get_category_hierarchy_view(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ階層ビュー取得"""
    hierarchy_views = db.query(CategoryHierarchyView).order_by(
        CategoryHierarchyView.hierarchy_level,
        CategoryHierarchyView.full_path
    ).all()
    
    return CategoryHierarchyListResponse(
        total=len(hierarchy_views),
        items=hierarchy_views
    )


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/bulk-operations")
def bulk_category_operations(
    operation_request: CategoryBulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリ一括操作"""
    category_crud = CategoryCRUD(db)
    results = {"successful": [], "failed": []}
    
    for category_id in operation_request.category_ids:
        try:
            if operation_request.operation == "activate":
                category_crud.activate(category_id, current_user["sub"])
                results["successful"].append(category_id)
            elif operation_request.operation == "deactivate":
                category_crud.deactivate(category_id, current_user["sub"])
                results["successful"].append(category_id)
            elif operation_request.operation == "delete":
                category_crud.delete(category_id, current_user["sub"])
                results["successful"].append(category_id)
            else:
                results["failed"].append({
                    "category_id": category_id,
                    "error": f"Unsupported operation: {operation_request.operation}"
                })
        except Exception as e:
            results["failed"].append({
                "category_id": category_id,
                "error": str(e)
            })
    
    return {
        "message": f"Bulk operation completed. {len(results['successful'])} successful, {len(results['failed'])} failed.",
        "results": results
    }


# =============================================================================
# Import/Export Operations
# =============================================================================

@router.post("/import")
def import_categories(
    import_request: CategoryImportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリインポート"""
    # Import implementation would go here
    # This would handle CSV, JSON, or XML format imports
    return {
        "message": "Import functionality not yet implemented",
        "import_format": import_request.import_format,
        "validate_only": import_request.validate_only
    }


@router.post("/export")
def export_categories(
    export_request: CategoryExportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリエクスポート"""
    # Export implementation would go here
    # This would handle CSV, JSON, XML, or Excel format exports
    return {
        "message": "Export functionality not yet implemented",
        "export_format": export_request.export_format,
        "include_hierarchy": export_request.include_hierarchy
    }


# =============================================================================
# Code Lookup Endpoint
# =============================================================================

@router.get("/by-code/{category_code}", response_model=CategoryResponse)
def get_category_by_code(
    category_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """カテゴリコードによる検索"""
    category_crud = CategoryCRUD(db)
    category = category_crud.get_by_code(category_code)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category