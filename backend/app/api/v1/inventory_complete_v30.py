from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.inventory_extended_v30 import (
    CycleCountCRUD,
    DuplicateError,
    InsufficientStockError,
    InventoryItemCRUD,
    NotFoundError,
    StockAlertCRUD,
    WarehouseCRUD,
)
from app.models.user_extended import User
from app.schemas.inventory_complete_v30 import (
    CycleCountCreate,
    CycleCountItemResponse,
    CycleCountItemUpdate,
    CycleCountResponse,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryReservationCreate,
    InventoryReservationResponse,
    InventoryStatsResponse,
    InventoryValuationResponse,
    StockAlertResponse,
    StockLevelSummaryResponse,
    StockMovementCreate,
    StockMovementResponse,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
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


# Warehouse Management


@router.get("/warehouses", response_model=List[WarehouseResponse])
async def list_warehouses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    warehouse_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    倉庫一覧取得

    - **search**: 検索キーワード (名前、コード)
    - **is_active**: アクティブ倉庫フィルター
    - **warehouse_type**: 倉庫タイプフィルター
    """
    crud = WarehouseCRUD(db)

    filters = {}
    for key, value in {
        "search": search,
        "is_active": is_active,
        "warehouse_type": warehouse_type,
    }.items():
        if value is not None:
            filters[key] = value

    skip = (page - 1) * per_page
    warehouses, total = crud.get_multi(skip=skip, limit=per_page, filters=filters)

    return warehouses


@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    warehouse_in: WarehouseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    倉庫作成（管理者のみ）

    - **code**: 倉庫コード（一意）
    - **name**: 倉庫名
    - **warehouse_type**: 倉庫タイプ (standard, cold_storage, hazardous)
    """
    crud = WarehouseCRUD(db)
    try:
        warehouse = crud.create(warehouse_in)
        return warehouse
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    倉庫詳細取得

    - **warehouse_id**: 倉庫ID
    """
    crud = WarehouseCRUD(db)
    warehouse = crud.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse_in: WarehouseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    倉庫情報更新（管理者のみ）

    - **warehouse_id**: 更新対象倉庫ID
    """
    crud = WarehouseCRUD(db)
    try:
        warehouse = crud.update(warehouse_id, warehouse_in)
        return warehouse
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Warehouse not found")


@router.delete("/warehouses/{warehouse_id}", status_code=204)
async def delete_warehouse(
    warehouse_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    倉庫削除（管理者のみ）

    - **warehouse_id**: 削除対象倉庫ID
    - 在庫がある場合は削除不可
    """
    crud = WarehouseCRUD(db)
    try:
        crud.delete(warehouse_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Inventory Management


@router.get("/inventory", response_model=List[InventoryItemResponse])
async def list_inventory_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    warehouse_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    quality_status: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    out_of_stock: Optional[bool] = Query(None),
    expired: Optional[bool] = Query(None),
    expiring_soon: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫アイテム一覧取得（高度なフィルタリング）

    - **warehouse_id**: 倉庫フィルター
    - **product_id**: 商品フィルター
    - **location_id**: ロケーションフィルター
    - **quality_status**: 品質ステータスフィルター
    - **low_stock**: 低在庫フィルター
    - **out_of_stock**: 在庫切れフィルター
    - **expired**: 期限切れフィルター
    - **expiring_soon**: 期限間近フィルター（30日以内）
    """
    crud = InventoryItemCRUD(db)

    filters = {}
    for key, value in {
        "warehouse_id": warehouse_id,
        "product_id": product_id,
        "location_id": location_id,
        "quality_status": quality_status,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "expired": expired,
        "expiring_soon": expiring_soon,
    }.items():
        if value is not None:
            filters[key] = value

    skip = (page - 1) * per_page
    items, total = crud.get_multi(skip=skip, limit=per_page, filters=filters)

    return items


@router.post("/inventory", response_model=InventoryItemResponse, status_code=201)
async def create_inventory_item(
    item_in: InventoryItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    在庫アイテム作成（管理者のみ）

    - **product_id**: 商品ID
    - **warehouse_id**: 倉庫ID
    - **location_id**: ロケーションID（オプション）
    - **quantity_available**: 利用可能数量
    """
    crud = InventoryItemCRUD(db)
    item = crud.create(item_in)
    return item


@router.get("/inventory/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫アイテム詳細取得

    - **item_id**: 在庫アイテムID
    """
    crud = InventoryItemCRUD(db)
    item = crud.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/inventory/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_in: InventoryItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    在庫アイテム更新（管理者のみ）

    - **item_id**: 更新対象在庫アイテムID
    """
    crud = InventoryItemCRUD(db)
    try:
        item = crud.update(item_id, item_in)
        return item
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Inventory item not found")


@router.post("/inventory/{item_id}/adjust", response_model=StockMovementResponse)
async def adjust_inventory(
    item_id: str,
    movement: StockMovementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    在庫調整（管理者のみ）

    - **item_id**: 在庫アイテムID
    - **movement_type**: 移動タイプ (inbound, outbound, adjustment)
    - **quantity**: 数量
    - **reason**: 調整理由
    """
    crud = InventoryItemCRUD(db)
    try:
        stock_movement = crud.adjust_quantity(item_id, movement, current_user.id)
        return stock_movement
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/inventory/reserve", response_model=InventoryReservationResponse)
async def reserve_inventory(
    reservation: InventoryReservationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫予約

    - **inventory_item_id**: 在庫アイテムID
    - **quantity_reserved**: 予約数量
    - **reservation_type**: 予約タイプ
    - **expected_release_date**: 予想リリース日
    """
    crud = InventoryItemCRUD(db)
    try:
        reservation_record = crud.reserve_inventory(reservation, current_user.id)
        return reservation_record
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory/summary", response_model=List[StockLevelSummaryResponse])
async def get_inventory_summary(
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫サマリー取得

    - **product_id**: 商品ID（指定しない場合は全商品）
    商品別の総在庫量、予約量、利用可能量を返す
    """
    crud = InventoryItemCRUD(db)
    summary = crud.get_stock_summary(product_id)

    # レスポンス形式に変換
    result = []
    for item in summary:
        result.append(
            StockLevelSummaryResponse(
                product_id=item["product_id"],
                product_name=f"Product {item['product_id']}",  # 実際の実装では商品名を取得
                total_available=item["total_available"],
                total_reserved=item["total_reserved"],
                total_allocated=item["total_allocated"],
                by_warehouse=[],  # 実際の実装では倉庫別詳細を取得
                reorder_needed=item["total_available"] <= 10,  # 簡易判定
                low_stock_warning=item["total_available"] <= 20,  # 簡易判定
            )
        )

    return result


@router.get("/inventory/valuation", response_model=InventoryValuationResponse)
async def get_inventory_valuation(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    在庫評価額取得（管理者のみ）

    平均コスト法による在庫評価額を返す
    """
    crud = InventoryItemCRUD(db)
    valuation = crud.get_inventory_valuation()

    return InventoryValuationResponse(
        total_value=valuation["total_value"],
        by_warehouse=valuation["by_warehouse"],
        by_category={},  # 実際の実装ではカテゴリ別評価額を計算
        by_cost_method={"average_cost": valuation["total_value"]},
        valuation_date=valuation["valuation_date"],
    )


@router.get("/inventory/stats/summary", response_model=InventoryStatsResponse)
async def get_inventory_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    在庫統計情報（管理者のみ）

    統計情報:
    - 総倉庫数・総在庫アイテム数
    - 在庫総額
    - 倉庫別統計
    - アラート数
    """
    from sqlalchemy import func

    from app.models.inventory_extended import InventoryItem, Warehouse

    total_warehouses = db.query(func.count(Warehouse.id)).scalar() or 0
    active_warehouses = (
        db.query(func.count(Warehouse.id)).filter(Warehouse.is_active).scalar() or 0
    )
    total_inventory_items = db.query(func.count(InventoryItem.id)).scalar() or 0

    # 簡易統計（実際の実装ではより詳細な計算）
    return InventoryStatsResponse(
        total_warehouses=total_warehouses,
        active_warehouses=active_warehouses,
        total_locations=0,  # 実装時に計算
        total_inventory_items=total_inventory_items,
        total_inventory_value=Decimal("0"),  # 実装時に計算
        by_warehouse={},  # 実装時に計算
        by_status={"good": total_inventory_items},  # 簡易版
        low_stock_alerts=0,  # 実装時に計算
        out_of_stock_alerts=0,  # 実装時に計算
        expiring_items=0,  # 実装時に計算
    )


# Cycle Count Management


@router.post("/cycle-counts", response_model=CycleCountResponse, status_code=201)
async def create_cycle_count(
    count_in: CycleCountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    棚卸作成（管理者のみ）

    - **cycle_count_number**: 棚卸番号（一意）
    - **warehouse_id**: 対象倉庫ID
    - **count_type**: 棚卸タイプ (full, partial, abc_analysis)
    - **scheduled_date**: 予定日
    """
    crud = CycleCountCRUD(db)
    try:
        cycle_count = crud.create(count_in)
        return cycle_count
    except DuplicateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cycle-counts/{count_id}", response_model=CycleCountResponse)
async def get_cycle_count(
    count_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    棚卸詳細取得

    - **count_id**: 棚卸ID
    """
    crud = CycleCountCRUD(db)
    cycle_count = crud.get_by_id(count_id)
    if not cycle_count:
        raise HTTPException(status_code=404, detail="Cycle count not found")
    return cycle_count


@router.put(
    "/cycle-counts/{count_id}/items/{item_id}", response_model=CycleCountItemResponse
)
async def update_cycle_count_item(
    count_id: str,
    item_id: str,
    item_in: CycleCountItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    棚卸アイテム更新（実地棚卸数量入力）

    - **count_id**: 棚卸ID
    - **item_id**: 棚卸アイテムID
    - **counted_quantity**: 実地棚卸数量
    """
    crud = CycleCountCRUD(db)
    try:
        count_item = crud.update_count_item(item_id, item_in)
        return count_item
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Cycle count item not found")


# Stock Alerts Management


@router.get("/alerts/stock", response_model=List[StockAlertResponse])
async def get_stock_alerts(
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫アラート一覧取得

    - **limit**: 取得件数上限
    アクティブな在庫アラートを重要度順で返す
    """
    crud = StockAlertCRUD(db)
    alerts = crud.get_active_alerts(limit)
    return alerts


@router.post("/alerts/stock/{alert_id}/acknowledge")
async def acknowledge_stock_alert(
    alert_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在庫アラート確認

    - **alert_id**: アラートID
    アラートを確認済みにマークする
    """
    crud = StockAlertCRUD(db)
    try:
        crud.acknowledge_alert(alert_id, current_user.id)
        return {"message": "Alert acknowledged successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Stock alert not found")


@router.post("/alerts/stock/generate")
async def generate_stock_alerts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    在庫アラート自動生成（管理者のみ）

    低在庫・在庫切れ・期限切れ商品のアラートを自動生成
    """
    crud = StockAlertCRUD(db)
    alerts_created = crud.create_low_stock_alerts()
    return {"message": f"{alerts_created} alerts created"}
