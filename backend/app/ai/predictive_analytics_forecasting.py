"""Predictive Analytics & Forecasting System - CC02 v75.0 Day 20."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from .ai_intelligence_engine import AIIntelligenceEngine


class ForecastType(str, Enum):
    """Types of forecasting models."""

    SALES_REVENUE = "sales_revenue"
    DEMAND_FORECASTING = "demand_forecasting"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    CASH_FLOW = "cash_flow"
    CUSTOMER_ACQUISITION = "customer_acquisition"
    RESOURCE_PLANNING = "resource_planning"
    MARKET_TRENDS = "market_trends"
    OPERATIONAL_COSTS = "operational_costs"


class TimeSeriesMethod(str, Enum):
    """Time series forecasting methods."""

    LINEAR_TREND = "linear_trend"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ARIMA = "arima"
    SARIMA = "sarima"
    PROPHET = "prophet"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"


class SeasonalityType(str, Enum):
    """Types of seasonality patterns."""

    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""

    LOW = "low"  # 80%
    MEDIUM = "medium"  # 90%
    HIGH = "high"  # 95%
    VERY_HIGH = "very_high"  # 99%


class ForecastModel(BaseModel):
    """Predictive forecasting model configuration."""

    model_id: str
    name: str
    description: str
    forecast_type: ForecastType

    # Time series configuration
    method: TimeSeriesMethod = TimeSeriesMethod.LINEAR_TREND
    target_variable: str
    time_column: str

    # Seasonality
    seasonality_type: SeasonalityType = SeasonalityType.NONE
    seasonal_periods: Optional[int] = None

    # External factors
    external_variables: List[str] = Field(default_factory=list)
    economic_indicators: List[str] = Field(default_factory=list)

    # Model parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Forecast settings
    forecast_horizon: int = 30  # days
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # Validation
    validation_period: int = 90  # days for backtesting
    accuracy_threshold: float = 0.8

    # Performance metrics
    mape: Optional[float] = None  # Mean Absolute Percentage Error
    rmse: Optional[float] = None  # Root Mean Square Error
    mae: Optional[float] = None  # Mean Absolute Error

    # Business context
    business_unit: str
    stakeholders: List[str] = Field(default_factory=list)
    decision_impact: str

    # Status and metadata
    status: str = "draft"  # draft, training, active, deprecated
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_trained: Optional[datetime] = None
    last_forecast: Optional[datetime] = None


class ForecastResult(BaseModel):
    """Forecast prediction result."""

    forecast_id: str
    model_id: str

    # Forecast data
    predictions: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_intervals: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    forecast_date: datetime = Field(default_factory=datetime.now)
    forecast_horizon_days: int
    data_points_used: int

    # Quality metrics
    model_accuracy: float
    confidence_score: float
    trend_direction: str  # "increasing", "decreasing", "stable"

    # Business insights
    key_insights: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Alert conditions
    anomalies_detected: List[Dict[str, Any]] = Field(default_factory=list)
    threshold_breaches: List[Dict[str, Any]] = Field(default_factory=list)


class ScenarioAnalysis(BaseModel):
    """Scenario-based forecasting analysis."""

    scenario_id: str
    name: str
    description: str
    model_id: str

    # Scenario parameters
    scenario_type: str  # "optimistic", "pessimistic", "most_likely", "custom"
    parameter_adjustments: Dict[str, float] = Field(default_factory=dict)
    external_assumptions: Dict[str, Any] = Field(default_factory=dict)

    # Results
    forecast_results: Optional[ForecastResult] = None
    probability: float = 0.33  # Likelihood of this scenario

    # Business impact
    revenue_impact: Optional[float] = None
    cost_impact: Optional[float] = None
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)

    # Risk assessment
    risk_level: str = "medium"  # low, medium, high
    mitigation_strategies: List[str] = Field(default_factory=list)

    # Created metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str


class AlertRule(BaseModel):
    """Alert rule for forecast monitoring."""

    rule_id: str
    name: str
    description: str
    model_id: str

    # Condition
    metric: str  # "actual_vs_forecast", "trend_change", "anomaly_score"
    condition: str  # "greater_than", "less_than", "outside_range"
    threshold: float
    threshold_range: Optional[Tuple[float, float]] = None

    # Alert configuration
    severity: str = "medium"  # low, medium, high, critical
    notification_channels: List[str] = Field(default_factory=list)

    # Status
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)


class TimeSeriesPreprocessor:
    """Time series data preprocessing utilities."""

    def __init__(self) -> dict:
        self.scalers: Dict[str, StandardScaler] = {}

    async def prepare_time_series(
        self,
        data: pd.DataFrame,
        time_column: str,
        target_column: str,
        external_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Prepare time series data for forecasting."""
        # Convert time column to datetime
        data[time_column] = pd.to_datetime(data[time_column])

        # Sort by time
        data = data.sort_values(time_column).reset_index(drop=True)

        # Handle missing values
        data = await self._handle_missing_values(
            data, target_column, external_columns or []
        )

        # Detect and handle outliers
        data = await self._handle_outliers(data, target_column)

        # Create time-based features
        data = await self._create_time_features(data, time_column)

        # Create lag features
        data = await self._create_lag_features(data, target_column)

        # Create rolling statistics
        data = await self._create_rolling_features(data, target_column)

        return data

    async def _handle_missing_values(
        self, data: pd.DataFrame, target_column: str, external_columns: List[str]
    ) -> pd.DataFrame:
        """Handle missing values in time series."""
        # Forward fill for target variable
        data[target_column] = data[target_column].fillna(method="ffill")

        # Interpolate remaining missing values
        data[target_column] = data[target_column].interpolate(method="linear")

        # Handle external variables
        for col in external_columns:
            if col in data.columns:
                data[col] = data[col].fillna(method="ffill")
                data[col] = data[col].interpolate(method="linear")

        return data

    async def _handle_outliers(
        self, data: pd.DataFrame, target_column: str
    ) -> pd.DataFrame:
        """Detect and handle outliers using statistical methods."""
        # Use IQR method for outlier detection
        Q1 = data[target_column].quantile(0.25)
        Q3 = data[target_column].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Cap outliers instead of removing them to preserve time series structure
        data[target_column] = data[target_column].clip(
            lower=lower_bound, upper=upper_bound
        )

        return data

    async def _create_time_features(
        self, data: pd.DataFrame, time_column: str
    ) -> pd.DataFrame:
        """Create time-based features."""
        data["year"] = data[time_column].dt.year
        data["month"] = data[time_column].dt.month
        data["day"] = data[time_column].dt.day
        data["dayofweek"] = data[time_column].dt.dayofweek
        data["quarter"] = data[time_column].dt.quarter
        data["week"] = data[time_column].dt.isocalendar().week

        # Cyclical encoding for seasonal patterns
        data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
        data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)
        data["dayofweek_sin"] = np.sin(2 * np.pi * data["dayofweek"] / 7)
        data["dayofweek_cos"] = np.cos(2 * np.pi * data["dayofweek"] / 7)

        return data

    async def _create_lag_features(
        self, data: pd.DataFrame, target_column: str, lags: List[int] = None
    ) -> pd.DataFrame:
        """Create lag features for time series."""
        if lags is None:
            lags = [1, 7, 14, 30]  # 1 day, 1 week, 2 weeks, 1 month

        for lag in lags:
            data[f"{target_column}_lag_{lag}"] = data[target_column].shift(lag)

        return data

    async def _create_rolling_features(
        self, data: pd.DataFrame, target_column: str, windows: List[int] = None
    ) -> pd.DataFrame:
        """Create rolling statistics features."""
        if windows is None:
            windows = [7, 14, 30]  # 1 week, 2 weeks, 1 month

        for window in windows:
            data[f"{target_column}_rolling_mean_{window}"] = (
                data[target_column].rolling(window).mean()
            )
            data[f"{target_column}_rolling_std_{window}"] = (
                data[target_column].rolling(window).std()
            )
            data[f"{target_column}_rolling_min_{window}"] = (
                data[target_column].rolling(window).min()
            )
            data[f"{target_column}_rolling_max_{window}"] = (
                data[target_column].rolling(window).max()
            )

        return data


class LinearTrendForecaster:
    """Simple linear trend forecasting."""

    def __init__(self) -> dict:
        self.model: Optional[LinearRegression] = None
        self.scaler: Optional[StandardScaler] = None

    async def fit(
        self, data: pd.DataFrame, target_column: str, time_column: str
    ) -> Dict[str, Any]:
        """Fit linear trend model."""
        # Create numeric time feature
        data["time_numeric"] = (data[time_column] - data[time_column].min()).dt.days

        X = data[["time_numeric"]].values
        y = data[target_column].values

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Fit model
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)

        # Calculate metrics
        y_pred = self.model.predict(X_scaled)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        return {
            "mse": mse,
            "rmse": np.sqrt(mse),
            "mae": mae,
            "r2_score": self.model.score(X_scaled, y),
        }

    async def predict(
        self, start_date: datetime, periods: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate predictions for future periods."""
        if not self.model or not self.scaler:
            raise ValueError("Model not fitted")

        # Create future time points
        future_times = pd.date_range(start=start_date, periods=periods, freq="D")
        time_numeric = (future_times - start_date).days.values.reshape(-1, 1)

        # Scale and predict
        time_scaled = self.scaler.transform(time_numeric)
        predictions = self.model.predict(time_scaled)

        # Simple confidence intervals (±1.96 * std for 95% confidence)
        residual_std = np.std(predictions) * 0.1  # Simplified
        confidence_intervals = np.column_stack(
            [predictions - 1.96 * residual_std, predictions + 1.96 * residual_std]
        )

        return predictions, confidence_intervals


class SeasonalDecomposer:
    """Seasonal decomposition for time series."""

    def __init__(self) -> dict:
        self.trend_component: Optional[np.ndarray] = None
        self.seasonal_component: Optional[np.ndarray] = None
        self.residual_component: Optional[np.ndarray] = None

    async def decompose(
        self, data: pd.Series, period: int = 12
    ) -> Dict[str, np.ndarray]:
        """Decompose time series into trend, seasonal, and residual components."""
        # Simple moving average for trend
        trend = data.rolling(window=period, center=True).mean()

        # Remove trend to get seasonal + residual
        detrended = data - trend

        # Calculate seasonal component
        seasonal = detrended.groupby(data.index % period).transform("mean")

        # Residual component
        residual = detrended - seasonal

        self.trend_component = trend.values
        self.seasonal_component = seasonal.values
        self.residual_component = residual.values

        return {
            "trend": self.trend_component,
            "seasonal": self.seasonal_component,
            "residual": self.residual_component,
            "original": data.values,
        }

    async def forecast(self, periods: int, seasonal_period: int = 12) -> np.ndarray:
        """Forecast using decomposed components."""
        if self.trend_component is None:
            raise ValueError("Must decompose data first")

        # Extrapolate trend (simple linear extrapolation)
        last_trend_values = self.trend_component[-seasonal_period:]
        trend_slope = np.nanmean(np.diff(last_trend_values))

        future_trend = []
        last_trend = np.nanmean(last_trend_values)

        for i in range(periods):
            future_trend.append(last_trend + trend_slope * (i + 1))

        # Repeat seasonal pattern
        seasonal_pattern = self.seasonal_component[-seasonal_period:]
        future_seasonal = np.tile(seasonal_pattern, (periods // seasonal_period) + 1)[
            :periods
        ]

        # Combine components
        forecast = np.array(future_trend) + future_seasonal

        return forecast


class AnomalyDetector:
    """Anomaly detection for time series data."""

    def __init__(self) -> dict:
        self.isolation_forest: Optional[IsolationForest] = None
        self.threshold: float = 0.1

    async def fit(
        self, data: pd.DataFrame, target_column: str, contamination: float = 0.1
    ) -> None:
        """Fit anomaly detection model."""
        # Prepare features
        features = []
        for col in data.columns:
            if col != target_column and data[col].dtype in ["int64", "float64"]:
                features.append(col)

        if not features:
            # Use only target column with its lags
            X = data[[target_column]].values
        else:
            X = data[features].values

        # Remove NaN values
        X = X[~np.isnan(X).any(axis=1)]

        # Fit Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=contamination, random_state=42
        )
        self.isolation_forest.fit(X)

        self.threshold = contamination

    async def detect_anomalies(
        self, data: pd.DataFrame, target_column: str
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in time series data."""
        if not self.isolation_forest:
            raise ValueError("Model not fitted")

        # Prepare features
        features = []
        for col in data.columns:
            if col != target_column and data[col].dtype in ["int64", "float64"]:
                features.append(col)

        if not features:
            X = data[[target_column]].values
        else:
            X = data[features].values

        # Predict anomalies
        anomaly_scores = self.isolation_forest.decision_function(X)
        is_anomaly = self.isolation_forest.predict(X) == -1

        anomalies = []
        for i, (is_anom, score) in enumerate(zip(is_anomaly, anomaly_scores)):
            if is_anom:
                anomalies.append(
                    {
                        "index": i,
                        "anomaly_score": float(score),
                        "value": float(data.iloc[i][target_column]),
                        "severity": "high"
                        if score < -0.5
                        else "medium"
                        if score < -0.2
                        else "low",
                    }
                )

        return anomalies


class PredictiveAnalyticsEngine:
    """Main predictive analytics and forecasting engine."""

    def __init__(self, ai_engine: AIIntelligenceEngine) -> dict:
        self.ai_engine = ai_engine

        # Forecasting models
        self.forecast_models: Dict[str, ForecastModel] = {}
        self.forecast_results: Dict[str, ForecastResult] = {}
        self.scenario_analyses: Dict[str, ScenarioAnalysis] = {}
        self.alert_rules: Dict[str, AlertRule] = {}

        # Engines and utilities
        self.preprocessor = TimeSeriesPreprocessor()
        self.anomaly_detector = AnomalyDetector()

        # Forecasting algorithms
        self.forecasters = {
            TimeSeriesMethod.LINEAR_TREND: LinearTrendForecaster(),
            TimeSeriesMethod.SEASONAL_DECOMPOSITION: SeasonalDecomposer(),
        }

        # Setup default models
        self._setup_default_forecast_models()

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()

    def _setup_default_forecast_models(self) -> None:
        """Setup default forecasting models."""
        # Sales Revenue Forecasting
        sales_forecast = ForecastModel(
            model_id="sales_revenue_forecast",
            name="Monthly Sales Revenue Forecast",
            description="Predict monthly sales revenue with seasonal adjustments",
            forecast_type=ForecastType.SALES_REVENUE,
            method=TimeSeriesMethod.SEASONAL_DECOMPOSITION,
            target_variable="sales_revenue",
            time_column="month",
            seasonality_type=SeasonalityType.MONTHLY,
            seasonal_periods=12,
            external_variables=["marketing_spend", "economic_index"],
            forecast_horizon=12,  # 12 months
            business_unit="Sales",
            stakeholders=["Sales Director", "CFO", "CEO"],
            decision_impact="Budget allocation and resource planning",
            created_by="system",
        )

        self.forecast_models[sales_forecast.model_id] = sales_forecast

        # Demand Forecasting
        demand_forecast = ForecastModel(
            model_id="product_demand_forecast",
            name="Product Demand Forecasting",
            description="Predict product demand for inventory optimization",
            forecast_type=ForecastType.DEMAND_FORECASTING,
            method=TimeSeriesMethod.LINEAR_TREND,
            target_variable="demand_quantity",
            time_column="date",
            seasonality_type=SeasonalityType.WEEKLY,
            seasonal_periods=7,
            external_variables=["price", "promotions", "competitor_price"],
            forecast_horizon=30,  # 30 days
            business_unit="Operations",
            stakeholders=["Operations Manager", "Procurement Team"],
            decision_impact="Inventory levels and procurement planning",
            created_by="system",
        )

        self.forecast_models[demand_forecast.model_id] = demand_forecast

        # Cash Flow Forecasting
        cashflow_forecast = ForecastModel(
            model_id="cash_flow_forecast",
            name="Weekly Cash Flow Forecast",
            description="Predict weekly cash flow for liquidity management",
            forecast_type=ForecastType.CASH_FLOW,
            method=TimeSeriesMethod.LINEAR_TREND,
            target_variable="net_cash_flow",
            time_column="week",
            external_variables=[
                "accounts_receivable",
                "accounts_payable",
                "seasonal_factor",
            ],
            forecast_horizon=52,  # 52 weeks
            confidence_level=ConfidenceLevel.HIGH,
            business_unit="Finance",
            stakeholders=["CFO", "Treasurer", "Finance Team"],
            decision_impact="Cash management and investment decisions",
            created_by="system",
        )

        self.forecast_models[cashflow_forecast.model_id] = cashflow_forecast

        # Customer Acquisition Forecasting
        customer_forecast = ForecastModel(
            model_id="customer_acquisition_forecast",
            name="Customer Acquisition Rate Forecast",
            description="Predict new customer acquisition rates",
            forecast_type=ForecastType.CUSTOMER_ACQUISITION,
            method=TimeSeriesMethod.LINEAR_TREND,
            target_variable="new_customers",
            time_column="month",
            external_variables=["marketing_spend", "referral_rate", "conversion_rate"],
            forecast_horizon=6,  # 6 months
            business_unit="Marketing",
            stakeholders=["Marketing Director", "Sales Director"],
            decision_impact="Marketing budget and strategy planning",
            created_by="system",
        )

        self.forecast_models[customer_forecast.model_id] = customer_forecast

    def _start_background_tasks(self) -> None:
        """Start background forecasting tasks."""
        # Automated forecasting
        task = asyncio.create_task(self._automated_forecasting_loop())
        self._background_tasks.append(task)

        # Alert monitoring
        task = asyncio.create_task(self._alert_monitoring_loop())
        self._background_tasks.append(task)

        # Model validation
        task = asyncio.create_task(self._model_validation_loop())
        self._background_tasks.append(task)

    async def _automated_forecasting_loop(self) -> None:
        """Background automated forecasting."""
        while True:
            try:
                await self._run_scheduled_forecasts()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                print(f"Error in automated forecasting loop: {e}")
                await asyncio.sleep(3600)

    async def _alert_monitoring_loop(self) -> None:
        """Background alert monitoring."""
        while True:
            try:
                await self._check_forecast_alerts()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _model_validation_loop(self) -> None:
        """Background model validation."""
        while True:
            try:
                await self._validate_model_performance()
                await asyncio.sleep(86400)  # Check daily
            except Exception as e:
                print(f"Error in model validation loop: {e}")
                await asyncio.sleep(86400)

    async def create_forecast(
        self, model_id: str, data: pd.DataFrame, forecast_horizon: Optional[int] = None
    ) -> ForecastResult:
        """Generate forecast using specified model."""
        model = self.forecast_models.get(model_id)
        if not model:
            raise ValueError(f"Forecast model {model_id} not found")

        forecast_id = f"forecast_{model_id}_{int(datetime.now().timestamp())}"
        horizon = forecast_horizon or model.forecast_horizon

        try:
            # Preprocess data
            processed_data = await self.preprocessor.prepare_time_series(
                data, model.time_column, model.target_variable, model.external_variables
            )

            # Detect anomalies
            await self.anomaly_detector.fit(processed_data, model.target_variable)
            anomalies = await self.anomaly_detector.detect_anomalies(
                processed_data, model.target_variable
            )

            # Generate forecast
            forecaster = self.forecasters.get(model.method)
            if not forecaster:
                raise ValueError(f"Forecasting method {model.method} not supported")

            if model.method == TimeSeriesMethod.LINEAR_TREND:
                # Fit and predict with linear trend
                await forecaster.fit(
                    processed_data, model.target_variable, model.time_column
                )

                last_date = processed_data[model.time_column].max()
                start_date = last_date + timedelta(days=1)

                predictions, confidence_intervals = await forecaster.predict(
                    start_date, horizon
                )

                # Create forecast result
                forecast_dates = pd.date_range(
                    start=start_date, periods=horizon, freq="D"
                )

                predictions_list = []
                confidence_list = []

                for i, date in enumerate(forecast_dates):
                    predictions_list.append(
                        {
                            "date": date.isoformat(),
                            "predicted_value": float(predictions[i]),
                            "day_offset": i + 1,
                        }
                    )

                    confidence_list.append(
                        {
                            "date": date.isoformat(),
                            "lower_bound": float(confidence_intervals[i, 0]),
                            "upper_bound": float(confidence_intervals[i, 1]),
                            "confidence_level": model.confidence_level,
                        }
                    )

            elif model.method == TimeSeriesMethod.SEASONAL_DECOMPOSITION:
                # Seasonal decomposition forecast
                decomposition = await forecaster.decompose(
                    processed_data[model.target_variable], model.seasonal_periods or 12
                )

                predictions = await forecaster.forecast(
                    horizon, model.seasonal_periods or 12
                )

                # Create forecast result
                last_date = processed_data[model.time_column].max()
                forecast_dates = pd.date_range(
                    start=last_date + timedelta(days=1), periods=horizon, freq="D"
                )

                predictions_list = []
                confidence_list = []

                for i, date in enumerate(forecast_dates):
                    predictions_list.append(
                        {
                            "date": date.isoformat(),
                            "predicted_value": float(predictions[i]),
                            "day_offset": i + 1,
                        }
                    )

                    # Simple confidence intervals for seasonal decomposition
                    residual_std = np.nanstd(decomposition["residual"]) or 0.1
                    margin = 1.96 * residual_std

                    confidence_list.append(
                        {
                            "date": date.isoformat(),
                            "lower_bound": float(predictions[i] - margin),
                            "upper_bound": float(predictions[i] + margin),
                            "confidence_level": model.confidence_level,
                        }
                    )

            # Analyze trend direction
            trend_direction = "stable"
            if len(predictions) > 1:
                trend_slope = (predictions[-1] - predictions[0]) / len(predictions)
                if trend_slope > 0.01:
                    trend_direction = "increasing"
                elif trend_slope < -0.01:
                    trend_direction = "decreasing"

            # Generate insights and recommendations
            insights = await self._generate_insights(model, predictions, processed_data)
            recommendations = await self._generate_recommendations(
                model, predictions, trend_direction
            )
            risk_factors = await self._identify_risk_factors(
                model, anomalies, predictions
            )

            # Calculate model accuracy (simplified)
            model_accuracy = max(
                0.7, 1.0 - len(anomalies) * 0.05
            )  # Mock accuracy calculation

            forecast_result = ForecastResult(
                forecast_id=forecast_id,
                model_id=model_id,
                predictions=predictions_list,
                confidence_intervals=confidence_list,
                forecast_horizon_days=horizon,
                data_points_used=len(processed_data),
                model_accuracy=model_accuracy,
                confidence_score=0.85,  # Mock confidence score
                trend_direction=trend_direction,
                key_insights=insights,
                risk_factors=risk_factors,
                recommendations=recommendations,
                anomalies_detected=anomalies,
            )

            # Store result
            self.forecast_results[forecast_id] = forecast_result

            # Update model status
            model.last_forecast = datetime.now()
            model.status = "active"

            return forecast_result

        except Exception as e:
            raise ValueError(f"Forecast generation failed: {str(e)}")

    async def _generate_insights(
        self, model: ForecastModel, predictions: np.ndarray, data: pd.DataFrame
    ) -> List[str]:
        """Generate business insights from forecast."""
        insights = []

        # Trend analysis
        if len(predictions) > 1:
            growth_rate = (predictions[-1] - predictions[0]) / predictions[0] * 100
            insights.append(f"Forecast shows {growth_rate:.1f}% change over the period")

        # Seasonality insights
        if model.seasonality_type != SeasonalityType.NONE:
            insights.append(
                f"Seasonal patterns detected with {model.seasonality_type} cycles"
            )

        # Volume insights
        avg_prediction = np.mean(predictions)
        historical_avg = data[model.target_variable].mean()

        if avg_prediction > historical_avg * 1.1:
            insights.append("Forecast indicates above-average performance expected")
        elif avg_prediction < historical_avg * 0.9:
            insights.append("Forecast indicates below-average performance expected")

        # Volatility insights
        prediction_std = np.std(predictions)
        if prediction_std > np.std(data[model.target_variable]):
            insights.append("Higher volatility expected compared to historical data")

        return insights

    async def _generate_recommendations(
        self, model: ForecastModel, predictions: np.ndarray, trend_direction: str
    ) -> List[str]:
        """Generate business recommendations based on forecast."""
        recommendations = []

        if model.forecast_type == ForecastType.SALES_REVENUE:
            if trend_direction == "increasing":
                recommendations.append(
                    "Consider increasing inventory levels to meet growing demand"
                )
                recommendations.append("Evaluate scaling sales team capacity")
            elif trend_direction == "decreasing":
                recommendations.append("Review pricing strategy and market positioning")
                recommendations.append("Consider cost reduction measures")

        elif model.forecast_type == ForecastType.CASH_FLOW:
            if trend_direction == "decreasing":
                recommendations.append("Review credit terms and collection processes")
                recommendations.append("Consider securing additional credit lines")
            else:
                recommendations.append(
                    "Evaluate investment opportunities for excess cash"
                )

        elif model.forecast_type == ForecastType.DEMAND_FORECASTING:
            max_demand = np.max(predictions)
            min_demand = np.min(predictions)

            recommendations.append(
                f"Plan inventory levels between {min_demand:.0f} and {max_demand:.0f} units"
            )

            if max_demand > min_demand * 1.5:
                recommendations.append(
                    "High demand variability - consider flexible supplier agreements"
                )

        return recommendations

    async def _identify_risk_factors(
        self,
        model: ForecastModel,
        anomalies: List[Dict[str, Any]],
        predictions: np.ndarray,
    ) -> List[str]:
        """Identify risk factors in forecast."""
        risk_factors = []

        # Anomaly-based risks
        if len(anomalies) > 0:
            high_severity_anomalies = [a for a in anomalies if a["severity"] == "high"]
            if high_severity_anomalies:
                risk_factors.append(
                    f"High-severity anomalies detected in historical data ({len(high_severity_anomalies)} instances)"
                )

        # Volatility risks
        prediction_cv = np.std(predictions) / np.mean(predictions)
        if prediction_cv > 0.3:
            risk_factors.append(
                "High forecast volatility indicates increased uncertainty"
            )

        # External factor risks
        if model.external_variables:
            risk_factors.append(
                "Forecast depends on external variables - monitor for changes"
            )

        # Data quality risks
        if model.forecast_type in [ForecastType.SALES_REVENUE, ForecastType.CASH_FLOW]:
            risk_factors.append("Economic conditions may impact forecast accuracy")

        return risk_factors

    async def create_scenario_analysis(
        self, model_id: str, scenarios: List[Dict[str, Any]]
    ) -> List[ScenarioAnalysis]:
        """Create multiple scenario forecasts."""
        model = self.forecast_models.get(model_id)
        if not model:
            raise ValueError(f"Forecast model {model_id} not found")

        scenario_results = []

        for scenario_config in scenarios:
            scenario_id = f"scenario_{model_id}_{scenario_config['type']}_{int(datetime.now().timestamp())}"

            scenario = ScenarioAnalysis(
                scenario_id=scenario_id,
                name=scenario_config["name"],
                description=scenario_config["description"],
                model_id=model_id,
                scenario_type=scenario_config["type"],
                parameter_adjustments=scenario_config.get("adjustments", {}),
                external_assumptions=scenario_config.get("assumptions", {}),
                probability=scenario_config.get("probability", 0.33),
                created_by=scenario_config.get("created_by", "system"),
            )

            # Generate forecast for scenario (simplified - would modify input data based on scenario)
            # For now, we'll create mock scenario results
            base_predictions = np.random.normal(1000, 100, model.forecast_horizon)

            # Apply scenario adjustments
            adjustment_factor = scenario_config.get("adjustments", {}).get(
                "growth_rate", 0
            )
            adjusted_predictions = base_predictions * (1 + adjustment_factor)

            # Create scenario forecast result
            forecast_dates = pd.date_range(
                start=datetime.now(), periods=model.forecast_horizon, freq="D"
            )

            predictions_list = []
            for i, (date, pred) in enumerate(zip(forecast_dates, adjusted_predictions)):
                predictions_list.append(
                    {
                        "date": date.isoformat(),
                        "predicted_value": float(pred),
                        "day_offset": i + 1,
                    }
                )

            scenario_forecast = ForecastResult(
                forecast_id=f"forecast_{scenario_id}",
                model_id=model_id,
                predictions=predictions_list,
                confidence_intervals=[],
                forecast_horizon_days=model.forecast_horizon,
                data_points_used=100,  # Mock
                model_accuracy=0.8,
                confidence_score=0.75,
                trend_direction="increasing"
                if adjustment_factor > 0
                else "decreasing"
                if adjustment_factor < 0
                else "stable",
                key_insights=[
                    f"Scenario assumes {adjustment_factor * 100:.1f}% adjustment"
                ],
                risk_factors=[],
                recommendations=[],
            )

            scenario.forecast_results = scenario_forecast

            # Calculate business impact
            if scenario_config["type"] == "optimistic":
                scenario.revenue_impact = sum(adjusted_predictions) * 0.2
                scenario.risk_level = "low"
            elif scenario_config["type"] == "pessimistic":
                scenario.revenue_impact = sum(adjusted_predictions) * -0.2
                scenario.risk_level = "high"
            else:
                scenario.revenue_impact = 0
                scenario.risk_level = "medium"

            scenario_results.append(scenario)
            self.scenario_analyses[scenario_id] = scenario

        return scenario_results

    async def _run_scheduled_forecasts(self) -> None:
        """Run scheduled forecasts for active models."""
        for model in self.forecast_models.values():
            if model.status == "active":
                try:
                    # Check if forecast is due (simplified logic)
                    if (
                        not model.last_forecast
                        or (datetime.now() - model.last_forecast).days >= 1
                    ):
                        # Generate mock data for demonstration
                        mock_data = self._generate_mock_data(model)

                        # Run forecast
                        await self.create_forecast(model.model_id, mock_data)

                        print(
                            f"Automated forecast completed for model {model.model_id}"
                        )

                except Exception as e:
                    print(f"Automated forecast failed for model {model.model_id}: {e}")

    def _generate_mock_data(self, model: ForecastModel) -> pd.DataFrame:
        """Generate mock historical data for demonstration."""
        # Create 90 days of mock data
        dates = pd.date_range(
            end=datetime.now() - timedelta(days=1), periods=90, freq="D"
        )

        # Generate synthetic time series with trend and seasonality
        trend = np.linspace(1000, 1200, 90)
        seasonal = 100 * np.sin(2 * np.pi * np.arange(90) / 30)  # 30-day cycle
        noise = np.random.normal(0, 50, 90)

        values = trend + seasonal + noise

        data = pd.DataFrame({model.time_column: dates, model.target_variable: values})

        # Add external variables if specified
        for ext_var in model.external_variables:
            data[ext_var] = np.random.normal(100, 20, 90)

        return data

    async def _check_forecast_alerts(self) -> None:
        """Check alert rules against recent forecasts."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            try:
                # Get recent forecasts for the model
                recent_forecasts = [
                    f
                    for f in self.forecast_results.values()
                    if f.model_id == rule.model_id
                    and f.forecast_date > datetime.now() - timedelta(hours=24)
                ]

                for forecast in recent_forecasts:
                    should_trigger = False

                    if rule.metric == "model_accuracy":
                        if (
                            rule.condition == "less_than"
                            and forecast.model_accuracy < rule.threshold
                        ):
                            should_trigger = True
                    elif rule.metric == "anomaly_count":
                        anomaly_count = len(forecast.anomalies_detected)
                        if (
                            rule.condition == "greater_than"
                            and anomaly_count > rule.threshold
                        ):
                            should_trigger = True

                    if should_trigger:
                        await self._trigger_alert(rule, forecast)

            except Exception as e:
                print(f"Error checking alert rule {rule.rule_id}: {e}")

    async def _trigger_alert(self, rule: AlertRule, forecast: ForecastResult) -> None:
        """Trigger alert notification."""
        rule.last_triggered = datetime.now()
        rule.trigger_count += 1

        print(f"ALERT: {rule.name} triggered for forecast {forecast.forecast_id}")
        print(f"Severity: {rule.severity}")
        print(f"Metric: {rule.metric}, Threshold: {rule.threshold}")

    async def _validate_model_performance(self) -> None:
        """Validate forecast model performance against actual results."""
        for model in self.forecast_models.values():
            try:
                # In real implementation, would compare forecasts with actual results
                # For now, simulate validation

                if model.last_forecast:
                    days_since_forecast = (datetime.now() - model.last_forecast).days

                    if days_since_forecast > 7:  # Validate weekly
                        # Mock validation results
                        accuracy = np.random.uniform(0.7, 0.95)

                        model.mape = (1 - accuracy) * 100  # Convert to MAPE
                        model.rmse = np.random.uniform(50, 200)
                        model.mae = np.random.uniform(30, 150)

                        if accuracy < model.accuracy_threshold:
                            print(
                                f"Model {model.model_id} performance below threshold: {accuracy:.3f}"
                            )

            except Exception as e:
                print(f"Error validating model {model.model_id}: {e}")

    def get_forecast_result(self, forecast_id: str) -> Optional[ForecastResult]:
        """Get forecast result by ID."""
        return self.forecast_results.get(forecast_id)

    def list_forecasts(
        self, model_id: Optional[str] = None, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """List recent forecasts."""
        cutoff_date = datetime.now() - timedelta(days=days_back)

        forecasts = []
        for forecast in self.forecast_results.values():
            if forecast.forecast_date < cutoff_date:
                continue

            if model_id and forecast.model_id != model_id:
                continue

            forecasts.append(
                {
                    "forecast_id": forecast.forecast_id,
                    "model_id": forecast.model_id,
                    "forecast_date": forecast.forecast_date.isoformat(),
                    "horizon_days": forecast.forecast_horizon_days,
                    "accuracy": forecast.model_accuracy,
                    "trend_direction": forecast.trend_direction,
                    "anomalies_count": len(forecast.anomalies_detected),
                }
            )

        return sorted(forecasts, key=lambda x: x["forecast_date"], reverse=True)

    def get_system_overview(self) -> Dict[str, Any]:
        """Get predictive analytics system overview."""
        total_models = len(self.forecast_models)
        active_models = len(
            [m for m in self.forecast_models.values() if m.status == "active"]
        )

        return {
            "total_models": total_models,
            "active_models": active_models,
            "total_forecasts": len(self.forecast_results),
            "scenario_analyses": len(self.scenario_analyses),
            "alert_rules": len(self.alert_rules),
            "model_types": {
                ft.value: len(
                    [m for m in self.forecast_models.values() if m.forecast_type == ft]
                )
                for ft in ForecastType
            },
            "recent_activity": {
                "forecasts_last_24h": len(
                    [
                        f
                        for f in self.forecast_results.values()
                        if f.forecast_date > datetime.now() - timedelta(days=1)
                    ]
                ),
                "alerts_triggered": sum(
                    rule.trigger_count for rule in self.alert_rules.values()
                ),
                "average_accuracy": np.mean(
                    [
                        f.model_accuracy
                        for f in self.forecast_results.values()
                        if f.forecast_date > datetime.now() - timedelta(days=7)
                    ]
                )
                if self.forecast_results
                else 0.0,
            },
        }
