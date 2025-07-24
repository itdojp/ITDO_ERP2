import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.product_extended import (
    InventoryMovement,
    Product,
    ProductCategory,
    ProductPriceHistory,
    Supplier,
)
from app.schemas.product_complete_v30 import (
    InventoryMovementCreate,
    ProductCategoryCreate,
    ProductCreate,
    ProductUpdate,
    SupplierCreate,
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class ProductCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return (
            self.db.query(Product)
            .options(joinedload(Product.category), joinedload(Product.supplier))
            .filter(Product.id == product_id)
            .first()
        )

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.sku == sku).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[List[Product], int]:
        query = self.db.query(Product)

        # フィルタリング
        if filters:
            if filters.get("category_id"):
                query = query.filter(Product.category_id == filters["category_id"])
            if filters.get("supplier_id"):
                query = query.filter(Product.supplier_id == filters["supplier_id"])
            if filters.get("brand"):
                query = query.filter(Product.brand == filters["brand"])
            if filters.get("product_status"):
                query = query.filter(
                    Product.product_status == filters["product_status"]
                )
            if filters.get("product_type"):
                query = query.filter(Product.product_type == filters["product_type"])
            if filters.get("is_sellable") is not None:
                query = query.filter(Product.is_sellable == filters["is_sellable"])
            if filters.get("low_stock"):
                query = query.filter(Product.stock_quantity <= Product.reorder_point)
            if filters.get("out_of_stock"):
                query = query.filter(Product.stock_quantity <= 0)
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search),
                        Product.sku.ilike(search),
                        Product.description.ilike(search),
                        Product.brand.ilike(search),
                    )
                )
            if filters.get("price_min"):
                query = query.filter(Product.selling_price >= filters["price_min"])
            if filters.get("price_max"):
                query = query.filter(Product.selling_price <= filters["price_max"])

        # カウント
        total = query.count()

        # ソート
        order_by = getattr(Product, sort_by, Product.created_at)
        if sort_desc:
            order_by = order_by.desc()
        query = query.order_by(order_by)

        # ページネーション
        products = query.offset(skip).limit(limit).all()

        # available_quantity を計算
        for product in products:
            product.available_quantity = max(
                0, product.stock_quantity - product.reserved_quantity
            )

        return products, total

    def create(self, product_in: ProductCreate) -> Product:
        # SKU重複チェック
        if self.get_by_sku(product_in.sku):
            raise DuplicateError("SKU already exists")

        # バーコード重複チェック
        if product_in.barcode:
            existing = (
                self.db.query(Product)
                .filter(Product.barcode == product_in.barcode)
                .first()
            )
            if existing:
                raise DuplicateError("Barcode already exists")

        # 体積計算
        volume = None
        if product_in.length and product_in.width and product_in.height:
            volume = (
                product_in.length * product_in.width * product_in.height / 1000
            )  # cm³ to L

        db_product = Product(
            id=str(uuid.uuid4()),
            sku=product_in.sku.upper(),
            name=product_in.name,
            description=product_in.description,
            short_description=product_in.short_description,
            category_id=product_in.category_id,
            brand=product_in.brand,
            manufacturer=product_in.manufacturer,
            supplier_id=product_in.supplier_id,
            cost_price=product_in.cost_price,
            selling_price=product_in.selling_price,
            list_price=product_in.list_price,
            min_price=product_in.min_price,
            weight=product_in.weight,
            length=product_in.length,
            width=product_in.width,
            height=product_in.height,
            volume=volume,
            track_inventory=product_in.track_inventory,
            reorder_point=product_in.reorder_point,
            reorder_quantity=product_in.reorder_quantity,
            max_stock_level=product_in.max_stock_level,
            unit_of_measure=product_in.unit_of_measure,
            product_type=product_in.product_type,
            product_status=product_in.product_status,
            quality_grade=product_in.quality_grade,
            certification=product_in.certification,
            warranty_period=product_in.warranty_period,
            expiry_period=product_in.expiry_period,
            is_purchaseable=product_in.is_purchaseable,
            is_sellable=product_in.is_sellable,
            min_order_quantity=product_in.min_order_quantity,
            max_order_quantity=product_in.max_order_quantity,
            search_keywords=product_in.search_keywords,
            barcode=product_in.barcode,
            tax_category=product_in.tax_category,
            tax_rate=product_in.tax_rate,
            attributes=product_in.attributes,
            specifications=product_in.specifications,
        )

        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)

        # 価格履歴記録
        self._record_price_history(db_product, "Product created")

        return db_product

    def update(self, product_id: str, product_in: ProductUpdate) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")

        # 価格変更チェック
        price_changed = False

        update_data = product_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if (
                field in ["cost_price", "selling_price", "list_price"]
                and getattr(product, field) != value
            ):
                price_changed = True
            setattr(product, field, value)

        # 体積再計算
        if any(field in update_data for field in ["length", "width", "height"]):
            if product.length and product.width and product.height:
                product.volume = product.length * product.width * product.height / 1000

        product.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(product)

        # 価格変更があった場合は履歴記録
        if price_changed:
            self._record_price_history(product, "Product updated")

        return product

    def delete(self, product_id: str) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")

        # 在庫がある場合は削除不可
        if product.stock_quantity > 0:
            raise ValueError("Cannot delete product with inventory")

        # ソフトデリート
        product.product_status = "discontinued"
        product.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def adjust_inventory(
        self, product_id: str, movement: InventoryMovementCreate, user_id: str
    ) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")

        if not product.track_inventory:
            raise ValueError("Product inventory is not tracked")

        # 在庫移動記録
        stock_before = product.stock_quantity

        if movement.movement_type == "in":
            product.stock_quantity += movement.quantity
        elif movement.movement_type == "out":
            if product.stock_quantity < movement.quantity:
                raise ValueError("Insufficient inventory")
            product.stock_quantity -= movement.quantity
        elif movement.movement_type == "adjustment":
            product.stock_quantity = movement.quantity

        stock_after = product.stock_quantity
        total_cost = None
        if movement.unit_cost:
            total_cost = movement.unit_cost * abs(movement.quantity)

        # 在庫移動レコード作成
        inventory_movement = InventoryMovement(
            id=str(uuid.uuid4()),
            product_id=product_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            unit_cost=movement.unit_cost,
            total_cost=total_cost,
            stock_before=stock_before,
            stock_after=stock_after,
            reference_type=movement.reference_type,
            reference_id=movement.reference_id,
            reason=movement.reason,
            notes=movement.notes,
            warehouse_from=movement.warehouse_from,
            warehouse_to=movement.warehouse_to,
            location=movement.location,
            created_by=user_id,
            movement_date=movement.movement_date,
        )

        self.db.add(inventory_movement)
        self.db.commit()
        self.db.refresh(product)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """商品統計情報を取得"""
        total_products = self.db.query(func.count(Product.id)).scalar()
        active_products = (
            self.db.query(func.count(Product.id))
            .filter(Product.product_status == "active")
            .scalar()
        )
        inactive_products = (
            self.db.query(func.count(Product.id))
            .filter(Product.product_status == "inactive")
            .scalar()
        )
        discontinued_products = (
            self.db.query(func.count(Product.id))
            .filter(Product.product_status == "discontinued")
            .scalar()
        )

        # カテゴリ別統計
        category_stats = {}
        category_results = (
            self.db.query(ProductCategory.name, func.count(Product.id))
            .join(Product, ProductCategory.id == Product.category_id, isouter=True)
            .group_by(ProductCategory.name)
            .all()
        )
        for category, count in category_results:
            category_stats[category or "未分類"] = count or 0

        # ブランド別統計
        brand_stats = {}
        brand_results = (
            self.db.query(Product.brand, func.count(Product.id))
            .group_by(Product.brand)
            .all()
        )
        for brand, count in brand_results:
            brand_stats[brand or "未設定"] = count

        # サプライヤー別統計
        supplier_stats = {}
        supplier_results = (
            self.db.query(Supplier.name, func.count(Product.id))
            .join(Product, Supplier.id == Product.supplier_id, isouter=True)
            .group_by(Supplier.name)
            .all()
        )
        for supplier, count in supplier_results:
            supplier_stats[supplier or "未設定"] = count or 0

        # 在庫状況
        low_stock_count = (
            self.db.query(func.count(Product.id))
            .filter(
                Product.stock_quantity <= Product.reorder_point, Product.track_inventory
            )
            .scalar()
        )

        out_of_stock_count = (
            self.db.query(func.count(Product.id))
            .filter(Product.stock_quantity <= 0, Product.track_inventory)
            .scalar()
        )

        # 在庫総額
        inventory_value = self.db.query(
            func.sum(Product.stock_quantity * Product.cost_price)
        ).filter(Product.cost_price.isnot(None)).scalar() or Decimal("0")

        return {
            "total_products": total_products or 0,
            "active_products": active_products or 0,
            "inactive_products": inactive_products or 0,
            "discontinued_products": discontinued_products or 0,
            "by_category": category_stats,
            "by_brand": brand_stats,
            "by_supplier": supplier_stats,
            "low_stock_count": low_stock_count or 0,
            "out_of_stock_count": out_of_stock_count or 0,
            "total_inventory_value": inventory_value,
        }

    def bulk_update_prices(
        self,
        product_ids: List[str],
        price_type: str,
        adjustment_type: str,
        adjustment_value: Decimal,
        reason: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """一括価格更新"""
        updated_products = []
        errors = []

        for product_id in product_ids:
            try:
                product = self.get_by_id(product_id)
                if not product:
                    errors.append(
                        {"product_id": product_id, "error": "Product not found"}
                    )
                    continue

                current_price = getattr(product, price_type)
                if current_price is None:
                    errors.append(
                        {"product_id": product_id, "error": f"{price_type} not set"}
                    )
                    continue

                if adjustment_type == "amount":
                    new_price = current_price + adjustment_value
                else:  # percentage
                    new_price = current_price * (1 + adjustment_value / 100)

                if new_price < 0:
                    errors.append(
                        {
                            "product_id": product_id,
                            "error": "Negative price not allowed",
                        }
                    )
                    continue

                setattr(product, price_type, new_price)
                product.updated_at = datetime.utcnow()

                # 価格履歴記録
                self._record_price_history(product, reason, user_id)

                updated_products.append(product_id)

            except Exception as e:
                errors.append({"product_id": product_id, "error": str(e)})

        self.db.commit()

        return {
            "success_count": len(updated_products),
            "error_count": len(errors),
            "updated_products": updated_products,
            "errors": errors,
        }

    def _record_price_history(self, product: Product, reason: str, user_id: str = None) -> dict:
        """価格履歴を記録"""
        price_history = ProductPriceHistory(
            id=str(uuid.uuid4()),
            product_id=product.id,
            cost_price=product.cost_price,
            selling_price=product.selling_price,
            list_price=product.list_price,
            change_reason=reason,
            changed_by=user_id,
            effective_from=datetime.utcnow(),
        )
        self.db.add(price_history)


class ProductCategoryCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, category_id: str) -> Optional[ProductCategory]:
        return (
            self.db.query(ProductCategory)
            .filter(ProductCategory.id == category_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[ProductCategory]:
        return (
            self.db.query(ProductCategory).filter(ProductCategory.code == code).first()
        )

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[ProductCategory], int]:
        query = self.db.query(ProductCategory)

        if parent_id is not None:
            query = query.filter(ProductCategory.parent_id == parent_id)
        if is_active is not None:
            query = query.filter(ProductCategory.is_active == is_active)

        total = query.count()
        categories = (
            query.offset(skip).limit(limit).order_by(ProductCategory.name).all()
        )

        return categories, total

    def create(self, category_in: ProductCategoryCreate) -> ProductCategory:
        if self.get_by_code(category_in.code):
            raise DuplicateError("Category code already exists")

        # 親カテゴリの確認
        parent = None
        level = 0
        path = f"/{category_in.code}"

        if category_in.parent_id:
            parent = self.get_by_id(category_in.parent_id)
            if not parent:
                raise NotFoundError("Parent category not found")
            level = parent.level + 1
            path = f"{parent.path}/{category_in.code}"

        db_category = ProductCategory(
            id=str(uuid.uuid4()),
            name=category_in.name,
            code=category_in.code,
            description=category_in.description,
            parent_id=category_in.parent_id,
            level=level,
            path=path,
            tax_rate=category_in.tax_rate,
            commission_rate=category_in.commission_rate,
            metadata_json=category_in.metadata_json,
        )

        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)

        return db_category


class SupplierCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_code(self, code: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.code == code).first()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Supplier], int]:
        query = self.db.query(Supplier)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Supplier.is_active == filters["is_active"])
            if filters.get("is_preferred") is not None:
                query = query.filter(Supplier.is_preferred == filters["is_preferred"])
            if filters.get("supplier_type"):
                query = query.filter(Supplier.supplier_type == filters["supplier_type"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(Supplier.name.ilike(search), Supplier.code.ilike(search))
                )

        total = query.count()
        suppliers = query.offset(skip).limit(limit).order_by(Supplier.name).all()

        return suppliers, total

    def create(self, supplier_in: SupplierCreate) -> Supplier:
        if self.get_by_code(supplier_in.code):
            raise DuplicateError("Supplier code already exists")

        db_supplier = Supplier(
            id=str(uuid.uuid4()),
            name=supplier_in.name,
            code=supplier_in.code,
            email=supplier_in.email,
            phone=supplier_in.phone,
            fax=supplier_in.fax,
            website=supplier_in.website,
            address_line1=supplier_in.address_line1,
            address_line2=supplier_in.address_line2,
            city=supplier_in.city,
            state=supplier_in.state,
            postal_code=supplier_in.postal_code,
            country=supplier_in.country,
            supplier_type=supplier_in.supplier_type,
            payment_terms=supplier_in.payment_terms,
            credit_limit=supplier_in.credit_limit,
            tax_id=supplier_in.tax_id,
            notes=supplier_in.notes,
            metadata_json=supplier_in.metadata_json,
        )

        self.db.add(db_supplier)
        self.db.commit()
        self.db.refresh(db_supplier)

        return db_supplier
