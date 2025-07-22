from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.crud.supplier_relationship_v30 import (
    DuplicateError,
    NotFoundError,
    SupplierContractCRUD,
    SupplierNegotiationCRUD,
    SupplierPerformanceReviewCRUD,
    SupplierRelationshipCRUD,
)
from app.schemas.supplier_relationship_v30 import (
    SupplierContractCreate,
    SupplierContractListResponse,
    SupplierContractResponse,
    SupplierContractUpdate,
    SupplierNegotiationCreate,
    SupplierNegotiationListResponse,
    SupplierNegotiationResponse,
    SupplierNegotiationUpdate,
    SupplierPerformanceAnalyticsResponse,
    SupplierPerformanceReviewCreate,
    SupplierPerformanceReviewListResponse,
    SupplierPerformanceReviewResponse,
    SupplierPerformanceReviewUpdate,
    SupplierRelationshipCreate,
    SupplierRelationshipListResponse,
    SupplierRelationshipResponse,
    SupplierRelationshipStatsResponse,
    SupplierRelationshipUpdate,
)

router = APIRouter(prefix="/supplier-relationships", tags=["supplier-relationships"])


@router.post(
    "/relationships",
    response_model=SupplierRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_relationship(
    relationship: SupplierRelationshipCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー関係作成"""
    try:
        relationship_crud = SupplierRelationshipCRUD(db)
        return relationship_crud.create(relationship, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/relationships/{relationship_id}", response_model=SupplierRelationshipResponse
)
def get_supplier_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー関係詳細取得"""
    relationship_crud = SupplierRelationshipCRUD(db)
    relationship = relationship_crud.get_by_id(relationship_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier relationship not found",
        )
    return relationship


@router.get("/relationships", response_model=SupplierRelationshipListResponse)
def list_supplier_relationships(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    relationship_manager_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
    partnership_level: Optional[str] = None,
    contract_type: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    strategic_importance: Optional[str] = None,
    overall_score_min: Optional[Decimal] = None,
    annual_spend_min: Optional[Decimal] = None,
    contract_expiring_days: Optional[int] = None,
    review_overdue: Optional[bool] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー関係一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    # Build filters dictionary
    filter_params = {
        "supplier_id": supplier_id,
        "relationship_manager_id": relationship_manager_id,
        "relationship_type": relationship_type,
        "partnership_level": partnership_level,
        "contract_type": contract_type,
        "status": status,
        "risk_level": risk_level,
        "strategic_importance": strategic_importance,
        "overall_score_min": overall_score_min,
        "annual_spend_min": annual_spend_min,
        "contract_expiring_days": contract_expiring_days,
        "review_overdue": review_overdue,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    relationship_crud = SupplierRelationshipCRUD(db)
    relationships, total = relationship_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return SupplierRelationshipListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=relationships
    )


@router.put(
    "/relationships/{relationship_id}", response_model=SupplierRelationshipResponse
)
def update_supplier_relationship(
    relationship_id: str,
    relationship_update: SupplierRelationshipUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー関係更新"""
    try:
        relationship_crud = SupplierRelationshipCRUD(db)
        return relationship_crud.update(relationship_id, relationship_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/relationships/{relationship_id}/approve",
    response_model=SupplierRelationshipResponse,
)
def approve_supplier_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー関係承認"""
    try:
        relationship_crud = SupplierRelationshipCRUD(db)
        return relationship_crud.approve(relationship_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/relationships/{relationship_id}/schedule-review")
def schedule_supplier_review(
    relationship_id: str,
    review_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤーレビュー日程設定"""
    relationship_crud = SupplierRelationshipCRUD(db)
    relationship_crud.schedule_review(relationship_id, review_date)
    return {"message": "Review scheduled successfully"}


@router.post(
    "/performance-reviews",
    response_model=SupplierPerformanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_review(
    review: SupplierPerformanceReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """パフォーマンスレビュー作成"""
    review_crud = SupplierPerformanceReviewCRUD(db)
    return review_crud.create(review, current_user["sub"])


@router.get(
    "/performance-reviews/{review_id}", response_model=SupplierPerformanceReviewResponse
)
def get_performance_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """パフォーマンスレビュー詳細取得"""
    review_crud = SupplierPerformanceReviewCRUD(db)
    review = review_crud.get_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Performance review not found"
        )
    return review


@router.get(
    "/relationships/{relationship_id}/performance-reviews",
    response_model=SupplierPerformanceReviewListResponse,
)
def list_relationship_performance_reviews(
    relationship_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """関係別パフォーマンスレビュー一覧取得"""
    skip = (page - 1) * per_page
    review_crud = SupplierPerformanceReviewCRUD(db)
    reviews, total = review_crud.get_multi_by_relationship(
        relationship_id, skip=skip, limit=per_page
    )

    pages = (total + per_page - 1) // per_page

    return SupplierPerformanceReviewListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=reviews
    )


@router.put(
    "/performance-reviews/{review_id}", response_model=SupplierPerformanceReviewResponse
)
def update_performance_review(
    review_id: str,
    review_update: SupplierPerformanceReviewUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """パフォーマンスレビュー更新"""
    try:
        review_crud = SupplierPerformanceReviewCRUD(db)
        return review_crud.update(review_id, review_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/performance-reviews/{review_id}/approve",
    response_model=SupplierPerformanceReviewResponse,
)
def approve_performance_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """パフォーマンスレビュー承認"""
    try:
        review_crud = SupplierPerformanceReviewCRUD(db)
        return review_crud.approve(review_id, current_user["sub"])
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/negotiations",
    response_model=SupplierNegotiationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_negotiation(
    negotiation: SupplierNegotiationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー交渉作成"""
    negotiation_crud = SupplierNegotiationCRUD(db)
    return negotiation_crud.create(negotiation, current_user["sub"])


@router.get(
    "/negotiations/{negotiation_id}", response_model=SupplierNegotiationResponse
)
def get_supplier_negotiation(
    negotiation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー交渉詳細取得"""
    negotiation_crud = SupplierNegotiationCRUD(db)
    negotiation = negotiation_crud.get_by_id(negotiation_id)
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Negotiation not found"
        )
    return negotiation


@router.get("/negotiations", response_model=SupplierNegotiationListResponse)
def list_supplier_negotiations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    supplier_relationship_id: Optional[str] = None,
    lead_negotiator_id: Optional[str] = None,
    negotiation_type: Optional[str] = None,
    status: Optional[str] = None,
    current_phase: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー交渉一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    filter_params = {
        "supplier_relationship_id": supplier_relationship_id,
        "lead_negotiator_id": lead_negotiator_id,
        "negotiation_type": negotiation_type,
        "status": status,
        "current_phase": current_phase,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    negotiation_crud = SupplierNegotiationCRUD(db)
    negotiations, total = negotiation_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return SupplierNegotiationListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=negotiations
    )


@router.put(
    "/negotiations/{negotiation_id}", response_model=SupplierNegotiationResponse
)
def update_supplier_negotiation(
    negotiation_id: str,
    negotiation_update: SupplierNegotiationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー交渉更新"""
    try:
        negotiation_crud = SupplierNegotiationCRUD(db)
        return negotiation_crud.update(negotiation_id, negotiation_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/negotiations/{negotiation_id}/complete",
    response_model=SupplierNegotiationResponse,
)
def complete_supplier_negotiation(
    negotiation_id: str,
    final_agreement_document: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー交渉完了"""
    try:
        negotiation_crud = SupplierNegotiationCRUD(db)
        return negotiation_crud.complete(negotiation_id, final_agreement_document)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/contracts",
    response_model=SupplierContractResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_contract(
    contract: SupplierContractCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー契約作成"""
    contract_crud = SupplierContractCRUD(db)
    return contract_crud.create(contract, current_user["sub"])


@router.get("/contracts/{contract_id}", response_model=SupplierContractResponse)
def get_supplier_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー契約詳細取得"""
    contract_crud = SupplierContractCRUD(db)
    contract = contract_crud.get_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )
    return contract


@router.get("/contracts", response_model=SupplierContractListResponse)
def list_supplier_contracts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    contract_manager_id: Optional[str] = None,
    contract_type: Optional[str] = None,
    status: Optional[str] = None,
    expiring_days: Optional[int] = None,
    signed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー契約一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    filter_params = {
        "supplier_id": supplier_id,
        "contract_manager_id": contract_manager_id,
        "contract_type": contract_type,
        "status": status,
        "expiring_days": expiring_days,
        "signed": signed,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    contract_crud = SupplierContractCRUD(db)
    contracts, total = contract_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return SupplierContractListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=contracts
    )


@router.put("/contracts/{contract_id}", response_model=SupplierContractResponse)
def update_supplier_contract(
    contract_id: str,
    contract_update: SupplierContractUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー契約更新"""
    try:
        contract_crud = SupplierContractCRUD(db)
        return contract_crud.update(contract_id, contract_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stats", response_model=SupplierRelationshipStatsResponse)
def get_supplier_relationship_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """サプライヤー関係統計取得"""
    contract_crud = SupplierContractCRUD(db)
    return contract_crud.get_relationship_analytics()


@router.get(
    "/performance-analytics", response_model=SupplierPerformanceAnalyticsResponse
)
def get_supplier_performance_analytics(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤーパフォーマンス分析データ取得"""

    from app.models.supplier_relationship_extended import (
        SupplierPerformanceReview,
    )

    # Period reviews
    review_query = db.query(SupplierPerformanceReview).filter(
        SupplierPerformanceReview.created_at >= date_from,
        SupplierPerformanceReview.created_at <= date_to,
        SupplierPerformanceReview.review_status == "completed",
    )

    reviews = review_query.all()
    total_suppliers_reviewed = len(set(r.supplier_relationship_id for r in reviews))

    # Average ratings
    quality_ratings = [r.quality_rating for r in reviews if r.quality_rating]
    delivery_ratings = [r.delivery_rating for r in reviews if r.delivery_rating]
    service_ratings = [r.service_rating for r in reviews if r.service_rating]
    overall_ratings = [r.overall_rating for r in reviews if r.overall_rating]

    avg_quality_rating = (
        sum(quality_ratings) / len(quality_ratings) if quality_ratings else Decimal("0")
    )
    avg_delivery_rating = (
        sum(delivery_ratings) / len(delivery_ratings)
        if delivery_ratings
        else Decimal("0")
    )
    avg_service_rating = (
        sum(service_ratings) / len(service_ratings) if service_ratings else Decimal("0")
    )
    avg_overall_rating = (
        sum(overall_ratings) / len(overall_ratings) if overall_ratings else Decimal("0")
    )

    # Top performing suppliers
    supplier_ratings = {}
    for review in reviews:
        if (
            review.overall_rating
            and review.supplier_relationship_id not in supplier_ratings
        ):
            supplier_ratings[review.supplier_relationship_id] = []
        if review.overall_rating:
            supplier_ratings[review.supplier_relationship_id].append(
                review.overall_rating
            )

    # Calculate average rating per supplier
    supplier_avg_ratings = {
        supplier_id: sum(ratings) / len(ratings)
        for supplier_id, ratings in supplier_ratings.items()
    }

    top_performers = sorted(
        supplier_avg_ratings.items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_performing_suppliers = [
        {
            "supplier_relationship_id": supplier_id,
            "avg_rating": rating,
            "review_count": len(supplier_ratings[supplier_id]),
        }
        for supplier_id, rating in top_performers
    ]

    # Improvement needed suppliers (rating < 3.0)
    improvement_needed = [
        {
            "supplier_relationship_id": supplier_id,
            "avg_rating": rating,
            "review_count": len(supplier_ratings[supplier_id]),
        }
        for supplier_id, rating in supplier_avg_ratings.items()
        if rating < Decimal("3.0")
    ]

    # Performance trends (monthly)
    performance_trends = []
    current_date = date_from.replace(day=1)  # Start of month
    while current_date <= date_to.date():
        month_end = (
            (
                current_date.replace(month=current_date.month % 12 + 1, day=1)
                - timedelta(days=1)
            )
            if current_date.month < 12
            else current_date.replace(year=current_date.year + 1, month=1, day=1)
            - timedelta(days=1)
        )

        month_reviews = [
            r for r in reviews if current_date <= r.created_at.date() <= month_end
        ]

        if month_reviews:
            month_avg = sum(
                r.overall_rating for r in month_reviews if r.overall_rating
            ) / len([r for r in month_reviews if r.overall_rating])
        else:
            month_avg = Decimal("0")

        performance_trends.append(
            {
                "period": current_date.isoformat(),
                "avg_rating": month_avg,
                "reviews_count": len(month_reviews),
            }
        )

        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    # Category performance (dummy data for this example)
    category_performance = {
        "Manufacturing": Decimal("4.2"),
        "Services": Decimal("3.8"),
        "Technology": Decimal("4.5"),
        "Logistics": Decimal("3.9"),
        "Raw Materials": Decimal("4.0"),
    }

    return SupplierPerformanceAnalyticsResponse(
        period_start=date_from,
        period_end=date_to,
        total_suppliers_reviewed=total_suppliers_reviewed,
        avg_overall_rating=avg_overall_rating,
        avg_quality_rating=avg_quality_rating,
        avg_delivery_rating=avg_delivery_rating,
        avg_service_rating=avg_service_rating,
        top_performing_suppliers=top_performing_suppliers,
        improvement_needed_suppliers=improvement_needed,
        performance_trends=performance_trends,
        category_performance=category_performance,
    )


@router.get("/contracts/expiring")
def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """期限が近い契約取得"""
    contract_crud = SupplierContractCRUD(db)
    expiring_contracts = contract_crud.get_expiring_contracts(days)

    return {
        "contracts_count": len(expiring_contracts),
        "contracts": [
            {
                "contract_id": c.id,
                "contract_number": c.contract_number,
                "supplier_id": c.supplier_id,
                "contract_title": c.contract_title,
                "expiration_date": c.expiration_date,
                "days_until_expiry": (c.expiration_date - date.today()).days,
                "contract_value": c.contract_value,
                "auto_renewal": c.auto_renewal,
            }
            for c in expiring_contracts
        ],
    }
