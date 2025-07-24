import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.inventory_extended import (
    CycleCount,
    CycleCountItem,
    InventoryItem,
    InventoryReservation,
    StockAlert,
    StockMovement,
    Warehouse,
)
from app.schemas.inventory_complete_v30 import (
    CycleCountCreate,
    CycleCountItemUpdate,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryReservationCreate,
    StockMovementCreate,
    WarehouseCreate,
    WarehouseUpdate,
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class WarehouseCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        return self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

    def get_by_code(self, code: str) -> Optional[Warehouse]:
        return self.db.query(Warehouse).filter(Warehouse.code == code).first()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Warehouse], int]:
        query = self.db.query(Warehouse)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Warehouse.is_active == filters["is_active"])
            if filters.get("warehouse_type"):
                query = query.filter(
                    Warehouse.warehouse_type == filters["warehouse_type"]
                )
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(Warehouse.name.ilike(search), Warehouse.code.ilike(search))
                )

        total = query.count()
        warehouses = query.offset(skip).limit(limit).order_by(Warehouse.name).all()

        return warehouses, total

    def create(self, warehouse_in: WarehouseCreate) -> Warehouse:
        if self.get_by_code(warehouse_in.code):
            raise DuplicateError("Warehouse code already exists")

        db_warehouse = Warehouse(
            id=str(uuid.uuid4()),
            code=warehouse_in.code,
            name=warehouse_in.name,
            description=warehouse_in.description,
            address_line1=warehouse_in.address_line1,
            address_line2=warehouse_in.address_line2,
            city=warehouse_in.city,
            state=warehouse_in.state,
            postal_code=warehouse_in.postal_code,
            country=warehouse_in.country,
            phone=warehouse_in.phone,
            email=warehouse_in.email,
            manager_id=warehouse_in.manager_id,
            warehouse_type=warehouse_in.warehouse_type,
            capacity_sqm=warehouse_in.capacity_sqm,
            capacity_volume=warehouse_in.capacity_volume,
            max_weight=warehouse_in.max_weight,
            latitude=warehouse_in.latitude,
            longitude=warehouse_in.longitude,
            operating_hours=warehouse_in.operating_hours,
            timezone=warehouse_in.timezone,
            is_default=warehouse_in.is_default,
            settings=warehouse_in.settings,
        )

        self.db.add(db_warehouse)
        self.db.commit()
        self.db.refresh(db_warehouse)

        return db_warehouse

    def update(
        self, warehouse_id: str, warehouse_in: WarehouseUpdate
    ) -> Optional[Warehouse]:
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        update_data = warehouse_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warehouse, field, value)

        warehouse.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(warehouse)

        return warehouse

    def delete(self, warehouse_id: str) -> bool:
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        # 在庫アイテムの確認
        inventory_count = (
            self.db.query(func.count(InventoryItem.id))
            .filter(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.quantity_available > 0,
            )
            .scalar()
        )

        if inventory_count > 0:
            raise ValueError("Cannot delete warehouse with active inventory")

        # ソフトデリート
        warehouse.is_active = False
        warehouse.updated_at = datetime.utcnow()

        self.db.commit()
        return True


class InventoryItemCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, item_id: str) -> Optional[InventoryItem]:
        return (
            self.db.query(InventoryItem)
            .options(
                joinedload(InventoryItem.product), joinedload(InventoryItem.warehouse)
            )
            .filter(InventoryItem.id == item_id)
            .first()
        )

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[InventoryItem], int]:
        query = self.db.query(InventoryItem)

        if filters:
            if filters.get("warehouse_id"):
                query = query.filter(
                    InventoryItem.warehouse_id == filters["warehouse_id"]
                )
            if filters.get("product_id"):
                query = query.filter(InventoryItem.product_id == filters["product_id"])
            if filters.get("location_id"):
                query = query.filter(
                    InventoryItem.location_id == filters["location_id"]
                )
            if filters.get("quality_status"):
                query = query.filter(
                    InventoryItem.quality_status == filters["quality_status"]
                )
            if filters.get("low_stock"):
                query = query.filter(
                    InventoryItem.quantity_available <= InventoryItem.reorder_point
                )
            if filters.get("out_of_stock"):
                query = query.filter(InventoryItem.quantity_available <= 0)
            if filters.get("expired"):
                query = query.filter(InventoryItem.expiry_date <= datetime.utcnow())
            if filters.get("expiring_soon"):
                next_month = datetime.utcnow() + timedelta(days=30)
                query = query.filter(
                    and_(
                        InventoryItem.expiry_date <= next_month,
                        InventoryItem.expiry_date > datetime.utcnow(),
                    )
                )

        total = query.count()
        items = (
            query.offset(skip)
            .limit(limit)
            .order_by(InventoryItem.created_at.desc())
            .all()
        )

        return items, total

    def create(self, item_in: InventoryItemCreate) -> InventoryItem:
        # 既存アイテムの確認（同一商品・倉庫・ロケーション・バッチ）
        existing = (
            self.db.query(InventoryItem)
            .filter(
                InventoryItem.product_id == item_in.product_id,
                InventoryItem.warehouse_id == item_in.warehouse_id,
                InventoryItem.location_id == item_in.location_id,
                InventoryItem.batch_number == item_in.batch_number,
            )
            .first()
        )

        if existing:
            # 既存アイテムに数量を追加
            existing.quantity_available += item_in.quantity_available
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        db_item = InventoryItem(
            id=str(uuid.uuid4()),
            product_id=item_in.product_id,
            warehouse_id=item_in.warehouse_id,
            location_id=item_in.location_id,
            quantity_available=item_in.quantity_available,
            batch_number=item_in.batch_number,
            lot_number=item_in.lot_number,
            expiry_date=item_in.expiry_date,
            manufacturing_date=item_in.manufacturing_date,
            unit_cost=item_in.unit_cost,
            quality_status=item_in.quality_status,
            reorder_point=item_in.reorder_point,
            safety_stock=item_in.safety_stock,
            attributes=item_in.attributes,
        )

        # 平均コスト計算
        if item_in.unit_cost:
            db_item.average_cost = item_in.unit_cost
            db_item.fifo_cost = item_in.unit_cost

        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)

        return db_item

    def update(
        self, item_id: str, item_in: InventoryItemUpdate
    ) -> Optional[InventoryItem]:
        item = self.get_by_id(item_id)
        if not item:
            raise NotFoundError(f"Inventory item {item_id} not found")

        update_data = item_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        item.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(item)

        return item

    def adjust_quantity(
        self, item_id: str, movement: StockMovementCreate, user_id: str
    ) -> StockMovement:
        item = self.get_by_id(item_id)
        if not item:
            raise NotFoundError(f"Inventory item {item_id} not found")

        stock_before = item.quantity_available

        if movement.movement_type == "inbound":
            item.quantity_available += movement.quantity
        elif movement.movement_type == "outbound":
            if item.quantity_available < movement.quantity:
                raise InsufficientStockError("Not enough inventory available")
            item.quantity_available -= movement.quantity
        elif movement.movement_type == "adjustment":
            item.quantity_available = movement.quantity

        stock_after = item.quantity_available
        item.last_movement_date = datetime.utcnow()
        item.updated_at = datetime.utcnow()

        # 在庫移動記録作成
        stock_movement = StockMovement(
            id=str(uuid.uuid4()),
            inventory_item_id=item_id,
            product_id=item.product_id,
            movement_type=movement.movement_type,
            transaction_type=movement.transaction_type,
            quantity=movement.quantity,
            unit_cost=movement.unit_cost,
            total_cost=movement.unit_cost * abs(movement.quantity)
            if movement.unit_cost
            else None,
            stock_before=stock_before,
            stock_after=stock_after,
            from_warehouse_id=movement.from_warehouse_id,
            to_warehouse_id=movement.to_warehouse_id,
            from_location_id=movement.from_location_id,
            to_location_id=movement.to_location_id,
            reference_type=movement.reference_type,
            reference_id=movement.reference_id,
            movement_date=movement.movement_date,
            requested_by=user_id,
            executed_by=user_id,
            executed_date=datetime.utcnow(),
            status="executed",
            reason=movement.reason,
            notes=movement.notes,
        )

        self.db.add(stock_movement)
        self.db.commit()
        self.db.refresh(item)
        self.db.refresh(stock_movement)

        return stock_movement

    def reserve_inventory(
        self, reservation_in: InventoryReservationCreate, user_id: str
    ) -> InventoryReservation:
        item = self.get_by_id(reservation_in.inventory_item_id)
        if not item:
            raise NotFoundError(
                f"Inventory item {reservation_in.inventory_item_id} not found"
            )

        available = item.quantity_available - item.quantity_reserved
        if available < reservation_in.quantity_reserved:
            raise InsufficientStockError(
                "Not enough inventory available for reservation"
            )

        reservation = InventoryReservation(
            id=str(uuid.uuid4()),
            inventory_item_id=reservation_in.inventory_item_id,
            product_id=item.product_id,
            quantity_reserved=reservation_in.quantity_reserved,
            reservation_type=reservation_in.reservation_type,
            reference_type=reservation_in.reference_type,
            reference_id=reservation_in.reference_id,
            reserved_date=datetime.utcnow(),
            expected_release_date=reservation_in.expected_release_date,
            reserved_by=user_id,
            notes=reservation_in.notes,
        )

        # 予約数量更新
        item.quantity_reserved += reservation_in.quantity_reserved
        item.updated_at = datetime.utcnow()

        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)

        return reservation

    def get_stock_summary(
        self, product_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """在庫サマリー取得"""
        query = self.db.query(
            InventoryItem.product_id,
            func.sum(InventoryItem.quantity_available).label("total_available"),
            func.sum(InventoryItem.quantity_reserved).label("total_reserved"),
            func.sum(InventoryItem.quantity_allocated).label("total_allocated"),
            func.count(InventoryItem.id).label("locations_count"),
        ).group_by(InventoryItem.product_id)

        if product_id:
            query = query.filter(InventoryItem.product_id == product_id)

        results = query.all()

        return [
            {
                "product_id": r.product_id,
                "total_available": r.total_available or 0,
                "total_reserved": r.total_reserved or 0,
                "total_allocated": r.total_allocated or 0,
                "net_available": (r.total_available or 0)
                - (r.total_reserved or 0)
                - (r.total_allocated or 0),
                "locations_count": r.locations_count,
            }
            for r in results
        ]

    def get_inventory_valuation(self) -> Dict[str, Any]:
        """在庫評価額取得"""
        # 平均コスト法での評価
        total_value = self.db.query(
            func.sum(InventoryItem.quantity_available * InventoryItem.average_cost)
        ).filter(InventoryItem.average_cost.isnot(None)).scalar() or Decimal("0")

        # 倉庫別評価額
        warehouse_values = {}
        warehouse_results = (
            self.db.query(
                Warehouse.name,
                func.sum(
                    InventoryItem.quantity_available * InventoryItem.average_cost
                ).label("value"),
            )
            .join(InventoryItem, Warehouse.id == InventoryItem.warehouse_id)
            .filter(InventoryItem.average_cost.isnot(None))
            .group_by(Warehouse.name)
            .all()
        )

        for name, value in warehouse_results:
            warehouse_values[name] = value or Decimal("0")

        return {
            "total_value": total_value,
            "by_warehouse": warehouse_values,
            "valuation_date": datetime.utcnow(),
        }


class CycleCountCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, count_id: str) -> Optional[CycleCount]:
        return (
            self.db.query(CycleCount)
            .options(joinedload(CycleCount.count_items))
            .filter(CycleCount.id == count_id)
            .first()
        )

    def create(self, count_in: CycleCountCreate) -> CycleCount:
        # 棚卸番号の重複チェック
        existing = (
            self.db.query(CycleCount)
            .filter(CycleCount.cycle_count_number == count_in.cycle_count_number)
            .first()
        )
        if existing:
            raise DuplicateError("Cycle count number already exists")

        db_count = CycleCount(
            id=str(uuid.uuid4()),
            cycle_count_number=count_in.cycle_count_number,
            warehouse_id=count_in.warehouse_id,
            location_id=count_in.location_id,
            count_type=count_in.count_type,
            scheduled_date=count_in.scheduled_date,
            assigned_to=count_in.assigned_to,
            supervised_by=count_in.supervised_by,
            notes=count_in.notes,
        )

        self.db.add(db_count)
        self.db.commit()
        self.db.refresh(db_count)

        # 棚卸対象アイテムの自動生成
        self._generate_count_items(db_count)

        return db_count

    def _generate_count_items(self, cycle_count: CycleCount) -> dict:
        """棚卸対象アイテムの自動生成"""
        query = self.db.query(InventoryItem).filter(
            InventoryItem.warehouse_id == cycle_count.warehouse_id,
            InventoryItem.is_active,
        )

        if cycle_count.location_id:
            query = query.filter(InventoryItem.location_id == cycle_count.location_id)

        items = query.all()

        count_items = []
        for item in items:
            count_item = CycleCountItem(
                id=str(uuid.uuid4()),
                cycle_count_id=cycle_count.id,
                inventory_item_id=item.id,
                product_id=item.product_id,
                system_quantity=item.quantity_available,
            )
            count_items.append(count_item)

        self.db.add_all(count_items)

        # 棚卸予定アイテム数更新
        cycle_count.total_items_planned = len(count_items)

        self.db.commit()

    def update_count_item(
        self, item_id: str, item_in: CycleCountItemUpdate
    ) -> CycleCountItem:
        item = (
            self.db.query(CycleCountItem).filter(CycleCountItem.id == item_id).first()
        )
        if not item:
            raise NotFoundError(f"Cycle count item {item_id} not found")

        # 実地棚卸数量の更新
        if item_in.counted_quantity is not None:
            item.counted_quantity = item_in.counted_quantity
            item.variance_quantity = item_in.counted_quantity - item.system_quantity

            # 差異金額の計算（在庫アイテムのコストを使用）
            inventory_item = (
                self.db.query(InventoryItem)
                .filter(InventoryItem.id == item.inventory_item_id)
                .first()
            )
            if inventory_item and inventory_item.average_cost:
                item.variance_value = (
                    item.variance_quantity * inventory_item.average_cost
                )

            item.count_date = datetime.utcnow()
            item.status = "counted"

        # その他の更新
        update_data = item_in.dict(exclude_unset=True, exclude={"counted_quantity"})
        for field, value in update_data.items():
            setattr(item, field, value)

        item.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(item)

        return item


class StockAlertCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def create_low_stock_alerts(self) -> dict:
        """低在庫アラート自動生成"""
        # 在庫レベルが発注点以下の商品を取得
        low_stock_items = (
            self.db.query(InventoryItem)
            .filter(
                InventoryItem.quantity_available <= InventoryItem.reorder_point,
                InventoryItem.is_active,
            )
            .all()
        )

        alerts = []
        for item in low_stock_items:
            # 既存のアクティブアラートをチェック
            existing = (
                self.db.query(StockAlert)
                .filter(
                    StockAlert.product_id == item.product_id,
                    StockAlert.warehouse_id == item.warehouse_id,
                    StockAlert.alert_type == "low_stock",
                    StockAlert.status == "active",
                )
                .first()
            )

            if not existing:
                alert = StockAlert(
                    id=str(uuid.uuid4()),
                    product_id=item.product_id,
                    warehouse_id=item.warehouse_id,
                    alert_type="low_stock",
                    severity="medium",
                    current_quantity=item.quantity_available,
                    threshold_quantity=item.reorder_point,
                    recommended_order_quantity=item.economic_order_qty
                    or item.reorder_point * 2,
                    message=f"Stock level ({item.quantity_available}) below reorder point ({item.reorder_point})",
                )
                alerts.append(alert)

        if alerts:
            self.db.add_all(alerts)
            self.db.commit()

        return len(alerts)

    def get_active_alerts(self, limit: int = 100) -> List[StockAlert]:
        """アクティブアラート取得"""
        return (
            self.db.query(StockAlert)
            .filter(StockAlert.status == "active")
            .order_by(StockAlert.severity.desc(), StockAlert.created_at.desc())
            .limit(limit)
            .all()
        )

    def acknowledge_alert(self, alert_id: str, user_id: str) -> StockAlert:
        """アラート確認"""
        alert = self.db.query(StockAlert).filter(StockAlert.id == alert_id).first()
        if not alert:
            raise NotFoundError(f"Stock alert {alert_id} not found")

        alert.status = "acknowledged"
        alert.acknowledged_by = user_id
        alert.acknowledged_date = datetime.utcnow()
        alert.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)

        return alert
