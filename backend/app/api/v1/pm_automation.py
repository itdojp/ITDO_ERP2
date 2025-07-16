"""Project Management Automation API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.services.pm_automation import PMAutomationService

router = APIRouter(prefix="/pm-automation", tags=["pm-automation"])


@router.post("/projects/{project_id}/auto-structure")
async def auto_create_project_structure(
    project_id: int = Path(..., description="Project ID"),
    template_type: str = Query("agile", description="Template type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Automatically create project structure based on template.

    Supported templates:
    - agile: Agile/Scrum project structure
    - waterfall: Waterfall project structure
    - kanban: Kanban project structure
    """
    try:
        service = PMAutomationService(db)
        result = service.auto_create_project_structure(
            project_id, template_type, current_user
        )
        return {
            "success": True,
            "data": result,
            "message": f"Project structure created successfully using {template_type} template",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project structure",
        )


@router.post("/projects/{project_id}/auto-assign")
async def auto_assign_tasks(
    project_id: int = Path(..., description="Project ID"),
    strategy: str = Query("balanced", description="Assignment strategy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Automatically assign tasks to team members.

    Supported strategies:
    - balanced: Distribute tasks evenly among team members
    - skill_based: Assign based on skills and expertise
    - workload_based: Assign based on current workload
    """
    try:
        service = PMAutomationService(db)
        result = service.auto_assign_tasks(project_id, current_user, strategy)
        return {
            "success": True,
            "data": result,
            "message": f"Tasks assigned successfully using {strategy} strategy",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign tasks",
        )


@router.get("/projects/{project_id}/progress-report")
async def generate_progress_report(
    project_id: int = Path(..., description="Project ID"),
    report_type: str = Query("weekly", description="Report type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Generate automated progress report.

    Supported report types:
    - daily: Daily progress report
    - weekly: Weekly progress report
    - monthly: Monthly progress report
    """
    try:
        service = PMAutomationService(db)
        result = service.generate_progress_report(project_id, current_user, report_type)
        return {
            "success": True,
            "data": result,
            "message": f"{report_type.capitalize()} progress report generated successfully",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate progress report",
        )


@router.post("/projects/{project_id}/optimize")
async def optimize_project_schedule(
    project_id: int = Path(..., description="Project ID"),
    optimization_type: str = Query("critical_path", description="Optimization type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Automatically optimize project schedule.

    Supported optimization types:
    - critical_path: Critical path method optimization
    - resource_leveling: Resource leveling optimization
    - risk_mitigation: Risk-based optimization
    """
    try:
        service = PMAutomationService(db)
        result = service.auto_schedule_optimization(
            project_id, current_user, optimization_type
        )
        return {
            "success": True,
            "data": result,
            "message": f"Schedule optimization completed using {optimization_type} method",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize project schedule",
        )


@router.get("/projects/{project_id}/analytics")
async def get_predictive_analytics(
    project_id: int = Path(..., description="Project ID"),
    prediction_type: str = Query("completion_date", description="Prediction type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Generate predictive analytics for project.

    Supported prediction types:
    - completion_date: Predict project completion date
    - budget_forecast: Forecast budget usage
    - risk_probability: Predict risk probability
    """
    try:
        service = PMAutomationService(db)
        result = service.predictive_analytics(project_id, current_user, prediction_type)
        return {
            "success": True,
            "data": result,
            "message": f"Predictive analytics generated for {prediction_type}",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate predictive analytics",
        )


@router.get("/projects/{project_id}/dashboard")
async def get_automation_dashboard(
    project_id: int = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get comprehensive automation dashboard for project."""
    try:
        service = PMAutomationService(db)

        # Get multiple analytics in parallel
        progress_report = service.generate_progress_report(
            project_id, current_user, "weekly"
        )
        completion_prediction = service.predictive_analytics(
            project_id, current_user, "completion_date"
        )
        risk_analysis = service.predictive_analytics(
            project_id, current_user, "risk_probability"
        )

        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "progress_report": progress_report,
                "completion_prediction": completion_prediction,
                "risk_analysis": risk_analysis,
                "last_updated": progress_report.get("generated_at"),
            },
            "message": "Automation dashboard data retrieved successfully",
        }
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


@router.get("/templates")
async def get_available_templates() -> Dict[str, Any]:
    """Get list of available project templates."""
    templates = {
        "agile": {
            "name": "Agile/Scrum",
            "description": "アジャイル開発に適したプロジェクト構造",
            "features": ["スプリント計画", "ユーザーストーリー", "レトロスペクティブ"],
            "typical_duration": "2-6 months",
            "team_size": "3-9 members",
        },
        "waterfall": {
            "name": "Waterfall",
            "description": "ウォーターフォール開発に適したプロジェクト構造",
            "features": ["フェーズゲート", "詳細計画", "品質管理"],
            "typical_duration": "6-24 months",
            "team_size": "5-20 members",
        },
        "kanban": {
            "name": "Kanban",
            "description": "カンバン方式に適したプロジェクト構造",
            "features": ["継続的フロー", "WIP制限", "リードタイム最適化"],
            "typical_duration": "継続的",
            "team_size": "2-8 members",
        },
    }

    return {
        "success": True,
        "data": {"templates": templates, "total_templates": len(templates)},
        "message": "Available templates retrieved successfully",
    }


@router.get("/strategies")
async def get_assignment_strategies() -> Dict[str, Any]:
    """Get list of available task assignment strategies."""
    strategies = {
        "balanced": {
            "name": "Balanced Assignment",
            "description": "タスクをチームメンバーに均等に分散",
            "best_for": "チームの経験が似ている場合",
            "considerations": ["作業負荷の平準化", "公平性の確保"],
        },
        "skill_based": {
            "name": "Skill-based Assignment",
            "description": "スキルと専門性に基づいてタスクを割り当て",
            "best_for": "多様なスキルセットを持つチーム",
            "considerations": ["スキルの向上", "品質の確保"],
        },
        "workload_based": {
            "name": "Workload-based Assignment",
            "description": "現在の作業負荷に基づいてタスクを割り当て",
            "best_for": "メンバーの作業量にばらつきがある場合",
            "considerations": ["リソース効率", "ボトルネックの回避"],
        },
    }

    return {
        "success": True,
        "data": {"strategies": strategies, "total_strategies": len(strategies)},
        "message": "Available assignment strategies retrieved successfully",
    }
