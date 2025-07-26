"""Enterprise Reporting & Analytics System - CC02 v73.0 Day 18."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from .enterprise_auth_system import EnterpriseAuthenticationSystem


class ReportType(str, Enum):
    """Report types supported by the system."""

    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Supported report output formats."""

    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    POWERPOINT = "powerpoint"


class AggregationType(str, Enum):
    """Data aggregation types."""

    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    DISTINCT_COUNT = "distinct_count"


class ChartType(str, Enum):
    """Chart visualization types."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TREEMAP = "treemap"


class ReportDataSource(BaseModel):
    """Report data source configuration."""

    source_id: str
    name: str
    type: str  # database, api, file, etc.
    connection_config: Dict[str, Any] = Field(default_factory=dict)

    # Query configuration
    query: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Data transformation
    transformations: List[Dict[str, Any]] = Field(default_factory=list)

    # Caching
    cache_enabled: bool = True
    cache_ttl_minutes: int = 60

    # Security
    required_permissions: Set[str] = Field(default_factory=set)
    data_classification: str = "internal"


class ReportVisualization(BaseModel):
    """Report visualization configuration."""

    visualization_id: str
    title: str
    chart_type: ChartType
    data_source_id: str

    # Chart configuration
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    group_by: Optional[str] = None
    aggregation: Optional[AggregationType] = None

    # Styling
    colors: List[str] = Field(default_factory=list)
    theme: str = "corporate"
    width: int = 800
    height: int = 400

    # Interactivity
    clickable: bool = False
    drilldown_enabled: bool = False
    filters: Dict[str, Any] = Field(default_factory=dict)


class ReportTemplate(BaseModel):
    """Report template definition."""

    template_id: str
    name: str
    description: str
    report_type: ReportType

    # Template structure
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    data_sources: List[ReportDataSource] = Field(default_factory=list)
    visualizations: List[ReportVisualization] = Field(default_factory=list)

    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_schema: Dict[str, Any] = Field(default_factory=dict)

    # Scheduling
    schedule_enabled: bool = False
    schedule_cron: Optional[str] = None

    # Output
    default_format: ReportFormat = ReportFormat.PDF
    supported_formats: Set[ReportFormat] = Field(default_factory=set)

    # Access control
    required_roles: Set[str] = Field(default_factory=set)
    required_permissions: Set[str] = Field(default_factory=set)

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: str = "1.0"


class ReportInstance(BaseModel):
    """Generated report instance."""

    instance_id: str
    template_id: str
    name: str

    # Generation info
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_time_seconds: float = 0.0

    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Output
    format: ReportFormat
    file_path: Optional[str] = None
    file_size_bytes: int = 0

    # Status
    status: str = "generating"  # generating, completed, failed
    error_message: Optional[str] = None

    # Data freshness
    data_timestamp: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Access tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class AnalyticsDashboard(BaseModel):
    """Analytics dashboard configuration."""

    dashboard_id: str
    name: str
    description: str

    # Layout
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)

    # Data refresh
    auto_refresh: bool = True
    refresh_interval_minutes: int = 15

    # Personalization
    customizable: bool = True
    user_customizations: Dict[str, Any] = Field(default_factory=dict)

    # Access control
    public: bool = False
    allowed_users: Set[str] = Field(default_factory=set)
    allowed_roles: Set[str] = Field(default_factory=set)

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class KPIMetric(BaseModel):
    """Key Performance Indicator metric."""

    metric_id: str
    name: str
    description: str
    category: str

    # Calculation
    calculation_formula: str
    data_source_id: str
    aggregation_type: AggregationType

    # Targets and thresholds
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None

    # Display format
    unit: str = ""
    decimal_places: int = 2
    format_as_percentage: bool = False
    format_as_currency: bool = False

    # Historical tracking
    track_history: bool = True
    history_retention_days: int = 365

    # Alerts
    alert_enabled: bool = False
    alert_conditions: Dict[str, Any] = Field(default_factory=dict)


class DataConnector(ABC):
    """Abstract data connector for report data sources."""

    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Establish connection to data source."""
        pass

    @abstractmethod
    async def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """Execute query and return data."""
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Get data source schema information."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to data source."""
        pass


class DatabaseConnector(DataConnector):
    """Database data connector."""

    def __init__(self, connection_string: str) -> dict:
        self.connection_string = connection_string
        self.connection = None

    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to database."""
        try:
            # Mock database connection
            self.connection = {"status": "connected", "config": config}
            return True
        except Exception:
            return False

    async def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """Execute SQL query."""
        # Mock query execution with sample data
        if "sales" in query.lower():
            return pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=30),
                    "revenue": [10000 + i * 500 for i in range(30)],
                    "orders": [100 + i * 5 for i in range(30)],
                    "customers": [50 + i * 2 for i in range(30)],
                }
            )
        elif "inventory" in query.lower():
            return pd.DataFrame(
                {
                    "product": ["Product A", "Product B", "Product C", "Product D"],
                    "quantity": [500, 750, 300, 900],
                    "value": [25000, 37500, 15000, 45000],
                    "category": ["Electronics", "Clothing", "Books", "Electronics"],
                }
            )
        else:
            # Default sample data
            return pd.DataFrame(
                {
                    "metric": ["Metric 1", "Metric 2", "Metric 3"],
                    "value": [100, 200, 150],
                    "trend": [0.05, -0.02, 0.08],
                }
            )

    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema."""
        return {
            "tables": [
                {
                    "name": "sales",
                    "columns": ["id", "date", "revenue", "orders", "customers"],
                },
                {
                    "name": "inventory",
                    "columns": ["id", "product", "quantity", "value", "category"],
                },
            ]
        }

    async def disconnect(self) -> None:
        """Disconnect from database."""
        self.connection = None


class APIConnector(DataConnector):
    """API data connector."""

    def __init__(self, base_url: str, auth_config: Dict[str, Any]) -> dict:
        self.base_url = base_url
        self.auth_config = auth_config
        self.session = None

    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to API."""
        try:
            # Mock API connection
            self.session = {"status": "authenticated", "config": config}
            return True
        except Exception:
            return False

    async def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """Execute API request."""
        # Mock API response
        if "analytics" in query:
            return pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01", periods=24, freq="H"),
                    "page_views": [1000 + i * 50 for i in range(24)],
                    "unique_visitors": [500 + i * 25 for i in range(24)],
                    "bounce_rate": [0.3 + (i % 10) * 0.01 for i in range(24)],
                }
            )
        else:
            return pd.DataFrame(
                {"key": ["Key 1", "Key 2", "Key 3"], "value": [10, 20, 15]}
            )

    async def get_schema(self) -> Dict[str, Any]:
        """Get API schema."""
        return {
            "endpoints": [
                {
                    "path": "/analytics",
                    "fields": [
                        "timestamp",
                        "page_views",
                        "unique_visitors",
                        "bounce_rate",
                    ],
                }
            ]
        }

    async def disconnect(self) -> None:
        """Disconnect from API."""
        self.session = None


class ReportEngine:
    """Core report generation engine."""

    def __init__(self, auth_system: EnterpriseAuthenticationSystem) -> dict:
        self.auth_system = auth_system
        self.templates: Dict[str, ReportTemplate] = {}
        self.instances: Dict[str, ReportInstance] = {}
        self.data_connectors: Dict[str, DataConnector] = {}
        self.data_cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}

        # Initialize default connectors
        self._initialize_connectors()

        # Setup default templates
        self._setup_default_templates()

    def _initialize_connectors(self) -> None:
        """Initialize data connectors."""
        # Database connector
        self.data_connectors["database"] = DatabaseConnector(
            "postgresql://localhost:5432/erp_db"
        )

        # API connector
        self.data_connectors["api"] = APIConnector(
            "https://api.company.com", {"type": "bearer", "token": "mock_token"}
        )

    def _setup_default_templates(self) -> None:
        """Setup default report templates."""
        # Financial Performance Report
        financial_template = ReportTemplate(
            template_id="financial_performance",
            name="Financial Performance Report",
            description="Comprehensive financial performance analysis",
            report_type=ReportType.FINANCIAL,
            data_sources=[
                ReportDataSource(
                    source_id="sales_data",
                    name="Sales Data",
                    type="database",
                    query="SELECT * FROM sales WHERE date >= :start_date AND date <= :end_date",
                    required_permissions={"finance.read"},
                )
            ],
            visualizations=[
                ReportVisualization(
                    visualization_id="revenue_trend",
                    title="Revenue Trend",
                    chart_type=ChartType.LINE,
                    data_source_id="sales_data",
                    x_axis="date",
                    y_axis="revenue",
                ),
                ReportVisualization(
                    visualization_id="orders_distribution",
                    title="Orders by Category",
                    chart_type=ChartType.PIE,
                    data_source_id="sales_data",
                    y_axis="orders",
                    group_by="category",
                ),
            ],
            parameters={
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True},
                "department": {"type": "string", "required": False},
            },
            required_roles={"finance_user", "finance_manager"},
            supported_formats={ReportFormat.PDF, ReportFormat.EXCEL},
            created_by="system",
        )

        self.templates[financial_template.template_id] = financial_template

        # Operational Dashboard Template
        operational_template = ReportTemplate(
            template_id="operational_dashboard",
            name="Operational Dashboard",
            description="Real-time operational metrics and KPIs",
            report_type=ReportType.OPERATIONAL,
            data_sources=[
                ReportDataSource(
                    source_id="inventory_data",
                    name="Inventory Data",
                    type="database",
                    query="SELECT * FROM inventory",
                    cache_ttl_minutes=30,
                )
            ],
            visualizations=[
                ReportVisualization(
                    visualization_id="inventory_levels",
                    title="Inventory Levels",
                    chart_type=ChartType.BAR,
                    data_source_id="inventory_data",
                    x_axis="product",
                    y_axis="quantity",
                )
            ],
            parameters={},
            required_roles={"operations_user"},
            supported_formats={ReportFormat.HTML, ReportFormat.JSON},
            created_by="system",
        )

        self.templates[operational_template.template_id] = operational_template

    async def create_template(
        self, template_data: Dict[str, Any], created_by: str
    ) -> ReportTemplate:
        """Create a new report template."""
        template = ReportTemplate(**template_data, created_by=created_by)

        self.templates[template.template_id] = template
        return template

    async def generate_report(
        self,
        template_id: str,
        user_id: str,
        parameters: Dict[str, Any] = None,
        format: ReportFormat = ReportFormat.PDF,
    ) -> ReportInstance:
        """Generate report from template."""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Check permissions
        user_info = self.auth_system.get_user_info(user_id)
        if not user_info:
            raise ValueError("User not found")

        user_roles = set(user_info["roles"])
        if template.required_roles and not template.required_roles.intersection(
            user_roles
        ):
            raise PermissionError("Insufficient roles for report template")

        # Create report instance
        instance = ReportInstance(
            instance_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}",
            template_id=template_id,
            name=f"{template.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            generated_by=user_id,
            parameters=parameters or {},
            format=format,
        )

        try:
            start_time = datetime.now()

            # Generate report data
            report_data = await self._generate_report_data(template, parameters or {})

            # Create visualizations
            visualizations = await self._create_visualizations(
                template.visualizations, report_data
            )

            # Generate output file
            file_path = await self._generate_output_file(
                instance, template, report_data, visualizations
            )

            # Update instance
            instance.status = "completed"
            instance.file_path = file_path
            instance.generation_time_seconds = (
                datetime.now() - start_time
            ).total_seconds()

        except Exception as e:
            instance.status = "failed"
            instance.error_message = str(e)

        self.instances[instance.instance_id] = instance
        return instance

    async def _generate_report_data(
        self, template: ReportTemplate, parameters: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """Generate data for report from data sources."""
        report_data = {}

        for data_source in template.data_sources:
            # Check cache first
            cache_key = f"{data_source.source_id}_{hash(str(parameters))}"
            if data_source.cache_enabled and cache_key in self.data_cache:
                cached_data, cached_time = self.data_cache[cache_key]
                cache_age = datetime.now() - cached_time
                if cache_age.total_seconds() < data_source.cache_ttl_minutes * 60:
                    report_data[data_source.source_id] = cached_data
                    continue

            # Get connector
            connector = self.data_connectors.get(data_source.type)
            if not connector:
                raise ValueError(
                    f"No connector for data source type: {data_source.type}"
                )

            # Connect and execute query
            await connector.connect(data_source.connection_config)

            query_params = {**data_source.parameters, **parameters}
            data = await connector.execute_query(data_source.query, query_params)

            # Apply transformations
            for transformation in data_source.transformations:
                data = await self._apply_transformation(data, transformation)

            # Cache data
            if data_source.cache_enabled:
                self.data_cache[cache_key] = (data, datetime.now())

            report_data[data_source.source_id] = data

            await connector.disconnect()

        return report_data

    async def _apply_transformation(
        self, data: pd.DataFrame, transformation: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply data transformation."""
        transform_type = transformation.get("type")

        if transform_type == "filter":
            condition = transformation.get("condition")
            return data.query(condition) if condition else data

        elif transform_type == "aggregate":
            group_by = transformation.get("group_by", [])
            aggregations = transformation.get("aggregations", {})

            if group_by:
                return data.groupby(group_by).agg(aggregations).reset_index()
            else:
                return data.agg(aggregations).to_frame().T

        elif transform_type == "sort":
            sort_by = transformation.get("sort_by")
            ascending = transformation.get("ascending", True)
            return data.sort_values(sort_by, ascending=ascending)

        elif transform_type == "rename":
            columns = transformation.get("columns", {})
            return data.rename(columns=columns)

        else:
            return data

    async def _create_visualizations(
        self,
        visualization_configs: List[ReportVisualization],
        report_data: Dict[str, pd.DataFrame],
    ) -> List[Dict[str, Any]]:
        """Create visualizations from data."""
        visualizations = []

        for config in visualization_configs:
            data = report_data.get(config.data_source_id)
            if data is None:
                continue

            # Create chart data
            chart_data = await self._create_chart_data(config, data)

            visualization = {
                "id": config.visualization_id,
                "title": config.title,
                "type": config.chart_type,
                "data": chart_data,
                "config": {
                    "width": config.width,
                    "height": config.height,
                    "colors": config.colors,
                    "theme": config.theme,
                },
            }

            visualizations.append(visualization)

        return visualizations

    async def _create_chart_data(
        self, config: ReportVisualization, data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Create chart data from DataFrame."""
        chart_data = {"labels": [], "datasets": []}

        if config.chart_type == ChartType.LINE:
            chart_data["labels"] = data[config.x_axis].tolist()
            chart_data["datasets"] = [
                {"label": config.y_axis, "data": data[config.y_axis].tolist()}
            ]

        elif config.chart_type == ChartType.BAR:
            chart_data["labels"] = data[config.x_axis].tolist()
            chart_data["datasets"] = [
                {"label": config.y_axis, "data": data[config.y_axis].tolist()}
            ]

        elif config.chart_type == ChartType.PIE:
            if config.group_by:
                grouped = data.groupby(config.group_by)[config.y_axis].sum()
                chart_data["labels"] = grouped.index.tolist()
                chart_data["datasets"] = [{"data": grouped.values.tolist()}]
            else:
                chart_data["labels"] = data[config.x_axis].tolist()
                chart_data["datasets"] = [{"data": data[config.y_axis].tolist()}]

        return chart_data

    async def _generate_output_file(
        self,
        instance: ReportInstance,
        template: ReportTemplate,
        report_data: Dict[str, pd.DataFrame],
        visualizations: List[Dict[str, Any]],
    ) -> str:
        """Generate output file for report."""
        # Mock file generation
        file_path = f"/tmp/reports/{instance.instance_id}.{instance.format.value}"

        # In real implementation, would generate actual files
        # For now, just return the path
        instance.file_size_bytes = 1024 * 1024  # 1MB mock size

        return file_path

    async def get_report_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get report generation status."""
        instance = self.instances.get(instance_id)
        if not instance:
            return None

        return {
            "instance_id": instance.instance_id,
            "status": instance.status,
            "progress": 100 if instance.status == "completed" else 50,
            "generated_at": instance.generated_at.isoformat(),
            "file_path": instance.file_path,
            "error_message": instance.error_message,
        }

    async def download_report(self, instance_id: str, user_id: str) -> Optional[str]:
        """Get download path for report."""
        instance = self.instances.get(instance_id)
        if not instance or instance.generated_by != user_id:
            return None

        if instance.status != "completed":
            return None

        # Track access
        instance.access_count += 1
        instance.last_accessed = datetime.now()

        return instance.file_path

    def list_templates(
        self, user_roles: Set[str], report_type: Optional[ReportType] = None
    ) -> List[Dict[str, Any]]:
        """List available report templates for user."""
        templates = []

        for template in self.templates.values():
            # Check role access
            if template.required_roles and not template.required_roles.intersection(
                user_roles
            ):
                continue

            # Filter by type
            if report_type and template.report_type != report_type:
                continue

            templates.append(
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "report_type": template.report_type,
                    "supported_formats": list(template.supported_formats),
                    "parameters": template.parameter_schema,
                }
            )

        return templates

    def list_reports(
        self, user_id: str, template_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List user's generated reports."""
        reports = []

        for instance in self.instances.values():
            if instance.generated_by != user_id:
                continue

            if template_id and instance.template_id != template_id:
                continue

            reports.append(
                {
                    "instance_id": instance.instance_id,
                    "name": instance.name,
                    "template_id": instance.template_id,
                    "status": instance.status,
                    "generated_at": instance.generated_at.isoformat(),
                    "format": instance.format,
                    "file_size_bytes": instance.file_size_bytes,
                }
            )

        return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


class AnalyticsEngine:
    """Advanced analytics and business intelligence engine."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.dashboards: Dict[str, AnalyticsDashboard] = {}
        self.kpi_metrics: Dict[str, KPIMetric] = {}
        self.analytics_data: Dict[str, List[Dict[str, Any]]] = {}

        # Setup default dashboards and KPIs
        self._setup_default_dashboards()
        self._setup_default_kpis()

    def _setup_default_dashboards(self) -> None:
        """Setup default analytics dashboards."""
        # Executive Dashboard
        executive_dashboard = AnalyticsDashboard(
            dashboard_id="executive_overview",
            name="Executive Overview",
            description="High-level KPIs and business metrics",
            widgets=[
                {
                    "type": "kpi_card",
                    "metric_id": "revenue_growth",
                    "position": {"row": 0, "col": 0, "width": 3, "height": 2},
                },
                {
                    "type": "kpi_card",
                    "metric_id": "customer_satisfaction",
                    "position": {"row": 0, "col": 3, "width": 3, "height": 2},
                },
                {
                    "type": "chart",
                    "chart_type": "line",
                    "data_source": "monthly_revenue",
                    "position": {"row": 2, "col": 0, "width": 6, "height": 4},
                },
            ],
            allowed_roles={"executive", "ceo", "cfo"},
            created_by="system",
        )

        self.dashboards[executive_dashboard.dashboard_id] = executive_dashboard

        # Operations Dashboard
        operations_dashboard = AnalyticsDashboard(
            dashboard_id="operations_overview",
            name="Operations Overview",
            description="Operational efficiency and performance metrics",
            widgets=[
                {
                    "type": "gauge",
                    "metric_id": "operational_efficiency",
                    "position": {"row": 0, "col": 0, "width": 2, "height": 2},
                },
                {
                    "type": "chart",
                    "chart_type": "bar",
                    "data_source": "department_performance",
                    "position": {"row": 0, "col": 2, "width": 4, "height": 3},
                },
            ],
            allowed_roles={"operations_manager", "operations_user"},
            created_by="system",
        )

        self.dashboards[operations_dashboard.dashboard_id] = operations_dashboard

    def _setup_default_kpis(self) -> None:
        """Setup default KPI metrics."""
        # Revenue Growth KPI
        revenue_growth = KPIMetric(
            metric_id="revenue_growth",
            name="Revenue Growth",
            description="Month-over-month revenue growth percentage",
            category="Financial",
            calculation_formula="((current_month_revenue / previous_month_revenue) - 1) * 100",
            data_source_id="revenue_data",
            aggregation_type=AggregationType.PERCENTILE,
            target_value=10.0,
            warning_threshold=5.0,
            critical_threshold=0.0,
            unit="%",
            format_as_percentage=True,
        )

        self.kpi_metrics[revenue_growth.metric_id] = revenue_growth

        # Customer Satisfaction KPI
        customer_satisfaction = KPIMetric(
            metric_id="customer_satisfaction",
            name="Customer Satisfaction Score",
            description="Average customer satisfaction rating",
            category="Customer",
            calculation_formula="AVG(satisfaction_rating)",
            data_source_id="customer_feedback",
            aggregation_type=AggregationType.AVERAGE,
            target_value=4.5,
            warning_threshold=4.0,
            critical_threshold=3.5,
            unit="stars",
            decimal_places=1,
        )

        self.kpi_metrics[customer_satisfaction.metric_id] = customer_satisfaction

        # Operational Efficiency KPI
        operational_efficiency = KPIMetric(
            metric_id="operational_efficiency",
            name="Operational Efficiency",
            description="Overall operational efficiency score",
            category="Operations",
            calculation_formula="(completed_tasks / total_tasks) * 100",
            data_source_id="operations_data",
            aggregation_type=AggregationType.PERCENTILE,
            target_value=95.0,
            warning_threshold=85.0,
            critical_threshold=75.0,
            unit="%",
            format_as_percentage=True,
        )

        self.kpi_metrics[operational_efficiency.metric_id] = operational_efficiency

    async def calculate_kpi(
        self, metric_id: str, time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Calculate KPI metric value."""
        metric = self.kpi_metrics.get(metric_id)
        if not metric:
            raise ValueError(f"KPI metric {metric_id} not found")

        # Mock calculation with sample data
        if metric_id == "revenue_growth":
            current_value = 12.5  # 12.5% growth
        elif metric_id == "customer_satisfaction":
            current_value = 4.2  # 4.2 stars
        elif metric_id == "operational_efficiency":
            current_value = 88.5  # 88.5% efficiency
        else:
            current_value = 75.0  # Default value

        # Determine status based on thresholds
        if (
            metric.critical_threshold is not None
            and current_value <= metric.critical_threshold
        ):
            status = "critical"
        elif (
            metric.warning_threshold is not None
            and current_value <= metric.warning_threshold
        ):
            status = "warning"
        elif metric.target_value is not None and current_value >= metric.target_value:
            status = "good"
        else:
            status = "ok"

        # Format value
        if metric.format_as_percentage:
            formatted_value = f"{current_value:.{metric.decimal_places}f}%"
        elif metric.format_as_currency:
            formatted_value = f"${current_value:,.{metric.decimal_places}f}"
        else:
            formatted_value = (
                f"{current_value:.{metric.decimal_places}f} {metric.unit}".strip()
            )

        # Calculate trend (mock)
        trend = 0.05 if current_value > (metric.target_value or 0) else -0.02

        return {
            "metric_id": metric_id,
            "name": metric.name,
            "current_value": current_value,
            "formatted_value": formatted_value,
            "target_value": metric.target_value,
            "status": status,
            "trend": trend,
            "unit": metric.unit,
            "calculated_at": datetime.now().isoformat(),
        }

    async def get_dashboard_data(
        self,
        dashboard_id: str,
        user_id: str,
        time_period: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """Get dashboard data for user."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        # Check access permissions (simplified)
        # In real implementation, would check user roles

        dashboard_data = {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "description": dashboard.description,
            "auto_refresh": dashboard.auto_refresh,
            "refresh_interval": dashboard.refresh_interval_minutes,
            "widgets": [],
        }

        # Load widget data
        for widget_config in dashboard.widgets:
            widget_data = await self._load_widget_data(widget_config, time_period)
            dashboard_data["widgets"].append(widget_data)

        return dashboard_data

    async def _load_widget_data(
        self,
        widget_config: Dict[str, Any],
        time_period: Optional[Tuple[datetime, datetime]],
    ) -> Dict[str, Any]:
        """Load data for dashboard widget."""
        widget_type = widget_config["type"]

        if widget_type == "kpi_card":
            metric_id = widget_config["metric_id"]
            kpi_data = await self.calculate_kpi(metric_id, time_period)

            return {
                "type": "kpi_card",
                "position": widget_config["position"],
                "data": kpi_data,
            }

        elif widget_type == "chart":
            chart_data = await self._generate_chart_data(
                widget_config["data_source"], widget_config["chart_type"], time_period
            )

            return {
                "type": "chart",
                "position": widget_config["position"],
                "chart_type": widget_config["chart_type"],
                "data": chart_data,
            }

        elif widget_type == "gauge":
            metric_id = widget_config["metric_id"]
            kpi_data = await self.calculate_kpi(metric_id, time_period)

            gauge_data = {
                "value": kpi_data["current_value"],
                "min": 0,
                "max": 100,
                "target": kpi_data["target_value"],
                "color": "green"
                if kpi_data["status"] == "good"
                else "yellow"
                if kpi_data["status"] == "warning"
                else "red",
            }

            return {
                "type": "gauge",
                "position": widget_config["position"],
                "data": gauge_data,
            }

        else:
            return {
                "type": widget_type,
                "position": widget_config["position"],
                "data": {},
            }

    async def _generate_chart_data(
        self,
        data_source: str,
        chart_type: str,
        time_period: Optional[Tuple[datetime, datetime]],
    ) -> Dict[str, Any]:
        """Generate chart data from data source."""
        # Mock chart data generation
        if data_source == "monthly_revenue":
            return {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "datasets": [
                    {
                        "label": "Revenue",
                        "data": [100000, 120000, 110000, 140000, 135000, 155000],
                    }
                ],
            }
        elif data_source == "department_performance":
            return {
                "labels": ["Sales", "Marketing", "Operations", "Finance"],
                "datasets": [{"label": "Performance Score", "data": [85, 92, 78, 88]}],
            }
        else:
            return {
                "labels": ["A", "B", "C"],
                "datasets": [{"label": "Data", "data": [10, 20, 15]}],
            }

    async def create_custom_dashboard(
        self, dashboard_data: Dict[str, Any], user_id: str
    ) -> AnalyticsDashboard:
        """Create custom dashboard for user."""
        dashboard = AnalyticsDashboard(**dashboard_data, created_by=user_id)

        self.dashboards[dashboard.dashboard_id] = dashboard
        return dashboard

    def list_dashboards(self, user_roles: Set[str]) -> List[Dict[str, Any]]:
        """List available dashboards for user."""
        dashboards = []

        for dashboard in self.dashboards.values():
            # Check access permissions
            if dashboard.allowed_roles and not dashboard.allowed_roles.intersection(
                user_roles
            ):
                if not dashboard.public:
                    continue

            dashboards.append(
                {
                    "dashboard_id": dashboard.dashboard_id,
                    "name": dashboard.name,
                    "description": dashboard.description,
                    "customizable": dashboard.customizable,
                    "auto_refresh": dashboard.auto_refresh,
                }
            )

        return dashboards

    def list_kpis(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available KPI metrics."""
        kpis = []

        for kpi in self.kpi_metrics.values():
            if category and kpi.category != category:
                continue

            kpis.append(
                {
                    "metric_id": kpi.metric_id,
                    "name": kpi.name,
                    "description": kpi.description,
                    "category": kpi.category,
                    "unit": kpi.unit,
                    "target_value": kpi.target_value,
                }
            )

        return kpis


class EnterpriseReportingAnalytics:
    """Main enterprise reporting and analytics system."""

    def __init__(self, sdk: MobileERPSDK, auth_system: EnterpriseAuthenticationSystem) -> dict:
        self.sdk = sdk
        self.auth_system = auth_system

        # Initialize engines
        self.report_engine = ReportEngine(auth_system)
        self.analytics_engine = AnalyticsEngine(sdk)

        # System metrics
        self.system_metrics = {
            "reports_generated": 0,
            "dashboards_viewed": 0,
            "kpis_calculated": 0,
            "data_queries_executed": 0,
        }

    async def generate_report(
        self,
        session_id: str,
        template_id: str,
        parameters: Dict[str, Any] = None,
        format: ReportFormat = ReportFormat.PDF,
    ) -> Dict[str, Any]:
        """Generate report with authentication check."""
        # Check session
        session_info = self.auth_system.get_session_info(session_id)
        if not session_info or not session_info["authenticated"]:
            raise PermissionError("Invalid or expired session")

        # Generate report
        instance = await self.report_engine.generate_report(
            template_id, session_info["user_id"], parameters, format
        )

        # Update metrics
        self.system_metrics["reports_generated"] += 1

        return {
            "instance_id": instance.instance_id,
            "status": instance.status,
            "name": instance.name,
            "generated_at": instance.generated_at.isoformat(),
            "format": instance.format,
            "error_message": instance.error_message,
        }

    async def get_dashboard_data(
        self,
        session_id: str,
        dashboard_id: str,
        time_period: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """Get dashboard data with authentication check."""
        # Check session
        session_info = self.auth_system.get_session_info(session_id)
        if not session_info or not session_info["authenticated"]:
            raise PermissionError("Invalid or expired session")

        # Get dashboard data
        dashboard_data = await self.analytics_engine.get_dashboard_data(
            dashboard_id, session_info["user_id"], time_period
        )

        # Update metrics
        self.system_metrics["dashboards_viewed"] += 1

        return dashboard_data

    async def calculate_kpi(
        self,
        session_id: str,
        metric_id: str,
        time_period: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """Calculate KPI with authentication check."""
        # Check session
        session_info = self.auth_system.get_session_info(session_id)
        if not session_info or not session_info["authenticated"]:
            raise PermissionError("Invalid or expired session")

        # Calculate KPI
        kpi_data = await self.analytics_engine.calculate_kpi(metric_id, time_period)

        # Update metrics
        self.system_metrics["kpis_calculated"] += 1

        return kpi_data

    def get_available_reports(self, session_id: str) -> List[Dict[str, Any]]:
        """Get available report templates for user."""
        session_info = self.auth_system.get_session_info(session_id)
        if not session_info or not session_info["authenticated"]:
            raise PermissionError("Invalid or expired session")

        user_roles = set(session_info["effective_roles"])
        return self.report_engine.list_templates(user_roles)

    def get_available_dashboards(self, session_id: str) -> List[Dict[str, Any]]:
        """Get available dashboards for user."""
        session_info = self.auth_system.get_session_info(session_id)
        if not session_info or not session_info["authenticated"]:
            raise PermissionError("Invalid or expired session")

        user_roles = set(session_info["effective_roles"])
        return self.analytics_engine.list_dashboards(user_roles)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system usage metrics."""
        return {
            **self.system_metrics,
            "active_sessions": len(self.auth_system.sessions),
            "total_templates": len(self.report_engine.templates),
            "total_dashboards": len(self.analytics_engine.dashboards),
            "total_kpis": len(self.analytics_engine.kpi_metrics),
        }
