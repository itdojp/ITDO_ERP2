from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, desc, asc, text
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from app.models.warehouse_extended import (
    Warehouse, WarehouseZone, WarehouseLocation, InventoryMovement, 
    CycleCount, CycleCountLine, WarehousePerformance
)
from app.schemas.warehouse_v30 import (
    WarehouseCreate, WarehouseUpdate, WarehouseZoneCreate, WarehouseZoneUpdate,
    WarehouseLocationCreate, WarehouseLocationUpdate, InventoryMovementCreate, InventoryMovementUpdate,
    CycleCountCreate, CycleCountUpdate
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class WarehouseCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        return (
            self.db.query(Warehouse)
            .options(
                joinedload(Warehouse.manager),
                joinedload(Warehouse.organization)
            )
            .filter(Warehouse.id == warehouse_id)
            .first()
        )

    def get_by_code(self, warehouse_code: str) -> Optional[Warehouse]:
        return self.db.query(Warehouse).filter(
            Warehouse.warehouse_code == warehouse_code
        ).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Warehouse], int]:
        query = self.db.query(Warehouse)

        if filters:
            if filters.get("warehouse_type"):
                query = query.filter(Warehouse.warehouse_type == filters["warehouse_type"])
            if filters.get("status"):
                query = query.filter(Warehouse.status == filters["status"])
            if filters.get("organization_id"):
                query = query.filter(Warehouse.organization_id == filters["organization_id"])
            if filters.get("warehouse_manager_id"):
                query = query.filter(Warehouse.warehouse_manager_id == filters["warehouse_manager_id"])
            if filters.get("automation_level"):
                query = query.filter(Warehouse.automation_level == filters["automation_level"])
            if filters.get("climate_controlled") is not None:
                query = query.filter(Warehouse.climate_controlled == filters["climate_controlled"])
            if filters.get("security_level"):
                query = query.filter(Warehouse.security_level == filters["security_level"])
            if filters.get("country"):
                query = query.filter(Warehouse.country == filters["country"])
            if filters.get("city"):
                query = query.filter(Warehouse.city.ilike(f"%{filters['city']}%"))
            if filters.get("min_area"):
                query = query.filter(Warehouse.total_area >= filters["min_area"])
            if filters.get("max_area"):
                query = query.filter(Warehouse.total_area <= filters["max_area"])
            if filters.get("utilization_above"):
                query = query.filter(Warehouse.current_utilization >= filters["utilization_above"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Warehouse.warehouse_name.ilike(search_term),
                        Warehouse.warehouse_code.ilike(search_term),
                        Warehouse.city.ilike(search_term)
                    )
                )
            if filters.get("tags"):
                for tag in filters["tags"]:
                    query = query.filter(Warehouse.tags.contains([tag]))

        total = query.count()

        # ソート
        sort_by = filters.get("sort_by", "warehouse_name") if filters else "warehouse_name"
        sort_order = filters.get("sort_order", "asc") if filters else "asc"
        
        sort_column = getattr(Warehouse, sort_by, Warehouse.warehouse_name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        warehouses = query.offset(skip).limit(limit).all()
        return warehouses, total

    def create(self, warehouse_in: WarehouseCreate, user_id: str) -> Warehouse:
        # 倉庫コード重複チェック
        existing = self.get_by_code(warehouse_in.warehouse_code)
        if existing:
            raise DuplicateError(f"Warehouse code '{warehouse_in.warehouse_code}' already exists")

        # 容量・面積の整合性チェック
        if warehouse_in.storage_area and warehouse_in.total_area:
            if warehouse_in.storage_area > warehouse_in.total_area:
                raise InvalidOperationError("Storage area cannot exceed total area")

        # 温度範囲の整合性チェック
        if warehouse_in.temperature_min and warehouse_in.temperature_max:
            if warehouse_in.temperature_min >= warehouse_in.temperature_max:
                raise InvalidOperationError("Minimum temperature must be less than maximum temperature")

        db_warehouse = Warehouse(
            id=str(uuid.uuid4()),
            warehouse_code=warehouse_in.warehouse_code,
            warehouse_name=warehouse_in.warehouse_name,
            warehouse_type=warehouse_in.warehouse_type,
            address_line1=warehouse_in.address_line1,
            address_line2=warehouse_in.address_line2,
            city=warehouse_in.city,
            state_province=warehouse_in.state_province,
            postal_code=warehouse_in.postal_code,
            country=warehouse_in.country,
            phone=warehouse_in.phone,
            fax=warehouse_in.fax,
            email=warehouse_in.email,
            latitude=warehouse_in.latitude,
            longitude=warehouse_in.longitude,
            timezone=warehouse_in.timezone,
            total_area=warehouse_in.total_area,
            storage_area=warehouse_in.storage_area,
            office_area=warehouse_in.office_area,
            loading_dock_count=warehouse_in.loading_dock_count,
            ceiling_height=warehouse_in.ceiling_height,
            floor_load_capacity=warehouse_in.floor_load_capacity,
            climate_controlled=warehouse_in.climate_controlled,
            temperature_min=warehouse_in.temperature_min,
            temperature_max=warehouse_in.temperature_max,
            humidity_controlled=warehouse_in.humidity_controlled,
            humidity_min=warehouse_in.humidity_min,
            humidity_max=warehouse_in.humidity_max,
            operating_hours_start=warehouse_in.operating_hours_start,
            operating_hours_end=warehouse_in.operating_hours_end,
            operating_days=warehouse_in.operating_days,
            shift_pattern=warehouse_in.shift_pattern,
            warehouse_manager_id=warehouse_in.warehouse_manager_id,
            supervisor_ids=warehouse_in.supervisor_ids,
            organization_id=warehouse_in.organization_id,
            cost_center_code=warehouse_in.cost_center_code,
            receiving_capacity=warehouse_in.receiving_capacity,
            shipping_capacity=warehouse_in.shipping_capacity,
            storage_systems=warehouse_in.storage_systems,
            handling_equipment=warehouse_in.handling_equipment,
            security_level=warehouse_in.security_level,
            access_control_system=warehouse_in.access_control_system,
            camera_surveillance=warehouse_in.camera_surveillance,
            fire_suppression_system=warehouse_in.fire_suppression_system,
            security_certifications=warehouse_in.security_certifications,
            wms_system=warehouse_in.wms_system,
            automation_level=warehouse_in.automation_level,
            barcode_scanning=warehouse_in.barcode_scanning,
            rfid_enabled=warehouse_in.rfid_enabled,
            voice_picking=warehouse_in.voice_picking,
            automated_sorting=warehouse_in.automated_sorting,
            erp_integration=warehouse_in.erp_integration,
            tms_integration=warehouse_in.tms_integration,
            customs_bonded=warehouse_in.customs_bonded,
            free_trade_zone=warehouse_in.free_trade_zone,
            utilization_target=warehouse_in.utilization_target,
            accuracy_target=warehouse_in.accuracy_target,
            annual_operating_cost=warehouse_in.annual_operating_cost,
            lease_cost_per_month=warehouse_in.lease_cost_per_month,
            labor_cost_per_hour=warehouse_in.labor_cost_per_hour,
            is_default=warehouse_in.is_default,
            allow_negative_inventory=warehouse_in.allow_negative_inventory,
            require_lot_tracking=warehouse_in.require_lot_tracking,
            require_serial_tracking=warehouse_in.require_serial_tracking,
            low_space_alert_threshold=warehouse_in.low_space_alert_threshold,
            high_temperature_alert=warehouse_in.high_temperature_alert,
            security_breach_alert=warehouse_in.security_breach_alert,
            tags=warehouse_in.tags,
            custom_fields=warehouse_in.custom_fields,
            notes=warehouse_in.notes,
            created_by=user_id
        )

        self.db.add(db_warehouse)
        self.db.commit()
        self.db.refresh(db_warehouse)

        return db_warehouse

    def update(self, warehouse_id: str, warehouse_in: WarehouseUpdate, user_id: str) -> Optional[Warehouse]:
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")

        update_data = warehouse_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warehouse, field, value)

        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = user_id

        self.db.commit()
        self.db.refresh(warehouse)

        return warehouse

    def activate(self, warehouse_id: str, user_id: str) -> Warehouse:
        """倉庫をアクティブ化"""
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")
        
        warehouse.status = "active"
        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(warehouse)
        
        return warehouse

    def deactivate(self, warehouse_id: str, user_id: str) -> Warehouse:
        """倉庫を非アクティブ化"""
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")
        
        warehouse.status = "inactive"
        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(warehouse)
        
        return warehouse

    def set_default(self, warehouse_id: str, user_id: str) -> Warehouse:
        """デフォルト倉庫として設定"""
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")
        
        # 他のデフォルトフラグをクリア
        self.db.query(Warehouse).update({Warehouse.is_default: False})
        
        # 指定倉庫をデフォルトに設定
        warehouse.is_default = True
        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(warehouse)
        
        return warehouse

    def calculate_utilization(self, warehouse_id: str) -> Decimal:
        """倉庫利用率を計算"""
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")
        
        # 総ロケーション数と占有ロケーション数を取得
        total_locations = self.db.query(WarehouseLocation).filter(
            WarehouseLocation.warehouse_id == warehouse_id
        ).count()
        
        occupied_locations = self.db.query(WarehouseLocation).filter(
            and_(
                WarehouseLocation.warehouse_id == warehouse_id,
                WarehouseLocation.is_occupied == True
            )
        ).count()
        
        if total_locations == 0:
            return Decimal('0')
        
        utilization = Decimal(occupied_locations) / Decimal(total_locations) * Decimal('100')
        
        # 利用率を更新
        warehouse.current_utilization = utilization
        self.db.commit()
        
        return utilization

    def get_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """倉庫分析データを取得"""
        base_query = self.db.query(Warehouse)
        
        if filters:
            if filters.get("date_from"):
                base_query = base_query.filter(Warehouse.created_at >= filters["date_from"])
            if filters.get("date_to"):
                base_query = base_query.filter(Warehouse.created_at <= filters["date_to"])
        
        warehouses = base_query.all()
        
        total_warehouses = len(warehouses)
        active_warehouses = len([w for w in warehouses if w.status == "active"])
        inactive_warehouses = total_warehouses - active_warehouses
        
        # 総保管面積
        total_storage_area = sum(w.storage_area or 0 for w in warehouses)
        
        # 利用率計算
        utilizations = [w.current_utilization for w in warehouses if w.current_utilization is not None]
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else Decimal('0')
        total_utilization = sum(utilizations) if utilizations else Decimal('0')
        
        # タイプ別分布
        warehouses_by_type = {}
        for warehouse in warehouses:
            wh_type = warehouse.warehouse_type
            warehouses_by_type[wh_type] = warehouses_by_type.get(wh_type, 0) + 1
        
        # 自動化レベル別分布
        warehouses_by_automation = {}
        for warehouse in warehouses:
            automation = warehouse.automation_level
            warehouses_by_automation[automation] = warehouses_by_automation.get(automation, 0) + 1
        
        # トップ倉庫（利用率別）
        top_warehouses_by_utilization = [
            {
                "id": w.id,
                "name": w.warehouse_name,
                "code": w.warehouse_code,
                "utilization": float(w.current_utilization) if w.current_utilization else 0,
                "total_area": float(w.total_area) if w.total_area else 0
            }
            for w in sorted(warehouses, key=lambda x: x.current_utilization or 0, reverse=True)[:10]
        ]
        
        # スループット上位倉庫（仮の計算）
        top_warehouses_by_throughput = [
            {
                "id": w.id,
                "name": w.warehouse_name,
                "code": w.warehouse_code,
                "receiving_capacity": w.receiving_capacity,
                "shipping_capacity": w.shipping_capacity,
                "total_capacity": w.receiving_capacity + w.shipping_capacity
            }
            for w in sorted(warehouses, key=lambda x: x.receiving_capacity + x.shipping_capacity, reverse=True)[:10]
        ]
        
        # 要注意倉庫
        warehouses_needing_attention = []
        for w in warehouses:
            issues = []
            if w.status != "active":
                issues.append("inactive")
            if w.current_utilization and w.current_utilization > 95:
                issues.append("high_utilization")
            if w.current_utilization and w.current_utilization < 20:
                issues.append("low_utilization")
            if not w.warehouse_manager_id:
                issues.append("no_manager")
            
            if issues:
                warehouses_needing_attention.append({
                    "id": w.id,
                    "name": w.warehouse_name,
                    "issues": issues,
                    "utilization": float(w.current_utilization) if w.current_utilization else 0
                })
        
        # 容量分析
        capacity_analysis = {
            "total_receiving_capacity": sum(w.receiving_capacity for w in warehouses),
            "total_shipping_capacity": sum(w.shipping_capacity for w in warehouses),
            "avg_receiving_capacity": sum(w.receiving_capacity for w in warehouses) / len(warehouses) if warehouses else 0,
            "avg_shipping_capacity": sum(w.shipping_capacity for w in warehouses) / len(warehouses) if warehouses else 0
        }
        
        # パフォーマンストレンド（仮データ）
        performance_trends = []
        for i in range(6):  # 過去6ヶ月
            month = datetime.now().replace(day=1) - timedelta(days=30*i)
            performance_trends.append({
                "period": month.strftime("%Y-%m"),
                "avg_utilization": float(avg_utilization) + (i * 2),  # 仮の傾向
                "total_capacity": int(capacity_analysis["total_receiving_capacity"])
            })
        
        return {
            "total_warehouses": total_warehouses,
            "active_warehouses": active_warehouses,
            "inactive_warehouses": inactive_warehouses,
            "total_storage_area": float(total_storage_area),
            "total_utilization": float(total_utilization),
            "avg_utilization": float(avg_utilization),
            "warehouses_by_type": warehouses_by_type,
            "warehouses_by_automation_level": warehouses_by_automation,
            "top_warehouses_by_utilization": top_warehouses_by_utilization,
            "top_warehouses_by_throughput": top_warehouses_by_throughput,
            "warehouses_needing_attention": warehouses_needing_attention,
            "capacity_analysis": capacity_analysis,
            "performance_trends": performance_trends
        }


class WarehouseZoneCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, zone_id: str) -> Optional[WarehouseZone]:
        return self.db.query(WarehouseZone).filter(
            WarehouseZone.id == zone_id
        ).first()

    def get_by_warehouse(self, warehouse_id: str) -> List[WarehouseZone]:
        return (
            self.db.query(WarehouseZone)
            .filter(WarehouseZone.warehouse_id == warehouse_id)
            .order_by(WarehouseZone.zone_code)
            .all()
        )

    def get_by_code(self, warehouse_id: str, zone_code: str) -> Optional[WarehouseZone]:
        return self.db.query(WarehouseZone).filter(
            and_(
                WarehouseZone.warehouse_id == warehouse_id,
                WarehouseZone.zone_code == zone_code
            )
        ).first()

    def create(self, zone_in: WarehouseZoneCreate, user_id: str) -> WarehouseZone:
        # ゾーンコード重複チェック
        existing = self.get_by_code(zone_in.warehouse_id, zone_in.zone_code)
        if existing:
            raise DuplicateError(f"Zone code '{zone_in.zone_code}' already exists in this warehouse")

        db_zone = WarehouseZone(
            id=str(uuid.uuid4()),
            warehouse_id=zone_in.warehouse_id,
            zone_code=zone_in.zone_code,
            zone_name=zone_in.zone_name,
            zone_type=zone_in.zone_type,
            area=zone_in.area,
            height=zone_in.height,
            volume=zone_in.volume,
            floor_level=zone_in.floor_level,
            grid_coordinates=zone_in.grid_coordinates,
            temperature_controlled=zone_in.temperature_controlled,
            min_temperature=zone_in.min_temperature,
            max_temperature=zone_in.max_temperature,
            humidity_controlled=zone_in.humidity_controlled,
            hazmat_approved=zone_in.hazmat_approved,
            security_level=zone_in.security_level,
            picking_zone=zone_in.picking_zone,
            replenishment_zone=zone_in.replenishment_zone,
            quarantine_zone=zone_in.quarantine_zone,
            fast_moving_items=zone_in.fast_moving_items,
            slow_moving_items=zone_in.slow_moving_items,
            max_weight_capacity=zone_in.max_weight_capacity,
            allowed_product_categories=zone_in.allowed_product_categories,
            prohibited_product_categories=zone_in.prohibited_product_categories,
            storage_rules=zone_in.storage_rules,
            restricted_access=zone_in.restricted_access,
            authorized_personnel=zone_in.authorized_personnel,
            access_equipment_required=zone_in.access_equipment_required,
            max_utilization_target=zone_in.max_utilization_target,
            created_by=user_id
        )

        self.db.add(db_zone)
        self.db.commit()
        self.db.refresh(db_zone)

        return db_zone

    def update(self, zone_id: str, zone_in: WarehouseZoneUpdate) -> Optional[WarehouseZone]:
        zone = self.get_by_id(zone_id)
        if not zone:
            raise NotFoundError(f"Zone {zone_id} not found")

        update_data = zone_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(zone, field, value)

        zone.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(zone)

        return zone

    def delete(self, zone_id: str) -> bool:
        zone = self.get_by_id(zone_id)
        if not zone:
            raise NotFoundError(f"Zone {zone_id} not found")

        # ロケーションがある場合は削除できない
        location_count = self.db.query(WarehouseLocation).filter(
            WarehouseLocation.zone_id == zone_id
        ).count()
        
        if location_count > 0:
            raise InvalidOperationError(f"Cannot delete zone with {location_count} locations")

        self.db.delete(zone)
        self.db.commit()

        return True


class WarehouseLocationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, location_id: str) -> Optional[WarehouseLocation]:
        return (
            self.db.query(WarehouseLocation)
            .options(
                joinedload(WarehouseLocation.zone),
                joinedload(WarehouseLocation.primary_product)
            )
            .filter(WarehouseLocation.id == location_id)
            .first()
        )

    def get_by_code(self, warehouse_id: str, location_code: str) -> Optional[WarehouseLocation]:
        return self.db.query(WarehouseLocation).filter(
            and_(
                WarehouseLocation.warehouse_id == warehouse_id,
                WarehouseLocation.location_code == location_code
            )
        ).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[WarehouseLocation], int]:
        query = self.db.query(WarehouseLocation)

        if filters:
            if filters.get("warehouse_id"):
                query = query.filter(WarehouseLocation.warehouse_id == filters["warehouse_id"])
            if filters.get("zone_id"):
                query = query.filter(WarehouseLocation.zone_id == filters["zone_id"])
            if filters.get("location_type"):
                query = query.filter(WarehouseLocation.location_type == filters["location_type"])
            if filters.get("status"):
                query = query.filter(WarehouseLocation.status == filters["status"])
            if filters.get("is_occupied") is not None:
                query = query.filter(WarehouseLocation.is_occupied == filters["is_occupied"])
            if filters.get("pickable") is not None:
                query = query.filter(WarehouseLocation.pickable == filters["pickable"])
            if filters.get("aisle"):
                query = query.filter(WarehouseLocation.aisle == filters["aisle"])
            if filters.get("product_id"):
                query = query.filter(WarehouseLocation.primary_product_id == filters["product_id"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        WarehouseLocation.location_code.ilike(search_term),
                        WarehouseLocation.barcode.ilike(search_term),
                        WarehouseLocation.coordinates.ilike(search_term)
                    )
                )

        total = query.count()

        # ソート
        sort_by = filters.get("sort_by", "location_code") if filters else "location_code"
        sort_order = filters.get("sort_order", "asc") if filters else "asc"
        
        sort_column = getattr(WarehouseLocation, sort_by, WarehouseLocation.location_code)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        locations = query.offset(skip).limit(limit).all()
        return locations, total

    def create(self, location_in: WarehouseLocationCreate, user_id: str) -> WarehouseLocation:
        # ロケーションコード重複チェック
        existing = self.get_by_code(location_in.warehouse_id, location_in.location_code)
        if existing:
            raise DuplicateError(f"Location code '{location_in.location_code}' already exists in this warehouse")

        # 座標の自動生成
        coordinates = location_in.coordinates
        if not coordinates and location_in.aisle and location_in.bay and location_in.level:
            coordinates = f"{location_in.aisle}-{location_in.bay}-{location_in.level}"

        # 容積の自動計算
        volume = location_in.volume
        if not volume and location_in.length and location_in.width and location_in.height:
            volume = location_in.length * location_in.width * location_in.height

        db_location = WarehouseLocation(
            id=str(uuid.uuid4()),
            warehouse_id=location_in.warehouse_id,
            zone_id=location_in.zone_id,
            location_code=location_in.location_code,
            barcode=location_in.barcode,
            qr_code=location_in.qr_code,
            location_type=location_in.location_type,
            length=location_in.length,
            width=location_in.width,
            height=location_in.height,
            volume=volume,
            weight_capacity=location_in.weight_capacity,
            aisle=location_in.aisle,
            bay=location_in.bay,
            level=location_in.level,
            position=location_in.position,
            coordinates=coordinates,
            pickable=location_in.pickable,
            replenishable=location_in.replenishable,
            mix_products_allowed=location_in.mix_products_allowed,
            mix_lots_allowed=location_in.mix_lots_allowed,
            product_restrictions=location_in.product_restrictions,
            temperature_requirements=location_in.temperature_requirements,
            handling_requirements=location_in.handling_requirements,
            access_method=location_in.access_method,
            equipment_required=location_in.equipment_required,
            pick_priority=location_in.pick_priority,
            location_attributes=location_in.location_attributes,
            tags=location_in.tags,
            notes=location_in.notes,
            created_by=user_id
        )

        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)

        # ゾーンのロケーション数を更新
        self._update_zone_location_count(location_in.zone_id)

        return db_location

    def update(self, location_id: str, location_in: WarehouseLocationUpdate) -> Optional[WarehouseLocation]:
        location = self.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location {location_id} not found")

        update_data = location_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)

        location.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(location)

        return location

    def block_location(self, location_id: str, reason: str) -> WarehouseLocation:
        """ロケーションをブロック"""
        location = self.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location {location_id} not found")
        
        location.status = "blocked"
        location.blocked_reason = reason
        location.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(location)
        
        return location

    def unblock_location(self, location_id: str) -> WarehouseLocation:
        """ロケーションのブロックを解除"""
        location = self.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location {location_id} not found")
        
        location.status = "available" if not location.is_occupied else "occupied"
        location.blocked_reason = None
        location.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(location)
        
        return location

    def get_available_locations(self, zone_id: Optional[str] = None) -> List[WarehouseLocation]:
        """利用可能なロケーションを取得"""
        query = self.db.query(WarehouseLocation).filter(
            and_(
                WarehouseLocation.status == "available",
                WarehouseLocation.is_occupied == False
            )
        )
        
        if zone_id:
            query = query.filter(WarehouseLocation.zone_id == zone_id)
        
        return query.order_by(WarehouseLocation.pick_priority.desc()).all()

    def _update_zone_location_count(self, zone_id: str):
        """ゾーンのロケーション数を更新"""
        zone = self.db.query(WarehouseZone).filter(WarehouseZone.id == zone_id).first()
        if zone:
            total_locations = self.db.query(WarehouseLocation).filter(
                WarehouseLocation.zone_id == zone_id
            ).count()
            
            occupied_locations = self.db.query(WarehouseLocation).filter(
                and_(
                    WarehouseLocation.zone_id == zone_id,
                    WarehouseLocation.is_occupied == True
                )
            ).count()
            
            zone.location_count = total_locations
            zone.occupied_locations = occupied_locations
            
            if total_locations > 0:
                zone.current_utilization = Decimal(occupied_locations) / Decimal(total_locations) * Decimal('100')
            
            self.db.commit()


class InventoryMovementCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: str) -> Optional[InventoryMovement]:
        return (
            self.db.query(InventoryMovement)
            .options(
                joinedload(InventoryMovement.warehouse),
                joinedload(InventoryMovement.location),
                joinedload(InventoryMovement.product)
            )
            .filter(InventoryMovement.id == movement_id)
            .first()
        )

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[InventoryMovement], int]:
        query = self.db.query(InventoryMovement)

        if filters:
            if filters.get("warehouse_id"):
                query = query.filter(InventoryMovement.warehouse_id == filters["warehouse_id"])
            if filters.get("product_id"):
                query = query.filter(InventoryMovement.product_id == filters["product_id"])
            if filters.get("movement_type"):
                query = query.filter(InventoryMovement.movement_type == filters["movement_type"])
            if filters.get("status"):
                query = query.filter(InventoryMovement.status == filters["status"])
            if filters.get("date_from"):
                query = query.filter(InventoryMovement.actual_date >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(InventoryMovement.actual_date <= filters["date_to"])
            if filters.get("reference_number"):
                query = query.filter(InventoryMovement.reference_number.ilike(f"%{filters['reference_number']}%"))

        total = query.count()
        movements = query.offset(skip).limit(limit).order_by(
            InventoryMovement.created_at.desc()
        ).all()

        return movements, total

    def create(self, movement_in: InventoryMovementCreate, user_id: str) -> InventoryMovement:
        # 総コストの自動計算
        total_cost = movement_in.total_cost
        if not total_cost and movement_in.cost_per_unit:
            total_cost = movement_in.cost_per_unit * movement_in.quantity

        # 在庫影響の計算
        inventory_impact = movement_in.quantity
        if movement_in.movement_type in ["shipment", "adjustment"]:
            # 出庫系は負の影響
            inventory_impact = -inventory_impact

        # 価値影響の計算
        value_impact = total_cost or Decimal('0')
        if movement_in.movement_type in ["shipment"]:
            value_impact = -value_impact

        db_movement = InventoryMovement(
            id=str(uuid.uuid4()),
            warehouse_id=movement_in.warehouse_id,
            location_id=movement_in.location_id,
            product_id=movement_in.product_id,
            movement_type=movement_in.movement_type,
            movement_subtype=movement_in.movement_subtype,
            reference_number=movement_in.reference_number,
            reference_line=movement_in.reference_line,
            quantity=movement_in.quantity,
            unit_of_measure=movement_in.unit_of_measure,
            cost_per_unit=movement_in.cost_per_unit,
            total_cost=total_cost,
            lot_number=movement_in.lot_number,
            serial_numbers=movement_in.serial_numbers,
            expiration_date=movement_in.expiration_date,
            manufacture_date=movement_in.manufacture_date,
            from_location_id=movement_in.from_location_id,
            to_location_id=movement_in.to_location_id,
            from_warehouse_id=movement_in.from_warehouse_id,
            to_warehouse_id=movement_in.to_warehouse_id,
            planned_date=movement_in.planned_date,
            actual_date=movement_in.actual_date or datetime.utcnow(),
            reason_code=movement_in.reason_code,
            reason_description=movement_in.reason_description,
            business_process=movement_in.business_process,
            quality_status=movement_in.quality_status,
            inspection_required=movement_in.inspection_required,
            carrier=movement_in.carrier,
            tracking_number=movement_in.tracking_number,
            freight_cost=movement_in.freight_cost,
            delivery_method=movement_in.delivery_method,
            tax_amount=movement_in.tax_amount,
            duty_amount=movement_in.duty_amount,
            accounting_period=movement_in.accounting_period,
            cost_center=movement_in.cost_center,
            source_system=movement_in.source_system,
            inventory_impact=inventory_impact,
            value_impact=value_impact,
            custom_fields=movement_in.custom_fields,
            tags=movement_in.tags,
            notes=movement_in.notes,
            performed_by=user_id,
            created_by=user_id
        )

        self.db.add(db_movement)
        self.db.commit()
        self.db.refresh(db_movement)

        return db_movement

    def update(self, movement_id: str, movement_in: InventoryMovementUpdate) -> Optional[InventoryMovement]:
        movement = self.get_by_id(movement_id)
        if not movement:
            raise NotFoundError(f"Movement {movement_id} not found")

        update_data = movement_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(movement, field, value)

        movement.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(movement)

        return movement

    def complete_movement(self, movement_id: str, user_id: str) -> InventoryMovement:
        """移動を完了"""
        movement = self.get_by_id(movement_id)
        if not movement:
            raise NotFoundError(f"Movement {movement_id} not found")
        
        movement.status = "completed"
        movement.actual_date = datetime.utcnow()
        movement.performed_by = user_id
        movement.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(movement)
        
        return movement


class CycleCountCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, count_id: str) -> Optional[CycleCount]:
        return (
            self.db.query(CycleCount)
            .options(joinedload(CycleCount.warehouse))
            .filter(CycleCount.id == count_id)
            .first()
        )

    def get_by_warehouse(self, warehouse_id: str) -> List[CycleCount]:
        return (
            self.db.query(CycleCount)
            .filter(CycleCount.warehouse_id == warehouse_id)
            .order_by(CycleCount.created_at.desc())
            .all()
        )

    def create(self, count_in: CycleCountCreate, user_id: str) -> CycleCount:
        # カウント番号の生成
        count_number = self._generate_count_number(count_in.warehouse_id)

        db_count = CycleCount(
            id=str(uuid.uuid4()),
            warehouse_id=count_in.warehouse_id,
            count_number=count_number,
            count_name=count_in.count_name,
            count_type=count_in.count_type,
            count_scope=count_in.count_scope,
            zone_ids=count_in.zone_ids,
            location_ids=count_in.location_ids,
            product_ids=count_in.product_ids,
            category_ids=count_in.category_ids,
            planned_date=count_in.planned_date,
            count_manager_id=count_in.count_manager_id,
            assigned_counters=count_in.assigned_counters,
            supervisor_id=count_in.supervisor_id,
            count_method=count_in.count_method,
            recount_required=count_in.recount_required,
            tolerance_percentage=count_in.tolerance_percentage,
            minimum_count_value=count_in.minimum_count_value,
            exclude_zero_quantities=count_in.exclude_zero_quantities,
            freeze_inventory=count_in.freeze_inventory,
            auto_adjust=count_in.auto_adjust,
            generate_adjustments=count_in.generate_adjustments,
            instructions=count_in.instructions,
            notes=count_in.notes,
            tags=count_in.tags,
            created_by=user_id
        )

        self.db.add(db_count)
        self.db.commit()
        self.db.refresh(db_count)

        # カウントラインの生成
        self._generate_count_lines(db_count)

        return db_count

    def start_count(self, count_id: str, user_id: str) -> CycleCount:
        """棚卸開始"""
        count = self.get_by_id(count_id)
        if not count:
            raise NotFoundError(f"Cycle count {count_id} not found")
        
        if count.status != "planned":
            raise InvalidOperationError("Count can only be started from planned status")
        
        count.status = "in_progress"
        count.start_date = datetime.utcnow()
        count.cutoff_time = datetime.utcnow()
        count.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(count)
        
        return count

    def complete_count(self, count_id: str, user_id: str) -> CycleCount:
        """棚卸完了"""
        count = self.get_by_id(count_id)
        if not count:
            raise NotFoundError(f"Cycle count {count_id} not found")
        
        count.status = "completed"
        count.end_date = datetime.utcnow()
        count.updated_at = datetime.utcnow()
        
        # 完了率と精度を計算
        self._calculate_completion_stats(count)
        
        self.db.commit()
        self.db.refresh(count)
        
        return count

    def _generate_count_number(self, warehouse_id: str) -> str:
        """カウント番号生成"""
        today = datetime.now()
        prefix = f"CC-{today.year}{today.month:02d}"
        
        last_count = (
            self.db.query(CycleCount)
            .filter(
                and_(
                    CycleCount.warehouse_id == warehouse_id,
                    CycleCount.count_number.like(f"{prefix}%")
                )
            )
            .order_by(CycleCount.count_number.desc())
            .first()
        )
        
        if last_count:
            last_number = int(last_count.count_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"

    def _generate_count_lines(self, cycle_count: CycleCount):
        """カウントライン生成"""
        # 対象ロケーションを特定してカウントライン生成
        # 実装は簡略化
        pass

    def _calculate_completion_stats(self, cycle_count: CycleCount):
        """完了統計を計算"""
        # カウントラインから統計を計算
        # 実装は簡略化
        pass