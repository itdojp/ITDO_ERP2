"""Report service for Phase 7 analytics functionality."""

import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from app.models.analytics import (
    Chart,
    ExecutionStatus,
    Report,
    ReportExecution,
    ReportSchedule,
)
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
)


class ReportService:
    """Service for report management and execution operations."""

    def __init__(self, db: Session) -> dict:
        self.db = db

    async def create_report(self, report_data: ReportCreate) -> Dict[str, Any]:
        """Create a new report definition."""
        report = Report(
            name=report_data.name,
            description=report_data.description,
            organization_id=report_data.organization_id,
            category=report_data.category,
            query_config=report_data.query_config,
            visualization_config=report_data.visualization_config,
            parameters_schema=report_data.parameters_schema,
            created_by=report_data.created_by,
            is_active=report_data.is_active,
            is_public=report_data.is_public,
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        return self._report_to_dict(report)

    async def get_reports(
        self,
        organization_id: Optional[int] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get list of reports with filtering."""
        query = self.db.query(Report).filter(not Report.is_deleted)

        if organization_id:
            query = query.filter(Report.organization_id == organization_id)

        if category:
            query = query.filter(Report.category == category)

        if is_active is not None:
            query = query.filter(Report.is_active == is_active)

        reports = query.offset(skip).limit(limit).all()
        return [self._report_to_dict(r) for r in reports]

    async def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        report = (
            self.db.query(Report)
            .filter(and_(Report.id == report_id, not Report.is_deleted))
            .first()
        )
        return self._report_to_dict(report) if report else None

    async def update_report(
        self, report_id: int, report_data: ReportUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update report definition."""
        report = (
            self.db.query(Report)
            .filter(and_(Report.id == report_id, not Report.is_deleted))
            .first()
        )

        if not report:
            return None

        for field, value in report_data.dict(exclude_unset=True).items():
            setattr(report, field, value)

        report.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(report)

        return self._report_to_dict(report)

    async def delete_report(self, report_id: int) -> bool:
        """Soft delete report."""
        report = (
            self.db.query(Report)
            .filter(and_(Report.id == report_id, not Report.is_deleted))
            .first()
        )

        if not report:
            return False

        report.is_deleted = True
        report.deleted_at = datetime.utcnow()
        self.db.commit()

        return True

    async def execute_report(
        self,
        report_id: int,
        parameters: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Dict[str, Any]:
        """Execute a report with optional parameters."""
        report = (
            self.db.query(Report)
            .filter(and_(Report.id == report_id, not Report.is_deleted))
            .first()
        )

        if not report:
            raise ValueError("Report not found")

        if not report.is_active:
            raise ValueError("Report is not active")

        execution = ReportExecution(
            report_id=report_id,
            parameters=parameters or {},
            status=ExecutionStatus.PENDING,
            organization_id=report.organization_id,
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # Execute report in background if available
        if background_tasks:
            background_tasks.add_task(self._execute_report_background, execution.id)
        else:
            # Execute synchronously for immediate results
            await self._execute_report_sync(execution.id)

        return self._execution_to_dict(execution)

    async def _execute_report_sync(self, execution_id: int) -> None:
        """Execute report synchronously."""
        execution = self.db.query(ReportExecution).get(execution_id)
        if not execution:
            return

        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            self.db.commit()

            # Get report and execute query
            report = self.db.query(Report).get(execution.report_id)
            if not report:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Report not found"
                self.db.commit()
                return

            # Execute the actual query based on query_config
            data = await self._execute_query(report, execution.parameters)

            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.result_data = data
            execution.row_count = len(data.get("rows", []))

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

        self.db.commit()

    async def _execute_report_background(self, execution_id: int) -> None:
        """Execute report in background task."""
        await self._execute_report_sync(execution_id)

    async def _execute_query(
        self, report: Report, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual database query for report."""
        query_config = report.query_config

        if query_config.get("type") == "sql":
            # Execute raw SQL query
            sql_query = query_config.get("query", "")

            # Replace parameters in query (basic implementation)
            for key, value in parameters.items():
                sql_query = sql_query.replace(f":{key}", str(value))

            result = self.db.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()

            return {
                "columns": list(columns),
                "rows": [dict(zip(columns, row)) for row in rows],
                "metadata": {
                    "query_type": "sql",
                    "execution_time": datetime.utcnow().isoformat(),
                    "row_count": len(rows),
                },
            }

        elif query_config.get("type") == "model":
            # Execute model-based query (placeholder)
            model_name = query_config.get("model")
            filters = query_config.get("filters", {})

            # Apply parameters to filters
            for key, value in parameters.items():
                if key in filters:
                    filters[key] = value

            return {
                "columns": ["id", "name", "value", "created_at"],
                "rows": [
                    {
                        "id": 1,
                        "name": "Sample Data",
                        "value": 100,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": 2,
                        "name": "Test Record",
                        "value": 250,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                ],
                "metadata": {
                    "query_type": "model",
                    "model": model_name,
                    "filters": filters,
                    "row_count": 2,
                },
            }

        else:
            raise ValueError(f"Unsupported query type: {query_config.get('type')}")

    async def get_report_executions(
        self,
        report_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get report execution history."""
        query = self.db.query(ReportExecution).filter(
            ReportExecution.report_id == report_id
        )

        if status:
            query = query.filter(ReportExecution.status == status)

        executions = (
            query.order_by(ReportExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._execution_to_dict(e) for e in executions]

    async def get_report_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """Get report execution by ID."""
        execution = self.db.query(ReportExecution).get(execution_id)
        return self._execution_to_dict(execution) if execution else None

    async def get_report_data(
        self, execution_id: int, format: str
    ) -> Optional[Dict[str, Any]]:
        """Get report execution data in specified format."""
        execution = self.db.query(ReportExecution).get(execution_id)
        if not execution or execution.status != ExecutionStatus.COMPLETED:
            return None

        data = execution.result_data

        if format == "json":
            return {
                "format": "json",
                "data": data,
                "execution_id": execution_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        elif format == "csv":
            # Convert to CSV format
            if data and "rows" in data:
                df = pd.DataFrame(data["rows"])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)

                return {
                    "format": "csv",
                    "data": csv_buffer.getvalue(),
                    "execution_id": execution_id,
                    "generated_at": datetime.utcnow().isoformat(),
                }

        elif format == "excel":
            # Convert to Excel format (placeholder)
            return {
                "format": "excel",
                "data": "Excel format not yet implemented",
                "execution_id": execution_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        return None

    async def download_report(self, execution_id: int, format: str) -> dict:
        """Download report in specified format."""
        execution = self.db.query(ReportExecution).get(execution_id)
        if not execution or execution.status != ExecutionStatus.COMPLETED:
            return None

        data = execution.result_data
        report_name = (
            f"report_{execution_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        if format == "csv" and data and "rows" in data:
            df = pd.DataFrame(data["rows"])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            return StreamingResponse(
                io.BytesIO(csv_buffer.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={report_name}.csv"
                },
            )

        # Placeholder for other formats
        return None

    async def get_report_templates(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available report templates."""
        templates = [
            {
                "id": "financial_summary",
                "name": "Financial Summary Report",
                "category": "financial",
                "description": "Summary of financial data with key metrics",
                "parameters": ["start_date", "end_date", "organization_id"],
            },
            {
                "id": "user_activity",
                "name": "User Activity Report",
                "category": "analytics",
                "description": "User engagement and activity metrics",
                "parameters": ["date_range", "user_group"],
            },
            {
                "id": "workflow_performance",
                "name": "Workflow Performance Report",
                "category": "operations",
                "description": "Workflow completion and efficiency metrics",
                "parameters": ["workflow_id", "time_period"],
            },
        ]

        if category:
            templates = [t for t in templates if t.get("category") == category]

        return templates

    async def get_report_categories(self) -> List[Dict[str, Any]]:
        """Get available report categories."""
        return [
            {"id": "financial", "name": "Financial Reports", "icon": "chart-line"},
            {"id": "analytics", "name": "Analytics Reports", "icon": "chart-bar"},
            {"id": "operations", "name": "Operations Reports", "icon": "cog"},
            {"id": "crm", "name": "CRM Reports", "icon": "users"},
            {"id": "workflow", "name": "Workflow Reports", "icon": "flow-chart"},
        ]

    async def schedule_report(
        self, report_id: int, schedule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule a report for automatic execution."""
        schedule = ReportSchedule(
            report_id=report_id,
            cron_expression=schedule_config.get("cron_expression"),
            parameters=schedule_config.get("parameters", {}),
            is_active=schedule_config.get("is_active", True),
            created_by=schedule_config.get("created_by"),
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        return self._schedule_to_dict(schedule)

    async def get_report_schedules(self, report_id: int) -> List[Dict[str, Any]]:
        """Get scheduled executions for a report."""
        schedules = (
            self.db.query(ReportSchedule)
            .filter(
                and_(
                    ReportSchedule.report_id == report_id,
                    not ReportSchedule.is_deleted,
                )
            )
            .all()
        )
        return [self._schedule_to_dict(s) for s in schedules]

    async def cancel_report_schedule(self, schedule_id: int) -> bool:
        """Cancel a scheduled report."""
        schedule = (
            self.db.query(ReportSchedule)
            .filter(
                and_(ReportSchedule.id == schedule_id, not ReportSchedule.is_deleted)
            )
            .first()
        )

        if not schedule:
            return False

        schedule.is_deleted = True
        schedule.deleted_at = datetime.utcnow()
        self.db.commit()

        return True

    async def get_report_analytics(
        self,
        report_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get report usage and performance analytics."""
        query = self.db.query(ReportExecution).filter(
            ReportExecution.report_id == report_id
        )

        if start_date:
            query = query.filter(ReportExecution.created_at >= start_date)

        if end_date:
            query = query.filter(ReportExecution.created_at <= end_date)

        executions = query.all()

        total_executions = len(executions)
        successful_executions = len(
            [e for e in executions if e.status == ExecutionStatus.COMPLETED]
        )
        avg_execution_time = self._calculate_avg_execution_time(executions)

        return {
            "report_id": report_id,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions
            if total_executions > 0
            else 0,
            "average_execution_time_seconds": avg_execution_time,
            "status_breakdown": self._get_execution_status_breakdown(executions),
            "usage_trend": self._get_usage_trend(executions),
        }

    async def get_system_performance(self) -> Dict[str, Any]:
        """Get overall reporting system performance metrics."""
        # Get recent executions (last 24 hours)
        since = datetime.utcnow() - timedelta(hours=24)
        recent_executions = (
            self.db.query(ReportExecution)
            .filter(ReportExecution.created_at >= since)
            .all()
        )

        total_reports = self.db.query(Report).filter(not Report.is_deleted).count()
        active_reports = (
            self.db.query(Report)
            .filter(and_(not Report.is_deleted, Report.is_active))
            .count()
        )

        return {
            "system_status": "healthy",
            "total_reports": total_reports,
            "active_reports": active_reports,
            "executions_24h": len(recent_executions),
            "success_rate_24h": len(
                [e for e in recent_executions if e.status == ExecutionStatus.COMPLETED]
            )
            / len(recent_executions)
            if recent_executions
            else 0,
            "average_execution_time": self._calculate_avg_execution_time(
                recent_executions
            ),
            "peak_usage_hours": self._get_peak_usage_hours(recent_executions),
        }

    async def get_realtime_report_data(
        self, report_id: int, refresh_interval: int
    ) -> Dict[str, Any]:
        """Get real-time report data for dashboard updates."""
        # Get latest execution for the report
        latest_execution = (
            self.db.query(ReportExecution)
            .filter(
                and_(
                    ReportExecution.report_id == report_id,
                    ReportExecution.status == ExecutionStatus.COMPLETED,
                )
            )
            .order_by(ReportExecution.completed_at.desc())
            .first()
        )

        if not latest_execution:
            return {"status": "no_data", "message": "No completed executions found"}

        # Check if data is fresh enough
        age_minutes = (
            datetime.utcnow() - latest_execution.completed_at
        ).total_seconds() / 60
        is_fresh = age_minutes <= refresh_interval

        return {
            "status": "success",
            "data": latest_execution.result_data,
            "execution_id": latest_execution.id,
            "last_updated": latest_execution.completed_at.isoformat(),
            "age_minutes": age_minutes,
            "is_fresh": is_fresh,
            "refresh_interval": refresh_interval,
        }

    async def get_report_charts(self, report_id: int) -> List[Dict[str, Any]]:
        """Get chart configurations for report visualization."""
        charts = self.db.query(Chart).filter(Chart.report_id == report_id).all()
        return [self._chart_to_dict(c) for c in charts]

    async def create_report_chart(
        self, report_id: int, chart_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new chart for report visualization."""
        chart = Chart(
            report_id=report_id,
            chart_type=chart_config.get("chart_type"),
            title=chart_config.get("title"),
            config=chart_config.get("config", {}),
            position_x=chart_config.get("position_x", 0),
            position_y=chart_config.get("position_y", 0),
            width=chart_config.get("width", 400),
            height=chart_config.get("height", 300),
        )

        self.db.add(chart)
        self.db.commit()
        self.db.refresh(chart)

        return self._chart_to_dict(chart)

    def _calculate_avg_execution_time(self, executions: List[ReportExecution]) -> float:
        """Calculate average execution time in seconds."""
        completed = [e for e in executions if e.completed_at and e.started_at]

        if not completed:
            return 0.0

        total_seconds = sum(
            (e.completed_at - e.started_at).total_seconds() for e in completed
        )

        return total_seconds / len(completed)

    def _get_execution_status_breakdown(
        self, executions: List[ReportExecution]
    ) -> Dict[str, int]:
        """Get status breakdown for executions."""
        breakdown = {}
        for execution in executions:
            status = execution.status
            breakdown[status] = breakdown.get(status, 0) + 1

        return breakdown

    def _get_usage_trend(
        self, executions: List[ReportExecution]
    ) -> List[Dict[str, Any]]:
        """Get usage trend data."""
        # Group by date and count executions
        trend_data = {}
        for execution in executions:
            date = execution.created_at.date().isoformat()
            trend_data[date] = trend_data.get(date, 0) + 1

        return [
            {"date": date, "count": count} for date, count in sorted(trend_data.items())
        ]

    def _get_peak_usage_hours(self, executions: List[ReportExecution]) -> List[int]:
        """Get peak usage hours."""
        hour_counts = {}
        for execution in executions:
            hour = execution.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Return top 3 hours by usage
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    def _report_to_dict(self, report: Report) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "id": report.id,
            "name": report.name,
            "description": report.description,
            "organization_id": report.organization_id,
            "category": report.category,
            "status": report.status,
            "is_active": report.is_active,
            "is_public": report.is_public,
            "query_config": report.query_config,
            "visualization_config": report.visualization_config,
            "parameters_schema": report.parameters_schema,
            "created_by": report.created_by,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
        }

    def _execution_to_dict(self, execution: ReportExecution) -> Dict[str, Any]:
        """Convert report execution to dictionary."""
        return {
            "id": execution.id,
            "report_id": execution.report_id,
            "status": execution.status,
            "parameters": execution.parameters,
            "organization_id": execution.organization_id,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "row_count": execution.row_count,
            "error_message": execution.error_message,
            "result_data": execution.result_data,
            "created_at": execution.created_at,
        }

    def _schedule_to_dict(self, schedule: ReportSchedule) -> Dict[str, Any]:
        """Convert report schedule to dictionary."""
        return {
            "id": schedule.id,
            "report_id": schedule.report_id,
            "cron_expression": schedule.cron_expression,
            "parameters": schedule.parameters,
            "is_active": schedule.is_active,
            "next_run": schedule.next_run,
            "last_run": schedule.last_run,
            "created_by": schedule.created_by,
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at,
        }

    def _chart_to_dict(self, chart: Chart) -> Dict[str, Any]:
        """Convert chart to dictionary."""
        return {
            "id": chart.id,
            "report_id": chart.report_id,
            "chart_type": chart.chart_type,
            "title": chart.title,
            "config": chart.config,
            "position_x": chart.position_x,
            "position_y": chart.position_y,
            "width": chart.width,
            "height": chart.height,
            "created_at": chart.created_at,
            "updated_at": chart.updated_at,
        }
