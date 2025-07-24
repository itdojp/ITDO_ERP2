from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from app.models.sales_extended import (
    Customer, SalesOrder, SalesOrderItem, Quote, QuoteItem,
    Invoice, Payment, Shipment, ShipmentItem
)
from app.schemas.sales_complete_v30 import (
    CustomerCreate, CustomerUpdate, SalesOrderCreate, SalesOrderUpdate,
    QuoteCreate, QuoteUpdate, InvoiceCreate, InvoiceUpdate,
    PaymentCreate, ShipmentCreate, ShipmentUpdate
)

class NotFoundError(Exception):
    pass

class DuplicateError(Exception):
    pass

class InvalidStatusError(Exception):
    pass

class CustomerCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_code(self, code: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.customer_code == code).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Customer], int]:
        query = self.db.query(Customer)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Customer.is_active == filters["is_active"])
            if filters.get("customer_type"):
                query = query.filter(Customer.customer_type == filters["customer_type"])
            if filters.get("customer_group"):
                query = query.filter(Customer.customer_group == filters["customer_group"])
            if filters.get("is_vip") is not None:
                query = query.filter(Customer.is_vip == filters["is_vip"])
            if filters.get("sales_rep_id"):
                query = query.filter(Customer.sales_rep_id == filters["sales_rep_id"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Customer.name.ilike(search),
                        Customer.company_name.ilike(search),
                        Customer.customer_code.ilike(search),
                        Customer.email.ilike(search)
                    )
                )

        total = query.count()
        customers = query.offset(skip).limit(limit).order_by(Customer.name).all()

        return customers, total

    def create(self, customer_in: CustomerCreate) -> Customer:
        if self.get_by_code(customer_in.customer_code):
            raise DuplicateError("Customer code already exists")

        db_customer = Customer(
            id=str(uuid.uuid4()),
            customer_code=customer_in.customer_code,
            name=customer_in.name,
            company_name=customer_in.company_name,
            email=customer_in.email,
            phone=customer_in.phone,
            mobile=customer_in.mobile,
            website=customer_in.website,
            billing_address_line1=customer_in.billing_address_line1,
            billing_city=customer_in.billing_city,
            billing_postal_code=customer_in.billing_postal_code,
            billing_country=customer_in.billing_country,
            shipping_address_line1=customer_in.shipping_address_line1,
            shipping_city=customer_in.shipping_city,
            shipping_postal_code=customer_in.shipping_postal_code,
            shipping_country=customer_in.shipping_country,
            customer_type=customer_in.customer_type,
            customer_group=customer_in.customer_group,
            priority_level=customer_in.priority_level,
            industry=customer_in.industry,
            credit_limit=customer_in.credit_limit,
            payment_terms=customer_in.payment_terms,
            tax_id=customer_in.tax_id,
            tax_exempt=customer_in.tax_exempt,
            sales_rep_id=customer_in.sales_rep_id,
            acquisition_source=customer_in.acquisition_source,
            acquisition_date=datetime.utcnow() if customer_in.acquisition_source else None,
            notes=customer_in.notes,
            preferences=customer_in.preferences
        )

        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)

        return db_customer

    def update(self, customer_id: str, customer_in: CustomerUpdate) -> Optional[Customer]:
        customer = self.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        update_data = customer_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def update_sales_stats(self, customer_id: str, order_amount: Decimal):
        """顧客の売上統計を更新"""
        customer = self.get_by_id(customer_id)
        if customer:
            customer.total_orders += 1
            customer.total_sales += order_amount
            customer.avg_order_value = customer.total_sales / customer.total_orders
            customer.last_order_date = datetime.utcnow()
            self.db.commit()


class SalesOrderCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: str) -> Optional[SalesOrder]:
        return (
            self.db.query(SalesOrder)
            .options(
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.order_items),
                joinedload(SalesOrder.sales_rep)
            )
            .filter(SalesOrder.id == order_id)
            .first()
        )

    def get_by_number(self, order_number: str) -> Optional[SalesOrder]:
        return self.db.query(SalesOrder).filter(SalesOrder.order_number == order_number).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[SalesOrder], int]:
        query = self.db.query(SalesOrder)

        if filters:
            if filters.get("customer_id"):
                query = query.filter(SalesOrder.customer_id == filters["customer_id"])
            if filters.get("status"):
                query = query.filter(SalesOrder.status == filters["status"])
            if filters.get("sales_rep_id"):
                query = query.filter(SalesOrder.sales_rep_id == filters["sales_rep_id"])
            if filters.get("sales_channel"):
                query = query.filter(SalesOrder.sales_channel == filters["sales_channel"])
            if filters.get("date_from"):
                query = query.filter(SalesOrder.order_date >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(SalesOrder.order_date <= filters["date_to"])
            if filters.get("amount_min"):
                query = query.filter(SalesOrder.total_amount >= filters["amount_min"])
            if filters.get("amount_max"):
                query = query.filter(SalesOrder.total_amount <= filters["amount_max"])

        total = query.count()
        orders = query.offset(skip).limit(limit).order_by(SalesOrder.order_date.desc()).all()

        return orders, total

    def create(self, order_in: SalesOrderCreate, user_id: str) -> SalesOrder:
        # 注文番号生成
        order_number = self._generate_order_number()

        # 注文作成
        db_order = SalesOrder(
            id=str(uuid.uuid4()),
            order_number=order_number,
            quote_id=order_in.quote_id,
            customer_id=order_in.customer_id,
            requested_delivery_date=order_in.requested_delivery_date,
            priority=order_in.priority,
            payment_terms=order_in.payment_terms,
            shipping_method=order_in.shipping_method,
            shipping_address_line1=order_in.shipping_address_line1,
            shipping_city=order_in.shipping_city,
            shipping_postal_code=order_in.shipping_postal_code,
            shipping_country=order_in.shipping_country,
            sales_rep_id=user_id,
            sales_channel=order_in.sales_channel,
            referral_source=order_in.referral_source,
            internal_notes=order_in.internal_notes,
            customer_notes=order_in.customer_notes,
            custom_fields=order_in.custom_fields
        )

        self.db.add(db_order)
        self.db.flush()  # IDを取得するため

        # 注文アイテム作成
        total_amount = Decimal('0')
        for item_data in order_in.items:
            line_total = item_data.quantity * item_data.unit_price
            if item_data.line_discount_percentage > 0:
                discount_amount = line_total * (item_data.line_discount_percentage / 100)
                line_total -= discount_amount

            order_item = SalesOrderItem(
                id=str(uuid.uuid4()),
                sales_order_id=db_order.id,
                product_id=item_data.product_id,
                product_sku=item_data.product_sku,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                line_discount_percentage=item_data.line_discount_percentage,
                line_discount_amount=line_total * (item_data.line_discount_percentage / 100) if item_data.line_discount_percentage > 0 else 0,
                line_total=line_total,
                custom_attributes=item_data.custom_attributes,
                notes=item_data.notes
            )
            self.db.add(order_item)
            total_amount += line_total

        # 注文合計更新
        db_order.subtotal = total_amount
        db_order.total_amount = total_amount  # 税金・送料は別途計算

        self.db.commit()
        self.db.refresh(db_order)

        # 顧客統計更新
        customer_crud = CustomerCRUD(self.db)
        customer_crud.update_sales_stats(order_in.customer_id, total_amount)

        return db_order

    def update(self, order_id: str, order_in: SalesOrderUpdate) -> Optional[SalesOrder]:
        order = self.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Sales order {order_id} not found")

        # ステータス遷移チェック
        if order_in.status and not self._is_valid_status_transition(order.status, order_in.status):
            raise InvalidStatusError(f"Invalid status transition from {order.status} to {order_in.status}")

        update_data = order_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)

        return order

    def confirm_order(self, order_id: str) -> SalesOrder:
        """注文確定"""
        order = self.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Sales order {order_id} not found")
        
        if order.status != "draft":
            raise InvalidStatusError("Only draft orders can be confirmed")

        order.status = "confirmed"
        order.updated_at = datetime.utcnow()

        # 在庫予約処理（実装時）
        # self._reserve_inventory(order)

        self.db.commit()
        self.db.refresh(order)

        return order

    def _generate_order_number(self) -> str:
        """注文番号生成"""
        today = datetime.now()
        prefix = f"SO-{today.year}{today.month:02d}"
        
        # 同日の最後の番号を取得
        last_order = (
            self.db.query(SalesOrder)
            .filter(SalesOrder.order_number.like(f"{prefix}%"))
            .order_by(SalesOrder.order_number.desc())
            .first()
        )
        
        if last_order:
            last_number = int(last_order.order_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """ステータス遷移の妥当性チェック"""
        valid_transitions = {
            "draft": ["confirmed", "cancelled"],
            "confirmed": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered"],
            "delivered": [],
            "cancelled": []
        }
        return new_status in valid_transitions.get(current_status, [])

    def get_sales_analytics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """売上分析データ取得"""
        query = self.db.query(SalesOrder).filter(
            SalesOrder.order_date >= date_from,
            SalesOrder.order_date <= date_to,
            SalesOrder.status != "cancelled"
        )

        orders = query.all()
        
        total_revenue = sum(order.total_amount for order in orders)
        orders_count = len(orders)
        customers_count = len(set(order.customer_id for order in orders))
        avg_order_value = total_revenue / orders_count if orders_count > 0 else 0

        # 日別売上
        daily_breakdown = {}
        for order in orders:
            date_key = order.order_date.date().isoformat()
            if date_key not in daily_breakdown:
                daily_breakdown[date_key] = {"revenue": Decimal('0'), "orders": 0}
            daily_breakdown[date_key]["revenue"] += order.total_amount
            daily_breakdown[date_key]["orders"] += 1

        return {
            "period_start": date_from,
            "period_end": date_to,
            "revenue": total_revenue,
            "orders_count": orders_count,
            "customers_count": customers_count,
            "avg_order_value": avg_order_value,
            "conversion_rate": Decimal('0'),  # 実装時に計算
            "growth_rate": Decimal('0'),  # 実装時に計算
            "daily_breakdown": [
                {"date": date, "revenue": data["revenue"], "orders": data["orders"]}
                for date, data in sorted(daily_breakdown.items())
            ]
        }


class QuoteCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, quote_id: str) -> Optional[Quote]:
        return (
            self.db.query(Quote)
            .options(joinedload(Quote.quote_items))
            .filter(Quote.id == quote_id)
            .first()
        )

    def create(self, quote_in: QuoteCreate, user_id: str) -> Quote:
        # 見積番号生成
        quote_number = self._generate_quote_number()

        db_quote = Quote(
            id=str(uuid.uuid4()),
            quote_number=quote_number,
            customer_id=quote_in.customer_id,
            valid_until=quote_in.valid_until,
            win_probability=quote_in.win_probability,
            expected_close_date=quote_in.expected_close_date,
            sales_rep_id=user_id,
            description=quote_in.description,
            terms_conditions=quote_in.terms_conditions,
            internal_notes=quote_in.internal_notes
        )

        self.db.add(db_quote)
        self.db.flush()

        # 見積アイテム作成
        total_amount = Decimal('0')
        for item_data in quote_in.items:
            line_total = item_data.quantity * item_data.unit_price - item_data.line_discount_amount

            quote_item = QuoteItem(
                id=str(uuid.uuid4()),
                quote_id=db_quote.id,
                product_id=item_data.product_id,
                product_sku=item_data.product_sku,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                line_discount_amount=item_data.line_discount_amount,
                line_total=line_total,
                notes=item_data.notes
            )
            self.db.add(quote_item)
            total_amount += line_total

        db_quote.subtotal = total_amount
        db_quote.total_amount = total_amount

        self.db.commit()
        self.db.refresh(db_quote)

        return db_quote

    def _generate_quote_number(self) -> str:
        """見積番号生成"""
        today = datetime.now()
        prefix = f"QT-{today.year}{today.month:02d}"
        
        last_quote = (
            self.db.query(Quote)
            .filter(Quote.quote_number.like(f"{prefix}%"))
            .order_by(Quote.quote_number.desc())
            .first()
        )
        
        if last_quote:
            last_number = int(last_quote.quote_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"


class InvoiceCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def create_from_order(self, order_id: str) -> Invoice:
        """注文から請求書作成"""
        order = self.db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise NotFoundError(f"Sales order {order_id} not found")

        invoice_number = self._generate_invoice_number()

        db_invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            sales_order_id=order_id,
            customer_id=order.customer_id,
            due_date=datetime.utcnow() + timedelta(days=30),  # デフォルト30日後
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            balance_due=order.total_amount,
            payment_terms=order.payment_terms
        )

        self.db.add(db_invoice)
        self.db.commit()
        self.db.refresh(db_invoice)

        return db_invoice

    def _generate_invoice_number(self) -> str:
        """請求書番号生成"""
        today = datetime.now()
        prefix = f"INV-{today.year}{today.month:02d}"
        
        last_invoice = (
            self.db.query(Invoice)
            .filter(Invoice.invoice_number.like(f"{prefix}%"))
            .order_by(Invoice.invoice_number.desc())
            .first()
        )
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"


class PaymentCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment_in: PaymentCreate) -> Payment:
        """支払記録作成"""
        invoice = self.db.query(Invoice).filter(Invoice.id == payment_in.invoice_id).first()
        if not invoice:
            raise NotFoundError(f"Invoice {payment_in.invoice_id} not found")

        db_payment = Payment(
            id=str(uuid.uuid4()),
            invoice_id=payment_in.invoice_id,
            customer_id=invoice.customer_id,
            payment_date=payment_in.payment_date,
            amount=payment_in.amount,
            payment_method=payment_in.payment_method,
            reference_number=payment_in.reference_number,
            transaction_id=payment_in.transaction_id,
            notes=payment_in.notes
        )

        # 請求書の支払状況更新
        invoice.paid_amount += payment_in.amount
        invoice.balance_due = invoice.total_amount - invoice.paid_amount
        
        if invoice.balance_due <= 0:
            invoice.status = "paid"
        else:
            invoice.status = "partial"

        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)

        return db_payment


class ShipmentCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, shipment_in: ShipmentCreate) -> Shipment:
        """出荷記録作成"""
        shipment_number = self._generate_shipment_number()

        db_shipment = Shipment(
            id=str(uuid.uuid4()),
            shipment_number=shipment_number,
            sales_order_id=shipment_in.sales_order_id,
            carrier=shipment_in.carrier,
            shipping_method=shipment_in.shipping_method,
            estimated_delivery_date=shipment_in.estimated_delivery_date,
            delivery_address_line1=shipment_in.delivery_address_line1,
            delivery_city=shipment_in.delivery_city,
            delivery_postal_code=shipment_in.delivery_postal_code,
            delivery_country=shipment_in.delivery_country,
            notes=shipment_in.notes
        )

        self.db.add(db_shipment)
        self.db.flush()

        # 出荷アイテム作成
        for item_data in shipment_in.items:
            shipment_item = ShipmentItem(
                id=str(uuid.uuid4()),
                shipment_id=db_shipment.id,
                sales_order_item_id=item_data.sales_order_item_id,
                product_id=item_data.product_id,
                quantity_shipped=item_data.quantity_shipped,
                serial_numbers=item_data.serial_numbers
            )
            self.db.add(shipment_item)

        self.db.commit()
        self.db.refresh(db_shipment)

        return db_shipment

    def _generate_shipment_number(self) -> str:
        """出荷番号生成"""
        today = datetime.now()
        prefix = f"SH-{today.year}{today.month:02d}"
        
        last_shipment = (
            self.db.query(Shipment)
            .filter(Shipment.shipment_number.like(f"{prefix}%"))
            .order_by(Shipment.shipment_number.desc())
            .first()
        )
        
        if last_shipment:
            last_number = int(last_shipment.shipment_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"