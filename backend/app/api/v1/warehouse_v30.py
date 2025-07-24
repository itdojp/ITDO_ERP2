from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.crud.warehouse_v30 import (
    CycleCountCRUD,
    DuplicateError,
    InvalidOperationError,
    InventoryMovementCRUD,
    NotFoundError,
    WarehouseCRUD,
    WarehouseLocationCRUD,
    WarehouseZoneCRUD,
)
from app.schemas.warehouse_v30 import (
    CycleCountCreate,
    CycleCountResponse,
    InventoryMovementCreate,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    InventoryMovementUpdate,
    LocationBulkOperationRequest,
    LocationImportRequest,
    WarehouseAnalyticsResponse,
    WarehouseBulkOperationRequest,
    WarehouseCreate,
    WarehouseImportRequest,
    WarehouseListResponse,
    WarehouseLocationCreate,
    WarehouseLocationListResponse,
    WarehouseLocationResponse,
    WarehouseLocationUpdate,
    WarehousePerformanceResponse,
    WarehouseResponse,
    WarehouseUpdate,
    WarehouseZoneCreate,
    WarehouseZoneResponse,
    WarehouseZoneUpdate,
)

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


# =============================================================================
# Warehouse Management Endpoints
# =============================================================================


@router.post("/", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    warehouse: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫作成"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        return warehouse_crud.create(warehouse, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫詳細取得"""
    warehouse_crud = WarehouseCRUD(db)
    warehouse = warehouse_crud.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )
    return warehouse


@router.get("/", response_model=WarehouseListResponse)
def list_warehouses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    warehouse_type: Optional[str] = None,
    status: Optional[str] = None,
    organization_id: Optional[str] = None,
    warehouse_manager_id: Optional[str] = None,
    automation_level: Optional[str] = None,
    climate_controlled: Optional[bool] = None,
    security_level: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    min_area: Optional[float] = Query(None, ge=0),
    max_area: Optional[float] = Query(None, ge=0),
    utilization_above: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: Optional[str] = "warehouse_name",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    # Build filters dictionary
    filter_params = {
        "warehouse_type": warehouse_type,
        "status": status,
        "organization_id": organization_id,
        "warehouse_manager_id": warehouse_manager_id,
        "automation_level": automation_level,
        "climate_controlled": climate_controlled,
        "security_level": security_level,
        "country": country,
        "city": city,
        "min_area": min_area,
        "max_area": max_area,
        "utilization_above": utilization_above,
        "search": search,
        "tags": tags,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    warehouse_crud = WarehouseCRUD(db)
    warehouses, total = warehouse_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return WarehouseListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=warehouses
    )


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: str,
    warehouse_update: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫更新"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        return warehouse_crud.update(
            warehouse_id, warehouse_update, current_user["sub"]
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{warehouse_id}/activate", response_model=WarehouseResponse)
def activate_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫アクティブ化"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        return warehouse_crud.activate(warehouse_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{warehouse_id}/deactivate", response_model=WarehouseResponse)
def deactivate_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫非アクティブ化"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        return warehouse_crud.deactivate(warehouse_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{warehouse_id}/set-default", response_model=WarehouseResponse)
def set_default_warehouse(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """デフォルト倉庫設定"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        return warehouse_crud.set_default(warehouse_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{warehouse_id}/utilization")
def get_warehouse_utilization(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫利用率取得・再計算"""
    try:
        warehouse_crud = WarehouseCRUD(db)
        utilization = warehouse_crud.calculate_utilization(warehouse_id)
        return {
            "warehouse_id": warehouse_id,
            "utilization_percentage": float(utilization),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/by-code/{warehouse_code}", response_model=WarehouseResponse)
def get_warehouse_by_code(
    warehouse_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫コードによる検索"""
    warehouse_crud = WarehouseCRUD(db)
    warehouse = warehouse_crud.get_by_code(warehouse_code)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )
    return warehouse


# =============================================================================
# Warehouse Zone Management
# =============================================================================


@router.post(
    "/{warehouse_id}/zones",
    response_model=WarehouseZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse_zone(
    warehouse_id: str,
    zone: WarehouseZoneCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ゾーン作成"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # ゾーンのwarehouse_idを設定
    zone.warehouse_id = warehouse_id

    try:
        zone_crud = WarehouseZoneCRUD(db)
        return zone_crud.create(zone, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{warehouse_id}/zones", response_model=List[WarehouseZoneResponse])
def list_warehouse_zones(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ゾーン一覧取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    zone_crud = WarehouseZoneCRUD(db)
    return zone_crud.get_by_warehouse(warehouse_id)


@router.get("/zones/{zone_id}", response_model=WarehouseZoneResponse)
def get_warehouse_zone(
    zone_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ゾーン詳細取得"""
    zone_crud = WarehouseZoneCRUD(db)
    zone = zone_crud.get_by_id(zone_id)
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found"
        )
    return zone


@router.put("/zones/{zone_id}", response_model=WarehouseZoneResponse)
def update_warehouse_zone(
    zone_id: str,
    zone_update: WarehouseZoneUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ゾーン更新"""
    try:
        zone_crud = WarehouseZoneCRUD(db)
        return zone_crud.update(zone_id, zone_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/zones/{zone_id}")
def delete_warehouse_zone(
    zone_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ゾーン削除"""
    try:
        zone_crud = WarehouseZoneCRUD(db)
        success = zone_crud.delete(zone_id)
        return (
            {"message": "Zone deleted successfully"}
            if success
            else {"message": "Failed to delete zone"}
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# Warehouse Location Management
# =============================================================================


@router.post(
    "/{warehouse_id}/locations",
    response_model=WarehouseLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse_location(
    warehouse_id: str,
    location: WarehouseLocationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーション作成"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # ロケーションのwarehouse_idを設定
    location.warehouse_id = warehouse_id

    try:
        location_crud = WarehouseLocationCRUD(db)
        return location_crud.create(location, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{warehouse_id}/locations", response_model=WarehouseLocationListResponse)
def list_warehouse_locations(
    warehouse_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    zone_id: Optional[str] = None,
    location_type: Optional[str] = None,
    status: Optional[str] = None,
    is_occupied: Optional[bool] = None,
    pickable: Optional[bool] = None,
    aisle: Optional[str] = None,
    product_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "location_code",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーション一覧取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    skip = (page - 1) * per_page
    filters = {"warehouse_id": warehouse_id}

    filter_params = {
        "zone_id": zone_id,
        "location_type": location_type,
        "status": status,
        "is_occupied": is_occupied,
        "pickable": pickable,
        "aisle": aisle,
        "product_id": product_id,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    location_crud = WarehouseLocationCRUD(db)
    locations, total = location_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return WarehouseLocationListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=locations
    )


@router.get("/locations/{location_id}", response_model=WarehouseLocationResponse)
def get_warehouse_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーション詳細取得"""
    location_crud = WarehouseLocationCRUD(db)
    location = location_crud.get_by_id(location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return location


@router.put("/locations/{location_id}", response_model=WarehouseLocationResponse)
def update_warehouse_location(
    location_id: str,
    location_update: WarehouseLocationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーション更新"""
    try:
        location_crud = WarehouseLocationCRUD(db)
        return location_crud.update(location_id, location_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/locations/{location_id}/block", response_model=WarehouseLocationResponse)
def block_warehouse_location(
    location_id: str,
    reason: str = Query(..., description="ブロック理由"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーションブロック"""
    try:
        location_crud = WarehouseLocationCRUD(db)
        return location_crud.block_location(location_id, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/locations/{location_id}/unblock", response_model=WarehouseLocationResponse
)
def unblock_warehouse_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫ロケーションブロック解除"""
    try:
        location_crud = WarehouseLocationCRUD(db)
        return location_crud.unblock_location(location_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{warehouse_id}/available-locations",
    response_model=List[WarehouseLocationResponse],
)
def get_available_locations(
    warehouse_id: str,
    zone_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """利用可能ロケーション取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    location_crud = WarehouseLocationCRUD(db)
    return location_crud.get_available_locations(zone_id)


# =============================================================================
# Inventory Movement Management
# =============================================================================


@router.post(
    "/{warehouse_id}/movements",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_movement(
    warehouse_id: str,
    movement: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """在庫移動作成"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # 移動のwarehouse_idを設定
    movement.warehouse_id = warehouse_id

    movement_crud = InventoryMovementCRUD(db)
    return movement_crud.create(movement, current_user["sub"])


@router.get("/{warehouse_id}/movements", response_model=InventoryMovementListResponse)
def list_inventory_movements(
    warehouse_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    product_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    reference_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """在庫移動一覧取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    skip = (page - 1) * per_page
    filters = {"warehouse_id": warehouse_id}

    filter_params = {
        "product_id": product_id,
        "movement_type": movement_type,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "reference_number": reference_number,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    movement_crud = InventoryMovementCRUD(db)
    movements, total = movement_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return InventoryMovementListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=movements
    )


@router.get("/movements/{movement_id}", response_model=InventoryMovementResponse)
def get_inventory_movement(
    movement_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """在庫移動詳細取得"""
    movement_crud = InventoryMovementCRUD(db)
    movement = movement_crud.get_by_id(movement_id)
    if not movement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found"
        )
    return movement


@router.put("/movements/{movement_id}", response_model=InventoryMovementResponse)
def update_inventory_movement(
    movement_id: str,
    movement_update: InventoryMovementUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """在庫移動更新"""
    try:
        movement_crud = InventoryMovementCRUD(db)
        return movement_crud.update(movement_id, movement_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/movements/{movement_id}/complete", response_model=InventoryMovementResponse
)
def complete_inventory_movement(
    movement_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """在庫移動完了"""
    try:
        movement_crud = InventoryMovementCRUD(db)
        return movement_crud.complete_movement(movement_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Cycle Count Management
# =============================================================================


@router.post(
    "/{warehouse_id}/cycle-counts",
    response_model=CycleCountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cycle_count(
    warehouse_id: str,
    cycle_count: CycleCountCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """棚卸作成"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # 棚卸のwarehouse_idを設定
    cycle_count.warehouse_id = warehouse_id

    count_crud = CycleCountCRUD(db)
    return count_crud.create(cycle_count, current_user["sub"])


@router.get("/{warehouse_id}/cycle-counts", response_model=List[CycleCountResponse])
def list_cycle_counts(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """棚卸一覧取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    count_crud = CycleCountCRUD(db)
    return count_crud.get_by_warehouse(warehouse_id)


@router.get("/cycle-counts/{count_id}", response_model=CycleCountResponse)
def get_cycle_count(
    count_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """棚卸詳細取得"""
    count_crud = CycleCountCRUD(db)
    cycle_count = count_crud.get_by_id(count_id)
    if not cycle_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cycle count not found"
        )
    return cycle_count


@router.post("/cycle-counts/{count_id}/start", response_model=CycleCountResponse)
def start_cycle_count(
    count_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """棚卸開始"""
    try:
        count_crud = CycleCountCRUD(db)
        return count_crud.start_count(count_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cycle-counts/{count_id}/complete", response_model=CycleCountResponse)
def complete_cycle_count(
    count_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """棚卸完了"""
    try:
        count_crud = CycleCountCRUD(db)
        return count_crud.complete_count(count_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Analytics and Reporting
# =============================================================================


@router.get("/analytics", response_model=WarehouseAnalyticsResponse)
def get_warehouse_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    warehouse_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫分析データ取得"""
    filters = {}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if warehouse_type:
        filters["warehouse_type"] = warehouse_type

    warehouse_crud = WarehouseCRUD(db)
    analytics = warehouse_crud.get_analytics(filters)

    return WarehouseAnalyticsResponse(**analytics)


@router.get(
    "/{warehouse_id}/performance", response_model=List[WarehousePerformanceResponse]
)
def get_warehouse_performance(
    warehouse_id: str,
    period_type: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    periods: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫パフォーマンス取得"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # パフォーマンスデータ取得（実装簡略化）
    performances = []
    for i in range(periods):
        if period_type == "monthly":
            period_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
            period_end = period_start + timedelta(days=30)
        else:
            period_start = datetime.now() - timedelta(days=7 * i)
            period_end = period_start + timedelta(days=7)

        # ダミーパフォーマンスデータ
        performance = {
            "id": f"perf-{warehouse_id}-{i}",
            "warehouse_id": warehouse_id,
            "performance_period": period_start.strftime("%Y-%m"),
            "period_type": period_type,
            "period_start": period_start,
            "period_end": period_end,
            "receipts_planned": 100,
            "receipts_actual": 95,
            "receipt_accuracy": 98.5,
            "receipt_timeliness": 92.0,
            "average_receipt_time": 2.5,
            "shipments_planned": 150,
            "shipments_actual": 148,
            "shipment_accuracy": 99.2,
            "shipment_timeliness": 95.5,
            "average_shipment_time": 1.8,
            "orders_processed": 500,
            "lines_picked": 2500,
            "pick_accuracy": 99.8,
            "picks_per_hour": 45.0,
            "inventory_accuracy": 99.5,
            "stock_adjustments_count": 10,
            "stock_adjustments_value": 5000.0,
            "stockouts_count": 2,
            "storage_utilization": 85.5,
            "dock_utilization": 78.0,
            "equipment_utilization": 82.0,
            "damage_incidents": 1,
            "damage_value": 500.0,
            "quality_holds": 3,
            "returns_processed": 15,
            "total_labor_hours": 1600.0,
            "overtime_hours": 80.0,
            "staff_count_average": 20.0,
            "labor_cost_total": 800000.0,
            "safety_incidents": 0,
            "near_misses": 2,
            "compliance_violations": 0,
            "training_hours": 40.0,
            "operating_cost_total": 1200000.0,
            "cost_per_shipment": 8000.0,
            "cost_per_receipt": 12600.0,
            "cost_per_pick": 480.0,
            "order_fulfillment_rate": 98.5,
            "customer_complaints": 2,
            "service_level_achievement": 97.5,
            "automation_uptime": 99.0,
            "system_downtime_hours": 2.0,
            "barcode_scan_accuracy": 99.9,
            "energy_consumption": 15000.0,
            "waste_generated": 200.0,
            "recycling_rate": 75.0,
            "carbon_footprint": 2500.0,
            "calculation_date": datetime.utcnow(),
            "calculated_by": current_user["sub"],
            "data_quality_score": 95.0,
            "performance_vs_target": {},
            "benchmark_comparison": {},
            "notes": None,
            "tags": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        performances.append(WarehousePerformanceResponse(**performance))

    return performances


# =============================================================================
# Bulk Operations
# =============================================================================


@router.post("/bulk-operations")
def bulk_warehouse_operations(
    operation_request: WarehouseBulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫一括操作"""
    warehouse_crud = WarehouseCRUD(db)
    results = {"successful": [], "failed": []}

    for warehouse_id in operation_request.warehouse_ids:
        try:
            if operation_request.operation == "activate":
                warehouse_crud.activate(warehouse_id, current_user["sub"])
                results["successful"].append(warehouse_id)
            elif operation_request.operation == "deactivate":
                warehouse_crud.deactivate(warehouse_id, current_user["sub"])
                results["successful"].append(warehouse_id)
            elif operation_request.operation == "update_status":
                new_status = operation_request.operation_data.get("status")
                if new_status:
                    warehouse = warehouse_crud.get_by_id(warehouse_id)
                    if warehouse:
                        warehouse.status = new_status
                        warehouse_crud.db.commit()
                        results["successful"].append(warehouse_id)
                    else:
                        results["failed"].append(
                            {
                                "warehouse_id": warehouse_id,
                                "error": "Warehouse not found",
                            }
                        )
                else:
                    results["failed"].append(
                        {
                            "warehouse_id": warehouse_id,
                            "error": "Status not provided in operation_data",
                        }
                    )
            else:
                results["failed"].append(
                    {
                        "warehouse_id": warehouse_id,
                        "error": f"Unsupported operation: {operation_request.operation}",
                    }
                )
        except Exception as e:
            results["failed"].append({"warehouse_id": warehouse_id, "error": str(e)})

    return {
        "message": f"Bulk operation completed. {len(results['successful'])} successful, {len(results['failed'])} failed.",
        "results": results,
    }


@router.post("/locations/bulk-operations")
def bulk_location_operations(
    operation_request: LocationBulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """ロケーション一括操作"""
    location_crud = WarehouseLocationCRUD(db)
    results = {"successful": [], "failed": []}

    for location_id in operation_request.location_ids:
        try:
            if operation_request.operation == "block":
                reason = operation_request.operation_data.get(
                    "reason", "Bulk block operation"
                )
                location_crud.block_location(location_id, reason)
                results["successful"].append(location_id)
            elif operation_request.operation == "unblock":
                location_crud.unblock_location(location_id)
                results["successful"].append(location_id)
            else:
                results["failed"].append(
                    {
                        "location_id": location_id,
                        "error": f"Unsupported operation: {operation_request.operation}",
                    }
                )
        except Exception as e:
            results["failed"].append({"location_id": location_id, "error": str(e)})

    return {
        "message": f"Bulk location operation completed. {len(results['successful'])} successful, {len(results['failed'])} failed.",
        "results": results,
    }


# =============================================================================
# Import/Export Operations
# =============================================================================


@router.post("/import")
def import_warehouses(
    import_request: WarehouseImportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """倉庫インポート"""
    # Import implementation would go here
    return {
        "message": "Warehouse import functionality not yet implemented",
        "import_format": import_request.import_format,
        "validate_only": import_request.validate_only,
    }


@router.post("/{warehouse_id}/locations/import")
def import_locations(
    warehouse_id: str,
    import_request: LocationImportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """ロケーションインポート"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    if not warehouse_crud.get_by_id(warehouse_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # Import implementation would go here
    return {
        "message": "Location import functionality not yet implemented",
        "warehouse_id": warehouse_id,
        "import_format": import_request.import_format,
        "validate_only": import_request.validate_only,
    }


# =============================================================================
# Dashboard and Summary Endpoints
# =============================================================================


@router.get("/dashboard-summary")
def get_warehouse_dashboard_summary(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """倉庫ダッシュボードサマリー"""
    warehouse_crud = WarehouseCRUD(db)
    analytics = warehouse_crud.get_analytics()

    # 追加のサマリー情報
    recent_movements = []  # 最近の在庫移動（簡略化）
    pending_counts = 0  # 進行中の棚卸（簡略化）
    alerts = []  # アラート情報（簡略化）

    return {
        "total_warehouses": analytics["total_warehouses"],
        "active_warehouses": analytics["active_warehouses"],
        "total_storage_area": analytics["total_storage_area"],
        "avg_utilization": analytics["avg_utilization"],
        "top_warehouses": analytics["top_warehouses_by_utilization"][:5],
        "warehouses_needing_attention": len(analytics["warehouses_needing_attention"]),
        "recent_movements_count": len(recent_movements),
        "pending_cycle_counts": pending_counts,
        "active_alerts": len(alerts),
        "capacity_summary": analytics["capacity_analysis"],
    }


@router.get("/{warehouse_id}/dashboard")
def get_warehouse_specific_dashboard(
    warehouse_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """個別倉庫ダッシュボード"""
    # 倉庫存在確認
    warehouse_crud = WarehouseCRUD(db)
    warehouse = warehouse_crud.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found"
        )

    # 利用率計算
    utilization = warehouse_crud.calculate_utilization(warehouse_id)

    # ゾーン情報
    zone_crud = WarehouseZoneCRUD(db)
    zones = zone_crud.get_by_warehouse(warehouse_id)

    # 最近の活動（簡略化）
    recent_activities = []

    return {
        "warehouse": {
            "id": warehouse.id,
            "name": warehouse.warehouse_name,
            "code": warehouse.warehouse_code,
            "type": warehouse.warehouse_type,
            "status": warehouse.status,
        },
        "utilization_percentage": float(utilization),
        "zones_count": len(zones),
        "active_zones": len([z for z in zones if z.status == "active"]),
        "total_locations": sum(z.location_count for z in zones),
        "occupied_locations": sum(z.occupied_locations for z in zones),
        "recent_activities": recent_activities,
        "capacity_info": {
            "total_area": float(warehouse.total_area) if warehouse.total_area else 0,
            "storage_area": float(warehouse.storage_area)
            if warehouse.storage_area
            else 0,
            "receiving_capacity": warehouse.receiving_capacity,
            "shipping_capacity": warehouse.shipping_capacity,
        },
    }
