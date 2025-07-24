"""
Financial Reports API endpoints for Phase 4 Financial Management.
財務レポートAPIエンドポイント（財務管理機能Phase 4）
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.financial_reports_service import FinancialReportsService

router = APIRouter()


@router.get("/budget-performance/{fiscal_year}")
async def get_budget_performance_report(
    fiscal_year: int,
    include_variance_analysis: bool = Query(
        True, description="Include detailed variance analysis"
    ),
    include_trend_data: bool = Query(True, description="Include historical trend data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate comprehensive budget performance report."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = FinancialReportsService(db)

    try:
        report = await service.generate_budget_performance_report(
            organization_id=current_user.organization_id,
            fiscal_year=fiscal_year,
            include_variance_analysis=include_variance_analysis,
            include_trend_data=include_trend_data,
        )
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate budget performance report: {str(e)}",
        )


@router.get("/expense-summary")
async def get_expense_summary_report(
    date_from: Optional[date] = Query(
        None, description="Start date for expense summary (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        None, description="End date for expense summary (YYYY-MM-DD)"
    ),
    include_employee_breakdown: bool = Query(
        True, description="Include breakdown by employee"
    ),
    include_category_breakdown: bool = Query(
        True, description="Include breakdown by category"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate expense summary report."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = FinancialReportsService(db)

    try:
        report = await service.generate_expense_summary_report(
            organization_id=current_user.organization_id,
            date_from=date_from,
            date_to=date_to,
            include_employee_breakdown=include_employee_breakdown,
            include_category_breakdown=include_category_breakdown,
        )
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate expense summary report: {str(e)}",
        )


@router.get("/monthly/{year}/{month}")
async def get_monthly_financial_report(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate monthly financial report."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12",
        )

    service = FinancialReportsService(db)

    try:
        report = await service.generate_monthly_financial_report(
            organization_id=current_user.organization_id,
            year=year,
            month=month,
        )
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate monthly financial report: {str(e)}",
        )


@router.get("/yearly/{year}")
async def get_yearly_financial_summary(
    year: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate yearly financial summary report."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = FinancialReportsService(db)

    try:
        report = await service.generate_yearly_financial_summary(
            organization_id=current_user.organization_id,
            year=year,
        )
        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate yearly financial summary: {str(e)}",
        )


@router.get("/dashboard/current-year")
async def get_current_year_financial_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get financial dashboard data for current year."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    from datetime import datetime

    current_year = datetime.now().year

    service = FinancialReportsService(db)

    try:
        # Get both yearly summary and current month data
        yearly_summary = await service.generate_yearly_financial_summary(
            organization_id=current_user.organization_id,
            year=current_year,
        )

        current_month = datetime.now().month
        monthly_report = await service.generate_monthly_financial_report(
            organization_id=current_user.organization_id,
            year=current_year,
            month=current_month,
        )

        return {
            "dashboard_type": "current_year_financial",
            "organization_id": current_user.organization_id,
            "year": current_year,
            "month": current_month,
            "generation_date": datetime.utcnow().isoformat(),
            "yearly_overview": yearly_summary["yearly_summary"],
            "current_month": monthly_report["monthly_summary"],
            "monthly_trends": yearly_summary["monthly_breakdown"],
            "top_expense_categories": yearly_summary["top_expense_categories"][:5],
            "recent_expenses": monthly_report["expense_details"][:10],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate financial dashboard: {str(e)}",
        )


@router.get("/analytics/variance-analysis/{fiscal_year}")
async def get_variance_analysis_report(
    fiscal_year: int,
    threshold_percentage: float = Query(
        20.0,
        description="Variance threshold percentage for highlighting significant "
        "variances",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate detailed variance analysis report."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    service = FinancialReportsService(db)

    try:
        # Get budget performance report with focus on variance analysis
        report = await service.generate_budget_performance_report(
            organization_id=current_user.organization_id,
            fiscal_year=fiscal_year,
            include_variance_analysis=True,
            include_trend_data=True,
        )

        # Filter and enhance variance analysis based on threshold
        variance_analysis = report.get("variance_analysis", {})

        # Add threshold-based analysis
        significant_variances = []
        for budget in report.get("budget_breakdown", []):
            if abs(budget["variance_percentage"]) >= threshold_percentage:
                budget["severity"] = (
                    "high"
                    if abs(budget["variance_percentage"]) >= 50
                    else "medium"
                    if abs(budget["variance_percentage"]) >= 30
                    else "low"
                )
                significant_variances.append(budget)

        return {
            "report_type": "variance_analysis",
            "organization_id": current_user.organization_id,
            "fiscal_year": fiscal_year,
            "threshold_percentage": threshold_percentage,
            "generation_date": report["generation_date"],
            "summary": report["summary"],
            "variance_analysis": variance_analysis,
            "significant_variances": significant_variances,
            "recommendations": await _generate_variance_recommendations(
                significant_variances
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate variance analysis report: {str(e)}",
        )


@router.get("/export/budget-performance/{fiscal_year}", response_model=None)
async def export_budget_performance_report(
    fiscal_year: int,
    format: str = Query("json", description="Export format: json, csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Union[Dict[str, Any], JSONResponse, StreamingResponse]:
    """Export budget performance report in various formats."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'json' or 'csv'",
        )

    service = FinancialReportsService(db)

    try:
        report = await service.generate_budget_performance_report(
            organization_id=current_user.organization_id,
            fiscal_year=fiscal_year,
            include_variance_analysis=True,
            include_trend_data=True,
        )

        if format == "json":
            from fastapi.responses import JSONResponse

            return JSONResponse(
                content=report,
                headers={
                    "Content-Disposition": (
                        f"attachment; filename=budget_performance_{fiscal_year}.json"
                    )
                },
            )

        elif format == "csv":
            # Convert to CSV format
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(
                [
                    "Budget Code",
                    "Budget Name",
                    "Budget Amount",
                    "Actual Amount",
                    "Variance",
                    "Variance %",
                    "Status",
                    "Utilization Rate",
                ]
            )

            # Write data
            for budget in report["budget_breakdown"]:
                writer.writerow(
                    [
                        budget["budget_code"],
                        budget["budget_name"],
                        budget["budget_amount"],
                        budget["actual_amount"],
                        budget["variance"],
                        budget["variance_percentage"],
                        budget["status"],
                        budget["utilization_rate"],
                    ]
                )

            from fastapi.responses import StreamingResponse

            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename=budget_performance_{fiscal_year}.csv"
                    )
                },
            )

        # This should never be reached, but needed for type checking
        return {"error": "Unknown format"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export budget performance report: {str(e)}",
        )


async def _generate_variance_recommendations(
    significant_variances: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate recommendations based on variance analysis."""
    recommendations = []

    for variance in significant_variances:
        if variance["variance_percentage"] < -20:  # Over budget
            recommendations.append(
                {
                    "budget_code": variance["budget_code"],
                    "type": "cost_control",
                    "priority": variance["severity"],
                    "message": (
                        f"Budget {variance['budget_code']} is "
                        f"{abs(variance['variance_percentage']):.1f}% over budget. "
                        f"Consider implementing cost control measures."
                    ),
                    "suggested_actions": [
                        "Review expense approval process",
                        "Identify cost reduction opportunities",
                        "Monitor spending more closely",
                    ],
                }
            )
        elif variance["variance_percentage"] > 20:  # Under budget
            recommendations.append(
                {
                    "budget_code": variance["budget_code"],
                    "type": "utilization",
                    "priority": "low",
                    "message": (
                        f"Budget {variance['budget_code']} is "
                        f"{variance['variance_percentage']:.1f}% under budget. "
                        f"Consider reallocating funds or reviewing budget planning."
                    ),
                    "suggested_actions": [
                        "Review budget allocation accuracy",
                        "Consider reallocating surplus to other areas",
                        "Evaluate if budget targets are realistic",
                    ],
                }
            )

    return recommendations
