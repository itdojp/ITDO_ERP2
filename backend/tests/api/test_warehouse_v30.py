"""
CC02 段階的API開発プロトコル v30.0 - Task 1.10
倉庫管理API (35+ endpoints) - 包括的テスト実装

テスト対象API:
- 倉庫CRUD操作 (10エンドポイント)
- ゾーン管理 (8エンドポイント)
- ロケーション管理 (8エンドポイント)
- 在庫移動管理 (9エンドポイント)
- 棚卸管理 (10エンドポイント)
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.warehouse_extended import (
    CycleCount,
    CycleCountLine,
    InventoryMovement,
    Warehouse,
    WarehouseLocation,
    WarehouseZone,
)

# テストクライアント設定
client = TestClient(app)


# モック用セキュリティ依存関係
def mock_get_current_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "is_active": True,
        "roles": ["admin"],
    }


def mock_require_permissions(permissions):
    def decorator(func):
        return func

    return decorator


# セキュリティ依存関係をモック化
app.dependency_overrides[app.dependencies["get_current_user"]] = mock_get_current_user
app.dependency_overrides[app.dependencies["require_permissions"]] = (
    mock_require_permissions
)


class TestWarehouseAPI:
    """倉庫CRUD操作のテストクラス (10エンドポイント)"""

    @pytest.fixture
    def sample_warehouse_data(self):
        return {
            "warehouse_code": "WH001",
            "warehouse_name": "Central Distribution Center",
            "warehouse_type": "distribution",
            "address_line1": "123 Industrial Blvd",
            "city": "Tokyo",
            "state_province": "Tokyo",
            "postal_code": "123-4567",
            "country": "JP",
            "phone": "+81-3-1234-5678",
            "email": "warehouse@company.com",
            "latitude": 35.6762,
            "longitude": 139.6503,
            "timezone": "Asia/Tokyo",
            "total_area": "50000.00",
            "storage_area": "40000.00",
            "office_area": "2000.00",
            "loading_dock_count": 10,
            "ceiling_height": "12.00",
            "floor_load_capacity": "5000.00",
            "climate_controlled": True,
            "temperature_min": "15.00",
            "temperature_max": "25.00",
            "humidity_controlled": True,
            "humidity_min": "40.00",
            "humidity_max": "60.00",
            "operating_hours_start": "08:00",
            "operating_hours_end": "18:00",
            "operating_days": ["mon", "tue", "wed", "thu", "fri"],
            "shift_pattern": "double",
            "warehouse_manager_id": "manager-001",
            "supervisor_ids": ["sup-001", "sup-002"],
            "organization_id": "org-001",
            "cost_center_code": "CC-WH001",
            "receiving_capacity": 500,
            "shipping_capacity": 600,
            "storage_systems": ["pallet_rack", "shelf", "floor"],
            "handling_equipment": ["forklift", "conveyor"],
            "security_level": "high",
            "access_control_system": True,
            "camera_surveillance": True,
            "fire_suppression_system": "sprinkler",
            "security_certifications": ["ISO_27001"],
            "wms_system": "SAP_WM",
            "automation_level": "semi_automated",
            "barcode_scanning": True,
            "rfid_enabled": True,
            "voice_picking": True,
            "automated_sorting": False,
            "erp_integration": True,
            "tms_integration": True,
            "customs_bonded": False,
            "free_trade_zone": False,
            "utilization_target": "85.00",
            "current_utilization": "78.50",
            "accuracy_target": "99.80",
            "current_accuracy": "99.65",
            "annual_operating_cost": "5000000.00",
            "lease_cost_per_month": "200000.00",
            "labor_cost_per_hour": "2500.00",
            "status": "active",
            "is_default": False,
            "allow_negative_inventory": False,
            "require_lot_tracking": True,
            "require_serial_tracking": False,
            "low_space_alert_threshold": "90.00",
            "high_temperature_alert": True,
            "security_breach_alert": True,
            "tags": ["distribution", "automated", "climate_controlled"],
            "custom_fields": {"vendor": "LogisticsCorp", "contract_end": "2025-12-31"},
            "notes": "Primary distribution center for Tokyo region",
        }

    @patch("app.crud.warehouse_v30.create_warehouse")
    def test_create_warehouse_success(self, mock_create, sample_warehouse_data):
        """倉庫作成APIのテスト"""
        # モック設定
        created_warehouse = Warehouse(**sample_warehouse_data)
        created_warehouse.id = str(uuid.uuid4())
        created_warehouse.created_at = datetime.utcnow()
        mock_create.return_value = created_warehouse

        # APIコール
        response = client.post("/api/v1/warehouses/", json=sample_warehouse_data)

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["warehouse_code"] == sample_warehouse_data["warehouse_code"]
        assert data["warehouse_name"] == sample_warehouse_data["warehouse_name"]
        assert data["warehouse_type"] == sample_warehouse_data["warehouse_type"]
        assert data["climate_controlled"]
        assert len(data["storage_systems"]) == 3
        mock_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_warehouses")
    def test_get_warehouses_with_filters(self, mock_get):
        """倉庫一覧取得APIのテスト（フィルタ付き）"""
        # モック設定
        mock_warehouses = [
            Warehouse(
                id=str(uuid.uuid4()),
                warehouse_code="WH001",
                warehouse_name="Central DC",
                warehouse_type="distribution",
                status="active",
            ),
            Warehouse(
                id=str(uuid.uuid4()),
                warehouse_code="WH002",
                warehouse_name="Regional DC",
                warehouse_type="distribution",
                status="active",
            ),
        ]
        mock_get.return_value = {"items": mock_warehouses, "total": 2}

        # APIコール
        response = client.get(
            "/api/v1/warehouses/?warehouse_type=distribution&status=active&skip=0&limit=10"
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["warehouse_code"] == "WH001"
        mock_get.assert_called_once()

    @patch("app.crud.warehouse_v30.get_warehouse_by_id")
    def test_get_warehouse_by_id_success(self, mock_get):
        """倉庫詳細取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_warehouse = Warehouse(
            id=warehouse_id,
            warehouse_code="WH001",
            warehouse_name="Central DC",
            warehouse_type="distribution",
            total_area=Decimal("50000.00"),
            current_utilization=Decimal("78.50"),
        )
        mock_get.return_value = mock_warehouse

        # APIコール
        response = client.get(f"/api/v1/warehouses/{warehouse_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == warehouse_id
        assert data["warehouse_code"] == "WH001"
        assert float(data["current_utilization"]) == 78.50
        mock_get.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.get_warehouse_by_id")
    def test_get_warehouse_not_found(self, mock_get):
        """存在しない倉庫取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_get.return_value = None

        # APIコール
        response = client.get(f"/api/v1/warehouses/{warehouse_id}")

        # 検証
        assert response.status_code == 404
        assert "Warehouse not found" in response.json()["detail"]

    @patch("app.crud.warehouse_v30.update_warehouse")
    @patch("app.crud.warehouse_v30.get_warehouse_by_id")
    def test_update_warehouse_success(
        self, mock_get, mock_update, sample_warehouse_data
    ):
        """倉庫更新APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        existing_warehouse = Warehouse(**sample_warehouse_data)
        existing_warehouse.id = warehouse_id
        mock_get.return_value = existing_warehouse

        updated_data = sample_warehouse_data.copy()
        updated_data["warehouse_name"] = "Updated Central DC"
        updated_data["current_utilization"] = "82.30"

        updated_warehouse = Warehouse(**updated_data)
        updated_warehouse.id = warehouse_id
        mock_update.return_value = updated_warehouse

        # APIコール
        response = client.put(f"/api/v1/warehouses/{warehouse_id}", json=updated_data)

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["warehouse_name"] == "Updated Central DC"
        assert float(data["current_utilization"]) == 82.30
        mock_update.assert_called_once()

    @patch("app.crud.warehouse_v30.delete_warehouse")
    @patch("app.crud.warehouse_v30.get_warehouse_by_id")
    def test_delete_warehouse_success(self, mock_get, mock_delete):
        """倉庫削除APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_warehouse = Warehouse(
            id=warehouse_id,
            warehouse_code="WH001",
            warehouse_name="Central DC",
            status="active",
        )
        mock_get.return_value = mock_warehouse
        mock_delete.return_value = True

        # APIコール
        response = client.delete(f"/api/v1/warehouses/{warehouse_id}")

        # 検証
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]
        mock_delete.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.get_warehouse_utilization")
    def test_get_warehouse_utilization(self, mock_get_utilization):
        """倉庫稼働率取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_utilization = {
            "warehouse_id": warehouse_id,
            "storage_utilization": Decimal("78.50"),
            "dock_utilization": Decimal("65.30"),
            "equipment_utilization": Decimal("82.10"),
            "zone_utilization": [
                {"zone_id": "zone-1", "utilization": Decimal("85.20")},
                {"zone_id": "zone-2", "utilization": Decimal("71.80")},
            ],
        }
        mock_get_utilization.return_value = mock_utilization

        # APIコール
        response = client.get(f"/api/v1/warehouses/{warehouse_id}/utilization")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert float(data["storage_utilization"]) == 78.50
        assert float(data["dock_utilization"]) == 65.30
        assert len(data["zone_utilization"]) == 2
        mock_get_utilization.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.get_warehouse_analytics")
    def test_get_warehouse_analytics(self, mock_get_analytics):
        """倉庫分析データ取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_analytics = {
            "warehouse_id": warehouse_id,
            "total_inventory_value": Decimal("2500000.00"),
            "inventory_turnover_rate": Decimal("8.5"),
            "average_dwell_time": Decimal("12.3"),
            "pick_accuracy": Decimal("99.65"),
            "shipment_on_time": Decimal("98.20"),
            "monthly_throughput": {"receipts": 1250, "shipments": 1320, "picks": 15680},
            "cost_metrics": {
                "cost_per_pick": Decimal("2.35"),
                "cost_per_shipment": Decimal("28.50"),
                "storage_cost_per_unit": Decimal("1.85"),
            },
        }
        mock_get_analytics.return_value = mock_analytics

        # APIコール
        response = client.get(f"/api/v1/warehouses/{warehouse_id}/analytics")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert float(data["total_inventory_value"]) == 2500000.00
        assert float(data["inventory_turnover_rate"]) == 8.5
        assert data["monthly_throughput"]["receipts"] == 1250
        assert float(data["cost_metrics"]["cost_per_pick"]) == 2.35
        mock_get_analytics.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.create_warehouses_bulk")
    def test_bulk_create_warehouses(self, mock_bulk_create):
        """倉庫一括作成APIのテスト"""
        # モック設定
        bulk_data = [
            {
                "warehouse_code": "WH001",
                "warehouse_name": "Central DC",
                "warehouse_type": "distribution",
            },
            {
                "warehouse_code": "WH002",
                "warehouse_name": "Regional DC",
                "warehouse_type": "distribution",
            },
        ]

        mock_result = {
            "created": 2,
            "failed": 0,
            "warehouse_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "errors": [],
        }
        mock_bulk_create.return_value = mock_result

        # APIコール
        response = client.post(
            "/api/v1/warehouses/bulk", json={"warehouses": bulk_data}
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["warehouse_ids"]) == 2
        mock_bulk_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_warehouse_dashboard")
    def test_get_warehouses_dashboard(self, mock_get_dashboard):
        """倉庫ダッシュボード取得APIのテスト"""
        # モック設定
        mock_dashboard = {
            "total_warehouses": 5,
            "active_warehouses": 4,
            "total_storage_area": Decimal("250000.00"),
            "average_utilization": Decimal("76.80"),
            "total_inventory_value": Decimal("12500000.00"),
            "alerts": [
                {"warehouse_id": "wh-1", "type": "low_space", "severity": "warning"},
                {
                    "warehouse_id": "wh-2",
                    "type": "high_temperature",
                    "severity": "critical",
                },
            ],
            "performance_summary": {
                "pick_accuracy": Decimal("99.42"),
                "shipment_on_time": Decimal("97.85"),
                "receiving_efficiency": Decimal("94.20"),
            },
        }
        mock_get_dashboard.return_value = mock_dashboard

        # APIコール
        response = client.get("/api/v1/warehouses/dashboard")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total_warehouses"] == 5
        assert data["active_warehouses"] == 4
        assert float(data["average_utilization"]) == 76.80
        assert len(data["alerts"]) == 2
        assert float(data["performance_summary"]["pick_accuracy"]) == 99.42
        mock_get_dashboard.assert_called_once()


class TestWarehouseZoneAPI:
    """ゾーン管理APIのテストクラス (8エンドポイント)"""

    @pytest.fixture
    def sample_zone_data(self):
        return {
            "warehouse_id": str(uuid.uuid4()),
            "zone_code": "Z001",
            "zone_name": "Receiving Zone A",
            "zone_type": "receiving",
            "area": "5000.00",
            "height": "8.00",
            "volume": "40000.000",
            "floor_level": 1,
            "grid_coordinates": "A1-A5",
            "temperature_controlled": True,
            "min_temperature": "18.00",
            "max_temperature": "22.00",
            "humidity_controlled": False,
            "hazmat_approved": False,
            "security_level": "standard",
            "picking_zone": True,
            "replenishment_zone": False,
            "quarantine_zone": False,
            "fast_moving_items": True,
            "slow_moving_items": False,
            "max_weight_capacity": "500000.00",
            "allowed_product_categories": ["electronics", "clothing"],
            "prohibited_product_categories": ["hazmat", "perishable"],
            "storage_rules": {"fifo_required": True, "max_stack_height": 3},
            "restricted_access": False,
            "authorized_personnel": [],
            "access_equipment_required": [],
            "current_utilization": "65.50",
            "max_utilization_target": "85.00",
            "location_count": 200,
            "occupied_locations": 131,
            "status": "active",
        }

    @patch("app.crud.warehouse_v30.create_zone")
    def test_create_zone_success(self, mock_create, sample_zone_data):
        """ゾーン作成APIのテスト"""
        # モック設定
        created_zone = WarehouseZone(**sample_zone_data)
        created_zone.id = str(uuid.uuid4())
        created_zone.created_at = datetime.utcnow()
        mock_create.return_value = created_zone

        # APIコール
        response = client.post("/api/v1/warehouse-zones/", json=sample_zone_data)

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["zone_code"] == sample_zone_data["zone_code"]
        assert data["zone_name"] == sample_zone_data["zone_name"]
        assert data["zone_type"] == "receiving"
        assert data["picking_zone"]
        assert len(data["allowed_product_categories"]) == 2
        mock_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_zones_by_warehouse")
    def test_get_zones_by_warehouse(self, mock_get):
        """倉庫別ゾーン一覧取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_zones = [
            WarehouseZone(
                id=str(uuid.uuid4()),
                warehouse_id=warehouse_id,
                zone_code="Z001",
                zone_name="Receiving Zone A",
                zone_type="receiving",
                status="active",
            ),
            WarehouseZone(
                id=str(uuid.uuid4()),
                warehouse_id=warehouse_id,
                zone_code="Z002",
                zone_name="Storage Zone B",
                zone_type="storage",
                status="active",
            ),
        ]
        mock_get.return_value = {"items": mock_zones, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/warehouse-zones/warehouse/{warehouse_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["zone_code"] == "Z001"
        assert data["items"][1]["zone_type"] == "storage"
        mock_get.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.get_zone_by_id")
    def test_get_zone_by_id_success(self, mock_get):
        """ゾーン詳細取得APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        mock_zone = WarehouseZone(
            id=zone_id,
            zone_code="Z001",
            zone_name="Receiving Zone A",
            zone_type="receiving",
            current_utilization=Decimal("65.50"),
            location_count=200,
            occupied_locations=131,
        )
        mock_get.return_value = mock_zone

        # APIコール
        response = client.get(f"/api/v1/warehouse-zones/{zone_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == zone_id
        assert data["zone_code"] == "Z001"
        assert float(data["current_utilization"]) == 65.50
        assert data["location_count"] == 200
        mock_get.assert_called_once_with(zone_id)

    @patch("app.crud.warehouse_v30.update_zone")
    @patch("app.crud.warehouse_v30.get_zone_by_id")
    def test_update_zone_success(self, mock_get, mock_update, sample_zone_data):
        """ゾーン更新APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        existing_zone = WarehouseZone(**sample_zone_data)
        existing_zone.id = zone_id
        mock_get.return_value = existing_zone

        updated_data = sample_zone_data.copy()
        updated_data["zone_name"] = "Updated Receiving Zone A"
        updated_data["current_utilization"] = "72.30"

        updated_zone = WarehouseZone(**updated_data)
        updated_zone.id = zone_id
        mock_update.return_value = updated_zone

        # APIコール
        response = client.put(f"/api/v1/warehouse-zones/{zone_id}", json=updated_data)

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["zone_name"] == "Updated Receiving Zone A"
        assert float(data["current_utilization"]) == 72.30
        mock_update.assert_called_once()

    @patch("app.crud.warehouse_v30.delete_zone")
    @patch("app.crud.warehouse_v30.get_zone_by_id")
    def test_delete_zone_success(self, mock_get, mock_delete):
        """ゾーン削除APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        mock_zone = WarehouseZone(
            id=zone_id, zone_code="Z001", zone_name="Receiving Zone A", status="active"
        )
        mock_get.return_value = mock_zone
        mock_delete.return_value = True

        # APIコール
        response = client.delete(f"/api/v1/warehouse-zones/{zone_id}")

        # 検証
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]
        mock_delete.assert_called_once_with(zone_id)

    @patch("app.crud.warehouse_v30.get_zone_utilization")
    def test_get_zone_utilization(self, mock_get_utilization):
        """ゾーン稼働率取得APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        mock_utilization = {
            "zone_id": zone_id,
            "current_utilization": Decimal("68.50"),
            "location_utilization": Decimal("65.50"),
            "volume_utilization": Decimal("71.20"),
            "weight_utilization": Decimal("42.80"),
            "location_breakdown": {
                "total_locations": 200,
                "occupied_locations": 131,
                "available_locations": 69,
                "blocked_locations": 0,
            },
        }
        mock_get_utilization.return_value = mock_utilization

        # APIコール
        response = client.get(f"/api/v1/warehouse-zones/{zone_id}/utilization")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert float(data["current_utilization"]) == 68.50
        assert data["location_breakdown"]["total_locations"] == 200
        assert data["location_breakdown"]["occupied_locations"] == 131
        mock_get_utilization.assert_called_once_with(zone_id)

    @patch("app.crud.warehouse_v30.create_zones_bulk")
    def test_bulk_create_zones(self, mock_bulk_create):
        """ゾーン一括作成APIのテスト"""
        # モック設定
        bulk_data = [
            {
                "warehouse_id": str(uuid.uuid4()),
                "zone_code": "Z001",
                "zone_name": "Receiving Zone A",
                "zone_type": "receiving",
            },
            {
                "warehouse_id": str(uuid.uuid4()),
                "zone_code": "Z002",
                "zone_name": "Storage Zone B",
                "zone_type": "storage",
            },
        ]

        mock_result = {
            "created": 2,
            "failed": 0,
            "zone_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "errors": [],
        }
        mock_bulk_create.return_value = mock_result

        # APIコール
        response = client.post(
            "/api/v1/warehouse-zones/bulk", json={"zones": bulk_data}
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["zone_ids"]) == 2
        mock_bulk_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_zone_analytics")
    def test_get_zone_analytics(self, mock_get_analytics):
        """ゾーン分析データ取得APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        mock_analytics = {
            "zone_id": zone_id,
            "inventory_turnover": Decimal("12.5"),
            "pick_frequency": 850,
            "replenishment_frequency": 45,
            "average_dwell_time": Decimal("8.3"),
            "pick_accuracy": Decimal("99.80"),
            "utilization_trend": [
                {"period": "2024-01", "utilization": Decimal("62.30")},
                {"period": "2024-02", "utilization": Decimal("68.50")},
                {"period": "2024-03", "utilization": Decimal("65.80")},
            ],
            "product_mix": {"electronics": 45, "clothing": 35, "accessories": 20},
        }
        mock_get_analytics.return_value = mock_analytics

        # APIコール
        response = client.get(f"/api/v1/warehouse-zones/{zone_id}/analytics")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert float(data["inventory_turnover"]) == 12.5
        assert data["pick_frequency"] == 850
        assert len(data["utilization_trend"]) == 3
        assert data["product_mix"]["electronics"] == 45
        mock_get_analytics.assert_called_once_with(zone_id)


class TestWarehouseLocationAPI:
    """ロケーション管理APIのテストクラス (8エンドポイント)"""

    @pytest.fixture
    def sample_location_data(self):
        return {
            "warehouse_id": str(uuid.uuid4()),
            "zone_id": str(uuid.uuid4()),
            "location_code": "A01-001-001",
            "barcode": "LOC001234567890",
            "qr_code": "QR_A01001001_DATA",
            "location_type": "bin",
            "length": "1.20",
            "width": "0.80",
            "height": "2.50",
            "volume": "2.400",
            "weight_capacity": "500.00",
            "aisle": "A01",
            "bay": "001",
            "level": "001",
            "position": "01",
            "coordinates": "A01-001-001",
            "pickable": True,
            "replenishable": True,
            "mix_products_allowed": False,
            "mix_lots_allowed": False,
            "product_restrictions": ["no_hazmat"],
            "temperature_requirements": {"min": 15, "max": 25},
            "handling_requirements": ["forklift_accessible"],
            "access_method": "forklift",
            "equipment_required": ["forklift", "scanner"],
            "pick_priority": 75,
            "is_occupied": False,
            "current_stock_quantity": "0.000",
            "current_weight": "0.00",
            "occupancy_percentage": "0.00",
            "primary_product_id": None,
            "lot_number": None,
            "expiration_date": None,
            "last_pick_date": None,
            "last_replenish_date": None,
            "last_count_date": None,
            "pick_frequency": 0,
            "status": "available",
            "blocked_reason": None,
            "priority_sequence": 1,
            "last_inspection_date": None,
            "cleanliness_rating": 5,
            "damage_assessment": None,
            "location_attributes": {"temperature_zone": "standard", "pick_face": True},
            "tags": ["pick_face", "forklift_accessible"],
            "notes": "Primary picking location for aisle A01",
        }

    @patch("app.crud.warehouse_v30.create_location")
    def test_create_location_success(self, mock_create, sample_location_data):
        """ロケーション作成APIのテスト"""
        # モック設定
        created_location = WarehouseLocation(**sample_location_data)
        created_location.id = str(uuid.uuid4())
        created_location.created_at = datetime.utcnow()
        mock_create.return_value = created_location

        # APIコール
        response = client.post(
            "/api/v1/warehouse-locations/", json=sample_location_data
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["location_code"] == sample_location_data["location_code"]
        assert data["location_type"] == "bin"
        assert data["pickable"]
        assert data["access_method"] == "forklift"
        assert len(data["equipment_required"]) == 2
        mock_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_locations_by_zone")
    def test_get_locations_by_zone(self, mock_get):
        """ゾーン別ロケーション一覧取得APIのテスト"""
        # モック設定
        zone_id = str(uuid.uuid4())
        mock_locations = [
            WarehouseLocation(
                id=str(uuid.uuid4()),
                zone_id=zone_id,
                location_code="A01-001-001",
                location_type="bin",
                status="available",
                is_occupied=False,
            ),
            WarehouseLocation(
                id=str(uuid.uuid4()),
                zone_id=zone_id,
                location_code="A01-001-002",
                location_type="bin",
                status="occupied",
                is_occupied=True,
            ),
        ]
        mock_get.return_value = {"items": mock_locations, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/warehouse-locations/zone/{zone_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["location_code"] == "A01-001-001"
        assert data["items"][1]["is_occupied"]
        mock_get.assert_called_once_with(zone_id)

    @patch("app.crud.warehouse_v30.get_location_by_id")
    def test_get_location_by_id_success(self, mock_get):
        """ロケーション詳細取得APIのテスト"""
        # モック設定
        location_id = str(uuid.uuid4())
        mock_location = WarehouseLocation(
            id=location_id,
            location_code="A01-001-001",
            location_type="bin",
            weight_capacity=Decimal("500.00"),
            current_stock_quantity=Decimal("125.500"),
            occupancy_percentage=Decimal("25.10"),
        )
        mock_get.return_value = mock_location

        # APIコール
        response = client.get(f"/api/v1/warehouse-locations/{location_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == location_id
        assert data["location_code"] == "A01-001-001"
        assert float(data["weight_capacity"]) == 500.00
        assert float(data["current_stock_quantity"]) == 125.500
        mock_get.assert_called_once_with(location_id)

    @patch("app.crud.warehouse_v30.update_location")
    @patch("app.crud.warehouse_v30.get_location_by_id")
    def test_update_location_success(self, mock_get, mock_update, sample_location_data):
        """ロケーション更新APIのテスト"""
        # モック設定
        location_id = str(uuid.uuid4())
        existing_location = WarehouseLocation(**sample_location_data)
        existing_location.id = location_id
        mock_get.return_value = existing_location

        updated_data = sample_location_data.copy()
        updated_data["pick_priority"] = 85
        updated_data["current_stock_quantity"] = "250.000"
        updated_data["is_occupied"] = True

        updated_location = WarehouseLocation(**updated_data)
        updated_location.id = location_id
        mock_update.return_value = updated_location

        # APIコール
        response = client.put(
            f"/api/v1/warehouse-locations/{location_id}", json=updated_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["pick_priority"] == 85
        assert float(data["current_stock_quantity"]) == 250.000
        assert data["is_occupied"]
        mock_update.assert_called_once()

    @patch("app.crud.warehouse_v30.delete_location")
    @patch("app.crud.warehouse_v30.get_location_by_id")
    def test_delete_location_success(self, mock_get, mock_delete):
        """ロケーション削除APIのテスト"""
        # モック設定
        location_id = str(uuid.uuid4())
        mock_location = WarehouseLocation(
            id=location_id,
            location_code="A01-001-001",
            status="available",
            is_occupied=False,
        )
        mock_get.return_value = mock_location
        mock_delete.return_value = True

        # APIコール
        response = client.delete(f"/api/v1/warehouse-locations/{location_id}")

        # 検証
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["message"]
        mock_delete.assert_called_once_with(location_id)

    @patch("app.crud.warehouse_v30.get_available_locations")
    def test_get_available_locations(self, mock_get_available):
        """利用可能ロケーション取得APIのテスト"""
        # モック設定
        warehouse_id = str(uuid.uuid4())
        mock_locations = [
            WarehouseLocation(
                id=str(uuid.uuid4()),
                location_code="A01-001-001",
                location_type="bin",
                status="available",
                is_occupied=False,
                weight_capacity=Decimal("500.00"),
            ),
            WarehouseLocation(
                id=str(uuid.uuid4()),
                location_code="A01-001-003",
                location_type="bin",
                status="available",
                is_occupied=False,
                weight_capacity=Decimal("500.00"),
            ),
        ]
        mock_get_available.return_value = {"items": mock_locations, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/warehouse-locations/available/{warehouse_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["status"] == "available"
        assert not data["items"][1]["is_occupied"]
        mock_get_available.assert_called_once_with(warehouse_id)

    @patch("app.crud.warehouse_v30.create_locations_bulk")
    def test_bulk_create_locations(self, mock_bulk_create):
        """ロケーション一括作成APIのテスト"""
        # モック設定
        bulk_data = [
            {
                "warehouse_id": str(uuid.uuid4()),
                "zone_id": str(uuid.uuid4()),
                "location_code": "A01-001-001",
                "location_type": "bin",
            },
            {
                "warehouse_id": str(uuid.uuid4()),
                "zone_id": str(uuid.uuid4()),
                "location_code": "A01-001-002",
                "location_type": "bin",
            },
        ]

        mock_result = {
            "created": 2,
            "failed": 0,
            "location_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "errors": [],
        }
        mock_bulk_create.return_value = mock_result

        # APIコール
        response = client.post(
            "/api/v1/warehouse-locations/bulk", json={"locations": bulk_data}
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["location_ids"]) == 2
        mock_bulk_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_location_history")
    def test_get_location_history(self, mock_get_history):
        """ロケーション履歴取得APIのテスト"""
        # モック設定
        location_id = str(uuid.uuid4())
        mock_history = [
            {
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "event_type": "stock_received",
                "quantity": Decimal("100.000"),
                "product_id": str(uuid.uuid4()),
                "performed_by": "user-001",
                "reference": "PO-12345",
            },
            {
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "event_type": "stock_picked",
                "quantity": Decimal("25.000"),
                "product_id": str(uuid.uuid4()),
                "performed_by": "user-002",
                "reference": "SO-67890",
            },
        ]
        mock_get_history.return_value = {"items": mock_history, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/warehouse-locations/{location_id}/history")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["event_type"] == "stock_received"
        assert float(data["items"][1]["quantity"]) == 25.000
        mock_get_history.assert_called_once_with(location_id)


class TestInventoryMovementAPI:
    """在庫移動管理APIのテストクラス (9エンドポイント)"""

    @pytest.fixture
    def sample_movement_data(self):
        return {
            "warehouse_id": str(uuid.uuid4()),
            "location_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "movement_type": "receipt",
            "movement_subtype": "purchase_receipt",
            "reference_number": "PO-12345",
            "reference_line": 1,
            "quantity": "100.000",
            "unit_of_measure": "PC",
            "cost_per_unit": "25.5000",
            "total_cost": "2550.00",
            "lot_number": "LOT-20240315-001",
            "serial_numbers": [],
            "expiration_date": None,
            "manufacture_date": "2024-03-15T00:00:00",
            "from_location_id": None,
            "to_location_id": str(uuid.uuid4()),
            "from_warehouse_id": None,
            "to_warehouse_id": str(uuid.uuid4()),
            "planned_date": "2024-03-20T10:00:00",
            "actual_date": None,
            "performed_by": None,
            "approved_by": None,
            "reason_code": "purchase_order",
            "reason_description": "New inventory received from supplier",
            "business_process": "procurement",
            "quality_status": "approved",
            "inspection_required": False,
            "inspector_id": None,
            "inspection_date": None,
            "inspection_notes": None,
            "carrier": "FastShip Logistics",
            "tracking_number": "FS123456789",
            "freight_cost": "125.00",
            "delivery_method": "ground",
            "tax_amount": "255.00",
            "duty_amount": "0.00",
            "accounting_period": "2024-03",
            "cost_center": "CC-PROC-001",
            "source_system": "ERP",
            "integration_batch_id": "BATCH-20240320-001",
            "sync_status": "pending",
            "error_messages": [],
            "retry_count": 0,
            "status": "pending",
            "is_reversed": False,
            "reversal_movement_id": None,
            "inventory_impact": "100.000",
            "value_impact": "2550.00",
            "custom_fields": {"supplier_id": "SUP-001", "po_line_id": "POL-001"},
            "tags": ["purchase", "bulk_receipt"],
            "notes": "Initial stock receipt for new product line",
        }

    @patch("app.crud.warehouse_v30.create_movement")
    def test_create_movement_success(self, mock_create, sample_movement_data):
        """在庫移動作成APIのテスト"""
        # モック設定
        created_movement = InventoryMovement(**sample_movement_data)
        created_movement.id = str(uuid.uuid4())
        created_movement.created_at = datetime.utcnow()
        mock_create.return_value = created_movement

        # APIコール
        response = client.post(
            "/api/v1/inventory-movements/", json=sample_movement_data
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["movement_type"] == "receipt"
        assert data["movement_subtype"] == "purchase_receipt"
        assert data["reference_number"] == "PO-12345"
        assert float(data["quantity"]) == 100.000
        assert data["lot_number"] == "LOT-20240315-001"
        mock_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_movements")
    def test_get_movements_with_filters(self, mock_get):
        """在庫移動一覧取得APIのテスト（フィルタ付き）"""
        # モック設定
        mock_movements = [
            InventoryMovement(
                id=str(uuid.uuid4()),
                movement_type="receipt",
                reference_number="PO-12345",
                quantity=Decimal("100.000"),
                status="completed",
            ),
            InventoryMovement(
                id=str(uuid.uuid4()),
                movement_type="shipment",
                reference_number="SO-67890",
                quantity=Decimal("50.000"),
                status="completed",
            ),
        ]
        mock_get.return_value = {"items": mock_movements, "total": 2}

        # APIコール
        response = client.get(
            "/api/v1/inventory-movements/?movement_type=receipt&status=completed"
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["movement_type"] == "receipt"
        assert data["items"][1]["movement_type"] == "shipment"
        mock_get.assert_called_once()

    @patch("app.crud.warehouse_v30.get_movement_by_id")
    def test_get_movement_by_id_success(self, mock_get):
        """在庫移動詳細取得APIのテスト"""
        # モック設定
        movement_id = str(uuid.uuid4())
        mock_movement = InventoryMovement(
            id=movement_id,
            movement_type="receipt",
            reference_number="PO-12345",
            quantity=Decimal("100.000"),
            cost_per_unit=Decimal("25.5000"),
            total_cost=Decimal("2550.00"),
            status="completed",
        )
        mock_get.return_value = mock_movement

        # APIコール
        response = client.get(f"/api/v1/inventory-movements/{movement_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == movement_id
        assert data["movement_type"] == "receipt"
        assert float(data["quantity"]) == 100.000
        assert float(data["cost_per_unit"]) == 25.5000
        mock_get.assert_called_once_with(movement_id)

    @patch("app.crud.warehouse_v30.update_movement")
    @patch("app.crud.warehouse_v30.get_movement_by_id")
    def test_update_movement_success(self, mock_get, mock_update, sample_movement_data):
        """在庫移動更新APIのテスト"""
        # モック設定
        movement_id = str(uuid.uuid4())
        existing_movement = InventoryMovement(**sample_movement_data)
        existing_movement.id = movement_id
        mock_get.return_value = existing_movement

        updated_data = sample_movement_data.copy()
        updated_data["status"] = "completed"
        updated_data["actual_date"] = "2024-03-20T14:30:00"
        updated_data["performed_by"] = "user-001"

        updated_movement = InventoryMovement(**updated_data)
        updated_movement.id = movement_id
        mock_update.return_value = updated_movement

        # APIコール
        response = client.put(
            f"/api/v1/inventory-movements/{movement_id}", json=updated_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["performed_by"] == "user-001"
        mock_update.assert_called_once()

    @patch("app.crud.warehouse_v30.complete_movement")
    @patch("app.crud.warehouse_v30.get_movement_by_id")
    def test_complete_movement_success(self, mock_get, mock_complete):
        """在庫移動完了APIのテスト"""
        # モック設定
        movement_id = str(uuid.uuid4())
        mock_movement = InventoryMovement(
            id=movement_id, movement_type="receipt", status="in_progress"
        )
        mock_get.return_value = mock_movement

        completed_movement = InventoryMovement(
            id=movement_id,
            movement_type="receipt",
            status="completed",
            actual_date=datetime.utcnow(),
        )
        mock_complete.return_value = completed_movement

        completion_data = {
            "actual_quantity": "98.000",
            "performed_by": "user-001",
            "completion_notes": "Received with minor damage to packaging",
        }

        # APIコール
        response = client.post(
            f"/api/v1/inventory-movements/{movement_id}/complete", json=completion_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        mock_complete.assert_called_once()

    @patch("app.crud.warehouse_v30.reverse_movement")
    @patch("app.crud.warehouse_v30.get_movement_by_id")
    def test_reverse_movement_success(self, mock_get, mock_reverse):
        """在庫移動取消APIのテスト"""
        # モック設定
        movement_id = str(uuid.uuid4())
        mock_movement = InventoryMovement(
            id=movement_id,
            movement_type="receipt",
            status="completed",
            is_reversed=False,
        )
        mock_get.return_value = mock_movement

        reversal_data = {
            "reversal_reason": "Damaged goods returned to supplier",
            "reversal_quantity": "100.000",
        }

        reversal_movement = InventoryMovement(
            id=str(uuid.uuid4()),
            movement_type="adjustment",
            status="completed",
            is_reversed=False,
            reversal_movement_id=movement_id,
        )
        mock_reverse.return_value = reversal_movement

        # APIコール
        response = client.post(
            f"/api/v1/inventory-movements/{movement_id}/reverse", json=reversal_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["movement_type"] == "adjustment"
        assert data["reversal_movement_id"] == movement_id
        mock_reverse.assert_called_once()

    @patch("app.crud.warehouse_v30.get_movements_by_product")
    def test_get_movements_by_product(self, mock_get_by_product):
        """商品別移動履歴取得APIのテスト"""
        # モック設定
        product_id = str(uuid.uuid4())
        mock_movements = [
            InventoryMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                movement_type="receipt",
                quantity=Decimal("100.000"),
                created_at=datetime.utcnow() - timedelta(days=5),
            ),
            InventoryMovement(
                id=str(uuid.uuid4()),
                product_id=product_id,
                movement_type="shipment",
                quantity=Decimal("30.000"),
                created_at=datetime.utcnow() - timedelta(days=3),
            ),
        ]
        mock_get_by_product.return_value = {"items": mock_movements, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/inventory-movements/product/{product_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["movement_type"] == "receipt"
        assert float(data["items"][1]["quantity"]) == 30.000
        mock_get_by_product.assert_called_once_with(product_id)

    @patch("app.crud.warehouse_v30.create_movements_bulk")
    def test_bulk_create_movements(self, mock_bulk_create):
        """在庫移動一括作成APIのテスト"""
        # モック設定
        bulk_data = [
            {
                "warehouse_id": str(uuid.uuid4()),
                "product_id": str(uuid.uuid4()),
                "movement_type": "receipt",
                "quantity": "100.000",
                "unit_of_measure": "PC",
            },
            {
                "warehouse_id": str(uuid.uuid4()),
                "product_id": str(uuid.uuid4()),
                "movement_type": "receipt",
                "quantity": "50.000",
                "unit_of_measure": "PC",
            },
        ]

        mock_result = {
            "created": 2,
            "failed": 0,
            "movement_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "errors": [],
        }
        mock_bulk_create.return_value = mock_result

        # APIコール
        response = client.post(
            "/api/v1/inventory-movements/bulk", json={"movements": bulk_data}
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["movement_ids"]) == 2
        mock_bulk_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_movement_analytics")
    def test_get_movement_analytics(self, mock_get_analytics):
        """移動分析データ取得APIのテスト"""
        # モック設定
        mock_analytics = {
            "total_movements": 2450,
            "movements_by_type": {
                "receipt": 650,
                "shipment": 580,
                "adjustment": 120,
                "transfer": 1100,
            },
            "monthly_volume": [
                {"month": "2024-01", "volume": 850},
                {"month": "2024-02", "volume": 920},
                {"month": "2024-03", "volume": 680},
            ],
            "value_summary": {
                "total_value": Decimal("12500000.00"),
                "receipts_value": Decimal("8200000.00"),
                "shipments_value": Decimal("4300000.00"),
            },
            "accuracy_metrics": {
                "movement_accuracy": Decimal("99.65"),
                "variance_rate": Decimal("0.35"),
                "error_count": 15,
            },
        }
        mock_get_analytics.return_value = mock_analytics

        # APIコール
        response = client.get("/api/v1/inventory-movements/analytics")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total_movements"] == 2450
        assert data["movements_by_type"]["receipt"] == 650
        assert len(data["monthly_volume"]) == 3
        assert float(data["value_summary"]["total_value"]) == 12500000.00
        assert float(data["accuracy_metrics"]["movement_accuracy"]) == 99.65
        mock_get_analytics.assert_called_once()


class TestCycleCountAPI:
    """棚卸管理APIのテストクラス (10エンドポイント)"""

    @pytest.fixture
    def sample_cycle_count_data(self):
        return {
            "warehouse_id": str(uuid.uuid4()),
            "count_number": "CC-2024-001",
            "count_name": "Quarterly Cycle Count - Q1 2024",
            "count_type": "cycle",
            "count_scope": "zone",
            "zone_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "location_ids": [],
            "product_ids": [],
            "category_ids": [],
            "planned_date": "2024-03-25T08:00:00",
            "start_date": None,
            "end_date": None,
            "cutoff_time": "2024-03-25T07:00:00",
            "count_manager_id": str(uuid.uuid4()),
            "assigned_counters": [str(uuid.uuid4()), str(uuid.uuid4())],
            "supervisor_id": str(uuid.uuid4()),
            "count_method": "scanner",
            "recount_required": True,
            "tolerance_percentage": "2.00",
            "minimum_count_value": "100.00",
            "exclude_zero_quantities": False,
            "status": "planned",
            "completion_percentage": "0.00",
            "total_locations_planned": 0,
            "locations_counted": 0,
            "locations_remaining": 0,
            "total_items_counted": 0,
            "items_with_variance": 0,
            "total_variance_value": "0.00",
            "accuracy_percentage": None,
            "requires_approval": True,
            "approved_by": None,
            "approved_at": None,
            "approval_notes": None,
            "freeze_inventory": True,
            "auto_adjust": False,
            "generate_adjustments": True,
            "instructions": "Count all items in assigned zones. Report any discrepancies immediately.",
            "notes": "Quarterly cycle count covering high-velocity zones",
            "tags": ["quarterly", "high_velocity", "zones_A_B"],
        }

    @patch("app.crud.warehouse_v30.create_cycle_count")
    def test_create_cycle_count_success(self, mock_create, sample_cycle_count_data):
        """棚卸作成APIのテスト"""
        # モック設定
        created_count = CycleCount(**sample_cycle_count_data)
        created_count.id = str(uuid.uuid4())
        created_count.created_at = datetime.utcnow()
        mock_create.return_value = created_count

        # APIコール
        response = client.post("/api/v1/cycle-counts/", json=sample_cycle_count_data)

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["count_number"] == "CC-2024-001"
        assert data["count_name"] == "Quarterly Cycle Count - Q1 2024"
        assert data["count_type"] == "cycle"
        assert data["count_scope"] == "zone"
        assert len(data["zone_ids"]) == 2
        assert data["count_method"] == "scanner"
        mock_create.assert_called_once()

    @patch("app.crud.warehouse_v30.get_cycle_counts")
    def test_get_cycle_counts_with_filters(self, mock_get):
        """棚卸一覧取得APIのテスト（フィルタ付き）"""
        # モック設定
        mock_counts = [
            CycleCount(
                id=str(uuid.uuid4()),
                count_number="CC-2024-001",
                count_name="Quarterly Count Q1",
                count_type="cycle",
                status="in_progress",
            ),
            CycleCount(
                id=str(uuid.uuid4()),
                count_number="CC-2024-002",
                count_name="Quarterly Count Q1 Zone C",
                count_type="cycle",
                status="completed",
            ),
        ]
        mock_get.return_value = {"items": mock_counts, "total": 2}

        # APIコール
        response = client.get(
            "/api/v1/cycle-counts/?count_type=cycle&status=in_progress"
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["count_number"] == "CC-2024-001"
        assert data["items"][1]["status"] == "completed"
        mock_get.assert_called_once()

    @patch("app.crud.warehouse_v30.get_cycle_count_by_id")
    def test_get_cycle_count_by_id_success(self, mock_get):
        """棚卸詳細取得APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_count = CycleCount(
            id=count_id,
            count_number="CC-2024-001",
            count_name="Quarterly Count Q1",
            total_locations_planned=500,
            locations_counted=320,
            completion_percentage=Decimal("64.00"),
            accuracy_percentage=Decimal("98.80"),
        )
        mock_get.return_value = mock_count

        # APIコール
        response = client.get(f"/api/v1/cycle-counts/{count_id}")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == count_id
        assert data["count_number"] == "CC-2024-001"
        assert data["total_locations_planned"] == 500
        assert data["locations_counted"] == 320
        assert float(data["completion_percentage"]) == 64.00
        mock_get.assert_called_once_with(count_id)

    @patch("app.crud.warehouse_v30.update_cycle_count")
    @patch("app.crud.warehouse_v30.get_cycle_count_by_id")
    def test_update_cycle_count_success(
        self, mock_get, mock_update, sample_cycle_count_data
    ):
        """棚卸更新APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        existing_count = CycleCount(**sample_cycle_count_data)
        existing_count.id = count_id
        mock_get.return_value = existing_count

        updated_data = sample_cycle_count_data.copy()
        updated_data["status"] = "in_progress"
        updated_data["start_date"] = "2024-03-25T08:00:00"
        updated_data["completion_percentage"] = "25.50"

        updated_count = CycleCount(**updated_data)
        updated_count.id = count_id
        mock_update.return_value = updated_count

        # APIコール
        response = client.put(f"/api/v1/cycle-counts/{count_id}", json=updated_data)

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert float(data["completion_percentage"]) == 25.50
        mock_update.assert_called_once()

    @patch("app.crud.warehouse_v30.start_cycle_count")
    @patch("app.crud.warehouse_v30.get_cycle_count_by_id")
    def test_start_cycle_count_success(self, mock_get, mock_start):
        """棚卸開始APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_count = CycleCount(
            id=count_id, count_number="CC-2024-001", status="planned"
        )
        mock_get.return_value = mock_count

        started_count = CycleCount(
            id=count_id,
            count_number="CC-2024-001",
            status="in_progress",
            start_date=datetime.utcnow(),
            total_locations_planned=450,
        )
        mock_start.return_value = started_count

        # APIコール
        response = client.post(f"/api/v1/cycle-counts/{count_id}/start")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["total_locations_planned"] == 450
        mock_start.assert_called_once_with(count_id)

    @patch("app.crud.warehouse_v30.complete_cycle_count")
    @patch("app.crud.warehouse_v30.get_cycle_count_by_id")
    def test_complete_cycle_count_success(self, mock_get, mock_complete):
        """棚卸完了APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_count = CycleCount(
            id=count_id, count_number="CC-2024-001", status="in_progress"
        )
        mock_get.return_value = mock_count

        completed_count = CycleCount(
            id=count_id,
            count_number="CC-2024-001",
            status="completed",
            end_date=datetime.utcnow(),
            completion_percentage=Decimal("100.00"),
            accuracy_percentage=Decimal("98.75"),
        )
        mock_complete.return_value = completed_count

        completion_data = {
            "final_notes": "Count completed successfully with minor variances",
            "generate_adjustments": True,
        }

        # APIコール
        response = client.post(
            f"/api/v1/cycle-counts/{count_id}/complete", json=completion_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert float(data["completion_percentage"]) == 100.00
        assert float(data["accuracy_percentage"]) == 98.75
        mock_complete.assert_called_once()

    @patch("app.crud.warehouse_v30.approve_cycle_count")
    @patch("app.crud.warehouse_v30.get_cycle_count_by_id")
    def test_approve_cycle_count_success(self, mock_get, mock_approve):
        """棚卸承認APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_count = CycleCount(
            id=count_id,
            count_number="CC-2024-001",
            status="completed",
            requires_approval=True,
        )
        mock_get.return_value = mock_count

        approved_count = CycleCount(
            id=count_id,
            count_number="CC-2024-001",
            status="completed",
            approved_by="user-001",
            approved_at=datetime.utcnow(),
        )
        mock_approve.return_value = approved_count

        approval_data = {
            "approval_notes": "Count results reviewed and approved. Minor variances acceptable.",
            "generate_adjustments": True,
        }

        # APIコール
        response = client.post(
            f"/api/v1/cycle-counts/{count_id}/approve", json=approval_data
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["approved_by"] == "user-001"
        mock_approve.assert_called_once()

    @patch("app.crud.warehouse_v30.get_cycle_count_lines")
    def test_get_cycle_count_lines(self, mock_get_lines):
        """棚卸明細取得APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_lines = [
            CycleCountLine(
                id=str(uuid.uuid4()),
                cycle_count_id=count_id,
                location_id=str(uuid.uuid4()),
                product_id=str(uuid.uuid4()),
                book_quantity=Decimal("100.000"),
                counted_quantity=Decimal("98.000"),
                variance_quantity=Decimal("-2.000"),
                count_status="counted",
            ),
            CycleCountLine(
                id=str(uuid.uuid4()),
                cycle_count_id=count_id,
                location_id=str(uuid.uuid4()),
                product_id=str(uuid.uuid4()),
                book_quantity=Decimal("50.000"),
                counted_quantity=Decimal("50.000"),
                variance_quantity=Decimal("0.000"),
                count_status="approved",
            ),
        ]
        mock_get_lines.return_value = {"items": mock_lines, "total": 2}

        # APIコール
        response = client.get(f"/api/v1/cycle-counts/{count_id}/lines")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert float(data["items"][0]["variance_quantity"]) == -2.000
        assert data["items"][1]["count_status"] == "approved"
        mock_get_lines.assert_called_once_with(count_id)

    @patch("app.crud.warehouse_v30.get_cycle_count_analytics")
    def test_get_cycle_count_analytics(self, mock_get_analytics):
        """棚卸分析データ取得APIのテスト"""
        # モック設定
        count_id = str(uuid.uuid4())
        mock_analytics = {
            "count_id": count_id,
            "accuracy_summary": {
                "overall_accuracy": Decimal("98.75"),
                "location_accuracy": Decimal("99.20"),
                "quantity_accuracy": Decimal("98.30"),
            },
            "variance_analysis": {
                "total_variances": 25,
                "positive_variances": 12,
                "negative_variances": 13,
                "variance_value": Decimal("2450.80"),
                "variance_percentage": Decimal("0.98"),
            },
            "productivity_metrics": {
                "locations_per_hour": Decimal("45.5"),
                "items_per_hour": Decimal("180.3"),
                "time_per_location": Decimal("1.32"),
            },
            "zone_performance": [
                {
                    "zone_id": "zone-1",
                    "accuracy": Decimal("99.10"),
                    "variance_count": 8,
                },
                {
                    "zone_id": "zone-2",
                    "accuracy": Decimal("98.40"),
                    "variance_count": 17,
                },
            ],
        }
        mock_get_analytics.return_value = mock_analytics

        # APIコール
        response = client.get(f"/api/v1/cycle-counts/{count_id}/analytics")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert float(data["accuracy_summary"]["overall_accuracy"]) == 98.75
        assert data["variance_analysis"]["total_variances"] == 25
        assert float(data["productivity_metrics"]["locations_per_hour"]) == 45.5
        assert len(data["zone_performance"]) == 2
        mock_get_analytics.assert_called_once_with(count_id)

    @patch("app.crud.warehouse_v30.create_cycle_counts_bulk")
    def test_bulk_create_cycle_counts(self, mock_bulk_create):
        """棚卸一括作成APIのテスト"""
        # モック設定
        bulk_data = [
            {
                "warehouse_id": str(uuid.uuid4()),
                "count_number": "CC-2024-001",
                "count_name": "Q1 Zone A Count",
                "count_type": "cycle",
                "planned_date": "2024-03-25T08:00:00",
            },
            {
                "warehouse_id": str(uuid.uuid4()),
                "count_number": "CC-2024-002",
                "count_name": "Q1 Zone B Count",
                "count_type": "cycle",
                "planned_date": "2024-03-26T08:00:00",
            },
        ]

        mock_result = {
            "created": 2,
            "failed": 0,
            "count_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "errors": [],
        }
        mock_bulk_create.return_value = mock_result

        # APIコール
        response = client.post(
            "/api/v1/cycle-counts/bulk", json={"cycle_counts": bulk_data}
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["count_ids"]) == 2
        mock_bulk_create.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
