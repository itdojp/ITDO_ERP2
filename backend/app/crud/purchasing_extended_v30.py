import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.purchasing_extended import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    PurchaseRequest,
    PurchaseRequestItem,
    Supplier,
    SupplierProduct,
)
from app.schemas.purchasing_complete_v30 import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseReceiptCreate,
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    SupplierCreate,
    SupplierProductCreate,
    SupplierUpdate,
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class InvalidStatusError(Exception):
    pass


class InsufficientBudgetError(Exception):
    pass


class SupplierCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_code(self, code: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.supplier_code == code).first()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Supplier], int]:
        query = self.db.query(Supplier)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Supplier.is_active == filters["is_active"])
            if filters.get("is_approved") is not None:
                query = query.filter(Supplier.is_approved == filters["is_approved"])
            if filters.get("supplier_type"):
                query = query.filter(Supplier.supplier_type == filters["supplier_type"])
            if filters.get("supplier_category"):
                query = query.filter(
                    Supplier.supplier_category == filters["supplier_category"]
                )
            if filters.get("priority_level"):
                query = query.filter(
                    Supplier.priority_level == filters["priority_level"]
                )
            if filters.get("preferred_supplier") is not None:
                query = query.filter(
                    Supplier.preferred_supplier == filters["preferred_supplier"]
                )
            if filters.get("buyer_id"):
                query = query.filter(Supplier.buyer_id == filters["buyer_id"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Supplier.name.ilike(search),
                        Supplier.company_name.ilike(search),
                        Supplier.supplier_code.ilike(search),
                        Supplier.email.ilike(search),
                    )
                )

        total = query.count()
        suppliers = query.offset(skip).limit(limit).order_by(Supplier.name).all()

        return suppliers, total

    def create(self, supplier_in: SupplierCreate) -> Supplier:
        if self.get_by_code(supplier_in.supplier_code):
            raise DuplicateError("Supplier code already exists")

        db_supplier = Supplier(
            id=str(uuid.uuid4()),
            supplier_code=supplier_in.supplier_code,
            name=supplier_in.name,
            company_name=supplier_in.company_name,
            email=supplier_in.email,
            phone=supplier_in.phone,
            mobile=supplier_in.mobile,
            website=supplier_in.website,
            billing_address_line1=supplier_in.billing_address_line1,
            billing_city=supplier_in.billing_city,
            billing_postal_code=supplier_in.billing_postal_code,
            billing_country=supplier_in.billing_country,
            shipping_address_line1=supplier_in.shipping_address_line1,
            shipping_city=supplier_in.shipping_city,
            shipping_postal_code=supplier_in.shipping_postal_code,
            shipping_country=supplier_in.shipping_country,
            supplier_type=supplier_in.supplier_type,
            supplier_category=supplier_in.supplier_category,
            priority_level=supplier_in.priority_level,
            industry=supplier_in.industry,
            credit_limit=supplier_in.credit_limit,
            payment_terms=supplier_in.payment_terms,
            tax_id=supplier_in.tax_id,
            tax_exempt=supplier_in.tax_exempt,
            buyer_id=supplier_in.buyer_id,
            notes=supplier_in.notes,
            certifications=supplier_in.certifications,
            capabilities=supplier_in.capabilities,
        )

        self.db.add(db_supplier)
        self.db.commit()
        self.db.refresh(db_supplier)

        return db_supplier

    def update(
        self, supplier_id: str, supplier_in: SupplierUpdate
    ) -> Optional[Supplier]:
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")

        update_data = supplier_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)

        supplier.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def update_purchase_stats(self, supplier_id: str, order_amount: Decimal) -> dict:
        """サプライヤーの購買統計を更新"""
        supplier = self.get_by_id(supplier_id)
        if supplier:
            supplier.total_orders += 1
            supplier.total_purchases += order_amount
            supplier.avg_order_value = supplier.total_purchases / supplier.total_orders
            supplier.last_order_date = datetime.utcnow()
            self.db.commit()

    def update_ratings(
        self,
        supplier_id: str,
        quality_rating: Optional[Decimal] = None,
        delivery_rating: Optional[Decimal] = None,
        service_rating: Optional[Decimal] = None,
    ):
        """サプライヤーの評価更新"""
        supplier = self.get_by_id(supplier_id)
        if supplier:
            if quality_rating is not None:
                supplier.quality_rating = quality_rating
            if delivery_rating is not None:
                supplier.delivery_rating = delivery_rating
            if service_rating is not None:
                supplier.service_rating = service_rating

            # 総合評価計算
            ratings = [
                supplier.quality_rating,
                supplier.delivery_rating,
                supplier.service_rating,
            ]
            valid_ratings = [r for r in ratings if r > 0]
            if valid_ratings:
                supplier.overall_rating = sum(valid_ratings) / len(valid_ratings)

            self.db.commit()


class PurchaseRequestCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, request_id: str) -> Optional[PurchaseRequest]:
        return (
            self.db.query(PurchaseRequest)
            .options(joinedload(PurchaseRequest.request_items))
            .filter(PurchaseRequest.id == request_id)
            .first()
        )

    def get_by_number(self, request_number: str) -> Optional[PurchaseRequest]:
        return (
            self.db.query(PurchaseRequest)
            .filter(PurchaseRequest.request_number == request_number)
            .first()
        )

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[PurchaseRequest], int]:
        query = self.db.query(PurchaseRequest)

        if filters:
            if filters.get("requester_id"):
                query = query.filter(
                    PurchaseRequest.requester_id == filters["requester_id"]
                )
            if filters.get("department_id"):
                query = query.filter(
                    PurchaseRequest.department_id == filters["department_id"]
                )
            if filters.get("supplier_id"):
                query = query.filter(
                    PurchaseRequest.supplier_id == filters["supplier_id"]
                )
            if filters.get("status"):
                query = query.filter(PurchaseRequest.status == filters["status"])
            if filters.get("approval_status"):
                query = query.filter(
                    PurchaseRequest.approval_status == filters["approval_status"]
                )
            if filters.get("priority"):
                query = query.filter(PurchaseRequest.priority == filters["priority"])
            if filters.get("date_from"):
                query = query.filter(
                    PurchaseRequest.request_date >= filters["date_from"]
                )
            if filters.get("date_to"):
                query = query.filter(PurchaseRequest.request_date <= filters["date_to"])
            if filters.get("amount_min"):
                query = query.filter(
                    PurchaseRequest.estimated_total >= filters["amount_min"]
                )
            if filters.get("amount_max"):
                query = query.filter(
                    PurchaseRequest.estimated_total <= filters["amount_max"]
                )

        total = query.count()
        requests = (
            query.offset(skip)
            .limit(limit)
            .order_by(PurchaseRequest.request_date.desc())
            .all()
        )

        return requests, total

    def create(
        self, request_in: PurchaseRequestCreate, user_id: str
    ) -> PurchaseRequest:
        # リクエスト番号生成
        request_number = self._generate_request_number()

        # リクエスト作成
        db_request = PurchaseRequest(
            id=str(uuid.uuid4()),
            request_number=request_number,
            requester_id=user_id,
            department_id=request_in.department_id,
            supplier_id=request_in.supplier_id,
            required_date=request_in.required_date,
            priority=request_in.priority,
            estimated_total=request_in.estimated_total or Decimal("0"),
            justification=request_in.justification,
            project_code=request_in.project_code,
            cost_center=request_in.cost_center,
            internal_notes=request_in.internal_notes,
        )

        self.db.add(db_request)
        self.db.flush()

        # リクエストアイテム作成
        total_amount = Decimal("0")
        for item_data in request_in.items:
            estimated_total = item_data.quantity * (
                item_data.estimated_unit_price or Decimal("0")
            )

            request_item = PurchaseRequestItem(
                id=str(uuid.uuid4()),
                purchase_request_id=db_request.id,
                product_id=item_data.product_id,
                product_sku=item_data.product_sku,
                product_name=item_data.product_name,
                product_description=item_data.product_description,
                specification=item_data.specification,
                quantity=item_data.quantity,
                estimated_unit_price=item_data.estimated_unit_price,
                estimated_total=estimated_total,
                required_delivery_date=item_data.required_delivery_date,
                quality_requirements=item_data.quality_requirements,
                preferred_brand=item_data.preferred_brand,
                notes=item_data.notes,
            )
            self.db.add(request_item)
            total_amount += estimated_total

        # 合計更新
        db_request.estimated_total = total_amount

        self.db.commit()
        self.db.refresh(db_request)

        return db_request

    def update(
        self, request_id: str, request_in: PurchaseRequestUpdate
    ) -> Optional[PurchaseRequest]:
        request = self.get_by_id(request_id)
        if not request:
            raise NotFoundError(f"Purchase request {request_id} not found")

        # ステータス遷移チェック
        if request_in.status and not self._is_valid_status_transition(
            request.status, request_in.status
        ):
            raise InvalidStatusError(
                f"Invalid status transition from {request.status} to {request_in.status}"
            )

        update_data = request_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(request, field, value)

        request.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(request)

        return request

    def approve_request(
        self, request_id: str, approver_id: str, approved_budget: Decimal
    ) -> PurchaseRequest:
        """購買リクエスト承認"""
        request = self.get_by_id(request_id)
        if not request:
            raise NotFoundError(f"Purchase request {request_id} not found")

        if request.approval_status != "pending":
            raise InvalidStatusError("Only pending requests can be approved")

        request.approval_status = "approved"
        request.approved_by = approver_id
        request.approved_at = datetime.utcnow()
        request.approved_budget = approved_budget
        request.status = "approved"
        request.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(request)

        return request

    def reject_request(
        self, request_id: str, approver_id: str, rejection_reason: str
    ) -> PurchaseRequest:
        """購買リクエスト却下"""
        request = self.get_by_id(request_id)
        if not request:
            raise NotFoundError(f"Purchase request {request_id} not found")

        if request.approval_status != "pending":
            raise InvalidStatusError("Only pending requests can be rejected")

        request.approval_status = "rejected"
        request.approved_by = approver_id
        request.approved_at = datetime.utcnow()
        request.rejection_reason = rejection_reason
        request.status = "rejected"
        request.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(request)

        return request

    def _generate_request_number(self) -> str:
        """リクエスト番号生成"""
        today = datetime.now()
        prefix = f"PR-{today.year}{today.month:02d}"

        last_request = (
            self.db.query(PurchaseRequest)
            .filter(PurchaseRequest.request_number.like(f"{prefix}%"))
            .order_by(PurchaseRequest.request_number.desc())
            .first()
        )

        if last_request:
            last_number = int(last_request.request_number.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:04d}"

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """ステータス遷移の妥当性チェック"""
        valid_transitions = {
            "draft": ["submitted", "cancelled"],
            "submitted": ["approved", "rejected", "cancelled"],
            "approved": ["cancelled"],
            "rejected": [],
            "cancelled": [],
        }
        return new_status in valid_transitions.get(current_status, [])


class PurchaseOrderCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, order_id: str) -> Optional[PurchaseOrder]:
        return (
            self.db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.order_items),
                joinedload(PurchaseOrder.buyer),
            )
            .filter(PurchaseOrder.id == order_id)
            .first()
        )

    def get_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        return (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number == po_number)
            .first()
        )

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[PurchaseOrder], int]:
        query = self.db.query(PurchaseOrder)

        if filters:
            if filters.get("supplier_id"):
                query = query.filter(
                    PurchaseOrder.supplier_id == filters["supplier_id"]
                )
            if filters.get("buyer_id"):
                query = query.filter(PurchaseOrder.buyer_id == filters["buyer_id"])
            if filters.get("status"):
                query = query.filter(PurchaseOrder.status == filters["status"])
            if filters.get("receipt_status"):
                query = query.filter(
                    PurchaseOrder.receipt_status == filters["receipt_status"]
                )
            if filters.get("payment_status"):
                query = query.filter(
                    PurchaseOrder.payment_status == filters["payment_status"]
                )
            if filters.get("date_from"):
                query = query.filter(PurchaseOrder.order_date >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(PurchaseOrder.order_date <= filters["date_to"])
            if filters.get("amount_min"):
                query = query.filter(
                    PurchaseOrder.total_amount >= filters["amount_min"]
                )
            if filters.get("amount_max"):
                query = query.filter(
                    PurchaseOrder.total_amount <= filters["amount_max"]
                )

        total = query.count()
        orders = (
            query.offset(skip)
            .limit(limit)
            .order_by(PurchaseOrder.order_date.desc())
            .all()
        )

        return orders, total

    def create(self, order_in: PurchaseOrderCreate, user_id: str) -> PurchaseOrder:
        # PO番号生成
        po_number = self._generate_po_number()

        # 注文作成
        db_order = PurchaseOrder(
            id=str(uuid.uuid4()),
            po_number=po_number,
            purchase_request_id=order_in.purchase_request_id,
            supplier_id=order_in.supplier_id,
            buyer_id=user_id,
            required_delivery_date=order_in.required_delivery_date,
            promised_delivery_date=order_in.promised_delivery_date,
            payment_terms=order_in.payment_terms,
            shipping_method=order_in.shipping_method,
            shipping_address_line1=order_in.shipping_address_line1,
            shipping_city=order_in.shipping_city,
            shipping_postal_code=order_in.shipping_postal_code,
            shipping_country=order_in.shipping_country,
            quality_requirements=order_in.quality_requirements,
            contract_terms=order_in.contract_terms,
            warranty_terms=order_in.warranty_terms,
            internal_notes=order_in.internal_notes,
            supplier_notes=order_in.supplier_notes,
            project_code=order_in.project_code,
            cost_center=order_in.cost_center,
        )

        self.db.add(db_order)
        self.db.flush()

        # 注文アイテム作成
        total_amount = Decimal("0")
        for item_data in order_in.items:
            line_total = item_data.quantity * item_data.unit_price
            if item_data.line_discount_percentage > 0:
                discount_amount = line_total * (
                    item_data.line_discount_percentage / 100
                )
                line_total -= discount_amount

            order_item = PurchaseOrderItem(
                id=str(uuid.uuid4()),
                purchase_order_id=db_order.id,
                product_id=item_data.product_id,
                product_sku=item_data.product_sku,
                product_name=item_data.product_name,
                product_description=item_data.product_description,
                specification=item_data.specification,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                line_discount_percentage=item_data.line_discount_percentage,
                line_discount_amount=line_total
                * (item_data.line_discount_percentage / 100)
                if item_data.line_discount_percentage > 0
                else 0,
                line_total=line_total,
                remaining_quantity=item_data.quantity,
                notes=item_data.notes,
            )
            self.db.add(order_item)
            total_amount += line_total

        # 注文合計更新
        db_order.subtotal = total_amount
        db_order.total_amount = total_amount

        self.db.commit()
        self.db.refresh(db_order)

        # サプライヤー統計更新
        supplier_crud = SupplierCRUD(self.db)
        supplier_crud.update_purchase_stats(order_in.supplier_id, total_amount)

        return db_order

    def update(
        self, order_id: str, order_in: PurchaseOrderUpdate
    ) -> Optional[PurchaseOrder]:
        order = self.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Purchase order {order_id} not found")

        # ステータス遷移チェック
        if order_in.status and not self._is_valid_status_transition(
            order.status, order_in.status
        ):
            raise InvalidStatusError(
                f"Invalid status transition from {order.status} to {order_in.status}"
            )

        update_data = order_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)

        return order

    def acknowledge_order(self, order_id: str) -> PurchaseOrder:
        """注文確認（サプライヤーからの受注確認）"""
        order = self.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Purchase order {order_id} not found")

        if order.status != "sent":
            raise InvalidStatusError("Only sent orders can be acknowledged")

        order.status = "acknowledged"
        order.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)

        return order

    def _generate_po_number(self) -> str:
        """PO番号生成"""
        today = datetime.now()
        prefix = f"PO-{today.year}{today.month:02d}"

        last_order = (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number.like(f"{prefix}%"))
            .order_by(PurchaseOrder.po_number.desc())
            .first()
        )

        if last_order:
            last_number = int(last_order.po_number.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:04d}"

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """ステータス遷移の妥当性チェック"""
        valid_transitions = {
            "draft": ["sent", "cancelled"],
            "sent": ["acknowledged", "cancelled"],
            "acknowledged": ["shipped", "cancelled"],
            "shipped": ["received"],
            "received": [],
            "cancelled": [],
        }
        return new_status in valid_transitions.get(current_status, [])

    def get_purchase_analytics(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """購買分析データ取得"""
        query = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.order_date >= date_from,
            PurchaseOrder.order_date <= date_to,
            PurchaseOrder.status != "cancelled",
        )

        orders = query.all()

        total_spend = sum(order.total_amount for order in orders)
        orders_count = len(orders)
        suppliers_count = len(set(order.supplier_id for order in orders))
        avg_order_value = total_spend / orders_count if orders_count > 0 else 0

        # 日別購買
        daily_breakdown = {}
        for order in orders:
            date_key = order.order_date.date().isoformat()
            if date_key not in daily_breakdown:
                daily_breakdown[date_key] = {"spend": Decimal("0"), "orders": 0}
            daily_breakdown[date_key]["spend"] += order.total_amount
            daily_breakdown[date_key]["orders"] += 1

        # サプライヤー別パフォーマンス
        supplier_performance = {}
        for order in orders:
            if order.supplier_id not in supplier_performance:
                supplier_performance[order.supplier_id] = {
                    "orders": 0,
                    "total_spend": Decimal("0"),
                    "on_time": 0,
                    "late": 0,
                    "quality_issues": 0,
                }
            perf = supplier_performance[order.supplier_id]
            perf["orders"] += 1
            perf["total_spend"] += order.total_amount

            # 配送パフォーマンス計算
            if order.actual_delivery_date and order.promised_delivery_date:
                if order.actual_delivery_date <= order.promised_delivery_date:
                    perf["on_time"] += 1
                else:
                    perf["late"] += 1

        return {
            "period_start": date_from,
            "period_end": date_to,
            "total_spend": total_spend,
            "orders_count": orders_count,
            "suppliers_count": suppliers_count,
            "avg_order_value": avg_order_value,
            "cost_savings": Decimal("0"),  # 実装時に計算
            "on_time_delivery_rate": Decimal("0"),  # 実装時に計算
            "quality_rejection_rate": Decimal("0"),  # 実装時に計算
            "daily_breakdown": [
                {"date": date, "spend": data["spend"], "orders": data["orders"]}
                for date, data in sorted(daily_breakdown.items())
            ],
            "supplier_performance": [
                {"supplier_id": sid, **perf}
                for sid, perf in supplier_performance.items()
            ],
        }


class PurchaseReceiptCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, receipt_id: str) -> Optional[PurchaseReceipt]:
        return (
            self.db.query(PurchaseReceipt)
            .options(joinedload(PurchaseReceipt.receipt_items))
            .filter(PurchaseReceipt.id == receipt_id)
            .first()
        )

    def create(
        self, receipt_in: PurchaseReceiptCreate, user_id: str
    ) -> PurchaseReceipt:
        """購買受領記録作成"""
        receipt_number = self._generate_receipt_number()

        db_receipt = PurchaseReceipt(
            id=str(uuid.uuid4()),
            receipt_number=receipt_number,
            purchase_order_id=receipt_in.purchase_order_id,
            receiver_id=user_id,
            receipt_date=receipt_in.receipt_date,
            delivery_note_number=receipt_in.delivery_note_number,
            carrier=receipt_in.carrier,
            inspection_status=receipt_in.inspection_status,
            inspection_notes=receipt_in.inspection_notes,
            notes=receipt_in.notes,
        )

        self.db.add(db_receipt)
        self.db.flush()

        # 受領アイテム作成
        for item_data in receipt_in.items:
            receipt_item = PurchaseReceiptItem(
                id=str(uuid.uuid4()),
                purchase_receipt_id=db_receipt.id,
                purchase_order_item_id=item_data.purchase_order_item_id,
                product_id=item_data.product_id,
                received_quantity=item_data.received_quantity,
                accepted_quantity=item_data.accepted_quantity
                or item_data.received_quantity,
                rejected_quantity=item_data.rejected_quantity or Decimal("0"),
                damaged_quantity=item_data.damaged_quantity or Decimal("0"),
                quality_status=item_data.quality_status,
                defect_reason=item_data.defect_reason,
                warehouse_location=item_data.warehouse_location,
                lot_number=item_data.lot_number,
                expiry_date=item_data.expiry_date,
                serial_numbers=item_data.serial_numbers,
                notes=item_data.notes,
            )
            self.db.add(receipt_item)

            # 購買注文アイテムの受領数量更新
            po_item = (
                self.db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.id == item_data.purchase_order_item_id)
                .first()
            )
            if po_item:
                po_item.received_quantity += item_data.received_quantity
                po_item.rejected_quantity += item_data.rejected_quantity or Decimal("0")
                po_item.remaining_quantity = (
                    po_item.quantity - po_item.received_quantity
                )

        self.db.commit()
        self.db.refresh(db_receipt)

        return db_receipt

    def _generate_receipt_number(self) -> str:
        """受領番号生成"""
        today = datetime.now()
        prefix = f"RC-{today.year}{today.month:02d}"

        last_receipt = (
            self.db.query(PurchaseReceipt)
            .filter(PurchaseReceipt.receipt_number.like(f"{prefix}%"))
            .order_by(PurchaseReceipt.receipt_number.desc())
            .first()
        )

        if last_receipt:
            last_number = int(last_receipt.receipt_number.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:04d}"


class SupplierProductCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, supplier_product_id: str) -> Optional[SupplierProduct]:
        return (
            self.db.query(SupplierProduct)
            .filter(SupplierProduct.id == supplier_product_id)
            .first()
        )

    def get_by_supplier_and_product(
        self, supplier_id: str, product_id: str
    ) -> Optional[SupplierProduct]:
        return (
            self.db.query(SupplierProduct)
            .filter(
                SupplierProduct.supplier_id == supplier_id,
                SupplierProduct.product_id == product_id,
            )
            .first()
        )

    def create(self, supplier_product_in: SupplierProductCreate) -> SupplierProduct:
        """サプライヤー商品関連作成"""
        existing = self.get_by_supplier_and_product(
            supplier_product_in.supplier_id, supplier_product_in.product_id
        )
        if existing:
            raise DuplicateError("Supplier product relationship already exists")

        db_supplier_product = SupplierProduct(
            id=str(uuid.uuid4()),
            supplier_id=supplier_product_in.supplier_id,
            product_id=supplier_product_in.product_id,
            supplier_product_code=supplier_product_in.supplier_product_code,
            supplier_product_name=supplier_product_in.supplier_product_name,
            unit_price=supplier_product_in.unit_price,
            currency=supplier_product_in.currency,
            minimum_order_quantity=supplier_product_in.minimum_order_quantity,
            lead_time_days=supplier_product_in.lead_time_days,
            contract_start_date=supplier_product_in.contract_start_date,
            contract_end_date=supplier_product_in.contract_end_date,
            preferred_supplier=supplier_product_in.preferred_supplier,
            notes=supplier_product_in.notes,
        )

        self.db.add(db_supplier_product)
        self.db.commit()
        self.db.refresh(db_supplier_product)

        return db_supplier_product
