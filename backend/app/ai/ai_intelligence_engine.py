"""AI Intelligence Engine & Machine Learning Platform - CC02 v75.0 Day 20."""

from __future__ import annotations

import asyncio
import pickle
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ..sdk.mobile_sdk_core import MobileERPSDK


class ModelType(str, Enum):
    """Machine learning model types."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    DEEP_LEARNING = "deep_learning"
    NATURAL_LANGUAGE = "natural_language"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"


class ModelStatus(str, Enum):
    """Model training and deployment status."""

    DRAFT = "draft"
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class DataSourceType(str, Enum):
    """Data source types for ML pipeline."""

    DATABASE = "database"
    FILE = "file"
    API = "api"
    STREAM = "stream"
    MANUAL = "manual"


class FeatureType(str, Enum):
    """Feature data types."""

    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEXT = "text"
    IMAGE = "image"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class AIModel(BaseModel):
    """AI/ML model definition."""

    model_id: str
    name: str
    description: str
    model_type: ModelType

    # Model configuration
    algorithm: str  # random_forest, linear_regression, neural_network, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Training configuration
    target_variable: str
    feature_variables: List[str] = Field(default_factory=list)

    # Data preprocessing
    preprocessing_steps: List[Dict[str, Any]] = Field(default_factory=list)
    feature_engineering: List[Dict[str, Any]] = Field(default_factory=list)

    # Model validation
    validation_split: float = 0.2
    cross_validation_folds: int = 5

    # Performance metrics
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    feature_importance: Dict[str, float] = Field(default_factory=dict)

    # Model artifacts
    model_path: Optional[str] = None
    scaler_path: Optional[str] = None

    # Status and metadata
    status: ModelStatus = ModelStatus.DRAFT
    version: str = "1.0"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_trained: Optional[datetime] = None
    last_deployed: Optional[datetime] = None

    # Business context
    business_problem: str
    success_criteria: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)


class Feature(BaseModel):
    """Feature definition for ML pipeline."""

    feature_id: str
    name: str
    description: str
    feature_type: FeatureType

    # Data source
    source_table: str
    source_column: str

    # Transformations
    transformations: List[Dict[str, Any]] = Field(default_factory=list)

    # Statistics
    statistics: Dict[str, Any] = Field(default_factory=dict)

    # Data quality
    null_percentage: float = 0.0
    unique_values: int = 0
    data_quality_score: float = 1.0

    # Business metadata
    business_meaning: str
    is_sensitive: bool = False

    # Usage tracking
    models_using: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class DataPipeline(BaseModel):
    """Data pipeline for ML workflow."""

    pipeline_id: str
    name: str
    description: str

    # Data sources
    data_sources: List[Dict[str, Any]] = Field(default_factory=list)

    # Processing steps
    extraction_steps: List[Dict[str, Any]] = Field(default_factory=list)
    transformation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    validation_steps: List[Dict[str, Any]] = Field(default_factory=list)

    # Scheduling
    schedule_cron: Optional[str] = None
    auto_retrain_enabled: bool = False

    # Data quality
    quality_checks: List[Dict[str, Any]] = Field(default_factory=list)

    # Output configuration
    output_format: str = "parquet"
    output_location: str

    # Status
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    status: str = "idle"

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


class ModelExperiment(BaseModel):
    """ML model experiment tracking."""

    experiment_id: str
    model_id: str
    name: str
    description: str

    # Experiment configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dataset_version: str

    # Results
    metrics: Dict[str, float] = Field(default_factory=dict)
    artifacts: Dict[str, str] = Field(default_factory=dict)

    # Execution details
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Environment
    python_version: str
    dependencies: Dict[str, str] = Field(default_factory=dict)
    hardware_specs: Dict[str, Any] = Field(default_factory=dict)

    # Status
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None

    # Tags and metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class AIInference(BaseModel):
    """AI model inference request/response."""

    inference_id: str
    model_id: str

    # Input data
    input_data: Dict[str, Any] = Field(default_factory=dict)

    # Prediction results
    prediction: Optional[Any] = None
    confidence_score: Optional[float] = None
    prediction_probabilities: Optional[Dict[str, float]] = None

    # Execution details
    inference_time_ms: Optional[float] = None
    model_version: str

    # Context
    user_id: str
    session_id: str
    business_context: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Feedback
    actual_outcome: Optional[Any] = None
    feedback_score: Optional[float] = None
    feedback_notes: Optional[str] = None


class DataPreprocessor:
    """Data preprocessing utilities for ML pipeline."""

    def __init__(self) -> dict:
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, Any] = {}

    async def preprocess_data(
        self, data: pd.DataFrame, preprocessing_steps: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Apply preprocessing steps to data."""
        processed_data = data.copy()

        for step in preprocessing_steps:
            step_type = step.get("type")

            if step_type == "drop_nulls":
                processed_data = processed_data.dropna()

            elif step_type == "fill_nulls":
                fill_value = step.get("fill_value", 0)
                columns = step.get("columns", processed_data.columns)
                processed_data[columns] = processed_data[columns].fillna(fill_value)

            elif step_type == "scale_features":
                scaler_id = step.get("scaler_id", "default")
                columns = step.get("columns", [])

                if scaler_id not in self.scalers:
                    self.scalers[scaler_id] = StandardScaler()
                    processed_data[columns] = self.scalers[scaler_id].fit_transform(
                        processed_data[columns]
                    )
                else:
                    processed_data[columns] = self.scalers[scaler_id].transform(
                        processed_data[columns]
                    )

            elif step_type == "encode_categorical":
                columns = step.get("columns", [])
                method = step.get("method", "one_hot")

                if method == "one_hot":
                    processed_data = pd.get_dummies(processed_data, columns=columns)
                elif method == "label":
                    from sklearn.preprocessing import LabelEncoder

                    for col in columns:
                        encoder_key = f"label_encoder_{col}"
                        if encoder_key not in self.encoders:
                            self.encoders[encoder_key] = LabelEncoder()
                            processed_data[col] = self.encoders[
                                encoder_key
                            ].fit_transform(processed_data[col])
                        else:
                            processed_data[col] = self.encoders[encoder_key].transform(
                                processed_data[col]
                            )

            elif step_type == "remove_outliers":
                method = step.get("method", "iqr")
                columns = step.get("columns", [])

                if method == "iqr":
                    for col in columns:
                        Q1 = processed_data[col].quantile(0.25)
                        Q3 = processed_data[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        processed_data = processed_data[
                            (processed_data[col] >= lower_bound)
                            & (processed_data[col] <= upper_bound)
                        ]

            elif step_type == "feature_selection":
                columns = step.get("selected_columns", [])
                processed_data = processed_data[columns]

        return processed_data

    async def engineer_features(
        self, data: pd.DataFrame, feature_engineering_steps: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Apply feature engineering steps."""
        engineered_data = data.copy()

        for step in feature_engineering_steps:
            step_type = step.get("type")

            if step_type == "create_polynomial":
                columns = step.get("columns", [])
                degree = step.get("degree", 2)

                from sklearn.preprocessing import PolynomialFeatures

                poly = PolynomialFeatures(degree=degree, include_bias=False)

                for col in columns:
                    if col in engineered_data.columns:
                        poly_features = poly.fit_transform(engineered_data[[col]])
                        feature_names = [
                            f"{col}_poly_{i}" for i in range(1, poly_features.shape[1])
                        ]
                        poly_df = pd.DataFrame(
                            poly_features[:, 1:], columns=feature_names
                        )
                        engineered_data = pd.concat([engineered_data, poly_df], axis=1)

            elif step_type == "create_interaction":
                col1 = step.get("column1")
                col2 = step.get("column2")
                operation = step.get("operation", "multiply")

                if col1 in engineered_data.columns and col2 in engineered_data.columns:
                    if operation == "multiply":
                        engineered_data[f"{col1}_{col2}_interaction"] = (
                            engineered_data[col1] * engineered_data[col2]
                        )
                    elif operation == "add":
                        engineered_data[f"{col1}_{col2}_sum"] = (
                            engineered_data[col1] + engineered_data[col2]
                        )
                    elif operation == "subtract":
                        engineered_data[f"{col1}_{col2}_diff"] = (
                            engineered_data[col1] - engineered_data[col2]
                        )

            elif step_type == "create_binning":
                column = step.get("column")
                bins = step.get("bins", 5)
                labels = step.get("labels")

                if column in engineered_data.columns:
                    engineered_data[f"{column}_binned"] = pd.cut(
                        engineered_data[column], bins=bins, labels=labels
                    )

            elif step_type == "create_lag_features":
                column = step.get("column")
                lags = step.get("lags", [1, 2, 3])

                if column in engineered_data.columns:
                    for lag in lags:
                        engineered_data[f"{column}_lag_{lag}"] = engineered_data[
                            column
                        ].shift(lag)

            elif step_type == "create_rolling_features":
                column = step.get("column")
                window = step.get("window", 3)
                functions = step.get("functions", ["mean", "std"])

                if column in engineered_data.columns:
                    for func in functions:
                        if func == "mean":
                            engineered_data[f"{column}_rolling_mean_{window}"] = (
                                engineered_data[column].rolling(window).mean()
                            )
                        elif func == "std":
                            engineered_data[f"{column}_rolling_std_{window}"] = (
                                engineered_data[column].rolling(window).std()
                            )
                        elif func == "max":
                            engineered_data[f"{column}_rolling_max_{window}"] = (
                                engineered_data[column].rolling(window).max()
                            )
                        elif func == "min":
                            engineered_data[f"{column}_rolling_min_{window}"] = (
                                engineered_data[column].rolling(window).min()
                            )

        return engineered_data


class ModelTrainer:
    """Machine learning model training engine."""

    def __init__(self) -> dict:
        self.models: Dict[str, Any] = {}
        self.preprocessor = DataPreprocessor()

    async def train_model(
        self, model_config: AIModel, training_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Train ML model with given configuration and data."""
        try:
            # Preprocess data
            processed_data = await self.preprocessor.preprocess_data(
                training_data, model_config.preprocessing_steps
            )

            # Feature engineering
            if model_config.feature_engineering:
                processed_data = await self.preprocessor.engineer_features(
                    processed_data, model_config.feature_engineering
                )

            # Prepare features and target
            available_features = [
                f for f in model_config.feature_variables if f in processed_data.columns
            ]
            if not available_features:
                raise ValueError("No valid features found in the data")

            X = processed_data[available_features]
            y = processed_data[model_config.target_variable]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=model_config.validation_split, random_state=42
            )

            # Select and configure model
            ml_model = self._create_model(
                model_config.algorithm, model_config.parameters
            )

            # Train model
            start_time = datetime.now()
            ml_model.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()

            # Evaluate model
            metrics = await self._evaluate_model(
                ml_model, X_test, y_test, model_config.model_type
            )

            # Calculate feature importance
            feature_importance = {}
            if hasattr(ml_model, "feature_importances_"):
                feature_importance = dict(
                    zip(available_features, ml_model.feature_importances_)
                )
            elif hasattr(ml_model, "coef_"):
                feature_importance = dict(zip(available_features, abs(ml_model.coef_)))

            # Save model
            model_path = f"models/{model_config.model_id}_v{model_config.version}.pkl"
            Path("models").mkdir(exist_ok=True)

            with open(model_path, "wb") as f:
                pickle.dump(ml_model, f)

            # Save preprocessor if needed
            scaler_path = None
            if self.preprocessor.scalers:
                scaler_path = (
                    f"models/{model_config.model_id}_scaler_v{model_config.version}.pkl"
                )
                with open(scaler_path, "wb") as f:
                    pickle.dump(self.preprocessor.scalers, f)

            # Update model configuration
            model_config.model_path = model_path
            model_config.scaler_path = scaler_path
            model_config.performance_metrics = metrics
            model_config.feature_importance = feature_importance
            model_config.status = ModelStatus.TRAINED
            model_config.last_trained = datetime.now()

            # Store model in memory
            self.models[model_config.model_id] = ml_model

            return {
                "success": True,
                "model_id": model_config.model_id,
                "metrics": metrics,
                "feature_importance": feature_importance,
                "training_time_seconds": training_time,
                "model_path": model_path,
            }

        except Exception as e:
            model_config.status = ModelStatus.FAILED
            return {
                "success": False,
                "error": str(e),
                "model_id": model_config.model_id,
            }

    def _create_model(self, algorithm: str, parameters: Dict[str, Any]) -> Any:
        """Create ML model instance based on algorithm."""
        if algorithm == "random_forest_classifier":
            return RandomForestClassifier(**parameters)
        elif algorithm == "random_forest_regressor":
            return RandomForestRegressor(**parameters)
        elif algorithm == "linear_regression":
            return LinearRegression(**parameters)
        elif algorithm == "logistic_regression":
            return LogisticRegression(**parameters)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    async def _evaluate_model(
        self, model: Any, X_test: pd.DataFrame, y_test: pd.Series, model_type: ModelType
    ) -> Dict[str, float]:
        """Evaluate model performance."""
        y_pred = model.predict(X_test)

        metrics = {}

        if model_type == ModelType.CLASSIFICATION:
            metrics["accuracy"] = accuracy_score(y_test, y_pred)

            # Get classification report
            report = classification_report(y_test, y_pred, output_dict=True)
            metrics["precision"] = report["weighted avg"]["precision"]
            metrics["recall"] = report["weighted avg"]["recall"]
            metrics["f1_score"] = report["weighted avg"]["f1-score"]

            # Confusion matrix metrics
            from sklearn.metrics import confusion_matrix

            cm = confusion_matrix(y_test, y_pred)
            metrics["true_positives"] = float(cm[1, 1]) if cm.shape == (2, 2) else 0
            metrics["false_positives"] = float(cm[0, 1]) if cm.shape == (2, 2) else 0
            metrics["true_negatives"] = float(cm[0, 0]) if cm.shape == (2, 2) else 0
            metrics["false_negatives"] = float(cm[1, 0]) if cm.shape == (2, 2) else 0

        elif model_type == ModelType.REGRESSION:
            metrics["mse"] = mean_squared_error(y_test, y_pred)
            metrics["rmse"] = np.sqrt(metrics["mse"])

            from sklearn.metrics import mean_absolute_error, r2_score

            metrics["r2_score"] = r2_score(y_test, y_pred)
            metrics["mae"] = mean_absolute_error(y_test, y_pred)

            # Additional regression metrics
            metrics["mape"] = (
                np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            )  # Mean Absolute Percentage Error

        return metrics

    async def predict(
        self, model_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make prediction using trained model."""
        if model_id not in self.models:
            # Try to load model from disk
            model_config = None  # This would come from model registry
            if model_config and model_config.model_path:
                try:
                    with open(model_config.model_path, "rb") as f:
                        self.models[model_id] = pickle.load(f)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to load model: {str(e)}",
                    }
            else:
                return {"success": False, "error": f"Model {model_id} not found"}

        try:
            model = self.models[model_id]

            # Convert input data to DataFrame
            input_df = pd.DataFrame([input_data])

            # Make prediction
            start_time = datetime.now()
            prediction = model.predict(input_df)
            inference_time = (datetime.now() - start_time).total_seconds() * 1000

            # Get prediction probabilities if available
            probabilities = None
            confidence_score = None

            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(input_df)
                probabilities = {
                    f"class_{i}": float(prob) for i, prob in enumerate(proba[0])
                }
                confidence_score = float(max(proba[0]))

            return {
                "success": True,
                "prediction": prediction[0]
                if len(prediction) == 1
                else prediction.tolist(),
                "confidence_score": confidence_score,
                "probabilities": probabilities,
                "inference_time_ms": inference_time,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class ExperimentTracker:
    """ML experiment tracking and management."""

    def __init__(self) -> dict:
        self.experiments: Dict[str, ModelExperiment] = {}
        self.experiment_results: Dict[str, Dict[str, Any]] = {}

    async def start_experiment(
        self,
        model_id: str,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        dataset_version: str,
    ) -> str:
        """Start a new ML experiment."""
        experiment_id = f"exp_{model_id}_{int(datetime.now().timestamp())}"

        experiment = ModelExperiment(
            experiment_id=experiment_id,
            model_id=model_id,
            name=name,
            description=description,
            parameters=parameters,
            dataset_version=dataset_version,
            python_version="3.11",
            dependencies={
                "scikit-learn": "1.3.0",
                "pandas": "2.0.3",
                "numpy": "1.24.3",
            },
        )

        self.experiments[experiment_id] = experiment

        return experiment_id

    async def log_metric(
        self, experiment_id: str, metric_name: str, value: float
    ) -> None:
        """Log metric for experiment."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].metrics[metric_name] = value

    async def log_artifact(
        self, experiment_id: str, artifact_name: str, artifact_path: str
    ) -> None:
        """Log artifact for experiment."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].artifacts[artifact_name] = artifact_path

    async def complete_experiment(
        self,
        experiment_id: str,
        status: str = "completed",
        error_message: Optional[str] = None,
    ) -> None:
        """Mark experiment as completed."""
        if experiment_id in self.experiments:
            experiment = self.experiments[experiment_id]
            experiment.end_time = datetime.now()
            experiment.duration_seconds = (
                experiment.end_time - experiment.start_time
            ).total_seconds()
            experiment.status = status
            if error_message:
                experiment.error_message = error_message

    async def compare_experiments(
        self, experiment_ids: List[str], metrics: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple experiments."""
        comparison_data = {
            "experiments": [],
            "metrics": metrics,
            "best_experiment": None,
        }

        best_score = None
        best_experiment_id = None
        primary_metric = metrics[0] if metrics else None

        for exp_id in experiment_ids:
            if exp_id in self.experiments:
                experiment = self.experiments[exp_id]
                exp_data = {
                    "experiment_id": exp_id,
                    "name": experiment.name,
                    "parameters": experiment.parameters,
                    "metrics": {
                        metric: experiment.metrics.get(metric) for metric in metrics
                    },
                    "duration_seconds": experiment.duration_seconds,
                    "status": experiment.status,
                }

                comparison_data["experiments"].append(exp_data)

                # Track best experiment based on primary metric
                if primary_metric and primary_metric in experiment.metrics:
                    score = experiment.metrics[primary_metric]
                    if best_score is None or score > best_score:
                        best_score = score
                        best_experiment_id = exp_id

        comparison_data["best_experiment"] = best_experiment_id

        return comparison_data

    def list_experiments(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List experiments with optional filtering."""
        experiments = []

        for experiment in self.experiments.values():
            if model_id and experiment.model_id != model_id:
                continue

            experiments.append(
                {
                    "experiment_id": experiment.experiment_id,
                    "model_id": experiment.model_id,
                    "name": experiment.name,
                    "status": experiment.status,
                    "start_time": experiment.start_time.isoformat(),
                    "duration_seconds": experiment.duration_seconds,
                    "metrics": experiment.metrics,
                }
            )

        return sorted(experiments, key=lambda x: x["start_time"], reverse=True)


class AIIntelligenceEngine:
    """Main AI Intelligence Engine and ML Platform."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk

        # Core components
        self.models: Dict[str, AIModel] = {}
        self.features: Dict[str, Feature] = {}
        self.pipelines: Dict[str, DataPipeline] = {}

        # Engines
        self.model_trainer = ModelTrainer()
        self.experiment_tracker = ExperimentTracker()
        self.preprocessor = DataPreprocessor()

        # Inference tracking
        self.inferences: Dict[str, AIInference] = {}

        # System metrics
        self.system_metrics = {
            "total_models": 0,
            "active_models": 0,
            "total_predictions": 0,
            "average_inference_time_ms": 0.0,
            "model_accuracy": {},
            "experiments_run": 0,
        }

        # Setup default models and features
        self._setup_default_models()
        self._setup_default_features()

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()

    def _setup_default_models(self) -> None:
        """Setup default AI models for ERP use cases."""
        # Sales Forecasting Model
        sales_forecast_model = AIModel(
            model_id="sales_forecast_rf",
            name="Sales Revenue Forecasting",
            description="Predict monthly sales revenue using historical data and market indicators",
            model_type=ModelType.REGRESSION,
            algorithm="random_forest_regressor",
            parameters={"n_estimators": 100, "max_depth": 10, "random_state": 42},
            target_variable="sales_revenue",
            feature_variables=[
                "previous_month_sales",
                "season",
                "marketing_spend",
                "economic_indicator",
                "customer_count",
                "avg_order_value",
            ],
            preprocessing_steps=[
                {"type": "fill_nulls", "fill_value": 0},
                {
                    "type": "scale_features",
                    "columns": ["marketing_spend", "customer_count"],
                },
                {
                    "type": "encode_categorical",
                    "columns": ["season"],
                    "method": "one_hot",
                },
            ],
            feature_engineering=[
                {
                    "type": "create_lag_features",
                    "column": "sales_revenue",
                    "lags": [1, 2, 3],
                },
                {
                    "type": "create_rolling_features",
                    "column": "sales_revenue",
                    "window": 3,
                    "functions": ["mean", "std"],
                },
            ],
            business_problem="Predict future sales revenue to optimize inventory and resource planning",
            success_criteria=["MAPE < 15%", "R² > 0.8", "Monthly prediction accuracy"],
            created_by="system",
        )

        self.models[sales_forecast_model.model_id] = sales_forecast_model

        # Customer Churn Prediction
        churn_prediction_model = AIModel(
            model_id="customer_churn_rf",
            name="Customer Churn Prediction",
            description="Predict customer churn probability based on behavior and transaction history",
            model_type=ModelType.CLASSIFICATION,
            algorithm="random_forest_classifier",
            parameters={
                "n_estimators": 150,
                "max_depth": 8,
                "min_samples_split": 5,
                "random_state": 42,
            },
            target_variable="churned",
            feature_variables=[
                "days_since_last_order",
                "total_orders",
                "avg_order_value",
                "customer_lifetime_value",
                "support_tickets",
                "payment_delays",
            ],
            preprocessing_steps=[
                {"type": "fill_nulls", "fill_value": 0},
                {
                    "type": "scale_features",
                    "columns": [
                        "total_orders",
                        "avg_order_value",
                        "customer_lifetime_value",
                    ],
                },
                {
                    "type": "remove_outliers",
                    "method": "iqr",
                    "columns": ["customer_lifetime_value"],
                },
            ],
            business_problem="Identify customers at risk of churning to enable proactive retention efforts",
            success_criteria=["Accuracy > 85%", "Precision > 80%", "Recall > 75%"],
            created_by="system",
        )

        self.models[churn_prediction_model.model_id] = churn_prediction_model

        # Inventory Optimization Model
        inventory_optimization_model = AIModel(
            model_id="inventory_optimization_lr",
            name="Inventory Level Optimization",
            description="Optimize inventory levels to minimize costs while avoiding stockouts",
            model_type=ModelType.REGRESSION,
            algorithm="linear_regression",
            parameters={},
            target_variable="optimal_stock_level",
            feature_variables=[
                "historical_demand_avg",
                "demand_variance",
                "lead_time",
                "holding_cost_per_unit",
                "stockout_cost",
                "seasonality_factor",
            ],
            preprocessing_steps=[
                {"type": "fill_nulls", "fill_value": 0},
                {
                    "type": "scale_features",
                    "columns": [
                        "historical_demand_avg",
                        "holding_cost_per_unit",
                        "stockout_cost",
                    ],
                },
            ],
            business_problem="Determine optimal inventory levels to balance carrying costs and service levels",
            success_criteria=[
                "Reduce stockouts by 30%",
                "Decrease holding costs by 20%",
            ],
            created_by="system",
        )

        self.models[inventory_optimization_model.model_id] = (
            inventory_optimization_model
        )

        # Fraud Detection Model
        fraud_detection_model = AIModel(
            model_id="fraud_detection_lr",
            name="Financial Transaction Fraud Detection",
            description="Detect fraudulent transactions in real-time",
            model_type=ModelType.CLASSIFICATION,
            algorithm="logistic_regression",
            parameters={"max_iter": 1000, "random_state": 42},
            target_variable="is_fraud",
            feature_variables=[
                "transaction_amount",
                "transaction_hour",
                "days_since_last_transaction",
                "merchant_category",
                "card_present",
                "cross_border",
                "velocity_1h",
                "velocity_24h",
            ],
            preprocessing_steps=[
                {
                    "type": "scale_features",
                    "columns": ["transaction_amount", "velocity_1h", "velocity_24h"],
                },
                {
                    "type": "encode_categorical",
                    "columns": ["merchant_category"],
                    "method": "one_hot",
                },
            ],
            business_problem="Detect and prevent fraudulent transactions while minimizing false positives",
            success_criteria=[
                "Precision > 90%",
                "Recall > 80%",
                "False positive rate < 1%",
            ],
            created_by="system",
        )

        self.models[fraud_detection_model.model_id] = fraud_detection_model

    def _setup_default_features(self) -> None:
        """Setup default feature definitions."""
        # Sales features
        sales_revenue_feature = Feature(
            feature_id="sales_revenue",
            name="Monthly Sales Revenue",
            description="Total sales revenue for the month",
            feature_type=FeatureType.NUMERICAL,
            source_table="sales_summary",
            source_column="total_revenue",
            business_meaning="Key performance indicator for business success",
            models_using=["sales_forecast_rf"],
        )

        self.features[sales_revenue_feature.feature_id] = sales_revenue_feature

        # Customer features
        customer_ltv_feature = Feature(
            feature_id="customer_lifetime_value",
            name="Customer Lifetime Value",
            description="Predicted total value of customer relationship",
            feature_type=FeatureType.NUMERICAL,
            source_table="customers",
            source_column="calculated_ltv",
            business_meaning="Measure of customer value for retention and acquisition decisions",
            models_using=["customer_churn_rf"],
        )

        self.features[customer_ltv_feature.feature_id] = customer_ltv_feature

        # Transaction features
        transaction_amount_feature = Feature(
            feature_id="transaction_amount",
            name="Transaction Amount",
            description="Monetary value of the transaction",
            feature_type=FeatureType.NUMERICAL,
            source_table="transactions",
            source_column="amount",
            business_meaning="Primary indicator for fraud detection and analysis",
            is_sensitive=True,
            models_using=["fraud_detection_lr"],
        )

        self.features[transaction_amount_feature.feature_id] = (
            transaction_amount_feature
        )

    def _start_background_tasks(self) -> None:
        """Start background AI processing tasks."""
        # Model performance monitoring
        task = asyncio.create_task(self._model_monitoring_loop())
        self._background_tasks.append(task)

        # Automated retraining
        task = asyncio.create_task(self._auto_retrain_loop())
        self._background_tasks.append(task)

        # Metrics collection
        task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.append(task)

    async def _model_monitoring_loop(self) -> None:
        """Background model performance monitoring."""
        while True:
            try:
                await self._monitor_model_performance()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                print(f"Error in model monitoring loop: {e}")
                await asyncio.sleep(3600)

    async def _auto_retrain_loop(self) -> None:
        """Background automated model retraining."""
        while True:
            try:
                await self._check_retrain_triggers()
                await asyncio.sleep(86400)  # Check daily
            except Exception as e:
                print(f"Error in auto retrain loop: {e}")
                await asyncio.sleep(86400)

    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection."""
        while True:
            try:
                await self._update_system_metrics()
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                print(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(300)

    async def train_model(
        self, model_id: str, training_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Train AI model with provided data."""
        model_config = self.models.get(model_id)
        if not model_config:
            return {"success": False, "error": f"Model {model_id} not found"}

        # Start experiment
        experiment_id = await self.experiment_tracker.start_experiment(
            model_id=model_id,
            name=f"Training {model_config.name}",
            description="Automated model training",
            parameters=model_config.parameters,
            dataset_version="latest",
        )

        try:
            # Train model
            result = await self.model_trainer.train_model(model_config, training_data)

            if result["success"]:
                # Log experiment results
                for metric_name, metric_value in result["metrics"].items():
                    await self.experiment_tracker.log_metric(
                        experiment_id, metric_name, metric_value
                    )

                await self.experiment_tracker.log_artifact(
                    experiment_id, "model", result["model_path"]
                )
                await self.experiment_tracker.complete_experiment(
                    experiment_id, "completed"
                )
            else:
                await self.experiment_tracker.complete_experiment(
                    experiment_id, "failed", result.get("error")
                )

            return result

        except Exception as e:
            await self.experiment_tracker.complete_experiment(
                experiment_id, "failed", str(e)
            )
            return {"success": False, "error": str(e)}

    async def predict(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        session_id: str,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make prediction using trained model."""
        # Create inference record
        inference_id = f"inf_{model_id}_{int(datetime.now().timestamp())}"

        inference = AIInference(
            inference_id=inference_id,
            model_id=model_id,
            input_data=input_data,
            user_id=user_id,
            session_id=session_id,
            business_context=business_context or {},
            model_version="1.0",
        )

        # Make prediction
        prediction_result = await self.model_trainer.predict(model_id, input_data)

        if prediction_result["success"]:
            inference.prediction = prediction_result["prediction"]
            inference.confidence_score = prediction_result.get("confidence_score")
            inference.prediction_probabilities = prediction_result.get("probabilities")
            inference.inference_time_ms = prediction_result["inference_time_ms"]
            inference.completed_at = datetime.now()

        # Store inference
        self.inferences[inference_id] = inference

        # Update system metrics
        self.system_metrics["total_predictions"] += 1

        return {**prediction_result, "inference_id": inference_id}

    async def _monitor_model_performance(self) -> None:
        """Monitor model performance and detect drift."""
        for model_id, model in self.models.items():
            if model.status != ModelStatus.DEPLOYED:
                continue

            try:
                # Get recent inferences
                recent_inferences = [
                    inf
                    for inf in self.inferences.values()
                    if inf.model_id == model_id
                    and inf.requested_at > datetime.now() - timedelta(days=7)
                ]

                if len(recent_inferences) < 10:
                    continue

                # Calculate performance metrics
                accuracy_scores = []
                response_times = []

                for inf in recent_inferences:
                    if inf.actual_outcome is not None and inf.prediction is not None:
                        # Simple accuracy check
                        if inf.actual_outcome == inf.prediction:
                            accuracy_scores.append(1.0)
                        else:
                            accuracy_scores.append(0.0)

                    if inf.inference_time_ms is not None:
                        response_times.append(inf.inference_time_ms)

                # Update model metrics
                if accuracy_scores:
                    current_accuracy = np.mean(accuracy_scores)
                    self.system_metrics["model_accuracy"][model_id] = current_accuracy

                    # Check for performance degradation
                    baseline_accuracy = model.performance_metrics.get("accuracy", 0.8)
                    if current_accuracy < baseline_accuracy * 0.9:  # 10% degradation
                        print(
                            f"Performance degradation detected for model {model_id}: "
                            f"{current_accuracy:.3f} vs baseline {baseline_accuracy:.3f}"
                        )

                if response_times:
                    avg_response_time = np.mean(response_times)
                    if avg_response_time > 1000:  # > 1 second
                        print(
                            f"High response time detected for model {model_id}: {avg_response_time:.1f}ms"
                        )

            except Exception as e:
                print(f"Error monitoring model {model_id}: {e}")

    async def _check_retrain_triggers(self) -> None:
        """Check if models need retraining."""
        for model_id, model in self.models.items():
            try:
                # Check if model hasn't been trained recently
                if model.last_trained:
                    days_since_training = (datetime.now() - model.last_trained).days

                    # Retrain if model is older than 30 days
                    if days_since_training > 30:
                        print(
                            f"Model {model_id} is {days_since_training} days old, scheduling retrain"
                        )
                        # In real implementation, would trigger retraining with fresh data

                # Check performance degradation
                current_accuracy = self.system_metrics["model_accuracy"].get(model_id)
                if current_accuracy is not None:
                    baseline_accuracy = model.performance_metrics.get("accuracy", 0.8)
                    if current_accuracy < baseline_accuracy * 0.85:  # 15% degradation
                        print(
                            f"Model {model_id} performance degraded, scheduling retrain"
                        )

            except Exception as e:
                print(f"Error checking retrain triggers for model {model_id}: {e}")

    async def _update_system_metrics(self) -> None:
        """Update system-wide AI metrics."""
        self.system_metrics["total_models"] = len(self.models)
        self.system_metrics["active_models"] = len(
            [
                m
                for m in self.models.values()
                if m.status in [ModelStatus.DEPLOYED, ModelStatus.TRAINED]
            ]
        )

        # Calculate average inference time
        recent_inferences = [
            inf
            for inf in self.inferences.values()
            if inf.completed_at
            and inf.completed_at > datetime.now() - timedelta(hours=1)
        ]

        if recent_inferences:
            avg_inference_time = np.mean(
                [
                    inf.inference_time_ms
                    for inf in recent_inferences
                    if inf.inference_time_ms is not None
                ]
            )
            self.system_metrics["average_inference_time_ms"] = avg_inference_time

        self.system_metrics["experiments_run"] = len(
            self.experiment_tracker.experiments
        )

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed model information."""
        model = self.models.get(model_id)
        if not model:
            return None

        return {
            "model_id": model.model_id,
            "name": model.name,
            "description": model.description,
            "model_type": model.model_type,
            "algorithm": model.algorithm,
            "status": model.status,
            "performance_metrics": model.performance_metrics,
            "feature_importance": model.feature_importance,
            "last_trained": model.last_trained.isoformat()
            if model.last_trained
            else None,
            "business_problem": model.business_problem,
            "success_criteria": model.success_criteria,
        }

    def list_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List AI models with optional filtering."""
        models = []

        for model in self.models.values():
            if model_type and model.model_type != model_type:
                continue
            if status and model.status != status:
                continue

            models.append(
                {
                    "model_id": model.model_id,
                    "name": model.name,
                    "model_type": model.model_type,
                    "algorithm": model.algorithm,
                    "status": model.status,
                    "last_trained": model.last_trained.isoformat()
                    if model.last_trained
                    else None,
                    "performance_score": model.performance_metrics.get("accuracy")
                    or model.performance_metrics.get("r2_score"),
                    "created_by": model.created_by,
                }
            )

        return sorted(models, key=lambda x: x["name"])

    def get_system_overview(self) -> Dict[str, Any]:
        """Get AI system overview and metrics."""
        return {
            **self.system_metrics,
            "model_status_breakdown": {
                "draft": len(
                    [m for m in self.models.values() if m.status == ModelStatus.DRAFT]
                ),
                "training": len(
                    [
                        m
                        for m in self.models.values()
                        if m.status == ModelStatus.TRAINING
                    ]
                ),
                "trained": len(
                    [m for m in self.models.values() if m.status == ModelStatus.TRAINED]
                ),
                "deployed": len(
                    [
                        m
                        for m in self.models.values()
                        if m.status == ModelStatus.DEPLOYED
                    ]
                ),
                "failed": len(
                    [m for m in self.models.values() if m.status == ModelStatus.FAILED]
                ),
            },
            "model_type_distribution": {
                "classification": len(
                    [
                        m
                        for m in self.models.values()
                        if m.model_type == ModelType.CLASSIFICATION
                    ]
                ),
                "regression": len(
                    [
                        m
                        for m in self.models.values()
                        if m.model_type == ModelType.REGRESSION
                    ]
                ),
                "clustering": len(
                    [
                        m
                        for m in self.models.values()
                        if m.model_type == ModelType.CLUSTERING
                    ]
                ),
                "time_series": len(
                    [
                        m
                        for m in self.models.values()
                        if m.model_type == ModelType.TIME_SERIES
                    ]
                ),
            },
            "recent_activity": {
                "predictions_last_24h": len(
                    [
                        inf
                        for inf in self.inferences.values()
                        if inf.requested_at > datetime.now() - timedelta(days=1)
                    ]
                ),
                "experiments_last_week": len(
                    [
                        exp
                        for exp in self.experiment_tracker.experiments.values()
                        if exp.start_time > datetime.now() - timedelta(days=7)
                    ]
                ),
            },
        }
