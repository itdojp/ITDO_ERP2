from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.product_extended_v30 import (
    DuplicateError,
    NotFoundError,
    ProductCategoryCRUD,
    ProductCRUD,
    SupplierCRUD,
)
from app.models.user_extended import User
from app.schemas.product_complete_v30 import (
    BulkPriceUpdateRequest,
    BulkPriceUpdateResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductListResponse,
    ProductPriceHistoryResponse,
    ProductResponse,
    ProductStatsResponse,
    ProductUpdate,
    SupplierCreate,
    SupplierResponse,
)

router = APIRouter()


# Mock security dependency
async def get_current_user() -> User:
    """Mock current user - replace with actual implementation"""
    user = User()
    user.id = "current-user-id"
    user.is_superuser = True
    return user


async def require_admin() -> User:
    """Mock admin requirement"""
    return await get_current_user()


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    product_status: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    is_sellable: Optional[bool] = Query(None),
    low_stock: Optional[bool] = Query(None),
    out_of_stock: Optional[bool] = Query(None),
    price_min: Optional[Decimal] = Query(None),
    price_max: Optional[Decimal] = Query(None),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    商品一覧取得（高度なフィルタリング対応）

    - **page**: ページ番号
    - **per_page**: 1ページあたりの件数
    - **search**: 検索キーワード (名前、SKU、説明、ブランド)
    - **category_id**: カテゴリフィルター
    - **supplier_id**: サプライヤーフィルター
    - **brand**: ブランドフィルター
    - **product_status**: 商品ステータスフィルター
    - **low_stock**: 低在庫商品フィルター
    - **out_of_stock**: 在庫切れ商品フィルター
    - **price_min/max**: 価格範囲フィルター
    """
    crud = ProductCRUD(db)

    filters = {}
    for key, value in {
        "search": search,
        "category_id": category_id,
        "supplier_id": supplier_id,
        "brand": brand,
        "product_status": product_status,
        "product_type": product_type,
        "is_sellable": is_sellable,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "price_min": price_min,
        "price_max": price_max,
    }.items():
        if value is not None:
            filters[key] = value

    skip = (page - 1) * per_page
    products, total = crud.get_multi(
        skip=skip, limit=per_page, filters=filters, sort_by=sort_by, sort_desc=sort_desc
    )

    return ProductListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
        items=products,
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    product_in: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    新規商品作成（管理者のみ）

    - **sku**: 商品SKU（一意）
    - **name**: 商品名
    - **selling_price**: 販売価格（必須）
    - **category_id**: カテゴリID
    - **supplier_id**: サプライヤーID
    """
    crud = ProductCRUD(db)
    try:
        product = crud.create(product_in)
        return product
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    商品詳細取得

    - **product_id**: 商品ID
    """
    crud = ProductCRUD(db)
    product = crud.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # available_quantity を計算
    product.available_quantity = max(
        0, product.stock_quantity - product.reserved_quantity
    )
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_in: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    商品情報更新（管理者のみ）

    - **product_id**: 更新対象商品ID
    """
    crud = ProductCRUD(db)
    try:
        product = crud.update(product_id, product_in)
        return product
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    商品削除（ソフトデリート、管理者のみ）

    - **product_id**: 削除対象商品ID
    - 在庫がある場合は削除不可
    """
    crud = ProductCRUD(db)
    try:
        crud.delete(product_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/products/{product_id}/inventory/adjust")
async def adjust_product_inventory(
    product_id: str,
    movement: InventoryMovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    在庫調整（管理者のみ）

    - **product_id**: 商品ID
    - **movement_type**: 移動タイプ (in, out, adjustment)
    - **quantity**: 数量（adjustmentの場合は絶対値）
    - **reason**: 調整理由
    """
    crud = ProductCRUD(db)
    try:
        crud.adjust_inventory(product_id, movement, current_user.id)
        return {"message": "Inventory adjusted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/products/{product_id}/inventory/movements",
    response_model=List[InventoryMovementResponse],
)
async def get_product_inventory_movements(
    product_id: str,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    商品の在庫移動履歴取得

    - **product_id**: 商品ID
    - **limit**: 取得件数上限
    """
    from app.models.product_extended import InventoryMovement

    movements = (
        db.query(InventoryMovement)
        .filter(InventoryMovement.product_id == product_id)
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
        .all()
    )
    return movements


@router.get(
    "/products/{product_id}/price-history",
    response_model=List[ProductPriceHistoryResponse],
)
async def get_product_price_history(
    product_id: str,
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    商品の価格履歴取得

    - **product_id**: 商品ID
    - **limit**: 取得件数上限
    """
    from app.models.product_extended import ProductPriceHistory

    price_history = (
        db.query(ProductPriceHistory)
        .filter(ProductPriceHistory.product_id == product_id)
        .order_by(ProductPriceHistory.effective_from.desc())
        .limit(limit)
        .all()
    )
    return price_history


@router.get("/products/stats/summary", response_model=ProductStatsResponse)
async def get_product_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    商品統計情報（管理者のみ）

    統計情報:
    - 総商品数・ステータス別商品数
    - カテゴリ別・ブランド別・サプライヤー別商品数
    - 在庫状況（低在庫・在庫切れ）
    - 在庫総額
    """
    crud = ProductCRUD(db)
    stats = crud.get_statistics()
    return ProductStatsResponse(**stats)


@router.post("/products/bulk/price-update", response_model=BulkPriceUpdateResponse)
async def bulk_update_product_prices(
    request_data: BulkPriceUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    商品価格一括更新（管理者のみ）

    - **product_ids**: 更新対象商品IDリスト
    - **price_type**: 価格タイプ (cost_price, selling_price, list_price)
    - **adjustment_type**: 調整タイプ (amount, percentage)
    - **adjustment_value**: 調整値
    - **reason**: 更新理由
    """
    crud = ProductCRUD(db)
    result = crud.bulk_update_prices(
        request_data.product_ids,
        request_data.price_type,
        request_data.adjustment_type,
        request_data.adjustment_value,
        request_data.reason,
        current_user.id,
    )
    return BulkPriceUpdateResponse(**result)


# Product Categories Management


@router.get("/products/categories", response_model=List[ProductCategoryResponse])
async def list_product_categories(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    parent_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    商品カテゴリ一覧取得

    - **parent_id**: 親カテゴリID（階層フィルター）
    - **is_active**: アクティブカテゴリフィルター
    """
    crud = ProductCategoryCRUD(db)
    skip = (page - 1) * per_page
    categories, total = crud.get_multi(
        skip=skip, limit=per_page, parent_id=parent_id, is_active=is_active
    )
    return categories


@router.post(
    "/products/categories", response_model=ProductCategoryResponse, status_code=201
)
async def create_product_category(
    category_in: ProductCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    商品カテゴリ作成（管理者のみ）

    - **name**: カテゴリ名
    - **code**: カテゴリコード（一意）
    - **parent_id**: 親カテゴリID（階層構造用）
    """
    crud = ProductCategoryCRUD(db)
    try:
        category = crud.create(category_in)
        return category
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Suppliers Management


@router.get("/suppliers", response_model=List[SupplierResponse])
async def list_suppliers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_preferred: Optional[bool] = Query(None),
    supplier_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    サプライヤー一覧取得

    - **search**: 検索キーワード (名前、コード)
    - **is_active**: アクティブサプライヤーフィルター
    - **is_preferred**: 優先サプライヤーフィルター
    - **supplier_type**: サプライヤータイプフィルター
    """
    crud = SupplierCRUD(db)

    filters = {}
    for key, value in {
        "search": search,
        "is_active": is_active,
        "is_preferred": is_preferred,
        "supplier_type": supplier_type,
    }.items():
        if value is not None:
            filters[key] = value

    skip = (page - 1) * per_page
    suppliers, total = crud.get_multi(skip=skip, limit=per_page, filters=filters)
    return suppliers


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    supplier_in: SupplierCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    サプライヤー作成（管理者のみ）

    - **name**: サプライヤー名
    - **code**: サプライヤーコード（一意）
    - **supplier_type**: サプライヤータイプ (manufacturer, distributor, wholesaler)
    """
    crud = SupplierCRUD(db)
    try:
        supplier = crud.create(supplier_in)
        return supplier
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))
