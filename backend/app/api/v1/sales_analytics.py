"""
Sales Analytics API endpoints for Phase 5 CRM - Advanced Sales Forecasting.
営業予測分析APIエンドポイント（CRM機能Phase 5）
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.sales_forecast_service import SalesForecastService

router = APIRouter()


@router.get("/forecast/sales")
async def get_sales_forecast(
    forecast_months: int = Query(
        12, ge=1, le=24, description="Number of months to forecast (1-24)"
    ),
    include_pipeline: bool = Query(
        True, description="Include detailed pipeline analysis"
    ),
    include_trends: bool = Query(
        True, description="Include historical trend analysis"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate comprehensive sales forecast analysis."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        forecast = await service.generate_sales_forecast(
            organization_id=current_user.organization_id,
            forecast_months=forecast_months,
            include_pipeline=include_pipeline,
            include_trends=include_trends,
        )
        return forecast

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales forecast: {str(e)}"
        )


@router.get("/probability/win-analysis")
async def get_win_probability_analysis(
    opportunity_id: Optional[int] = Query(
        None, description="Specific opportunity ID for detailed analysis"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate win probability using historical data and advanced analytics."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        probability_analysis = await service.calculate_win_probability(
            organization_id=current_user.organization_id,
            opportunity_id=opportunity_id,
        )
        return probability_analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate win probability: {str(e)}"
        )


@router.get("/customers/sales-potential")
async def get_customer_sales_potential(
    customer_id: Optional[int] = Query(
        None, description="Specific customer ID for detailed analysis"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze sales potential for customers with AI-driven insights."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        potential_analysis = await service.analyze_customer_sales_potential(
            organization_id=current_user.organization_id,
            customer_id=customer_id,
        )
        return potential_analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze customer sales potential: {str(e)}"
        )


@router.get("/performance/sales-rep")
async def get_sales_performance_analysis(
    user_id: Optional[int] = Query(
        None, description="Specific sales rep user ID for analysis"
    ),
    period_months: int = Query(
        6, ge=1, le=24, description="Analysis period in months (1-24)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate sales performance analysis for sales representatives."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        performance_analysis = await service.generate_sales_performance_analysis(
            organization_id=current_user.organization_id,
            user_id=user_id,
            period_months=period_months,
        )
        return performance_analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales performance analysis: {str(e)}"
        )


@router.get("/dashboard/sales-overview")
async def get_sales_analytics_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive sales analytics dashboard data."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        # Get multiple analytics in parallel
        forecast = await service.generate_sales_forecast(
            organization_id=current_user.organization_id,
            forecast_months=6,
            include_pipeline=True,
            include_trends=True,
        )

        probability_analysis = await service.calculate_win_probability(
            organization_id=current_user.organization_id
        )

        customer_potential = await service.analyze_customer_sales_potential(
            organization_id=current_user.organization_id
        )

        performance_analysis = await service.generate_sales_performance_analysis(
            organization_id=current_user.organization_id,
            period_months=3,
        )

        return {
            "dashboard_type": "sales_analytics_overview",
            "organization_id": current_user.organization_id,
            "generation_date": forecast["generation_date"],
            "forecast_summary": {
                "next_6_months": forecast["monthly_forecast"][:6],
                "total_pipeline": forecast["summary"]["total_pipeline_value"],
                "weighted_pipeline": forecast["summary"]["weighted_pipeline_value"],
                "open_opportunities": forecast["summary"]["open_opportunities"],
            },
            "probability_insights": {
                "overall_win_rate": (
                    probability_analysis.get("organization_analysis", {})
                    .get("overall_win_rate", 0)
                ),
                "stage_analysis": (
                    probability_analysis.get("organization_analysis", {})
                    .get("stage_analysis", {})
                ),
            },
            "customer_insights": {
                "total_customers": (
                    customer_potential["summary"]["total_customers_analyzed"]
                ),
                "high_potential_customers": (
                    customer_potential["summary"]["high_potential_customers"]
                ),
                "top_potential_customers": customer_potential["customer_analyses"][:5],
            },
            "team_performance": {
                "team_summary": performance_analysis.get("team_summary", {}),
                "top_performers": sorted(
                    performance_analysis.get("sales_rep_performance", []),
                    key=lambda x: x["won_value"],
                    reverse=True
                )[:3],
            },
            "trends": forecast.get("trend_analysis", {}),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales analytics dashboard: {str(e)}"
        )


@router.get("/insights/pipeline-health")
async def get_pipeline_health_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pipeline health insights and recommendations."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        # Get forecast data to analyze pipeline health
        forecast = await service.generate_sales_forecast(
            organization_id=current_user.organization_id,
            forecast_months=3,
            include_pipeline=True,
            include_trends=False,
        )

        pipeline_analysis = forecast.get("pipeline_analysis", {})
        pipeline_by_stage = pipeline_analysis.get("pipeline_by_stage", {})
        age_analysis = pipeline_analysis.get("age_analysis", {})

        # Generate health insights
        health_insights = []
        recommendations = []

        # Analyze stage distribution
        total_pipeline = pipeline_analysis.get("total_pipeline", {}).get("count", 0)
        if total_pipeline > 0:
            lead_count = pipeline_by_stage.get("lead", {}).get("count", 0)
            qualified_count = pipeline_by_stage.get("qualified", {}).get("count", 0)
            proposal_count = pipeline_by_stage.get("proposal", {}).get("count", 0)

            lead_ratio = lead_count / total_pipeline * 100
            qualified_ratio = qualified_count / total_pipeline * 100

            if lead_ratio > 60:
                health_insights.append({
                    "type": "warning",
                    "message": (
                        f"High percentage of leads ({lead_ratio:.1f}%) - "
                        f"focus on qualification"
                    ),
                    "severity": "medium"
                })
                recommendations.append("Implement better lead qualification process")

            if qualified_ratio < 20:
                health_insights.append({
                    "type": "alert",
                    "message": (
                        f"Low qualified opportunities ({qualified_ratio:.1f}%) - "
                        f"need more qualified leads"
                    ),
                    "severity": "high"
                })
                recommendations.append("Increase lead qualification activities")

            if proposal_count == 0:
                health_insights.append({
                    "type": "warning",
                    "message": (
                        "No opportunities in proposal stage - potential revenue risk"
                    ),
                    "severity": "high"
                })
                recommendations.append(
                    "Focus on moving qualified opportunities to proposal stage"
                )

        # Analyze age distribution
        old_opportunities = age_analysis.get("90+ days", {}).get("count", 0)
        if old_opportunities > 0:
            old_ratio = (
                old_opportunities / total_pipeline * 100
                if total_pipeline > 0 else 0
            )
            if old_ratio > 30:
                health_insights.append({
                    "type": "alert",
                    "message": (
                        f"High percentage of stale opportunities "
                        f"({old_ratio:.1f}%) over 90 days"
                    ),
                    "severity": "high"
                })
                recommendations.append("Review and update old opportunities")

        # Overall health score
        health_score = 100
        for insight in health_insights:
            if insight["severity"] == "high":
                health_score -= 20
            elif insight["severity"] == "medium":
                health_score -= 10

        health_score = max(0, health_score)

        return {
            "pipeline_health": {
                "health_score": health_score,
                "health_status": (
                    "excellent" if health_score >= 80
                    else "good" if health_score >= 60
                    else "needs_attention" if health_score >= 40
                    else "poor"
                ),
                "insights": health_insights,
                "recommendations": recommendations,
            },
            "pipeline_metrics": {
                "total_opportunities": total_pipeline,
                "total_value": (
                    pipeline_analysis.get("total_pipeline", {}).get("total_value", 0)
                ),
                "weighted_value": (
                    pipeline_analysis.get("total_pipeline", {})
                    .get("weighted_value", 0)
                ),
                "stage_distribution": pipeline_by_stage,
                "age_distribution": age_analysis,
            },
            "analysis_date": forecast["generation_date"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pipeline health insights: {str(e)}"
        )


@router.get("/recommendations/sales-actions")
async def get_sales_action_recommendations(
    focus_area: Optional[str] = Query(
        None, description="Focus area: pipeline, conversion, performance, customers"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-driven sales action recommendations."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    service = SalesForecastService(db)

    try:
        recommendations = []

        if focus_area in [None, "pipeline"]:
            # Pipeline recommendations
            forecast = await service.generate_sales_forecast(
                organization_id=current_user.organization_id,
                forecast_months=3,
                include_pipeline=True,
                include_trends=False,
            )

            pipeline_analysis = forecast.get("pipeline_analysis", {})
            total_pipeline = pipeline_analysis.get("total_pipeline", {}).get("count", 0)

            if total_pipeline < 10:
                recommendations.append({
                    "category": "pipeline",
                    "priority": "high",
                    "action": "Increase lead generation activities",
                    "description": (
                        "Pipeline appears thin - focus on generating more opportunities"
                    ),
                    "expected_impact": "Increase future revenue potential"
                })

        if focus_area in [None, "customers"]:
            # Customer recommendations
            customer_analysis = await service.analyze_customer_sales_potential(
                organization_id=current_user.organization_id
            )

            high_potential = customer_analysis["summary"]["high_potential_customers"]
            total_customers = customer_analysis["summary"]["total_customers_analyzed"]

            if total_customers > 0 and high_potential / total_customers < 0.3:
                recommendations.append({
                    "category": "customers",
                    "priority": "medium",
                    "action": "Focus on high-value customer development",
                    "description": (
                        "Identify and develop relationships with "
                        "high-potential customers"
                    ),
                    "expected_impact": "Improve customer lifetime value"
                })

        if focus_area in [None, "performance"]:
            # Performance recommendations
            performance = await service.generate_sales_performance_analysis(
                organization_id=current_user.organization_id,
                period_months=3,
            )

            team_summary = performance.get("team_summary", {})
            team_win_rate = team_summary.get("team_win_rate", 0)

            if team_win_rate < 30:
                recommendations.append({
                    "category": "performance",
                    "priority": "high",
                    "action": "Improve sales process and training",
                    "description": (
                        "Low team win rate indicates need for process improvement"
                    ),
                    "expected_impact": "Increase conversion rates and revenue"
                })

        # Default recommendations if none generated
        if not recommendations:
            recommendations.append({
                "category": "general",
                "priority": "medium",
                "action": "Monitor sales metrics regularly",
                "description": "Continue tracking key sales performance indicators",
                "expected_impact": "Maintain sales performance visibility"
            })

        return {
            "recommendations": recommendations,
            "focus_area": focus_area,
            "total_recommendations": len(recommendations),
            "generation_date": (
                forecast["generation_date"] if 'forecast' in locals() else None
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales action recommendations: {str(e)}"
        )

