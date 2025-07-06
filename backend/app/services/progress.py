"""Progress service for progress calculations and reports."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import csv
import io

from app.core.exceptions import NotFound, PermissionDenied


class ProgressService:
    """Service for progress management functionality."""

    def __init__(self):
        """Initialize progress service."""
        pass

    def calculate_task_completion_rate(
        self,
        project_id: int,
        db: Session
    ) -> float:
        """Calculate task completion rate for a project.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            Task completion rate (0.0 to 100.0)
        """
        # Mock implementation - would query tasks for the project
        total_tasks = 20
        completed_tasks = 15
        
        if total_tasks == 0:
            return 0.0
        
        completion_rate = (completed_tasks / total_tasks) * 100.0
        return round(completion_rate, 2)

    def calculate_effort_completion_rate(
        self,
        project_id: int,
        db: Session
    ) -> float:
        """Calculate effort completion rate for a project.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            Effort completion rate (0.0 to 100.0)
        """
        # Mock implementation - would query task hours for the project
        total_hours = 100
        completed_hours = 60
        
        if total_hours == 0:
            return 0.0
        
        completion_rate = (completed_hours / total_hours) * 100.0
        return round(completion_rate, 2)

    def calculate_duration_completion_rate(
        self,
        project_id: int,
        db: Session
    ) -> float:
        """Calculate duration completion rate for a project.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            Duration completion rate (0.0 to 100.0)
        """
        # Mock implementation - would calculate based on project dates
        start_date = date(2025, 6, 1)
        end_date = date(2025, 8, 31)
        current_date = date.today()
        
        if current_date < start_date:
            return 0.0
        
        if current_date >= end_date:
            return 100.0
        
        total_days = (end_date - start_date).days
        elapsed_days = (current_date - start_date).days
        
        if total_days == 0:
            return 100.0
        
        completion_rate = (elapsed_days / total_days) * 100.0
        return round(min(100.0, max(0.0, completion_rate)), 2)

    def detect_overdue_projects(
        self,
        organization_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Detect overdue projects.
        
        Args:
            organization_id: Organization ID
            db: Database session
            
        Returns:
            List of overdue projects
        """
        # Mock implementation - would query overdue projects from database
        current_date = date.today()
        return [
            {
                "project_id": 3,
                "project_name": "遅延プロジェクト",
                "end_date": "2025-06-30",
                "days_overdue": (current_date - date(2025, 6, 30)).days
            }
        ]

    def detect_overdue_tasks(
        self,
        organization_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Detect overdue tasks.
        
        Args:
            organization_id: Organization ID
            db: Database session
            
        Returns:
            List of overdue tasks
        """
        # Mock implementation - would query overdue tasks from database
        current_date = date.today()
        return [
            {
                "task_id": 25,
                "task_title": "遅延タスク",
                "project_name": "プロジェクトB",
                "end_date": "2025-07-03",
                "days_overdue": max(0, (current_date - date(2025, 7, 3)).days)
            }
        ]

    def detect_upcoming_deadlines(
        self,
        organization_id: int,
        db: Session,
        days_ahead: int = 3
    ) -> List[Dict[str, Any]]:
        """Detect upcoming deadlines.
        
        Args:
            organization_id: Organization ID
            db: Database session
            days_ahead: Days to look ahead for deadlines
            
        Returns:
            List of upcoming deadlines
        """
        # Mock implementation - would query upcoming deadlines
        future_date = date.today() + timedelta(days=2)
        return [
            {
                "type": "project",
                "id": 3,
                "name": "期限間近プロジェクト",
                "end_date": future_date.isoformat(),
                "days_remaining": 2
            }
        ]

    def generate_progress_report(
        self,
        project_id: int,
        db: Session,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Generate progress report.
        
        Args:
            project_id: Project ID
            db: Database session
            format: Report format (json/csv)
            
        Returns:
            Progress report data
        """
        # Generate base report data
        report_data = {
            "project_id": project_id,
            "project_name": "テストプロジェクト",
            "completion_percentage": 75.0,
            "total_tasks": 20,
            "completed_tasks": 15,
            "timeline": {
                "start_date": "2025-06-01",
                "end_date": "2025-08-31",
                "days_elapsed": 35,
                "days_remaining": 56,
                "is_on_track": True
            }
        }
        
        if format == "csv":
            # Convert to CSV format
            csv_data = self._convert_to_csv(report_data)
            return {"csv_data": csv_data, "format": "csv"}
        
        return report_data
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert report data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ["project_id", "project_name", "completion_percentage", 
                  "total_tasks", "completed_tasks", "start_date", "end_date"]
        writer.writerow(headers)
        
        # Write data
        row = [
            data["project_id"],
            data["project_name"],
            data["completion_percentage"],
            data["total_tasks"],
            data["completed_tasks"],
            data["timeline"]["start_date"],
            data["timeline"]["end_date"]
        ]
        writer.writerow(row)
        
        return output.getvalue()