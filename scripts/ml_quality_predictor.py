#!/usr/bin/env python3
"""
CC02 v33.0 機械学習品質予測システム - Infinite Loop Cycle 7
Machine Learning Quality Prediction System for Proactive Quality Management
"""

import json
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# Simulated ML libraries (since sklearn might not be available)
class SimpleMLModel:
    """簡易機械学習モデル"""
    
    def __init__(self, model_type: str = "quality_predictor"):
        self.model_type = model_type
        self.is_trained = False
        self.feature_names = []
        self.weights = {}
        self.bias = 0.0
        self.training_data = []
        
    def fit(self, X: List[List[float]], y: List[float], feature_names: List[str]):
        """モデル訓練（簡易線形回帰）"""
        self.feature_names = feature_names
        self.training_data = list(zip(X, y))
        
        # Simple linear regression implementation
        if len(X) > 0 and len(X[0]) > 0:
            n_features = len(X[0])
            
            # Initialize weights randomly
            self.weights = {name: np.random.normal(0, 0.1) for name in feature_names}
            self.bias = np.random.normal(0, 0.1)
            
            # Simple gradient descent
            learning_rate = 0.01
            epochs = 100
            
            for epoch in range(epochs):
                total_loss = 0
                for features, target in zip(X, y):
                    # Forward pass
                    prediction = self.bias + sum(self.weights[name] * features[i] 
                                               for i, name in enumerate(feature_names))
                    
                    # Calculate loss
                    loss = (prediction - target) ** 2
                    total_loss += loss
                    
                    # Backward pass
                    error = prediction - target
                    for i, name in enumerate(feature_names):
                        self.weights[name] -= learning_rate * error * features[i]
                    self.bias -= learning_rate * error
        
        self.is_trained = True
        return self
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """予測実行"""
        if not self.is_trained:
            return [50.0] * len(X)  # Default prediction
        
        predictions = []
        for features in X:
            prediction = self.bias + sum(self.weights[name] * features[i] 
                                       for i, name in enumerate(self.feature_names))
            predictions.append(max(0.0, min(100.0, prediction)))  # Clamp to 0-100
        
        return predictions
    
    def feature_importance(self) -> Dict[str, float]:
        """特徴量重要度"""
        if not self.is_trained:
            return {}
        
        total_weight = sum(abs(w) for w in self.weights.values())
        if total_weight == 0:
            return {name: 0.0 for name in self.feature_names}
        
        return {name: abs(weight) / total_weight 
                for name, weight in self.weights.items()}


@dataclass
class QualityPrediction:
    """品質予測結果"""
    file_path: str
    current_score: float
    predicted_score: float
    prediction_confidence: float
    risk_level: str
    recommended_actions: List[str]
    trend_analysis: str


@dataclass
class QualityTrend:
    """品質トレンド"""
    metric_name: str
    historical_values: List[float]
    trend_direction: str
    predicted_next_value: float
    confidence_interval: Tuple[float, float]


class MLQualityPredictor:
    """機械学習品質予測システム"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.scripts_path = project_root / "scripts"
        self.output_path = project_root / "scripts" / "ml_quality_reports"
        self.models_path = project_root / "scripts" / "ml_models"
        self.output_path.mkdir(exist_ok=True)
        self.models_path.mkdir(exist_ok=True)
        
        # ML Models for different aspects
        self.models = {
            "code_quality": SimpleMLModel("code_quality_predictor"),
            "security_risk": SimpleMLModel("security_risk_predictor"),
            "performance_trend": SimpleMLModel("performance_trend_predictor"),
            "bug_probability": SimpleMLModel("bug_probability_predictor"),
            "maintenance_effort": SimpleMLModel("maintenance_effort_predictor")
        }
        
        # Feature extractors
        self.feature_extractors = {
            "code_metrics": self._extract_code_metrics,
            "historical_data": self._extract_historical_data,
            "complexity_features": self._extract_complexity_features,
            "security_features": self._extract_security_features,
            "collaboration_features": self._extract_collaboration_features
        }
        
        # Quality thresholds for predictions
        self.quality_thresholds = {
            "excellent": 90,
            "good": 75,
            "acceptable": 60,
            "poor": 40,
            "critical": 20
        }
        
        # Historical data storage
        self.historical_data = self._load_historical_data()
    
    def _load_historical_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """履歴データ読み込み"""
        historical_data = defaultdict(list)
        
        # Load data from all previous analysis reports
        for report_type in ["code_review_reports", "security_reports", 
                           "performance_analysis_reports", "db_optimization_reports"]:
            report_dir = self.scripts_path / report_type
            if report_dir.exists():
                for report_file in report_dir.glob("*.json"):
                    try:
                        with open(report_file, 'r') as f:
                            data = json.load(f)
                        
                        timestamp = data.get("analysis_timestamp") or data.get("scan_timestamp") or datetime.now().isoformat()
                        historical_data[report_type].append({
                            "timestamp": timestamp,
                            "data": data,
                            "file": str(report_file)
                        })
                    except Exception as e:
                        print(f"Warning: Could not load {report_file}: {e}")
        
        return historical_data
    
    def _extract_code_metrics(self, file_data: Dict[str, Any]) -> List[float]:
        """コードメトリクス特徴量抽出"""
        features = []
        
        # Basic metrics
        features.append(file_data.get("lines_of_code", 0))
        features.append(file_data.get("cyclomatic_complexity", 0))
        features.append(file_data.get("function_count", 0))
        features.append(file_data.get("class_count", 0))
        
        # Quality indicators
        features.append(file_data.get("comment_ratio", 0))
        features.append(file_data.get("test_coverage", 0))
        features.append(file_data.get("documentation_score", 0))
        
        # Complexity indicators
        features.append(file_data.get("max_nesting_level", 0))
        features.append(file_data.get("average_function_length", 0))
        features.append(file_data.get("parameter_count_avg", 0))
        
        return features
    
    def _extract_historical_data(self, file_path: str) -> List[float]:
        """履歴データ特徴量抽出"""
        features = []
        
        # Calculate historical trends for this file
        file_history = []
        for report_type, reports in self.historical_data.items():
            for report in reports:
                if file_path in str(report.get("data", {})):
                    file_history.append(report)
        
        # Sort by timestamp
        file_history.sort(key=lambda x: x["timestamp"])
        
        # Extract trend features
        if len(file_history) >= 2:
            # Recent change frequency
            recent_changes = len([h for h in file_history[-5:]])
            features.append(recent_changes)
            
            # Quality score trend
            quality_scores = []
            for h in file_history:
                score = self._extract_quality_score_from_history(h["data"])
                if score is not None:
                    quality_scores.append(score)
            
            if len(quality_scores) >= 2:
                trend = quality_scores[-1] - quality_scores[-2] if len(quality_scores) >= 2 else 0
                features.append(trend)
                features.append(np.mean(quality_scores))
                features.append(np.std(quality_scores))
            else:
                features.extend([0, 50, 0])
        else:
            features.extend([0, 0, 50, 0])
        
        return features
    
    def _extract_complexity_features(self, file_data: Dict[str, Any]) -> List[float]:
        """複雑度特徴量抽出"""
        features = []
        
        # Structural complexity
        features.append(file_data.get("import_count", 0))
        features.append(file_data.get("dependency_count", 0))
        features.append(file_data.get("inheritance_depth", 0))
        
        # Code smell indicators
        features.append(file_data.get("long_functions", 0))
        features.append(file_data.get("god_classes", 0))
        features.append(file_data.get("duplicate_code_blocks", 0))
        
        # Maintainability indicators
        features.append(file_data.get("maintainability_index", 50))
        features.append(file_data.get("technical_debt_ratio", 0))
        
        return features
    
    def _extract_security_features(self, file_data: Dict[str, Any]) -> List[float]:
        """セキュリティ特徴量抽出"""
        features = []
        
        # Security vulnerability indicators
        features.append(file_data.get("critical_vulnerabilities", 0))
        features.append(file_data.get("high_vulnerabilities", 0))
        features.append(file_data.get("medium_vulnerabilities", 0))
        
        # Security patterns
        features.append(file_data.get("input_validation_score", 50))
        features.append(file_data.get("authentication_strength", 50))
        features.append(file_data.get("encryption_usage", 50))
        
        return features
    
    def _extract_collaboration_features(self, file_data: Dict[str, Any]) -> List[float]:
        """協働特徴量抽出"""
        features = []
        
        # Developer activity indicators
        features.append(file_data.get("recent_commits", 0))
        features.append(file_data.get("contributor_count", 1))
        features.append(file_data.get("review_frequency", 0))
        
        # Code review quality
        features.append(file_data.get("review_comments_avg", 0))
        features.append(file_data.get("approval_time_avg", 24))  # hours
        
        return features
    
    def _extract_quality_score_from_history(self, historical_report: Dict[str, Any]) -> Optional[float]:
        """履歴レポートから品質スコア抽出"""
        # Try different score extraction methods
        if "overall_statistics" in historical_report:
            return historical_report["overall_statistics"].get("average_code_quality_score", None)
        
        if "security_metrics" in historical_report:
            return historical_report["security_metrics"].get("security_score", None)
        
        if "quality_metrics" in historical_report:
            return historical_report["quality_metrics"].get("overall_quality_grade", None)
        
        return None
    
    def train_prediction_models(self) -> Dict[str, Any]:
        """予測モデル訓練"""
        print("🧠 Training ML quality prediction models...")
        
        training_results = {
            "models_trained": 0,
            "training_data_points": 0,
            "feature_importance": {},
            "model_performance": {}
        }
        
        # Prepare training data from historical reports
        training_data = self._prepare_training_data()
        
        if not training_data or len(training_data) < 10:
            print("⚠️ Insufficient historical data for ML training. Using baseline models.")
            training_results["warning"] = "Insufficient data - using baseline models"
            return training_results
        
        # Train each model
        for model_name, model in self.models.items():
            print(f"  📈 Training {model_name} model...")
            
            try:
                # Prepare features and targets for this model
                X, y, feature_names = self._prepare_model_data(training_data, model_name)
                
                if len(X) > 0:
                    # Train the model
                    model.fit(X, y, feature_names)
                    
                    # Calculate basic performance metrics
                    predictions = model.predict(X)
                    mse = np.mean([(pred - actual) ** 2 for pred, actual in zip(predictions, y)])
                    
                    training_results["models_trained"] += 1
                    training_results["feature_importance"][model_name] = model.feature_importance()
                    training_results["model_performance"][model_name] = {
                        "mse": mse,
                        "training_samples": len(X)
                    }
                    
                    # Save trained model
                    self._save_model(model, model_name)
            
            except Exception as e:
                print(f"Warning: Could not train {model_name} model: {e}")
        
        training_results["training_data_points"] = len(training_data)
        return training_results
    
    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """訓練データ準備"""
        training_data = []
        
        # Extract training examples from historical data
        for report_type, reports in self.historical_data.items():
            for report in reports:
                try:
                    data = report["data"]
                    timestamp = report["timestamp"]
                    
                    # Extract features and targets based on report type
                    if report_type == "code_review_reports":
                        training_examples = self._extract_code_review_training_data(data, timestamp)
                        training_data.extend(training_examples)
                    
                    elif report_type == "security_reports":
                        training_examples = self._extract_security_training_data(data, timestamp)
                        training_data.extend(training_examples)
                    
                    elif report_type == "performance_analysis_reports":
                        training_examples = self._extract_performance_training_data(data, timestamp)
                        training_data.extend(training_examples)
                
                except Exception as e:
                    print(f"Warning: Could not extract training data from {report['file']}: {e}")
        
        return training_data
    
    def _extract_code_review_training_data(self, data: Dict[str, Any], timestamp: str) -> List[Dict[str, Any]]:
        """コードレビューデータから訓練例抽出"""
        training_examples = []
        
        file_reviews = data.get("file_reviews", {})
        for file_path, review_data in file_reviews.items():
            summary = review_data.get("summary", {})
            
            example = {
                "file_path": file_path,
                "timestamp": timestamp,
                "features": {
                    "lines_of_code": summary.get("lines_of_code", 0),
                    "comment_count": summary.get("comment_count", 0),
                    "critical_issues": summary.get("critical_issues", 0),
                    "code_smells": summary.get("code_smells", 0)
                },
                "targets": {
                    "code_quality": summary.get("overall_score", 50),
                    "bug_probability": min(100, summary.get("critical_issues", 0) * 10),
                    "maintenance_effort": 100 - summary.get("overall_score", 50)
                }
            }
            training_examples.append(example)
        
        return training_examples
    
    def _extract_security_training_data(self, data: Dict[str, Any], timestamp: str) -> List[Dict[str, Any]]:
        """セキュリティデータから訓練例抽出"""
        training_examples = []
        
        vulnerabilities = data.get("scan_results", {}).get("vulnerabilities", [])
        
        # Group vulnerabilities by file
        file_vulns = defaultdict(list)
        for vuln in vulnerabilities:
            file_path = vuln.get("file_path", "unknown")
            file_vulns[file_path].append(vuln)
        
        for file_path, vulns in file_vulns.items():
            critical_count = len([v for v in vulns if v.get("severity") == "critical"])
            high_count = len([v for v in vulns if v.get("severity") == "high"])
            
            example = {
                "file_path": file_path,
                "timestamp": timestamp,
                "features": {
                    "total_vulnerabilities": len(vulns),
                    "critical_vulnerabilities": critical_count,
                    "high_vulnerabilities": high_count
                },
                "targets": {
                    "security_risk": min(100, (critical_count * 20 + high_count * 10)),
                    "bug_probability": min(100, critical_count * 15)
                }
            }
            training_examples.append(example)
        
        return training_examples
    
    def _extract_performance_training_data(self, data: Dict[str, Any], timestamp: str) -> List[Dict[str, Any]]:
        """パフォーマンスデータから訓練例抽出"""
        training_examples = []
        
        # Extract performance-related training data
        performance_issues = data.get("performance_issues", [])
        
        for issue in performance_issues:
            example = {
                "file_path": issue.get("file", "unknown"),
                "timestamp": timestamp,
                "features": {
                    "performance_score": 100 - len(performance_issues) * 5
                },
                "targets": {
                    "performance_trend": 100 - len(performance_issues) * 5
                }
            }
            training_examples.append(example)
        
        return training_examples
    
    def _prepare_model_data(self, training_data: List[Dict[str, Any]], model_name: str) -> Tuple[List[List[float]], List[float], List[str]]:
        """モデル用データ準備"""
        X = []
        y = []
        
        # Define feature names for each model
        feature_sets = {
            "code_quality": ["lines_of_code", "comment_count", "critical_issues", "code_smells"],
            "security_risk": ["total_vulnerabilities", "critical_vulnerabilities", "high_vulnerabilities"],
            "performance_trend": ["performance_score"],
            "bug_probability": ["critical_issues", "total_vulnerabilities", "code_smells"],
            "maintenance_effort": ["lines_of_code", "comment_count", "code_smells"]
        }
        
        feature_names = feature_sets.get(model_name, ["default_feature"])
        
        for example in training_data:
            features = example.get("features", {})
            targets = example.get("targets", {})
            
            # Extract features for this model
            feature_vector = []
            for feature_name in feature_names:
                feature_vector.append(features.get(feature_name, 0))
            
            # Extract target for this model
            target = targets.get(model_name, 50)
            
            if len(feature_vector) == len(feature_names):
                X.append(feature_vector)
                y.append(target)
        
        return X, y, feature_names
    
    def _save_model(self, model: SimpleMLModel, model_name: str):
        """モデル保存"""
        model_file = self.models_path / f"{model_name}_model.json"
        
        model_data = {
            "model_type": model.model_type,
            "is_trained": model.is_trained,
            "feature_names": model.feature_names,
            "weights": model.weights,
            "bias": model.bias,
            "training_data_size": len(model.training_data)
        }
        
        with open(model_file, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
    
    def predict_quality_trends(self) -> List[QualityTrend]:
        """品質トレンド予測"""
        print("🔮 Predicting quality trends...")
        
        trends = []
        
        # Analyze historical metrics for trend prediction
        metric_histories = self._extract_metric_histories()
        
        for metric_name, history in metric_histories.items():
            if len(history) >= 3:  # Need at least 3 data points
                trend = self._analyze_trend(metric_name, history)
                trends.append(trend)
        
        return trends
    
    def _extract_metric_histories(self) -> Dict[str, List[float]]:
        """メトリクス履歴抽出"""
        metric_histories = defaultdict(list)
        
        # Extract key metrics from historical data
        for report_type, reports in self.historical_data.items():
            sorted_reports = sorted(reports, key=lambda x: x["timestamp"])
            
            for report in sorted_reports:
                data = report["data"]
                
                # Extract different metrics based on report type
                if report_type == "code_review_reports":
                    if "overall_statistics" in data:
                        score = data["overall_statistics"].get("average_code_quality_score", None)
                        if score is not None:
                            metric_histories["code_quality_score"].append(score)
                
                elif report_type == "security_reports":
                    if "security_metrics" in data:
                        score = data["security_metrics"].get("security_score", None)
                        if score is not None:
                            metric_histories["security_score"].append(score)
        
        return metric_histories
    
    def _analyze_trend(self, metric_name: str, history: List[float]) -> QualityTrend:
        """トレンド分析"""
        if len(history) < 2:
            return QualityTrend(
                metric_name=metric_name,
                historical_values=history,
                trend_direction="stable",
                predicted_next_value=history[0] if history else 50.0,
                confidence_interval=(40.0, 60.0)
            )
        
        # Simple trend analysis
        recent_values = history[-3:] if len(history) >= 3 else history
        trend_slope = (recent_values[-1] - recent_values[0]) / len(recent_values)
        
        # Determine trend direction
        if trend_slope > 2:
            trend_direction = "improving"
        elif trend_slope < -2:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        # Predict next value
        predicted_next = recent_values[-1] + trend_slope
        predicted_next = max(0, min(100, predicted_next))
        
        # Calculate confidence interval
        std_dev = np.std(recent_values) if len(recent_values) > 1 else 5.0
        confidence_interval = (
            max(0, predicted_next - std_dev),
            min(100, predicted_next + std_dev)
        )
        
        return QualityTrend(
            metric_name=metric_name,
            historical_values=history,
            trend_direction=trend_direction,
            predicted_next_value=predicted_next,
            confidence_interval=confidence_interval
        )
    
    def predict_file_quality(self, file_path: str) -> QualityPrediction:
        """ファイル品質予測"""
        # Extract current features for the file
        current_features = self._extract_current_file_features(file_path)
        
        # Get current quality score
        current_score = current_features.get("current_quality_score", 50.0)
        
        # Predict future quality using trained models
        feature_vector = self._convert_to_feature_vector(current_features)
        
        # Use code quality model for prediction
        if self.models["code_quality"].is_trained:
            predicted_scores = self.models["code_quality"].predict([feature_vector])
            predicted_score = predicted_scores[0] if predicted_scores else current_score
        else:
            # Simple heuristic prediction
            predicted_score = self._heuristic_quality_prediction(current_features)
        
        # Calculate confidence and risk level
        confidence = self._calculate_prediction_confidence(current_features)
        risk_level = self._determine_risk_level(predicted_score, current_score)
        
        # Generate recommendations
        recommendations = self._generate_quality_recommendations(current_features, predicted_score)
        
        # Analyze trend
        trend_analysis = self._analyze_file_trend(file_path, current_score, predicted_score)
        
        return QualityPrediction(
            file_path=file_path,
            current_score=current_score,
            predicted_score=predicted_score,
            prediction_confidence=confidence,
            risk_level=risk_level,
            recommended_actions=recommendations,
            trend_analysis=trend_analysis
        )
    
    def _extract_current_file_features(self, file_path: str) -> Dict[str, Any]:
        """現在のファイル特徴量抽出"""
        features = {
            "file_path": file_path,
            "current_quality_score": 50.0,
            "lines_of_code": 100,
            "comment_count": 5,
            "critical_issues": 0,
            "code_smells": 2,
            "recent_changes": 1
        }
        
        # Try to extract real features from latest reports
        try:
            # Check latest AI code review report
            code_review_files = list((self.scripts_path / "code_review_reports").glob("ai_code_review_*.json"))
            if code_review_files:
                latest_file = max(code_review_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                file_reviews = data.get("file_reviews", {})
                if file_path in file_reviews:
                    file_data = file_reviews[file_path]
                    summary = file_data.get("summary", {})
                    
                    features.update({
                        "current_quality_score": summary.get("overall_score", 50.0),
                        "comment_count": summary.get("comment_count", 0),
                        "critical_issues": summary.get("critical_issues", 0),
                        "code_smells": summary.get("code_smells", 0)
                    })
        
        except Exception as e:
            print(f"Warning: Could not extract features for {file_path}: {e}")
        
        return features
    
    def _convert_to_feature_vector(self, features: Dict[str, Any]) -> List[float]:
        """特徴量ベクトルに変換"""
        return [
            features.get("lines_of_code", 0),
            features.get("comment_count", 0),
            features.get("critical_issues", 0),
            features.get("code_smells", 0)
        ]
    
    def _heuristic_quality_prediction(self, features: Dict[str, Any]) -> float:
        """ヒューリスティック品質予測"""
        base_score = features.get("current_quality_score", 50.0)
        
        # Apply simple heuristics
        if features.get("critical_issues", 0) > 0:
            base_score -= features["critical_issues"] * 5
        
        if features.get("code_smells", 0) > 3:
            base_score -= (features["code_smells"] - 3) * 2
        
        if features.get("recent_changes", 0) > 5:
            base_score -= 3  # Recently changed files might introduce issues
        
        return max(0, min(100, base_score))
    
    def _calculate_prediction_confidence(self, features: Dict[str, Any]) -> float:
        """予測信頼度計算"""
        confidence = 0.7  # Base confidence
        
        # Higher confidence for files with more data
        if features.get("comment_count", 0) > 0:
            confidence += 0.1
        
        if features.get("lines_of_code", 0) > 50:
            confidence += 0.1
        
        # Lower confidence for files with many issues
        if features.get("critical_issues", 0) > 2:
            confidence -= 0.2
        
        return max(0.3, min(1.0, confidence))
    
    def _determine_risk_level(self, predicted_score: float, current_score: float) -> str:
        """リスクレベル決定"""
        score_change = predicted_score - current_score
        
        if predicted_score < 30 or score_change < -10:
            return "high"
        elif predicted_score < 50 or score_change < -5:
            return "medium"
        elif predicted_score < 70:
            return "low"
        else:
            return "minimal"
    
    def _generate_quality_recommendations(self, features: Dict[str, Any], predicted_score: float) -> List[str]:
        """品質推奨事項生成"""
        recommendations = []
        
        if features.get("critical_issues", 0) > 0:
            recommendations.append("Address critical code quality issues immediately")
        
        if features.get("code_smells", 0) > 3:
            recommendations.append("Refactor code to eliminate code smells")
        
        if predicted_score < 50:
            recommendations.append("Implement comprehensive code review process")
            recommendations.append("Add unit tests to improve reliability")
        
        if features.get("comment_count", 0) == 0:
            recommendations.append("Add documentation and comments for better maintainability")
        
        if not recommendations:
            recommendations.append("Continue current development practices")
        
        return recommendations
    
    def _analyze_file_trend(self, file_path: str, current_score: float, predicted_score: float) -> str:
        """ファイルトレンド分析"""
        score_change = predicted_score - current_score
        
        if score_change > 5:
            return "Quality improving - positive trend"
        elif score_change < -5:
            return "Quality declining - intervention needed"
        else:
            return "Quality stable - maintaining current level"
    
    def run_comprehensive_prediction_analysis(self) -> Dict[str, Any]:
        """包括的予測分析実行"""
        print("🚀 CC02 v33.0 ML Quality Predictor - Cycle 7")
        print("=" * 60)
        print("🧠 ADVANCED MACHINE LEARNING QUALITY PREDICTION")
        print("=" * 60)
        
        # Train ML models
        training_results = self.train_prediction_models()
        
        # Predict quality trends
        quality_trends = self.predict_quality_trends()
        
        # Predict quality for key files
        file_predictions = []
        key_files = self._identify_key_files()
        
        print(f"🔮 Generating predictions for {len(key_files)} key files...")
        for file_path in key_files:
            try:
                prediction = self.predict_file_quality(file_path)
                file_predictions.append(asdict(prediction))
            except Exception as e:
                print(f"Warning: Could not predict quality for {file_path}: {e}")
        
        # Generate insights and recommendations
        insights = self._generate_ml_insights(quality_trends, file_predictions)
        
        # Create comprehensive report
        comprehensive_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "ml_training_results": training_results,
            "quality_trends": [asdict(trend) for trend in quality_trends],
            "file_predictions": file_predictions,
            "ml_insights": insights,
            "prediction_summary": self._create_prediction_summary(quality_trends, file_predictions),
            "recommended_actions": self._generate_proactive_actions(quality_trends, file_predictions),
            "model_status": {name: model.is_trained for name, model in self.models.items()},
            "next_cycle_improvements": [
                "Expand training dataset with more historical data",
                "Implement ensemble prediction models",
                "Add real-time quality monitoring",
                "Integrate with development workflow for predictive alerts",
                "Develop custom quality metrics for domain-specific predictions"
            ]
        }
        
        # Save comprehensive report
        report_file = self.output_path / f"ml_quality_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ ML quality prediction complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_prediction_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _identify_key_files(self) -> List[str]:
        """重要ファイル特定"""
        key_files = []
        
        # Get files from latest AI code review
        try:
            code_review_files = list((self.scripts_path / "code_review_reports").glob("ai_code_review_*.json"))
            if code_review_files:
                latest_file = max(code_review_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                file_reviews = data.get("file_reviews", {})
                
                # Sort files by issue count and select top ones
                sorted_files = sorted(file_reviews.items(), 
                                    key=lambda x: x[1].get("summary", {}).get("comment_count", 0), 
                                    reverse=True)
                
                key_files = [file_path for file_path, _ in sorted_files[:20]]  # Top 20 files
        
        except Exception as e:
            print(f"Warning: Could not identify key files: {e}")
            # Fallback to common important files
            key_files = [
                "backend/app/main.py",
                "backend/app/api/v1/router.py",
                "backend/app/core/config.py",
                "backend/app/models/base.py"
            ]
        
        return key_files
    
    def _generate_ml_insights(self, quality_trends: List[QualityTrend], 
                            file_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ML洞察生成"""
        insights = []
        
        # Trend insights
        declining_trends = [t for t in quality_trends if t.trend_direction == "declining"]
        if declining_trends:
            insights.append({
                "type": "quality_decline_alert",
                "severity": "high",
                "title": "Quality Decline Trend Detected",
                "description": f"{len(declining_trends)} quality metrics showing declining trends",
                "metrics_affected": [t.metric_name for t in declining_trends],
                "recommendation": "Implement immediate quality improvement measures"
            })
        
        # High-risk file insights
        high_risk_files = [f for f in file_predictions if f["risk_level"] == "high"]
        if high_risk_files:
            insights.append({
                "type": "high_risk_files",
                "severity": "critical",
                "title": "High-Risk Files Identified",
                "description": f"{len(high_risk_files)} files predicted to have significant quality issues",
                "files": [f["file_path"] for f in high_risk_files],
                "recommendation": "Prioritize review and refactoring of high-risk files"
            })
        
        # Positive trend insights
        improving_trends = [t for t in quality_trends if t.trend_direction == "improving"]
        if improving_trends:
            insights.append({
                "type": "quality_improvement",
                "severity": "info",
                "title": "Quality Improvement Detected",
                "description": f"{len(improving_trends)} quality metrics showing improvement",
                "metrics_affected": [t.metric_name for t in improving_trends],
                "recommendation": "Continue current practices that are driving quality improvements"
            })
        
        # Prediction confidence insights
        low_confidence_predictions = [f for f in file_predictions if f["prediction_confidence"] < 0.5]
        if len(low_confidence_predictions) > len(file_predictions) * 0.3:
            insights.append({
                "type": "prediction_uncertainty",
                "severity": "medium",
                "title": "High Prediction Uncertainty",
                "description": "Many predictions have low confidence due to insufficient historical data",
                "recommendation": "Collect more historical data to improve prediction accuracy"
            })
        
        return insights
    
    def _create_prediction_summary(self, quality_trends: List[QualityTrend], 
                                 file_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """予測サマリー作成"""
        return {
            "total_trends_analyzed": len(quality_trends),
            "files_predicted": len(file_predictions),
            "trend_analysis": {
                "improving": len([t for t in quality_trends if t.trend_direction == "improving"]),
                "stable": len([t for t in quality_trends if t.trend_direction == "stable"]),
                "declining": len([t for t in quality_trends if t.trend_direction == "declining"])
            },
            "risk_distribution": {
                "high": len([f for f in file_predictions if f["risk_level"] == "high"]),
                "medium": len([f for f in file_predictions if f["risk_level"] == "medium"]),
                "low": len([f for f in file_predictions if f["risk_level"] == "low"]),
                "minimal": len([f for f in file_predictions if f["risk_level"] == "minimal"])
            },
            "average_prediction_confidence": np.mean([f["prediction_confidence"] for f in file_predictions]) if file_predictions else 0.5,
            "overall_quality_outlook": self._determine_overall_outlook(quality_trends, file_predictions)
        }
    
    def _determine_overall_outlook(self, quality_trends: List[QualityTrend], 
                                 file_predictions: List[Dict[str, Any]]) -> str:
        """全体見通し決定"""
        declining_count = len([t for t in quality_trends if t.trend_direction == "declining"])
        improving_count = len([t for t in quality_trends if t.trend_direction == "improving"])
        high_risk_count = len([f for f in file_predictions if f["risk_level"] == "high"])
        
        if declining_count > improving_count and high_risk_count > 3:
            return "concerning"
        elif declining_count > improving_count:
            return "cautious"
        elif improving_count > declining_count and high_risk_count <= 1:
            return "positive"
        else:
            return "stable"
    
    def _generate_proactive_actions(self, quality_trends: List[QualityTrend], 
                                  file_predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """積極的アクション生成"""
        actions = []
        
        # Actions based on declining trends
        declining_trends = [t for t in quality_trends if t.trend_direction == "declining"]
        if declining_trends:
            actions.append({
                "category": "trend_intervention",
                "priority": "high",
                "title": "Address Quality Decline Trends",
                "description": "Implement measures to reverse declining quality trends",
                "specific_actions": [
                    f"Focus on improving {t.metric_name}" for t in declining_trends
                ],
                "timeline": "1-2 weeks"
            })
        
        # Actions for high-risk files
        high_risk_files = [f for f in file_predictions if f["risk_level"] == "high"]
        if high_risk_files:
            actions.append({
                "category": "file_remediation",
                "priority": "critical",
                "title": "High-Risk File Intervention",
                "description": "Immediate attention required for high-risk files",
                "specific_actions": [
                    f"Review and refactor {f['file_path']}" for f in high_risk_files[:5]
                ],
                "timeline": "3-5 days"
            })
        
        # Predictive maintenance actions
        actions.append({
            "category": "predictive_maintenance",
            "priority": "medium",
            "title": "Predictive Quality Maintenance",
            "description": "Set up automated quality monitoring and alerts",
            "specific_actions": [
                "Implement real-time quality dashboards",
                "Set up predictive quality alerts",
                "Create quality trend monitoring reports",
                "Establish quality intervention thresholds"
            ],
            "timeline": "2-3 weeks"
        })
        
        return actions
    
    def _print_prediction_summary(self, report: Dict[str, Any]):
        """予測サマリー出力"""
        print("\n" + "=" * 60)
        print("🔮 ML Quality Prediction Summary")
        print("=" * 60)
        
        summary = report["prediction_summary"]
        training_results = report["ml_training_results"]
        
        print(f"🧠 ML Models Status:")
        model_status = report["model_status"]
        trained_models = sum(1 for trained in model_status.values() if trained)
        print(f"  Trained Models: {trained_models}/{len(model_status)}")
        print(f"  Training Data Points: {training_results.get('training_data_points', 0)}")
        
        print(f"\n📊 Prediction Results:")
        print(f"  Trends Analyzed: {summary['total_trends_analyzed']}")
        print(f"  Files Predicted: {summary['files_predicted']}")
        print(f"  Average Confidence: {summary['average_prediction_confidence']:.2f}")
        print(f"  Overall Outlook: {summary['overall_quality_outlook'].upper()}")
        
        print(f"\n📈 Trend Analysis:")
        trend_analysis = summary["trend_analysis"]
        print(f"  Improving: {trend_analysis['improving']}")
        print(f"  Stable: {trend_analysis['stable']}")
        print(f"  Declining: {trend_analysis['declining']}")
        
        print(f"\n⚠️ Risk Distribution:")
        risk_dist = summary["risk_distribution"]
        print(f"  High Risk: {risk_dist['high']}")
        print(f"  Medium Risk: {risk_dist['medium']}")
        print(f"  Low Risk: {risk_dist['low']}")
        print(f"  Minimal Risk: {risk_dist['minimal']}")
        
        # Top insights
        insights = report["ml_insights"]
        if insights:
            print(f"\n🧠 Key ML Insights:")
            for i, insight in enumerate(insights[:3], 1):
                print(f"  {i}. {insight['title']}: {insight['description']}")
        
        # Proactive actions
        actions = report["recommended_actions"]
        if actions:
            print(f"\n🎯 Proactive Actions:")
            for action in actions:
                print(f"  • {action['title']} ({action['priority']} priority)")
        
        print(f"\n🔄 Next Cycle Improvements:")
        for improvement in report["next_cycle_improvements"][:3]:
            print(f"  - {improvement}")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🔬 CC02 v33.0 ML Quality Predictor")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    predictor = MLQualityPredictor(project_root)
    report = predictor.run_comprehensive_prediction_analysis()
    
    return report


if __name__ == "__main__":
    main()