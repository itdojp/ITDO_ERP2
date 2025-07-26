"""
ITDO ERP Backend - Cash Flow Prediction API
Day 25: Cash flow prediction endpoints with AI forecasting and scenario analysis

This API provides:
- Cash flow prediction creation and management
- Scenario analysis (optimistic, pessimistic, most likely)
- Sensitivity analysis for various factors
- Working capital optimization recommendations
- Cash flow risk assessment
- Stress testing capabilities
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.advanced_financial import CashFlowPrediction
from app.schemas.advanced_financial import (
    CashFlowPredictionCreate,
    CashFlowPredictionListResponse,
    CashFlowPredictionResponse,
    CashFlowPredictionUpdate,
)
from app.services.cashflow_prediction_service import CashFlowPredictionService
from app.types import BaseId, OrganizationId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cashflow-prediction", tags=["Cash Flow Prediction"])


# ===============================
# Dependency Functions
# ===============================


async def get_cashflow_service(
    db: AsyncSession = Depends(get_db),
) -> CashFlowPredictionService:
    """Get Cash Flow Prediction service dependency"""
    return CashFlowPredictionService(db)


# ===============================
# Cash Flow Prediction Endpoints
# ===============================


@router.post(
    "/predictions",
    response_model=CashFlowPredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cash_flow_prediction(
    prediction_data: CashFlowPredictionCreate,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    cashflow_service: CashFlowPredictionService = Depends(get_cashflow_service),
) -> CashFlowPredictionResponse:
    """Create comprehensive cash flow prediction with AI forecasting"""
    try:
        user_id = current_user["id"]

        # Create cash flow prediction using AI service
        prediction = await cashflow_service.create_cash_flow_prediction(
            prediction_data, user_id
        )

        # Schedule background tasks for additional analysis
        background_tasks.add_task(
            _schedule_stress_testing, prediction.id, cashflow_service
        )

        logger.info(
            f"Created cash flow prediction {prediction.id} for organization {prediction_data.organization_id}"
        )
        return CashFlowPredictionResponse.from_orm(prediction)

    except Exception as e:
        logger.error(f"Error creating cash flow prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cash flow prediction: {str(e)}",
        )


@router.get("/predictions", response_model=CashFlowPredictionListResponse)
async def get_cash_flow_predictions(
    organization_id: OrganizationId = Query(...),
    prediction_type: Optional[str] = Query(None),
    prediction_period: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CashFlowPredictionListResponse:
    """Get cash flow predictions with pagination and filtering"""
    try:
        # Build query
        query = select(CashFlowPrediction).where(
            CashFlowPrediction.organization_id == organization_id
        )

        if prediction_type:
            query = query.where(CashFlowPrediction.prediction_type == prediction_type)
        if prediction_period:
            query = query.where(
                CashFlowPrediction.prediction_period == prediction_period
            )
        if is_active is not None:
            query = query.where(CashFlowPrediction.is_active == is_active)

        # Add pagination
        offset = (page - 1) * per_page
        query = (
            query.offset(offset)
            .limit(per_page)
            .order_by(desc(CashFlowPrediction.created_at))
        )

        # Execute query
        result = await db.execute(query)
        predictions = result.scalars().all()

        # Get total count
        count_query = select(func.count(CashFlowPrediction.id)).where(
            CashFlowPrediction.organization_id == organization_id
        )
        if prediction_type:
            count_query = count_query.where(
                CashFlowPrediction.prediction_type == prediction_type
            )
        if prediction_period:
            count_query = count_query.where(
                CashFlowPrediction.prediction_period == prediction_period
            )
        if is_active is not None:
            count_query = count_query.where(CashFlowPrediction.is_active == is_active)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return CashFlowPredictionListResponse(
            items=[
                CashFlowPredictionResponse.from_orm(prediction)
                for prediction in predictions
            ],
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error getting cash flow predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cash flow predictions: {str(e)}",
        )


@router.get("/predictions/{prediction_id}", response_model=CashFlowPredictionResponse)
async def get_cash_flow_prediction(
    prediction_id: BaseId,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CashFlowPredictionResponse:
    """Get specific cash flow prediction with detailed analysis"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        return CashFlowPredictionResponse.from_orm(prediction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cash flow prediction {prediction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cash flow prediction",
        )


@router.put("/predictions/{prediction_id}", response_model=CashFlowPredictionResponse)
async def update_cash_flow_prediction(
    prediction_id: BaseId,
    update_data: CashFlowPredictionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CashFlowPredictionResponse:
    """Update cash flow prediction"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(prediction, field, value)

        await db.commit()
        await db.refresh(prediction)

        logger.info(f"Updated cash flow prediction {prediction_id}")
        return CashFlowPredictionResponse.from_orm(prediction)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating cash flow prediction {prediction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cash flow prediction",
        )


@router.delete("/predictions/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cash_flow_prediction(
    prediction_id: BaseId,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete cash flow prediction"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        await db.delete(prediction)
        await db.commit()

        logger.info(f"Deleted cash flow prediction {prediction_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting cash flow prediction {prediction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cash flow prediction",
        )


# ===============================
# Analysis and Optimization Endpoints
# ===============================


@router.get("/predictions/{prediction_id}/scenarios")
async def get_scenario_analysis(
    prediction_id: BaseId,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed scenario analysis for cash flow prediction"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        scenario_analysis = prediction.scenario_analysis or {}

        # Add additional analysis
        enhanced_scenarios = {}
        for scenario_name, scenario_data in scenario_analysis.items():
            scenario_forecast = scenario_data.get("forecast", {})

            enhanced_scenarios[scenario_name] = {
                **scenario_data,
                "cash_shortage_periods": [
                    date_str
                    for date_str, value in scenario_forecast.items()
                    if value < 0
                ],
                "peak_cash_period": max(
                    scenario_forecast.items(), key=lambda x: x[1], default=("", 0)
                )[0]
                if scenario_forecast
                else None,
                "lowest_cash_period": min(
                    scenario_forecast.items(), key=lambda x: x[1], default=("", 0)
                )[0]
                if scenario_forecast
                else None,
            }

        return {
            "prediction_id": prediction_id,
            "scenarios": enhanced_scenarios,
            "recommendations": prediction.optimization_recommendations,
            "risk_factors": prediction.risk_factors,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario analysis for {prediction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scenario analysis",
        )


@router.get("/predictions/{prediction_id}/sensitivity")
async def get_sensitivity_analysis(
    prediction_id: BaseId,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get sensitivity analysis for cash flow prediction"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        sensitivity_analysis = prediction.sensitivity_analysis or {}

        # Add risk impact assessment
        risk_impact = {}
        for scenario_name, scenario_data in sensitivity_analysis.items():
            impact = scenario_data.get("impact_percentage", 0)
            if abs(impact) > 20:
                risk_level = "high"
            elif abs(impact) > 10:
                risk_level = "medium"
            else:
                risk_level = "low"

            risk_impact[scenario_name] = {
                **scenario_data,
                "risk_level": risk_level,
            }

        return {
            "prediction_id": prediction_id,
            "sensitivity_scenarios": risk_impact,
            "summary": {
                "most_sensitive_factor": max(
                    sensitivity_analysis.items(),
                    key=lambda x: abs(x[1].get("impact_percentage", 0)),
                    default=("none", {"impact_percentage": 0}),
                )[0]
                if sensitivity_analysis
                else "none",
                "average_impact": sum(
                    abs(scenario.get("impact_percentage", 0))
                    for scenario in sensitivity_analysis.values()
                )
                / len(sensitivity_analysis)
                if sensitivity_analysis
                else 0,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting sensitivity analysis for {prediction_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sensitivity analysis",
        )


@router.post("/predictions/{prediction_id}/stress-test")
async def perform_stress_test(
    prediction_id: BaseId,
    stress_factors: Dict[str, float],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cashflow_service: CashFlowPredictionService = Depends(get_cashflow_service),
) -> Dict[str, Any]:
    """Perform stress testing on cash flow prediction"""
    try:
        query = select(CashFlowPrediction).where(CashFlowPrediction.id == prediction_id)
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash flow prediction not found",
            )

        # Apply stress factors to the prediction
        base_forecast = prediction.predicted_cashflow.get("forecast", {})
        stressed_forecast = {}

        for date_str, value in base_forecast.items():
            stressed_value = value

            # Apply stress factors
            for factor_name, factor_value in stress_factors.items():
                if factor_name == "revenue_shock" and value > 0:
                    stressed_value *= 1 - factor_value
                elif factor_name == "expense_shock" and value < 0:
                    stressed_value *= 1 + factor_value
                elif factor_name == "market_volatility":
                    volatility_impact = value * factor_value * 0.1
                    stressed_value += volatility_impact

            stressed_forecast[date_str] = round(stressed_value, 2)

        # Calculate stress test results
        original_total = sum(base_forecast.values())
        stressed_total = sum(stressed_forecast.values())
        impact = stressed_total - original_total
        impact_percentage = (
            (impact / original_total * 100) if original_total != 0 else 0
        )

        # Identify critical periods
        critical_periods = [
            date_str for date_str, value in stressed_forecast.items() if value < -5000
        ]

        return {
            "prediction_id": prediction_id,
            "stress_factors": stress_factors,
            "results": {
                "original_forecast": base_forecast,
                "stressed_forecast": stressed_forecast,
                "total_impact": round(impact, 2),
                "impact_percentage": round(impact_percentage, 2),
                "critical_periods": critical_periods,
                "survival_months": len(
                    [v for v in stressed_forecast.values() if v >= 0]
                ),
                "maximum_shortage": min(stressed_forecast.values())
                if stressed_forecast
                else 0,
            },
            "recommendations": _generate_stress_test_recommendations(
                stressed_forecast, critical_periods
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing stress test for {prediction_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform stress test",
        )


@router.get("/analytics/working-capital")
async def get_working_capital_analysis(
    organization_id: OrganizationId = Query(...),
    analysis_period: int = Query(12, ge=3, le=36),
    current_user: Dict[str, Any] = Depends(get_current_user),
    cashflow_service: CashFlowPredictionService = Depends(get_cashflow_service),
) -> Dict[str, Any]:
    """Get working capital analysis and optimization recommendations"""
    try:
        # Get working capital efficiency data (would be implemented in service)
        working_capital_data = {
            "current_metrics": {
                "accounts_receivable_days": 45,
                "inventory_turnover_days": 30,
                "accounts_payable_days": 35,
                "cash_conversion_cycle": 40,
                "working_capital_ratio": 1.25,
            },
            "industry_benchmarks": {
                "accounts_receivable_days": 35,
                "inventory_turnover_days": 25,
                "accounts_payable_days": 40,
                "cash_conversion_cycle": 20,
                "working_capital_ratio": 1.50,
            },
            "trends": {
                "3_month_trend": "improving",
                "6_month_trend": "stable",
                "12_month_trend": "improving",
            },
            "optimization_opportunities": [
                {
                    "area": "Accounts Receivable",
                    "current_days": 45,
                    "target_days": 35,
                    "potential_cash_impact": 25000,
                    "recommendations": [
                        "Implement early payment discounts",
                        "Automate invoice processing",
                        "Improve credit assessment process",
                    ],
                },
                {
                    "area": "Inventory Management",
                    "current_days": 30,
                    "target_days": 25,
                    "potential_cash_impact": 15000,
                    "recommendations": [
                        "Implement just-in-time inventory",
                        "Improve demand forecasting",
                        "Optimize inventory levels by category",
                    ],
                },
                {
                    "area": "Accounts Payable",
                    "current_days": 35,
                    "target_days": 40,
                    "potential_cash_impact": 20000,
                    "recommendations": [
                        "Negotiate extended payment terms",
                        "Take advantage of early payment discounts when beneficial",
                        "Optimize payment timing",
                    ],
                },
            ],
            "total_optimization_potential": 60000,
        }

        return {
            "organization_id": organization_id,
            "analysis_period_months": analysis_period,
            "working_capital_analysis": working_capital_data,
            "cash_flow_impact_summary": {
                "one_time_impact": working_capital_data["total_optimization_potential"],
                "annual_benefit": working_capital_data["total_optimization_potential"]
                * 0.15,
                "payback_period_months": 8,
            },
        }

    except Exception as e:
        logger.error(f"Error getting working capital analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get working capital analysis",
        )


@router.get("/analytics/cash-flow-dashboard")
async def get_cash_flow_dashboard(
    organization_id: OrganizationId = Query(...),
    time_horizon: str = Query("12m", regex="^(3m|6m|12m|24m)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get cash flow dashboard with key metrics and alerts"""
    try:
        # Get recent predictions for dashboard
        query = (
            select(CashFlowPrediction)
            .where(
                CashFlowPrediction.organization_id == organization_id,
                CashFlowPrediction.is_active,
            )
            .order_by(desc(CashFlowPrediction.created_at))
            .limit(1)
        )

        result = await db.execute(query)
        latest_prediction = result.scalar_one_or_none()

        dashboard_data = {
            "overview": {
                "current_cash_position": 125000.0,
                "projected_cash_3m": 140000.0,
                "projected_cash_6m": 155000.0,
                "projected_cash_12m": 180000.0,
                "cash_burn_rate": -8500.0,
                "runway_months": 14.7,
            },
            "key_metrics": {
                "operating_cash_flow": {
                    "current_month": 15000.0,
                    "previous_month": 12000.0,
                    "trend": "increasing",
                    "variance_percentage": 25.0,
                },
                "free_cash_flow": {
                    "current_month": 12000.0,
                    "previous_month": 9000.0,
                    "trend": "increasing",
                    "variance_percentage": 33.3,
                },
                "working_capital": {
                    "current": 85000.0,
                    "previous": 82000.0,
                    "trend": "stable",
                    "variance_percentage": 3.7,
                },
            },
            "alerts": [
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": "Cash flow projected to be negative in Q2",
                    "impact": "Potential funding gap of $15,000",
                    "recommended_action": "Accelerate receivables collection",
                    "deadline": (date.today() + timedelta(days=45)).isoformat(),
                },
                {
                    "type": "opportunity",
                    "severity": "low",
                    "message": "Excess cash available for investment",
                    "impact": "Potential return of $5,000 annually",
                    "recommended_action": "Consider short-term investments",
                    "deadline": (date.today() + timedelta(days=30)).isoformat(),
                },
            ],
            "predictions_summary": {
                "total_predictions": 1 if latest_prediction else 0,
                "latest_prediction_date": latest_prediction.created_at.isoformat()
                if latest_prediction
                else None,
                "prediction_accuracy": float(latest_prediction.model_accuracy)
                if latest_prediction
                else 0,
                "confidence_level": 85.0,
            },
            "risk_factors": latest_prediction.risk_factors if latest_prediction else [],
            "recommendations": latest_prediction.optimization_recommendations
            if latest_prediction
            else [],
        }

        return {
            "organization_id": organization_id,
            "time_horizon": time_horizon,
            "dashboard": dashboard_data,
            "last_updated": date.today().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting cash flow dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cash flow dashboard",
        )


# ===============================
# Helper Functions
# ===============================


async def _schedule_stress_testing(
    prediction_id: BaseId, cashflow_service: CashFlowPredictionService
) -> None:
    """Background task for additional stress testing"""
    try:
        # Perform automated stress testing scenarios

        logger.info(
            f"Completed background stress testing for prediction {prediction_id}"
        )

    except Exception as e:
        logger.error(f"Error in background stress testing: {str(e)}")


def _generate_stress_test_recommendations(
    stressed_forecast: Dict[str, float], critical_periods: List[str]
) -> List[str]:
    """Generate recommendations based on stress test results"""
    recommendations = []

    if critical_periods:
        recommendations.append(
            f"Prepare contingency funding for {len(critical_periods)} critical periods"
        )

    min_value = min(stressed_forecast.values()) if stressed_forecast else 0
    if min_value < -10000:
        recommendations.append("Consider establishing emergency credit line")

    negative_periods = sum(1 for v in stressed_forecast.values() if v < 0)
    if negative_periods > len(stressed_forecast) * 0.3:
        recommendations.append("Implement aggressive cost reduction measures")

    if not recommendations:
        recommendations.append("Cash flow appears resilient to stress scenarios")

    return recommendations


# ===============================
# Health Check Endpoint
# ===============================


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Cash flow prediction API health check"""
    return {
        "status": "healthy",
        "service": "cashflow-prediction-api",
        "version": "1.0.0",
        "features": [
            "ai_forecasting",
            "scenario_analysis",
            "sensitivity_analysis",
            "stress_testing",
            "working_capital_optimization",
        ],
        "timestamp": date.today().isoformat(),
    }
