"""
Analytics System CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for analytics system including:
- Multi-Dimensional Analytics & KPI Tracking
- Real-Time Data Processing & Aggregation
- Advanced Business Intelligence & Reporting
- Performance Metrics & Benchmarking
- Predictive Analytics & Forecasting
- Custom Dashboard & Visualization
- Data Mining & Machine Learning Integration
- Executive Analytics & Strategic Insights
- Operational Analytics & Process Optimization
- Compliance Analytics & Risk Management
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session, joinedload
import json
import statistics
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd

from app.models.analytics_extended import (
    AnalyticsDataSource,
    AnalyticsMetric,
    AnalyticsDataPoint,
    AnalyticsDashboard,
    AnalyticsReport,
    AnalyticsReportExecution,
    AnalyticsAlert,
    AnalyticsPrediction,
    AnalyticsInsight,
    AnalyticsAuditLog,
    AnalyticsType,
    MetricType,
    AggregationType,
    PeriodType,
    DashboardType,
    ReportStatus,
    AlertPriority,
)


class AnalyticsService:
    """Service class for analytics system operations."""

    # =============================================================================
    # Data Source Management
    # =============================================================================

    async def create_data_source(
        self, 
        db: Session, 
        data_source_data: dict
    ) -> AnalyticsDataSource:
        """Create a new analytics data source with connection configuration."""
        
        data_source = AnalyticsDataSource(
            organization_id=data_source_data["organization_id"],
            name=data_source_data["name"],
            code=data_source_data["code"],
            description=data_source_data.get("description"),
            source_type=data_source_data["source_type"],
            connection_string=data_source_data.get("connection_string"),
            connection_config=data_source_data.get("connection_config", {}),
            authentication_config=data_source_data.get("authentication_config", {}),
            schema_definition=data_source_data.get("schema_definition", {}),
            table_mappings=data_source_data.get("table_mappings", {}),
            field_mappings=data_source_data.get("field_mappings", {}),
            transformation_rules=data_source_data.get("transformation_rules", {}),
            sync_frequency=data_source_data.get("sync_frequency", "daily"),
            sync_schedule=data_source_data.get("sync_schedule"),
            validation_rules=data_source_data.get("validation_rules", {}),
            cleansing_rules=data_source_data.get("cleansing_rules", {}),
            is_realtime=data_source_data.get("is_realtime", False),
            tags=data_source_data.get("tags", []),
            analytics_metadata=data_source_data.get("metadata", {}),
            custom_fields=data_source_data.get("custom_fields", {}),
            created_by=data_source_data["created_by"]
        )
        
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        
        await self._log_analytics_action(
            db, "create_data_source", "data_source", data_source.id,
            data_source_data["created_by"], {"name": data_source.name}
        )
        
        return data_source

    async def test_data_source_connection(
        self, 
        db: Session, 
        data_source_id: str
    ) -> Dict[str, Any]:
        """Test data source connection and return health status."""
        
        data_source = db.query(AnalyticsDataSource).filter(
            AnalyticsDataSource.id == data_source_id
        ).first()
        
        if not data_source:
            return {"status": "error", "message": "Data source not found"}
        
        try:
            # Simulate connection test based on source type
            connection_result = await self._test_connection_by_type(data_source)
            
            # Update health status
            data_source.health_status = "healthy" if connection_result["success"] else "unhealthy"
            data_source.last_error = None if connection_result["success"] else connection_result.get("error")
            
            db.commit()
            
            return {
                "status": "success" if connection_result["success"] else "error",
                "connection_time_ms": connection_result.get("connection_time_ms", 0),
                "message": connection_result.get("message", ""),
                "details": connection_result.get("details", {})
            }
            
        except Exception as e:
            data_source.health_status = "unhealthy"
            data_source.last_error = str(e)
            data_source.error_count += 1
            db.commit()
            
            return {"status": "error", "message": str(e)}

    async def sync_data_source(
        self, 
        db: Session, 
        data_source_id: str
    ) -> Dict[str, Any]:
        """Sync data from data source and update metrics."""
        
        data_source = db.query(AnalyticsDataSource).filter(
            AnalyticsDataSource.id == data_source_id
        ).first()
        
        if not data_source:
            return {"status": "error", "message": "Data source not found"}
        
        sync_start = datetime.utcnow()
        
        try:
            # Perform data sync based on source type
            sync_result = await self._sync_data_by_type(db, data_source)
            
            # Update sync status
            data_source.last_sync_at = sync_start
            data_source.next_sync_at = await self._calculate_next_sync(data_source)
            data_source.records_processed += sync_result.get("records_processed", 0)
            
            processing_time = (datetime.utcnow() - sync_start).total_seconds()
            data_source.processing_time_avg = (
                (data_source.processing_time_avg or 0 + processing_time) / 2
            )
            
            db.commit()
            
            return {
                "status": "success",
                "records_processed": sync_result.get("records_processed", 0),
                "processing_time_seconds": processing_time,
                "metrics_updated": sync_result.get("metrics_updated", 0)
            }
            
        except Exception as e:
            data_source.last_error = str(e)
            data_source.error_count += 1
            db.commit()
            
            return {"status": "error", "message": str(e)}

    async def _test_connection_by_type(self, data_source: AnalyticsDataSource) -> Dict[str, Any]:
        """Test connection based on data source type."""
        
        if data_source.source_type == "database":
            return await self._test_database_connection(data_source)
        elif data_source.source_type == "api":
            return await self._test_api_connection(data_source)
        elif data_source.source_type == "file":
            return await self._test_file_connection(data_source)
        else:
            return {"success": True, "message": "Mock connection test successful"}

    async def _sync_data_by_type(
        self, 
        db: Session, 
        data_source: AnalyticsDataSource
    ) -> Dict[str, Any]:
        """Sync data based on data source type."""
        
        # Mock data sync - in real implementation, this would connect to actual data sources
        records_processed = np.random.randint(100, 1000)
        metrics_updated = np.random.randint(5, 20)
        
        return {
            "records_processed": records_processed,
            "metrics_updated": metrics_updated
        }

    # =============================================================================
    # Metric Management
    # =============================================================================

    async def create_metric(
        self, 
        db: Session, 
        metric_data: dict
    ) -> AnalyticsMetric:
        """Create a new analytics metric with calculation configuration."""
        
        metric = AnalyticsMetric(
            organization_id=metric_data["organization_id"],
            data_source_id=metric_data.get("data_source_id"),
            name=metric_data["name"],
            code=metric_data["code"],
            display_name=metric_data.get("display_name"),
            description=metric_data.get("description"),
            category=metric_data.get("category"),
            metric_type=metric_data["metric_type"],
            analytics_type=metric_data["analytics_type"],
            aggregation_type=metric_data["aggregation_type"],
            calculation_formula=metric_data["calculation_formula"],
            calculation_fields=metric_data.get("calculation_fields", []),
            calculation_filters=metric_data.get("calculation_filters", {}),
            calculation_parameters=metric_data.get("calculation_parameters", {}),
            unit=metric_data.get("unit"),
            format_pattern=metric_data.get("format_pattern"),
            decimal_places=metric_data.get("decimal_places", 2),
            multiplier=metric_data.get("multiplier", 1),
            target_value=metric_data.get("target_value"),
            min_threshold=metric_data.get("min_threshold"),
            max_threshold=metric_data.get("max_threshold"),
            warning_threshold=metric_data.get("warning_threshold"),
            critical_threshold=metric_data.get("critical_threshold"),
            benchmark_value=metric_data.get("benchmark_value"),
            benchmark_source=metric_data.get("benchmark_source"),
            industry_average=metric_data.get("industry_average"),
            calculation_frequency=metric_data.get("calculation_frequency", "daily"),
            calculation_schedule=metric_data.get("calculation_schedule"),
            chart_type=metric_data.get("chart_type", "line"),
            color_scheme=metric_data.get("color_scheme"),
            display_order=metric_data.get("display_order", 0),
            access_level=metric_data.get("access_level", "organization"),
            allowed_roles=metric_data.get("allowed_roles", []),
            allowed_users=metric_data.get("allowed_users", []),
            tags=metric_data.get("tags", []),
            analytics_metadata=metric_data.get("metadata", {}),
            created_by=metric_data["created_by"]
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        # Schedule first calculation
        await self._schedule_metric_calculation(db, metric.id)
        
        await self._log_analytics_action(
            db, "create_metric", "metric", metric.id,
            metric_data["created_by"], {"name": metric.name, "type": metric.metric_type.value}
        )
        
        return metric

    async def calculate_metric_value(
        self, 
        db: Session, 
        metric_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate metric value for specified period."""
        
        metric = db.query(AnalyticsMetric).filter(
            AnalyticsMetric.id == metric_id
        ).first()
        
        if not metric:
            return {"status": "error", "message": "Metric not found"}
        
        try:
            # Default period to last 24 hours if not specified
            if not period_end:
                period_end = datetime.utcnow()
            if not period_start:
                period_start = period_end - timedelta(days=1)
            
            # Execute calculation based on formula
            calculation_result = await self._execute_metric_calculation(
                db, metric, period_start, period_end
            )
            
            # Store data point
            data_point = AnalyticsDataPoint(
                organization_id=metric.organization_id,
                metric_id=metric_id,
                timestamp=datetime.utcnow(),
                period_type=PeriodType.DAY,
                period_start=period_start,
                period_end=period_end,
                value=calculation_result["value"],
                raw_value=calculation_result.get("raw_value"),
                calculated_value=calculation_result["value"],
                count=calculation_result.get("count"),
                sum_value=calculation_result.get("sum_value"),
                avg_value=calculation_result.get("avg_value"),
                min_value=calculation_result.get("min_value"),
                max_value=calculation_result.get("max_value"),
                median_value=calculation_result.get("median_value"),
                std_deviation=calculation_result.get("std_deviation"),
                dimensions=calculation_result.get("dimensions", {}),
                quality_score=calculation_result.get("quality_score", Decimal("1.0")),
                source_query=calculation_result.get("source_query"),
                calculation_metadata=calculation_result.get("metadata", {})
            )
            
            db.add(data_point)
            
            # Update metric current value and trend
            await self._update_metric_trend(db, metric, calculation_result["value"])
            
            metric.last_calculated_at = datetime.utcnow()
            metric.next_calculation_at = await self._calculate_next_calculation(metric)
            
            db.commit()
            
            # Check for alerts
            await self._check_metric_alerts(db, metric, calculation_result["value"])
            
            return {
                "status": "success",
                "metric_id": metric_id,
                "value": float(calculation_result["value"]),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "quality_score": float(calculation_result.get("quality_score", 1.0)),
                "calculation_metadata": calculation_result.get("metadata", {})
            }
            
        except Exception as e:
            await self._log_analytics_action(
                db, "calculate_metric_error", "metric", metric_id,
                None, {"error": str(e)}
            )
            return {"status": "error", "message": str(e)}

    async def _execute_metric_calculation(
        self,
        db: Session,
        metric: AnalyticsMetric,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Execute metric calculation based on formula and configuration."""
        
        # Mock calculation - in real implementation, this would execute actual SQL queries
        # or call external APIs based on the data source and formula
        
        base_value = np.random.uniform(100, 1000)
        
        if metric.aggregation_type == AggregationType.SUM:
            value = base_value * np.random.uniform(1, 10)
        elif metric.aggregation_type == AggregationType.COUNT:
            value = np.random.randint(10, 100)
        elif metric.aggregation_type == AggregationType.AVERAGE:
            value = base_value
        elif metric.aggregation_type == AggregationType.MIN:
            value = base_value * 0.5
        elif metric.aggregation_type == AggregationType.MAX:
            value = base_value * 2
        else:
            value = base_value
        
        # Apply multiplier
        value = value * float(metric.multiplier or 1)
        
        return {
            "value": Decimal(str(round(value, metric.decimal_places or 2))),
            "raw_value": Decimal(str(round(base_value, 2))),
            "count": np.random.randint(10, 1000),
            "sum_value": Decimal(str(round(value * 10, 2))),
            "avg_value": Decimal(str(round(value, 2))),
            "min_value": Decimal(str(round(value * 0.8, 2))),
            "max_value": Decimal(str(round(value * 1.2, 2))),
            "median_value": Decimal(str(round(value, 2))),
            "std_deviation": Decimal(str(round(value * 0.1, 2))),
            "quality_score": Decimal("0.95"),
            "source_query": f"SELECT {metric.calculation_formula} FROM data WHERE period BETWEEN '{period_start}' AND '{period_end}'",
            "metadata": {
                "calculation_time_ms": np.random.randint(50, 500),
                "data_points_analyzed": np.random.randint(100, 10000)
            }
        }

    async def get_metric_trends(
        self,
        db: Session,
        metric_id: str,
        period_type: PeriodType = PeriodType.DAY,
        period_count: int = 30
    ) -> List[Dict[str, Any]]:
        """Get metric trend data for specified periods."""
        
        data_points = db.query(AnalyticsDataPoint).filter(
            AnalyticsDataPoint.metric_id == metric_id,
            AnalyticsDataPoint.period_type == period_type
        ).order_by(desc(AnalyticsDataPoint.timestamp)).limit(period_count).all()
        
        trends = []
        for point in reversed(data_points):
            trends.append({
                "timestamp": point.timestamp.isoformat(),
                "period_start": point.period_start.isoformat() if point.period_start else None,
                "period_end": point.period_end.isoformat() if point.period_end else None,
                "value": float(point.value),
                "raw_value": float(point.raw_value) if point.raw_value else None,
                "quality_score": float(point.quality_score) if point.quality_score else None,
                "is_anomaly": point.is_anomaly
            })
        
        return trends

    # =============================================================================
    # Dashboard Management
    # =============================================================================

    async def create_dashboard(
        self, 
        db: Session, 
        dashboard_data: dict
    ) -> AnalyticsDashboard:
        """Create a new analytics dashboard with widget configuration."""
        
        # Generate unique slug
        slug = dashboard_data.get("slug") or self._generate_dashboard_slug(dashboard_data["name"])
        
        dashboard = AnalyticsDashboard(
            organization_id=dashboard_data["organization_id"],
            name=dashboard_data["name"],
            slug=slug,
            description=dashboard_data.get("description"),
            dashboard_type=dashboard_data["dashboard_type"],
            layout_config=dashboard_data.get("layout_config", {}),
            grid_config=dashboard_data.get("grid_config", {}),
            responsive_config=dashboard_data.get("responsive_config", {}),
            widgets=dashboard_data.get("widgets", []),
            widget_positions=dashboard_data.get("widget_positions", {}),
            widget_settings=dashboard_data.get("widget_settings", {}),
            global_filters=dashboard_data.get("global_filters", {}),
            default_period=dashboard_data.get("default_period", "last_30_days"),
            auto_refresh=dashboard_data.get("auto_refresh", True),
            refresh_interval=dashboard_data.get("refresh_interval", 300),
            is_public=dashboard_data.get("is_public", False),
            is_shared=dashboard_data.get("is_shared", False),
            access_level=dashboard_data.get("access_level", "private"),
            allowed_roles=dashboard_data.get("allowed_roles", []),
            allowed_users=dashboard_data.get("allowed_users", []),
            theme=dashboard_data.get("theme", "default"),
            color_scheme=dashboard_data.get("color_scheme"),
            custom_css=dashboard_data.get("custom_css"),
            export_formats=dashboard_data.get("export_formats", ["pdf", "png", "excel"]),
            email_recipients=dashboard_data.get("email_recipients", []),
            email_schedule=dashboard_data.get("email_schedule"),
            tags=dashboard_data.get("tags", []),
            analytics_metadata=dashboard_data.get("metadata", {}),
            created_by=dashboard_data["created_by"]
        )
        
        # Generate share token if shared
        if dashboard.is_shared:
            dashboard.share_token = str(uuid.uuid4())
        
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        
        await self._log_analytics_action(
            db, "create_dashboard", "dashboard", dashboard.id,
            dashboard_data["created_by"], {"name": dashboard.name, "type": dashboard.dashboard_type.value}
        )
        
        return dashboard

    async def get_dashboard_data(
        self,
        db: Session,
        dashboard_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get dashboard data with all widget information."""
        
        dashboard = db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.id == dashboard_id
        ).first()
        
        if not dashboard:
            return {"status": "error", "message": "Dashboard not found"}
        
        # Update view count
        dashboard.view_count += 1
        dashboard.last_viewed_at = datetime.utcnow()
        db.commit()
        
        # Get widget data
        widget_data = {}
        for widget in dashboard.widgets:
            widget_id = widget.get("id")
            if widget_id:
                widget_data[widget_id] = await self._get_widget_data(
                    db, widget, period_start, period_end, filters
                )
        
        return {
            "status": "success",
            "dashboard": {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "dashboard_type": dashboard.dashboard_type.value,
                "layout_config": dashboard.layout_config,
                "widgets": dashboard.widgets,
                "widget_positions": dashboard.widget_positions,
                "widget_settings": dashboard.widget_settings,
                "global_filters": dashboard.global_filters,
                "theme": dashboard.theme,
                "last_updated": dashboard.updated_at.isoformat() if dashboard.updated_at else None
            },
            "widget_data": widget_data,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None
        }

    async def _get_widget_data(
        self,
        db: Session,
        widget: Dict[str, Any],
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for individual dashboard widget."""
        
        widget_type = widget.get("type", "metric")
        
        if widget_type == "metric":
            return await self._get_metric_widget_data(db, widget, period_start, period_end, filters)
        elif widget_type == "chart":
            return await self._get_chart_widget_data(db, widget, period_start, period_end, filters)
        elif widget_type == "table":
            return await self._get_table_widget_data(db, widget, period_start, period_end, filters)
        elif widget_type == "kpi":
            return await self._get_kpi_widget_data(db, widget, period_start, period_end, filters)
        else:
            return {"type": widget_type, "data": {}, "status": "unknown_widget_type"}

    async def _get_metric_widget_data(
        self,
        db: Session,
        widget: Dict[str, Any],
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for metric widget."""
        
        metric_id = widget.get("metric_id")
        if not metric_id:
            return {"type": "metric", "data": {}, "status": "missing_metric_id"}
        
        metric = db.query(AnalyticsMetric).filter(
            AnalyticsMetric.id == metric_id
        ).first()
        
        if not metric:
            return {"type": "metric", "data": {}, "status": "metric_not_found"}
        
        # Get latest value
        latest_point = db.query(AnalyticsDataPoint).filter(
            AnalyticsDataPoint.metric_id == metric_id
        ).order_by(desc(AnalyticsDataPoint.timestamp)).first()
        
        return {
            "type": "metric",
            "data": {
                "metric": {
                    "id": metric.id,
                    "name": metric.name,
                    "display_name": metric.display_name or metric.name,
                    "unit": metric.unit,
                    "format_pattern": metric.format_pattern
                },
                "current_value": float(latest_point.value) if latest_point else 0,
                "previous_value": float(metric.previous_value) if metric.previous_value else None,
                "trend_direction": metric.trend_direction,
                "trend_percentage": float(metric.trend_percentage) if metric.trend_percentage else None,
                "target_value": float(metric.target_value) if metric.target_value else None,
                "last_updated": latest_point.timestamp.isoformat() if latest_point else None
            },
            "status": "success"
        }

    # =============================================================================
    # Report Management
    # =============================================================================

    async def create_report(
        self, 
        db: Session, 
        report_data: dict
    ) -> AnalyticsReport:
        """Create a new analytics report with scheduling configuration."""
        
        report = AnalyticsReport(
            organization_id=report_data["organization_id"],
            name=report_data["name"],
            title=report_data.get("title"),
            description=report_data.get("description"),
            report_type=report_data["report_type"],
            metrics=report_data.get("metrics", []),
            dashboards=report_data.get("dashboards", []),
            data_sources=report_data.get("data_sources", []),
            parameters=report_data.get("parameters", {}),
            filters=report_data.get("filters", {}),
            period_config=report_data.get("period_config", {}),
            is_scheduled=report_data.get("is_scheduled", False),
            schedule_config=report_data.get("schedule_config", {}),
            schedule_cron=report_data.get("schedule_cron"),
            format=report_data.get("format", "pdf"),
            template_id=report_data.get("template_id"),
            output_settings=report_data.get("output_settings", {}),
            recipients=report_data.get("recipients", []),
            delivery_method=report_data.get("delivery_method", "email"),
            delivery_config=report_data.get("delivery_config", {}),
            is_confidential=report_data.get("is_confidential", False),
            access_level=report_data.get("access_level", "organization"),
            allowed_roles=report_data.get("allowed_roles", []),
            allowed_users=report_data.get("allowed_users", []),
            tags=report_data.get("tags", []),
            analytics_metadata=report_data.get("metadata", {}),
            created_by=report_data["created_by"]
        )
        
        # Calculate next run if scheduled
        if report.is_scheduled and report.schedule_cron:
            report.next_run_at = await self._calculate_next_report_run(report.schedule_cron)
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        await self._log_analytics_action(
            db, "create_report", "report", report.id,
            report_data["created_by"], {"name": report.name, "type": report.report_type}
        )
        
        return report

    async def generate_report(
        self, 
        db: Session, 
        report_id: str,
        execution_type: str = "manual",
        triggered_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate report and create execution record."""
        
        report = db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id
        ).first()
        
        if not report:
            return {"status": "error", "message": "Report not found"}
        
        # Create execution record
        execution = AnalyticsReportExecution(
            organization_id=report.organization_id,
            report_id=report_id,
            execution_type=execution_type,
            triggered_by=triggered_by,
            status=ReportStatus.RUNNING,
            started_at=datetime.utcnow(),
            parameters=report.parameters,
            filters=report.filters,
            output_format=report.format
        )
        
        db.add(execution)
        db.commit()
        
        try:
            # Generate report
            generation_result = await self._generate_report_content(db, report, execution)
            
            # Update execution with results
            execution.status = ReportStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            execution.output_path = generation_result.get("output_path")
            execution.output_size_bytes = generation_result.get("output_size_bytes")
            execution.records_processed = generation_result.get("records_processed")
            execution.metrics_calculated = generation_result.get("metrics_calculated")
            execution.charts_generated = generation_result.get("charts_generated")
            
            # Update report statistics
            report.generation_count += 1
            report.last_run_at = execution.completed_at
            report.last_generation_duration = execution.duration_ms
            report.avg_generation_time = (
                (report.avg_generation_time or 0 + execution.duration_ms) // 2
            )
            report.last_output_path = execution.output_path
            report.last_output_size = execution.output_size_bytes
            
            db.commit()
            
            # Send notifications if configured
            if report.recipients:
                await self._send_report_notifications(db, report, execution)
            
            return {
                "status": "success",
                "execution_id": execution.id,
                "output_path": execution.output_path,
                "generation_time_ms": execution.duration_ms,
                "records_processed": execution.records_processed
            }
            
        except Exception as e:
            execution.status = ReportStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)
            
            report.last_error = str(e)
            
            db.commit()
            
            return {"status": "error", "message": str(e), "execution_id": execution.id}

    # =============================================================================
    # Predictive Analytics
    # =============================================================================

    async def create_prediction_model(
        self, 
        db: Session, 
        prediction_data: dict
    ) -> AnalyticsPrediction:
        """Create and train a predictive analytics model."""
        
        prediction = AnalyticsPrediction(
            organization_id=prediction_data["organization_id"],
            metric_id=prediction_data.get("metric_id"),
            name=prediction_data["name"],
            description=prediction_data.get("description"),
            prediction_type=prediction_data["prediction_type"],
            model_type=prediction_data["model_type"],
            model_parameters=prediction_data.get("model_parameters", {}),
            feature_columns=prediction_data.get("feature_columns", []),
            target_column=prediction_data.get("target_column"),
            prediction_horizon=prediction_data["prediction_horizon"],
            prediction_intervals=prediction_data.get("prediction_intervals", []),
            update_frequency=prediction_data.get("update_frequency", "weekly"),
            tags=prediction_data.get("tags", []),
            model_metadata=prediction_data.get("metadata", {}),
            created_by=prediction_data["created_by"]
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        # Train initial model
        await self._train_prediction_model(db, prediction.id)
        
        await self._log_analytics_action(
            db, "create_prediction", "prediction", prediction.id,
            prediction_data["created_by"], {"name": prediction.name, "type": prediction.prediction_type}
        )
        
        return prediction

    async def _train_prediction_model(
        self, 
        db: Session, 
        prediction_id: str
    ) -> Dict[str, Any]:
        """Train prediction model with historical data."""
        
        prediction = db.query(AnalyticsPrediction).filter(
            AnalyticsPrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"status": "error", "message": "Prediction model not found"}
        
        try:
            training_start = datetime.utcnow()
            
            # Get training data (mock implementation)
            training_data = await self._get_prediction_training_data(db, prediction)
            
            # Train model based on type
            if prediction.model_type == "linear_regression":
                model_result = await self._train_linear_regression(training_data, prediction)
            elif prediction.model_type == "arima":
                model_result = await self._train_arima(training_data, prediction)
            else:
                model_result = await self._train_default_model(training_data, prediction)
            
            # Update prediction with results
            prediction.last_trained_at = training_start
            prediction.training_duration = int((datetime.utcnow() - training_start).total_seconds())
            prediction.accuracy_score = model_result.get("accuracy_score")
            prediction.mae_score = model_result.get("mae_score")
            prediction.rmse_score = model_result.get("rmse_score")
            prediction.r2_score = model_result.get("r2_score")
            prediction.model_version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            prediction.training_data_points = model_result.get("data_points", 0)
            
            # Generate and cache predictions
            predictions = await self._generate_predictions(model_result["model"], prediction)
            prediction.cached_predictions = predictions
            prediction.cache_valid_until = datetime.utcnow() + timedelta(
                days=7 if prediction.update_frequency == "weekly" else 1
            )
            
            db.commit()
            
            return {
                "status": "success",
                "accuracy_score": float(prediction.accuracy_score) if prediction.accuracy_score else None,
                "training_duration": prediction.training_duration,
                "data_points": model_result.get("data_points", 0),
                "predictions_generated": len(predictions)
            }
            
        except Exception as e:
            prediction.last_error = str(e)
            db.commit()
            
            return {"status": "error", "message": str(e)}

    async def get_predictions(
        self,
        db: Session,
        prediction_id: str,
        forecast_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get predictions from trained model."""
        
        prediction = db.query(AnalyticsPrediction).filter(
            AnalyticsPrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"status": "error", "message": "Prediction model not found"}
        
        # Check if cached predictions are valid
        if (prediction.cached_predictions and 
            prediction.cache_valid_until and 
            prediction.cache_valid_until > datetime.utcnow()):
            
            predictions = prediction.cached_predictions
        else:
            # Regenerate predictions
            await self._train_prediction_model(db, prediction_id)
            db.refresh(prediction)
            predictions = prediction.cached_predictions or []
        
        # Filter by forecast days if specified
        if forecast_days:
            predictions = predictions[:forecast_days]
        
        return {
            "status": "success",
            "prediction_id": prediction_id,
            "model_type": prediction.model_type,
            "last_trained_at": prediction.last_trained_at.isoformat() if prediction.last_trained_at else None,
            "accuracy_score": float(prediction.accuracy_score) if prediction.accuracy_score else None,
            "predictions": predictions,
            "forecast_horizon": len(predictions)
        }

    # =============================================================================
    # Alert Management
    # =============================================================================

    async def create_alert(
        self, 
        db: Session, 
        alert_data: dict
    ) -> AnalyticsAlert:
        """Create a new analytics alert with threshold configuration."""
        
        alert = AnalyticsAlert(
            organization_id=alert_data["organization_id"],
            metric_id=alert_data["metric_id"],
            name=alert_data["name"],
            description=alert_data.get("description"),
            alert_type=alert_data["alert_type"],
            conditions=alert_data["conditions"],
            threshold_config=alert_data.get("threshold_config", {}),
            comparison_config=alert_data.get("comparison_config", {}),
            evaluation_frequency=alert_data.get("evaluation_frequency", "hourly"),
            evaluation_window=alert_data.get("evaluation_window", "1_hour"),
            grace_period=alert_data.get("grace_period", 0),
            priority=alert_data.get("priority", AlertPriority.MEDIUM),
            severity_rules=alert_data.get("severity_rules", {}),
            escalation_rules=alert_data.get("escalation_rules", []),
            notification_channels=alert_data.get("notification_channels", ["email"]),
            notification_recipients=alert_data.get("notification_recipients", []),
            notification_template=alert_data.get("notification_template"),
            tags=alert_data.get("tags", []),
            alert_metadata=alert_data.get("metadata", {}),
            created_by=alert_data["created_by"]
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        await self._log_analytics_action(
            db, "create_alert", "alert", alert.id,
            alert_data["created_by"], {"name": alert.name, "metric_id": alert.metric_id}
        )
        
        return alert

    async def _check_metric_alerts(
        self, 
        db: Session, 
        metric: AnalyticsMetric, 
        current_value: Decimal
    ) -> List[Dict[str, Any]]:
        """Check if metric value triggers any alerts."""
        
        alerts = db.query(AnalyticsAlert).filter(
            AnalyticsAlert.metric_id == metric.id,
            AnalyticsAlert.is_active == True,
            AnalyticsAlert.is_suppressed == False
        ).all()
        
        triggered_alerts = []
        
        for alert in alerts:
            is_triggered = await self._evaluate_alert_condition(alert, current_value, metric)
            
            if is_triggered:
                # Update alert status
                alert.is_triggered = True
                alert.trigger_count += 1
                alert.last_triggered_at = datetime.utcnow()
                
                # Send notifications
                await self._send_alert_notifications(db, alert, metric, current_value)
                
                triggered_alerts.append({
                    "alert_id": alert.id,
                    "name": alert.name,
                    "priority": alert.priority.value,
                    "current_value": float(current_value),
                    "triggered_at": alert.last_triggered_at.isoformat()
                })
            
            alert.last_evaluated_at = datetime.utcnow()
        
        db.commit()
        
        return triggered_alerts

    # =============================================================================
    # Insight Generation
    # =============================================================================

    async def generate_insights(
        self, 
        db: Session, 
        organization_id: str,
        analytics_types: Optional[List[AnalyticsType]] = None,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered analytics insights."""
        
        insights = []
        
        # Get metrics for analysis
        query = db.query(AnalyticsMetric).filter(
            AnalyticsMetric.organization_id == organization_id,
            AnalyticsMetric.is_active == True
        )
        
        if analytics_types:
            query = query.filter(AnalyticsMetric.analytics_type.in_(analytics_types))
        
        metrics = query.all()
        
        for metric in metrics:
            # Generate insights for each metric
            metric_insights = await self._generate_metric_insights(db, metric, period_days)
            insights.extend(metric_insights)
        
        # Generate cross-metric insights
        cross_insights = await self._generate_cross_metric_insights(db, metrics, period_days)
        insights.extend(cross_insights)
        
        # Store insights in database
        for insight_data in insights:
            insight = AnalyticsInsight(
                organization_id=organization_id,
                title=insight_data["title"],
                summary=insight_data["summary"],
                description=insight_data.get("description"),
                insight_type=insight_data["insight_type"],
                related_metrics=insight_data.get("related_metrics", []),
                key_findings=insight_data.get("key_findings", []),
                supporting_data=insight_data.get("supporting_data", {}),
                statistical_significance=insight_data.get("statistical_significance"),
                confidence_level=insight_data.get("confidence_level"),
                recommendations=insight_data.get("recommendations", []),
                action_items=insight_data.get("action_items", []),
                potential_impact=insight_data.get("potential_impact"),
                priority_score=insight_data.get("priority_score"),
                urgency_level=insight_data.get("urgency_level", "medium"),
                business_value=insight_data.get("business_value"),
                generation_model="analytics_ai_v1",
                generation_version="1.0",
                generation_parameters={"period_days": period_days},
                tags=insight_data.get("tags", []),
                insight_metadata=insight_data.get("metadata", {})
            )
            
            db.add(insight)
        
        db.commit()
        
        return insights

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _log_analytics_action(
        self,
        db: Session,
        action_type: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str],
        context_data: Optional[Dict[str, Any]] = None
    ):
        """Log analytics action for audit trail."""
        
        audit_log = AnalyticsAuditLog(
            organization_id=context_data.get("organization_id") if context_data else None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            context_data=context_data or {},
            impact_level="medium"
        )
        
        db.add(audit_log)
        db.commit()

    def _generate_dashboard_slug(self, name: str) -> str:
        """Generate unique slug for dashboard."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug)
        return f"{slug}-{uuid.uuid4().hex[:8]}"

    async def _calculate_next_sync(self, data_source: AnalyticsDataSource) -> datetime:
        """Calculate next sync time based on frequency."""
        now = datetime.utcnow()
        
        if data_source.sync_frequency == "realtime":
            return now
        elif data_source.sync_frequency == "hourly":
            return now + timedelta(hours=1)
        elif data_source.sync_frequency == "daily":
            return now + timedelta(days=1)
        elif data_source.sync_frequency == "weekly":
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(days=1)

    async def get_system_health(self, db: Session) -> Dict[str, Any]:
        """Get analytics system health status."""
        
        try:
            # Test database connectivity
            db.execute(text("SELECT 1"))
            
            # Get system statistics
            total_metrics = db.query(AnalyticsMetric).count()
            active_data_sources = db.query(AnalyticsDataSource).filter(
                AnalyticsDataSource.is_active == True
            ).count()
            total_dashboards = db.query(AnalyticsDashboard).filter(
                AnalyticsDashboard.is_active == True
            ).count()
            recent_data_points = db.query(AnalyticsDataPoint).filter(
                AnalyticsDataPoint.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                "status": "healthy",
                "database_connection": "OK",
                "services_available": True,
                "statistics": {
                    "total_metrics": total_metrics,
                    "active_data_sources": active_data_sources,
                    "total_dashboards": total_dashboards,
                    "recent_data_points": recent_data_points
                },
                "version": "31.0",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }