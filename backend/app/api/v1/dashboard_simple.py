"""Simple Dashboard API endpoints for immediate integration."""

from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics")
async def get_simple_metrics() -> Dict:
    """Get basic dashboard metrics."""
    
    return {
        "data": {
            "total_users": 25,
            "active_users": 18,
            "total_organizations": 3,
            "total_departments": 12,
            "total_projects": 8,
            "active_projects": 6,
            "total_tasks": 150,
            "completed_tasks": 95,
            "pending_tasks": 55,
            "task_completion_rate": 63.3
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/system-health")
async def get_simple_system_health() -> Dict:
    """Get system health metrics."""
    
    return {
        "data": {
            "overall_score": 94,
            "uptime_percentage": 99.8,
            "response_time_avg": 145,
            "active_sessions": 18,
            "error_rate": 0.2,
            "last_updated": "2025-07-19T16:20:00Z"
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/user-activity")
async def get_simple_user_activity() -> Dict:
    """Get user activity metrics."""
    
    return {
        "data": {
            "daily_active_users": 5,
            "weekly_active_users": 12,
            "monthly_active_users": 18,
            "new_users_today": 2,
            "new_users_this_week": 5,
            "new_users_this_month": 8,
            "user_growth_rate": 15.3
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/task-analytics")
async def get_simple_task_analytics() -> Dict:
    """Get task analytics."""
    
    return {
        "data": {
            "tasks_created_today": 12,
            "tasks_completed_today": 8,
            "tasks_overdue": 3,
            "avg_completion_time": 4.2,
            "most_active_projects": [
                {"project_id": 1, "project_name": "ERP Migration", "task_count": 45, "completion_rate": 78.2},
                {"project_id": 2, "project_name": "Mobile App", "task_count": 32, "completion_rate": 65.4},
                {"project_id": 3, "project_name": "Data Analytics", "task_count": 28, "completion_rate": 82.1}
            ],
            "task_priority_breakdown": {
                "high": 25,
                "medium": 85,
                "low": 40
            }
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/organization-analytics")
async def get_simple_organization_analytics() -> Dict:
    """Get organization analytics."""
    
    return {
        "data": {
            "most_active_organizations": [
                {
                    "organization_id": 1,
                    "organization_name": "Tech Solutions Inc.",
                    "user_count": 12,
                    "project_count": 4,
                    "task_count": 75,
                    "activity_score": 89
                },
                {
                    "organization_id": 2,
                    "organization_name": "Digital Innovations Ltd.",
                    "user_count": 8,
                    "project_count": 3,
                    "task_count": 48,
                    "activity_score": 76
                }
            ],
            "department_performance": [
                {
                    "department_id": 1,
                    "department_name": "Engineering",
                    "organization_name": "Tech Solutions Inc.",
                    "user_count": 6,
                    "task_completion_rate": 84.2,
                    "avg_response_time": 2.3
                },
                {
                    "department_id": 2,
                    "department_name": "Marketing",
                    "organization_name": "Tech Solutions Inc.",
                    "user_count": 4,
                    "task_completion_rate": 91.7,
                    "avg_response_time": 1.8
                }
            ]
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/timeseries")
async def get_simple_timeseries() -> Dict:
    """Get simple time series data."""
    
    # Generate 30 days of sample data
    import datetime
    from typing import List
    
    data: List[Dict] = []
    base_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    for i in range(30):
        date = base_date + datetime.timedelta(days=i)
        value = 800 + (i * 2) + (i % 7) * 10  # Simple trend with weekly variation
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": value,
            "category": "users"
        })
    
    return {
        "data": data,
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }


@router.get("/")
async def get_dashboard_overview() -> Dict:
    """Get complete dashboard data."""
    
    metrics = await get_simple_metrics()
    system_health = await get_simple_system_health()
    user_activity = await get_simple_user_activity()
    task_analytics = await get_simple_task_analytics()
    organization_analytics = await get_simple_organization_analytics()
    
    return {
        "data": {
            "metrics": metrics["data"],
            "system_health": system_health["data"],
            "user_activity": user_activity["data"],
            "task_analytics": task_analytics["data"],
            "organization_analytics": organization_analytics["data"],
            "timestamp": "2025-07-19T16:20:00Z"
        },
        "success": True,
        "timestamp": "2025-07-19T16:20:00Z"
    }