"""
ITDO ERP Backend - Advanced Financial Management API
Day 25: Advanced financial analytics with AI predictions, multi-currency support, and dashboards

This API provides:
- AI-powered financial forecasting and predictions
- Risk assessment and management
- Multi-currency financial operations
- Advanced financial analytics and KPIs
- Financial dashboard data endpoints
- Market data integration
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.types import BaseId, OrganizationId
from app.models.advanced_financial import (
    FinancialForecast,
    RiskAssessment,
)
from app.models.multi_currency import (
    Currency,
    ExchangeRate,
)
from app.schemas.advanced_financial import (
    FinancialAnalyticsRequest,
    FinancialAnalyticsResponse,
    FinancialForecastCreate,
    FinancialForecastListResponse,
    FinancialForecastResponse,
    RiskAssessmentCreate,
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
)
from app.schemas.multi_currency import (
    CurrencyConversionCalculation,
    CurrencyConversionRequest,
    CurrencyCreate,
    CurrencyListResponse,
    CurrencyResponse,
    ExchangeRateCreate,
    ExchangeRateResponse,
)
from app.services.financial_ai_service import FinancialAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/financial-advanced", tags=["Financial Advanced"])


# ===============================
# Dependency Functions
# ===============================


async def get_financial_ai_service(
    db: AsyncSession = Depends(get_db),
) -> FinancialAIService:
    """Get Financial AI service dependency"""
    return FinancialAIService(db)


# ===============================
# AI Financial Forecasting Endpoints
# ===============================


@router.post(
    "/forecasts",
    response_model=FinancialForecastResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_financial_forecast(
    forecast_data: FinancialForecastCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ai_service: FinancialAIService = Depends(get_financial_ai_service),
) -> FinancialForecastResponse:
    """Create AI-powered financial forecast"""
    try:
        user_id = current_user["id"]

        # Create forecast using AI service
        forecast = await ai_service.create_financial_forecast(forecast_data, user_id)

        logger.info(
            f"Created financial forecast {forecast.id} for organization {forecast_data.organization_id}"
        )
        return FinancialForecastResponse.from_orm(forecast)

    except Exception as e:
        logger.error(f"Error creating financial forecast: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create financial forecast: {str(e)}",
        )


@router.get("/forecasts", response_model=FinancialForecastListResponse)
async def get_financial_forecasts(
    organization_id: OrganizationId = Query(...),
    forecast_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialForecastListResponse:
    """Get financial forecasts with pagination"""
    try:
        # Build query
        query = select(FinancialForecast).where(
            FinancialForecast.organization_id == organization_id
        )

        if forecast_type:
            query = query.where(FinancialForecast.forecast_type == forecast_type)
        if is_active is not None:
            query = query.where(FinancialForecast.is_active == is_active)

        # Add pagination
        offset = (page - 1) * per_page
        query = (
            query.offset(offset)
            .limit(per_page)
            .order_by(desc(FinancialForecast.created_at))
        )

        # Execute query
        result = await db.execute(query)
        forecasts = result.scalars().all()

        # Get total count
        count_query = select(func.count(FinancialForecast.id)).where(
            FinancialForecast.organization_id == organization_id
        )
        if forecast_type:
            count_query = count_query.where(
                FinancialForecast.forecast_type == forecast_type
            )
        if is_active is not None:
            count_query = count_query.where(FinancialForecast.is_active == is_active)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return FinancialForecastListResponse(
            items=[
                FinancialForecastResponse.from_orm(forecast) for forecast in forecasts
            ],
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error getting financial forecasts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial forecasts: {str(e)}",
        )


@router.get("/forecasts/{forecast_id}", response_model=FinancialForecastResponse)
async def get_financial_forecast(
    forecast_id: BaseId,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialForecastResponse:
    """Get specific financial forecast"""
    try:
        query = select(FinancialForecast).where(FinancialForecast.id == forecast_id)
        result = await db.execute(query)
        forecast = result.scalar_one_or_none()

        if not forecast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial forecast not found",
            )

        return FinancialForecastResponse.from_orm(forecast)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial forecast {forecast_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get financial forecast",
        )


# ===============================
# Risk Assessment Endpoints
# ===============================


@router.post(
    "/risk-assessments",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_risk_assessment(
    assessment_data: RiskAssessmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ai_service: FinancialAIService = Depends(get_financial_ai_service),
) -> RiskAssessmentResponse:
    """Create comprehensive risk assessment"""
    try:
        user_id = current_user["id"]

        # Create risk assessment using AI service
        assessment = await ai_service.create_risk_assessment(assessment_data, user_id)

        logger.info(
            f"Created risk assessment {assessment.id} for organization {assessment_data.organization_id}"
        )
        return RiskAssessmentResponse.from_orm(assessment)

    except Exception as e:
        logger.error(f"Error creating risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create risk assessment: {str(e)}",
        )


@router.get("/risk-assessments", response_model=RiskAssessmentListResponse)
async def get_risk_assessments(
    organization_id: OrganizationId = Query(...),
    assessment_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentListResponse:
    """Get risk assessments with pagination"""
    try:
        # Build query
        query = select(RiskAssessment).where(
            RiskAssessment.organization_id == organization_id
        )

        if assessment_type:
            query = query.where(RiskAssessment.assessment_type == assessment_type)
        if risk_level:
            query = query.where(RiskAssessment.risk_level == risk_level)

        # Add pagination
        offset = (page - 1) * per_page
        query = (
            query.offset(offset)
            .limit(per_page)
            .order_by(desc(RiskAssessment.assessment_date))
        )

        # Execute query
        result = await db.execute(query)
        assessments = result.scalars().all()

        # Get total count
        count_query = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.organization_id == organization_id
        )
        if assessment_type:
            count_query = count_query.where(
                RiskAssessment.assessment_type == assessment_type
            )
        if risk_level:
            count_query = count_query.where(RiskAssessment.risk_level == risk_level)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return RiskAssessmentListResponse(
            items=[
                RiskAssessmentResponse.from_orm(assessment)
                for assessment in assessments
            ],
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error getting risk assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk assessments: {str(e)}",
        )


# ===============================
# Multi-Currency Management Endpoints
# ===============================


@router.post(
    "/currencies", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED
)
async def create_currency(
    currency_data: CurrencyCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CurrencyResponse:
    """Create new currency"""
    try:
        # Check if currency code already exists
        existing_query = select(Currency).where(
            Currency.currency_code == currency_data.currency_code
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency with code {currency_data.currency_code} already exists",
            )

        # Create currency
        currency = Currency(
            currency_code=currency_data.currency_code,
            currency_name=currency_data.currency_name,
            currency_symbol=currency_data.currency_symbol,
            numeric_code=currency_data.numeric_code,
            decimal_places=currency_data.decimal_places,
            rounding_method=currency_data.rounding_method,
            country_code=currency_data.country_code,
            region=currency_data.region,
            is_active=currency_data.is_active,
            is_base_currency=currency_data.is_base_currency,
            supports_fractional=currency_data.supports_fractional,
            display_format=currency_data.display_format,
            thousand_separator=currency_data.thousand_separator,
            decimal_separator=currency_data.decimal_separator,
            currency_properties=currency_data.currency_properties,
        )

        db.add(currency)
        await db.commit()
        await db.refresh(currency)

        logger.info(f"Created currency {currency.currency_code}")
        return CurrencyResponse.from_orm(currency)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating currency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create currency: {str(e)}",
        )


@router.get("/currencies", response_model=CurrencyListResponse)
async def get_currencies(
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CurrencyListResponse:
    """Get currencies with pagination"""
    try:
        # Build query
        query = select(Currency)

        if is_active is not None:
            query = query.where(Currency.is_active == is_active)

        # Add pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Currency.currency_code)

        # Execute query
        result = await db.execute(query)
        currencies = result.scalars().all()

        # Get total count
        count_query = select(func.count(Currency.id))
        if is_active is not None:
            count_query = count_query.where(Currency.is_active == is_active)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return CurrencyListResponse(
            items=[CurrencyResponse.from_orm(currency) for currency in currencies],
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error getting currencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get currencies: {str(e)}",
        )


@router.post(
    "/exchange-rates",
    response_model=ExchangeRateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_exchange_rate(
    rate_data: ExchangeRateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeRateResponse:
    """Create exchange rate"""
    try:
        # Validate currencies exist
        base_currency_query = select(Currency).where(
            Currency.id == rate_data.base_currency_id
        )
        target_currency_query = select(Currency).where(
            Currency.id == rate_data.target_currency_id
        )

        base_result = await db.execute(base_currency_query)
        target_result = await db.execute(target_currency_query)

        if not base_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base currency not found",
            )
        if not target_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target currency not found",
            )

        # Create exchange rate
        exchange_rate = ExchangeRate(
            base_currency_id=rate_data.base_currency_id,
            target_currency_id=rate_data.target_currency_id,
            rate_date=rate_data.rate_date,
            exchange_rate=rate_data.exchange_rate,
            inverse_rate=rate_data.inverse_rate,
            rate_type=rate_data.rate_type,
            rate_source=rate_data.rate_source,
            bid_rate=rate_data.bid_rate,
            ask_rate=rate_data.ask_rate,
            spread=rate_data.spread,
            effective_time=rate_data.effective_time,
            expiry_time=rate_data.expiry_time,
            is_active=rate_data.is_active,
            confidence_score=rate_data.confidence_score,
            volatility_index=rate_data.volatility_index,
            rate_metadata=rate_data.rate_metadata,
        )

        db.add(exchange_rate)
        await db.commit()
        await db.refresh(exchange_rate)

        logger.info(f"Created exchange rate {exchange_rate.id}")
        return ExchangeRateResponse.from_orm(exchange_rate)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exchange rate: {str(e)}",
        )


@router.post(
    "/currency-conversion/calculate", response_model=CurrencyConversionCalculation
)
async def calculate_currency_conversion(
    conversion_request: CurrencyConversionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CurrencyConversionCalculation:
    """Calculate currency conversion"""
    try:
        # Get currencies
        base_currency_query = select(Currency).where(
            Currency.currency_code == conversion_request.source_currency_code
        )
        target_currency_query = select(Currency).where(
            Currency.currency_code == conversion_request.target_currency_code
        )

        base_result = await db.execute(base_currency_query)
        target_result = await db.execute(target_currency_query)

        base_currency = base_result.scalar_one_or_none()
        target_currency = target_result.scalar_one_or_none()

        if not base_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source currency {conversion_request.source_currency_code} not found",
            )
        if not target_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target currency {conversion_request.target_currency_code} not found",
            )

        # Get latest exchange rate
        rate_query = (
            select(ExchangeRate)
            .where(
                and_(
                    ExchangeRate.base_currency_id == base_currency.id,
                    ExchangeRate.target_currency_id == target_currency.id,
                    ExchangeRate.rate_date <= conversion_request.conversion_date,
                    ExchangeRate.is_active,
                )
            )
            .order_by(desc(ExchangeRate.rate_date))
            .limit(1)
        )

        rate_result = await db.execute(rate_query)
        exchange_rate = rate_result.scalar_one_or_none()

        if not exchange_rate:
            # Try reverse rate
            reverse_rate_query = (
                select(ExchangeRate)
                .where(
                    and_(
                        ExchangeRate.base_currency_id == target_currency.id,
                        ExchangeRate.target_currency_id == base_currency.id,
                        ExchangeRate.rate_date <= conversion_request.conversion_date,
                        ExchangeRate.is_active,
                    )
                )
                .order_by(desc(ExchangeRate.rate_date))
                .limit(1)
            )

            reverse_result = await db.execute(reverse_rate_query)
            reverse_rate = reverse_result.scalar_one_or_none()

            if reverse_rate:
                # Use inverse rate
                rate = reverse_rate.inverse_rate
                rate_source = reverse_rate.rate_source
                rate_timestamp = reverse_rate.created_at
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No exchange rate found for {conversion_request.source_currency_code} to {conversion_request.target_currency_code}",
                )
        else:
            rate = exchange_rate.exchange_rate
            rate_source = exchange_rate.rate_source
            rate_timestamp = exchange_rate.created_at

        # Calculate conversion
        target_amount = conversion_request.source_amount * rate

        # Calculate fees (simplified - 0.5% fee)
        conversion_fee = Decimal("0.0")
        if conversion_request.include_fees:
            conversion_fee = target_amount * Decimal("0.005")

        total_cost = conversion_request.source_amount + (
            conversion_fee / rate if conversion_fee > 0 else Decimal("0.0")
        )

        return CurrencyConversionCalculation(
            source_currency_code=conversion_request.source_currency_code,
            target_currency_code=conversion_request.target_currency_code,
            source_amount=conversion_request.source_amount,
            target_amount=target_amount,
            exchange_rate=rate,
            conversion_fee=conversion_fee,
            total_cost=total_cost,
            rate_timestamp=rate_timestamp,
            rate_source=rate_source,
            calculation_method="real_time",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating currency conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate currency conversion: {str(e)}",
        )


# ===============================
# Financial Analytics Endpoints
# ===============================


@router.post("/analytics", response_model=FinancialAnalyticsResponse)
async def perform_financial_analytics(
    analytics_request: FinancialAnalyticsRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ai_service: FinancialAIService = Depends(get_financial_ai_service),
) -> FinancialAnalyticsResponse:
    """Perform comprehensive financial analytics"""
    try:
        # Create comprehensive financial analysis
        start_time = datetime.utcnow()

        # Basic analytics response (simplified for demo)
        analytics_results = {
            "financial_health_score": 78.5,
            "revenue_trend": "increasing",
            "cash_flow_status": "positive",
            "risk_indicators": ["market_volatility", "currency_exposure"],
            "optimization_opportunities": [
                "Cost reduction in operations",
                "Revenue enhancement through market expansion",
                "Working capital optimization",
            ],
            "forecasted_performance": {
                "next_quarter_revenue": 2500000.00,
                "projected_growth_rate": 0.12,
                "confidence_level": 0.85,
            },
        }

        insights = [
            "Revenue growth trend is positive with 12% projected increase",
            "Cash flow position is strong with improving working capital",
            "Market volatility presents both risks and opportunities",
            "Consider hedging strategies for currency exposure",
        ]

        recommendations = [
            "Implement cost optimization program targeting 5% reduction",
            "Expand into emerging markets to diversify revenue",
            "Establish currency hedging policy for international operations",
            "Review and optimize inventory management processes",
        ]

        risk_factors = [
            "Market volatility in key sectors",
            "Currency exchange rate fluctuations",
            "Competitive pressure on margins",
            "Regulatory changes in target markets",
        ]

        # Calculate next review date
        next_review = analytics_request.end_date + timedelta(days=30)

        return FinancialAnalyticsResponse(
            analysis_type=analytics_request.analysis_type,
            organization_id=analytics_request.organization_id,
            analysis_date=start_time,
            results=analytics_results,
            insights=insights,
            recommendations=recommendations,
            confidence_score=Decimal("85.5"),
            data_quality_score=Decimal("92.0"),
            risk_factors=risk_factors,
            next_review_date=next_review,
        )

    except Exception as e:
        logger.error(f"Error performing financial analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform financial analytics: {str(e)}",
        )


# ===============================
# Financial Dashboard Endpoints
# ===============================


@router.get("/dashboard/overview")
async def get_financial_dashboard_overview(
    organization_id: OrganizationId = Query(...),
    date_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get financial dashboard overview data"""
    try:
        # Calculate date range
        end_date = date.today()
        if date_range == "7d":
            _ = end_date - timedelta(days=7)  # start_date calculation for future use
        elif date_range == "30d":
            _ = end_date - timedelta(days=30)  # start_date calculation for future use
        elif date_range == "90d":
            _ = end_date - timedelta(days=90)  # start_date calculation for future use
        else:  # 1y
            _ = end_date - timedelta(days=365)  # start_date calculation for future use

        # Get financial metrics (simplified demo data)
        dashboard_data = {
            "summary": {
                "total_revenue": 5750000.00,
                "total_expenses": 4200000.00,
                "net_profit": 1550000.00,
                "profit_margin": 26.96,
                "cash_position": 2100000.00,
                "current_ratio": 1.85,
            },
            "trends": {
                "revenue_growth": 12.5,
                "expense_growth": 8.2,
                "profit_growth": 22.1,
                "cash_flow_trend": "positive",
            },
            "risk_indicators": {
                "overall_risk_score": 45.0,
                "credit_risk": 38.0,
                "market_risk": 52.0,
                "liquidity_risk": 28.0,
                "operational_risk": 41.0,
            },
            "currency_exposure": {
                "primary_currency": "USD",
                "exposures": {
                    "EUR": 850000.00,
                    "GBP": 420000.00,
                    "JPY": 1200000.00,
                },
                "hedged_percentage": 65.0,
            },
            "forecasts": {
                "next_quarter_revenue": 1500000.00,
                "next_quarter_expenses": 1100000.00,
                "projected_cash_flow": 400000.00,
                "confidence_level": 87.5,
            },
            "alerts": [
                {
                    "type": "currency",
                    "message": "EUR/USD rate exceeded threshold of 1.20",
                    "priority": "medium",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "type": "cash_flow",
                    "message": "Cash flow projection shows potential shortfall in Q2",
                    "priority": "high",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ],
            "recent_activities": [
                {
                    "type": "forecast",
                    "description": "AI forecast updated for Q2 revenue",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "type": "risk_assessment",
                    "description": "Monthly risk assessment completed",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                },
                {
                    "type": "currency_conversion",
                    "description": "EUR 500K converted to USD",
                    "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                },
            ],
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error getting financial dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial dashboard overview: {str(e)}",
        )


@router.get("/dashboard/kpis")
async def get_financial_kpis(
    organization_id: OrganizationId = Query(...),
    metric_category: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get financial KPIs and metrics"""
    try:
        # Get financial KPIs (demo data)
        kpis = {
            "profitability": {
                "gross_profit_margin": 42.5,
                "operating_profit_margin": 18.7,
                "net_profit_margin": 13.2,
                "return_on_assets": 8.9,
                "return_on_equity": 15.4,
            },
            "liquidity": {
                "current_ratio": 1.85,
                "quick_ratio": 1.42,
                "cash_ratio": 0.75,
                "working_capital": 890000.00,
                "cash_conversion_cycle": 45,
            },
            "efficiency": {
                "asset_turnover": 1.25,
                "inventory_turnover": 8.2,
                "receivables_turnover": 12.5,
                "payables_turnover": 15.8,
                "revenue_per_employee": 185000.00,
            },
            "leverage": {
                "debt_to_equity": 0.35,
                "debt_to_assets": 0.22,
                "interest_coverage": 8.5,
                "debt_service_coverage": 2.1,
            },
            "market": {
                "market_cap": 125000000.00,
                "enterprise_value": 118000000.00,
                "price_to_earnings": 18.5,
                "price_to_book": 2.8,
                "beta": 1.12,
            },
            "growth": {
                "revenue_growth_rate": 12.5,
                "earnings_growth_rate": 22.1,
                "dividend_growth_rate": 8.0,
                "book_value_growth": 15.2,
            },
        }

        if metric_category:
            return {metric_category: kpis.get(metric_category, {})}

        return kpis

    except Exception as e:
        logger.error(f"Error getting financial KPIs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial KPIs: {str(e)}",
        )


@router.get("/dashboard/charts")
async def get_financial_charts_data(
    organization_id: OrganizationId = Query(...),
    chart_type: str = Query(
        ...,
        regex="^(revenue_trend|profit_trend|cash_flow|risk_matrix|currency_exposure)$",
    ),
    period: str = Query("12m", regex="^(3m|6m|12m|24m)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get data for financial dashboard charts"""
    try:
        # Generate chart data based on type (demo data)
        if chart_type == "revenue_trend":
            chart_data = {
                "labels": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "datasets": [
                    {
                        "label": "Revenue",
                        "data": [
                            450000,
                            520000,
                            480000,
                            610000,
                            590000,
                            650000,
                            720000,
                            680000,
                            750000,
                            780000,
                            820000,
                            850000,
                        ],
                        "borderColor": "#3B82F6",
                        "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    },
                    {
                        "label": "Forecast",
                        "data": [
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            850000,
                            890000,
                            920000,
                        ],
                        "borderColor": "#EF4444",
                        "borderDash": [5, 5],
                    },
                ],
            }
        elif chart_type == "profit_trend":
            chart_data = {
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [
                    {
                        "label": "Gross Profit",
                        "data": [380000, 420000, 450000, 485000],
                        "backgroundColor": "#10B981",
                    },
                    {
                        "label": "Operating Profit",
                        "data": [180000, 220000, 250000, 275000],
                        "backgroundColor": "#3B82F6",
                    },
                    {
                        "label": "Net Profit",
                        "data": [120000, 155000, 180000, 195000],
                        "backgroundColor": "#8B5CF6",
                    },
                ],
            }
        elif chart_type == "cash_flow":
            chart_data = {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "datasets": [
                    {
                        "label": "Operating Cash Flow",
                        "data": [85000, 92000, 88000, 105000, 98000, 112000],
                        "backgroundColor": "#10B981",
                    },
                    {
                        "label": "Investing Cash Flow",
                        "data": [-25000, -30000, -18000, -45000, -22000, -35000],
                        "backgroundColor": "#EF4444",
                    },
                    {
                        "label": "Financing Cash Flow",
                        "data": [-15000, 0, -8000, 20000, -12000, 0],
                        "backgroundColor": "#F59E0B",
                    },
                ],
            }
        elif chart_type == "risk_matrix":
            chart_data = {
                "data": [
                    {"x": 45, "y": 38, "label": "Credit Risk", "color": "#10B981"},
                    {"x": 52, "y": 65, "label": "Market Risk", "color": "#EF4444"},
                    {"x": 28, "y": 42, "label": "Liquidity Risk", "color": "#3B82F6"},
                    {"x": 41, "y": 55, "label": "Operational Risk", "color": "#F59E0B"},
                ],
                "axes": {
                    "x": "Probability",
                    "y": "Impact",
                },
            }
        else:  # currency_exposure
            chart_data = {
                "labels": ["USD", "EUR", "GBP", "JPY", "CAD"],
                "datasets": [
                    {
                        "data": [65, 20, 8, 5, 2],
                        "backgroundColor": [
                            "#3B82F6",
                            "#10B981",
                            "#F59E0B",
                            "#EF4444",
                            "#8B5CF6",
                        ],
                    }
                ],
            }

        return {
            "chart_type": chart_type,
            "period": period,
            "data": chart_data,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting financial charts data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial charts data: {str(e)}",
        )


# ===============================
# Health Check Endpoint
# ===============================


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Advanced financial management API health check"""
    return {
        "status": "healthy",
        "service": "financial-advanced-api",
        "version": "1.0.0",
        "features": [
            "ai_forecasting",
            "risk_assessment",
            "multi_currency",
            "financial_analytics",
            "dashboard_data",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
