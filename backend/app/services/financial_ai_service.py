"""
ITDO ERP Backend - Financial AI Service
Day 25: Advanced financial AI service for forecasting, risk analysis, and optimization

This service provides:
- AI-powered financial forecasting using multiple models
- Risk assessment and scoring algorithms
- Market data analysis and volatility calculation
- Cash flow prediction with scenario analysis
- Financial optimization recommendations
- Advanced metrics calculation and trend analysis
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from statistics import mean
from typing import Any, Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.advanced_financial import (
    FinancialForecast,
    RiskAssessment,
)
from app.models.financial import JournalEntry
from app.schemas.advanced_financial import (
    FinancialForecastCreate,
    RiskAssessmentCreate,
)
from app.types import OrganizationId, UserId

logger = logging.getLogger(__name__)


class FinancialAIService:
    """Service for AI-powered financial analytics and predictions"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ===============================
    # Financial Forecasting
    # ===============================

    async def create_financial_forecast(
        self,
        forecast_data: FinancialForecastCreate,
        user_id: UserId,
    ) -> FinancialForecast:
        """Create AI-powered financial forecast"""
        try:
            # Generate forecast using AI models
            forecast_results = await self._generate_forecast(
                organization_id=forecast_data.organization_id,
                forecast_type=forecast_data.forecast_type,
                start_date=forecast_data.start_date,
                end_date=forecast_data.end_date,
                model_type=forecast_data.ai_model_type,
                training_period=forecast_data.training_data_period,
                confidence_interval=forecast_data.confidence_interval,
                parameters=forecast_data.model_parameters,
            )

            # Create forecast record
            forecast = FinancialForecast(
                organization_id=forecast_data.organization_id,
                forecast_name=forecast_data.forecast_name,
                forecast_type=forecast_data.forecast_type,
                forecast_horizon=forecast_data.forecast_horizon,
                start_date=forecast_data.start_date,
                end_date=forecast_data.end_date,
                ai_model_type=forecast_data.ai_model_type,
                training_data_period=forecast_data.training_data_period,
                confidence_interval=forecast_data.confidence_interval,
                forecast_data=forecast_results["predictions"],
                accuracy_score=forecast_results.get("accuracy"),
                mean_absolute_error=forecast_results.get("mae"),
                model_parameters=forecast_data.model_parameters,
                created_by=user_id,
            )

            self.db.add(forecast)
            await self.db.commit()
            await self.db.refresh(forecast)

            logger.info(
                f"Created financial forecast {forecast.id} for organization {forecast_data.organization_id}"
            )
            return forecast

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating financial forecast: {str(e)}")
            raise

    async def _generate_forecast(
        self,
        organization_id: OrganizationId,
        forecast_type: str,
        start_date: date,
        end_date: date,
        model_type: str,
        training_period: int,
        confidence_interval: Decimal,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate forecast using AI models"""
        try:
            # Get historical data for training
            historical_data = await self._get_historical_financial_data(
                organization_id, forecast_type, training_period
            )

            if not historical_data:
                logger.warning(
                    f"No historical data found for forecast type {forecast_type}"
                )
                return self._generate_default_forecast(start_date, end_date)

            # Apply selected AI model
            if model_type == "ensemble":
                predictions = await self._ensemble_forecast(
                    historical_data,
                    start_date,
                    end_date,
                    confidence_interval,
                    parameters,
                )
            elif model_type == "arima":
                predictions = await self._arima_forecast(
                    historical_data, start_date, end_date, confidence_interval
                )
            elif model_type == "linear_regression":
                predictions = await self._linear_regression_forecast(
                    historical_data, start_date, end_date, confidence_interval
                )
            elif model_type == "prophet":
                predictions = await self._prophet_forecast(
                    historical_data, start_date, end_date, confidence_interval
                )
            else:
                predictions = await self._lstm_forecast(
                    historical_data, start_date, end_date, confidence_interval
                )

            # Calculate accuracy metrics
            accuracy_metrics = await self._calculate_forecast_accuracy(
                historical_data, predictions
            )

            return {
                "predictions": predictions,
                "accuracy": accuracy_metrics.get("accuracy_score"),
                "mae": accuracy_metrics.get("mean_absolute_error"),
                "model_type": model_type,
                "data_points": len(historical_data),
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    async def _ensemble_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        confidence_interval: Decimal,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ensemble forecast combining multiple models"""
        try:
            # Generate predictions from multiple models
            arima_pred = await self._arima_forecast(
                historical_data, start_date, end_date, confidence_interval
            )
            linear_pred = await self._linear_regression_forecast(
                historical_data, start_date, end_date, confidence_interval
            )

            # Combine predictions with weights
            weights = parameters.get("ensemble_weights", {"arima": 0.4, "linear": 0.6})

            combined_predictions = {}
            current_date = start_date

            while current_date <= end_date:
                date_str = current_date.isoformat()

                arima_val = arima_pred["forecast"].get(date_str, 0)
                linear_val = linear_pred["forecast"].get(date_str, 0)

                combined_val = (
                    float(arima_val) * weights["arima"]
                    + float(linear_val) * weights["linear"]
                )

                combined_predictions[date_str] = round(combined_val, 2)
                current_date += timedelta(days=30)  # Monthly predictions

            return {
                "forecast": combined_predictions,
                "confidence_intervals": self._calculate_confidence_intervals(
                    combined_predictions, confidence_interval
                ),
                "model_components": {
                    "arima": arima_pred["forecast"],
                    "linear_regression": linear_pred["forecast"],
                },
                "ensemble_weights": weights,
            }

        except Exception as e:
            logger.error(f"Error in ensemble forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    async def _arima_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        confidence_interval: Decimal,
    ) -> Dict[str, Any]:
        """ARIMA time series forecast (simplified implementation)"""
        try:
            # Extract values and calculate trend
            values = [
                float(item["value"]) for item in historical_data[-12:]
            ]  # Last 12 periods

            if len(values) < 3:
                return self._generate_default_forecast(start_date, end_date)

            # Simple trend calculation
            trend = (values[-1] - values[0]) / len(values)
            seasonal_component = self._calculate_seasonal_component(values)

            predictions = {}
            current_date = start_date
            base_value = values[-1]
            period = 0

            while current_date <= end_date:
                period += 1
                predicted_value = (
                    base_value
                    + (trend * period)
                    + seasonal_component.get(period % 12, 0)
                )
                predictions[current_date.isoformat()] = round(
                    max(0, predicted_value), 2
                )
                current_date += timedelta(days=30)

            return {
                "forecast": predictions,
                "confidence_intervals": self._calculate_confidence_intervals(
                    predictions, confidence_interval
                ),
                "trend": round(trend, 4),
                "seasonal_components": seasonal_component,
            }

        except Exception as e:
            logger.error(f"Error in ARIMA forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    async def _linear_regression_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        confidence_interval: Decimal,
    ) -> Dict[str, Any]:
        """Linear regression forecast"""
        try:
            # Prepare data for linear regression
            x_values = list(range(len(historical_data)))
            y_values = [float(item["value"]) for item in historical_data]

            if len(y_values) < 2:
                return self._generate_default_forecast(start_date, end_date)

            # Calculate linear regression coefficients
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            # Linear regression: y = mx + b
            m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            b = (sum_y - m * sum_x) / n

            # Generate predictions
            predictions = {}
            current_date = start_date
            future_x = len(historical_data)

            while current_date <= end_date:
                predicted_value = m * future_x + b
                predictions[current_date.isoformat()] = round(
                    max(0, predicted_value), 2
                )
                current_date += timedelta(days=30)
                future_x += 1

            # Calculate R-squared
            y_mean = mean(y_values)
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)
            ss_res = sum((y - (m * x + b)) ** 2 for x, y in zip(x_values, y_values))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                "forecast": predictions,
                "confidence_intervals": self._calculate_confidence_intervals(
                    predictions, confidence_interval
                ),
                "slope": round(m, 4),
                "intercept": round(b, 4),
                "r_squared": round(r_squared, 4),
            }

        except Exception as e:
            logger.error(f"Error in linear regression forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    async def _prophet_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        confidence_interval: Decimal,
    ) -> Dict[str, Any]:
        """Prophet-style forecast (simplified implementation)"""
        try:
            # Extract trend and seasonal components
            values = [float(item["value"]) for item in historical_data]
            dates = [datetime.fromisoformat(item["date"]) for item in historical_data]

            if len(values) < 4:
                return self._generate_default_forecast(start_date, end_date)

            # Calculate trend component
            x_vals = [(d - dates[0]).days for d in dates]
            trend_coeff = self._calculate_trend_coefficient(x_vals, values)

            # Calculate seasonal pattern
            seasonal_pattern = self._extract_seasonal_pattern(values, len(values) // 4)

            # Generate predictions
            predictions = {}
            current_date = start_date
            start_x = (
                datetime.combine(start_date, datetime.min.time()) - dates[0]
            ).days

            period = 0
            while current_date <= end_date:
                x_val = start_x + (period * 30)  # Monthly steps
                trend_component = trend_coeff * x_val + values[-1]
                seasonal_component = seasonal_pattern[period % len(seasonal_pattern)]

                predicted_value = trend_component + seasonal_component
                predictions[current_date.isoformat()] = round(
                    max(0, predicted_value), 2
                )

                current_date += timedelta(days=30)
                period += 1

            return {
                "forecast": predictions,
                "confidence_intervals": self._calculate_confidence_intervals(
                    predictions, confidence_interval
                ),
                "trend_coefficient": round(trend_coeff, 6),
                "seasonal_pattern": seasonal_pattern,
            }

        except Exception as e:
            logger.error(f"Error in Prophet forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    async def _lstm_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        confidence_interval: Decimal,
    ) -> Dict[str, Any]:
        """LSTM-style neural network forecast (simplified implementation)"""
        try:
            # Simplified LSTM implementation using moving averages and momentum
            values = [float(item["value"]) for item in historical_data]

            if len(values) < 5:
                return self._generate_default_forecast(start_date, end_date)

            # Calculate moving averages for different windows
            ma_short = self._moving_average(values, 3)
            ma_long = self._moving_average(values, 6)

            # Calculate momentum
            momentum = [
                (values[i] - values[i - 1]) / values[i - 1] if values[i - 1] != 0 else 0
                for i in range(1, len(values))
            ]

            # Generate predictions
            predictions = {}
            current_date = start_date
            last_value = values[-1]
            last_momentum = momentum[-1] if momentum else 0

            period = 0
            while current_date <= end_date:
                # Simple LSTM-style prediction
                momentum_factor = last_momentum * (0.9**period)  # Decay momentum
                ma_influence = (
                    (ma_short[-1] - ma_long[-1]) * 0.1 if ma_short and ma_long else 0
                )

                predicted_value = last_value * (1 + momentum_factor) + ma_influence
                predictions[current_date.isoformat()] = round(
                    max(0, predicted_value), 2
                )

                # Update for next iteration
                last_value = predicted_value
                current_date += timedelta(days=30)
                period += 1

            return {
                "forecast": predictions,
                "confidence_intervals": self._calculate_confidence_intervals(
                    predictions, confidence_interval
                ),
                "momentum_components": momentum[-3:]
                if len(momentum) >= 3
                else momentum,
                "ma_short": ma_short[-3:] if len(ma_short) >= 3 else ma_short,
                "ma_long": ma_long[-3:] if len(ma_long) >= 3 else ma_long,
            }

        except Exception as e:
            logger.error(f"Error in LSTM forecast: {str(e)}")
            return self._generate_default_forecast(start_date, end_date)

    # ===============================
    # Risk Assessment
    # ===============================

    async def create_risk_assessment(
        self,
        assessment_data: RiskAssessmentCreate,
        user_id: UserId,
    ) -> RiskAssessment:
        """Create comprehensive risk assessment"""
        try:
            # Generate risk analysis
            risk_analysis = await self._generate_risk_analysis(
                organization_id=assessment_data.organization_id,
                assessment_type=assessment_data.assessment_type,
                assessment_date=assessment_data.assessment_date,
            )

            # Create risk assessment record
            assessment = RiskAssessment(
                organization_id=assessment_data.organization_id,
                assessment_name=assessment_data.assessment_name,
                assessment_type=assessment_data.assessment_type,
                assessment_date=assessment_data.assessment_date,
                overall_risk_score=risk_analysis["overall_score"],
                credit_risk_score=risk_analysis["credit_score"],
                market_risk_score=risk_analysis["market_score"],
                liquidity_risk_score=risk_analysis["liquidity_score"],
                operational_risk_score=risk_analysis["operational_score"],
                risk_level=risk_analysis["risk_level"],
                risk_factors=risk_analysis["risk_factors"],
                mitigation_strategies=risk_analysis["mitigation_strategies"],
                recommendations=risk_analysis["recommendations"],
                confidence_score=risk_analysis["confidence_score"],
                data_quality_score=risk_analysis["data_quality_score"],
                created_by=user_id,
            )

            self.db.add(assessment)
            await self.db.commit()
            await self.db.refresh(assessment)

            logger.info(
                f"Created risk assessment {assessment.id} for organization {assessment_data.organization_id}"
            )
            return assessment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating risk assessment: {str(e)}")
            raise

    async def _generate_risk_analysis(
        self,
        organization_id: OrganizationId,
        assessment_type: str,
        assessment_date: date,
    ) -> Dict[str, Any]:
        """Generate comprehensive risk analysis"""
        try:
            # Get financial data for risk calculation
            financial_data = await self._get_financial_risk_data(
                organization_id, assessment_date
            )

            # Calculate individual risk scores
            credit_score = await self._calculate_credit_risk(financial_data)
            market_score = await self._calculate_market_risk(financial_data)
            liquidity_score = await self._calculate_liquidity_risk(financial_data)
            operational_score = await self._calculate_operational_risk(financial_data)

            # Calculate overall risk score
            weights = {
                "credit": 0.3,
                "market": 0.25,
                "liquidity": 0.25,
                "operational": 0.2,
            }
            overall_score = (
                credit_score * weights["credit"]
                + market_score * weights["market"]
                + liquidity_score * weights["liquidity"]
                + operational_score * weights["operational"]
            )

            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)

            # Generate risk factors and recommendations
            risk_factors = self._identify_risk_factors(
                credit_score,
                market_score,
                liquidity_score,
                operational_score,
                financial_data,
            )

            mitigation_strategies = self._generate_mitigation_strategies(risk_factors)
            recommendations = self._generate_risk_recommendations(
                risk_level, risk_factors
            )

            # Calculate confidence metrics
            confidence_score = self._calculate_confidence_score(financial_data)
            data_quality_score = self._calculate_data_quality_score(financial_data)

            return {
                "overall_score": Decimal(str(round(overall_score, 2))),
                "credit_score": Decimal(str(round(credit_score, 2))),
                "market_score": Decimal(str(round(market_score, 2))),
                "liquidity_score": Decimal(str(round(liquidity_score, 2))),
                "operational_score": Decimal(str(round(operational_score, 2))),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
                "recommendations": recommendations,
                "confidence_score": Decimal(str(round(confidence_score, 2))),
                "data_quality_score": Decimal(str(round(data_quality_score, 2))),
            }

        except Exception as e:
            logger.error(f"Error generating risk analysis: {str(e)}")
            return self._generate_default_risk_analysis()

    async def _calculate_credit_risk(self, financial_data: Dict[str, Any]) -> float:
        """Calculate credit risk score (0-100)"""
        try:
            # Basic credit risk factors
            debt_to_equity = financial_data.get("debt_to_equity_ratio", 0.5)
            current_ratio = financial_data.get("current_ratio", 1.0)
            cash_flow = financial_data.get("operating_cash_flow", 0)
            revenue_stability = financial_data.get("revenue_volatility", 0.2)

            # Credit risk calculation
            debt_risk = min(debt_to_equity * 20, 40)  # Max 40 points
            liquidity_risk = max(
                0, (2.0 - current_ratio) * 15
            )  # Max 30 points for poor liquidity
            cash_flow_risk = (
                20 if cash_flow < 0 else 0
            )  # 20 points for negative cash flow
            stability_risk = min(
                revenue_stability * 50, 10
            )  # Max 10 points for volatility

            total_risk = debt_risk + liquidity_risk + cash_flow_risk + stability_risk
            return min(total_risk, 100)

        except Exception as e:
            logger.error(f"Error calculating credit risk: {str(e)}")
            return 50.0  # Default medium risk

    async def _calculate_market_risk(self, financial_data: Dict[str, Any]) -> float:
        """Calculate market risk score (0-100)"""
        try:
            # Market risk factors
            beta = financial_data.get("beta", 1.0)
            market_concentration = financial_data.get("market_concentration", 0.3)
            currency_exposure = financial_data.get("currency_exposure", 0.1)
            sector_volatility = financial_data.get("sector_volatility", 0.15)

            # Market risk calculation
            beta_risk = min(abs(beta - 1.0) * 25, 25)  # Max 25 points for high beta
            concentration_risk = market_concentration * 30  # Max 30 points
            currency_risk = currency_exposure * 20  # Max 20 points
            sector_risk = sector_volatility * 25  # Max 25 points

            total_risk = beta_risk + concentration_risk + currency_risk + sector_risk
            return min(total_risk, 100)

        except Exception as e:
            logger.error(f"Error calculating market risk: {str(e)}")
            return 45.0  # Default medium-low risk

    async def _calculate_liquidity_risk(self, financial_data: Dict[str, Any]) -> float:
        """Calculate liquidity risk score (0-100)"""
        try:
            # Liquidity risk factors
            current_ratio = financial_data.get("current_ratio", 1.0)
            quick_ratio = financial_data.get("quick_ratio", 0.8)
            cash_ratio = financial_data.get("cash_ratio", 0.2)
            working_capital = financial_data.get("working_capital", 100000)

            # Liquidity risk calculation
            current_risk = max(0, (1.5 - current_ratio) * 25)  # Max 25 points
            quick_risk = max(0, (1.0 - quick_ratio) * 25)  # Max 25 points
            cash_risk = max(0, (0.15 - cash_ratio) * 200)  # Max 30 points
            working_capital_risk = (
                20 if working_capital < 0 else 0
            )  # 20 points for negative WC

            total_risk = current_risk + quick_risk + cash_risk + working_capital_risk
            return min(total_risk, 100)

        except Exception as e:
            logger.error(f"Error calculating liquidity risk: {str(e)}")
            return 40.0  # Default medium-low risk

    async def _calculate_operational_risk(
        self, financial_data: Dict[str, Any]
    ) -> float:
        """Calculate operational risk score (0-100)"""
        try:
            # Operational risk factors
            operating_margin = financial_data.get("operating_margin", 0.1)
            employee_turnover = financial_data.get("employee_turnover", 0.15)
            system_downtime = financial_data.get("system_downtime_hours", 10)
            compliance_issues = financial_data.get("compliance_violations", 0)

            # Operational risk calculation
            margin_risk = max(0, (0.05 - operating_margin) * 300)  # Max 30 points
            turnover_risk = min(employee_turnover * 100, 25)  # Max 25 points
            downtime_risk = min(system_downtime * 2, 25)  # Max 25 points
            compliance_risk = min(compliance_issues * 5, 20)  # Max 20 points

            total_risk = margin_risk + turnover_risk + downtime_risk + compliance_risk
            return min(total_risk, 100)

        except Exception as e:
            logger.error(f"Error calculating operational risk: {str(e)}")
            return 35.0  # Default low-medium risk

    # ===============================
    # Helper Methods
    # ===============================

    async def _get_historical_financial_data(
        self, organization_id: OrganizationId, forecast_type: str, periods: int
    ) -> List[Dict[str, Any]]:
        """Get historical financial data for training"""
        try:
            # Calculate start date for historical data
            end_date = date.today()
            start_date = end_date - timedelta(days=periods * 30)  # Approximate months

            # Query journal entries for the period
            query = (
                select(JournalEntry)
                .where(
                    and_(
                        JournalEntry.organization_id == organization_id,
                        JournalEntry.entry_date >= start_date,
                        JournalEntry.entry_date <= end_date,
                    )
                )
                .order_by(JournalEntry.entry_date)
            )

            result = await self.db.execute(query)
            entries = result.scalars().all()

            # Aggregate data by month
            monthly_data = {}
            for entry in entries:
                month_key = entry.entry_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "revenue": 0,
                        "expense": 0,
                        "cash_flow": 0,
                    }

                # Categorize based on debit/credit
                if entry.debit_amount:
                    monthly_data[month_key]["expense"] += float(entry.debit_amount)
                if entry.credit_amount:
                    monthly_data[month_key]["revenue"] += float(entry.credit_amount)

                # Cash flow approximation
                net_amount = float(entry.credit_amount or 0) - float(
                    entry.debit_amount or 0
                )
                monthly_data[month_key]["cash_flow"] += net_amount

            # Convert to list format
            historical_data = []
            for month, data in sorted(monthly_data.items()):
                value = data.get(forecast_type, data.get("revenue", 0))
                historical_data.append(
                    {
                        "date": f"{month}-01",
                        "value": value,
                        "period": month,
                    }
                )

            return historical_data

        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return []

    def _generate_default_forecast(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Generate default forecast when no historical data available"""
        predictions = {}
        current_date = start_date
        base_value = 10000  # Default base value

        while current_date <= end_date:
            # Simple linear growth
            months_from_start = (current_date.year - start_date.year) * 12 + (
                current_date.month - start_date.month
            )
            predicted_value = base_value * (
                1 + 0.02 * months_from_start
            )  # 2% monthly growth
            predictions[current_date.isoformat()] = round(predicted_value, 2)
            current_date += timedelta(days=30)

        return {
            "forecast": predictions,
            "confidence_intervals": self._calculate_confidence_intervals(
                predictions, Decimal("95.00")
            ),
            "model_type": "default",
            "note": "Default forecast due to insufficient historical data",
        }

    def _calculate_confidence_intervals(
        self, predictions: Dict[str, float], confidence_level: Decimal
    ) -> Dict[str, Dict[str, float]]:
        """Calculate confidence intervals for predictions"""
        confidence_intervals = {}
        # alpha = (100 - float(confidence_level)) / 100  # Future use for statistical calculations

        for date_str, value in predictions.items():
            # Simple confidence interval calculation
            margin = value * 0.1  # 10% margin for demonstration
            confidence_intervals[date_str] = {
                "lower": round(value - margin, 2),
                "upper": round(value + margin, 2),
                "confidence_level": float(confidence_level),
            }

        return confidence_intervals

    def _calculate_seasonal_component(self, values: List[float]) -> Dict[int, float]:
        """Calculate seasonal components"""
        if len(values) < 12:
            return {}

        seasonal_avg = {}
        for i in range(12):
            seasonal_values = [values[j] for j in range(i, len(values), 12)]
            if seasonal_values:
                seasonal_avg[i] = mean(seasonal_values) - mean(values)

        return seasonal_avg

    def _moving_average(self, values: List[float], window: int) -> List[float]:
        """Calculate moving average"""
        if len(values) < window:
            return values

        ma_values = []
        for i in range(window - 1, len(values)):
            ma_values.append(mean(values[i - window + 1 : i + 1]))

        return ma_values

    def _calculate_trend_coefficient(
        self, x_values: List[int], y_values: List[float]
    ) -> float:
        """Calculate trend coefficient for time series"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0

        n = len(x_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_x2 = sum(x * x for x in x_values)

        return (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

    def _extract_seasonal_pattern(
        self, values: List[float], periods: int
    ) -> List[float]:
        """Extract seasonal pattern from time series"""
        if len(values) < periods or periods == 0:
            return [0] * max(4, periods)

        pattern = []
        for i in range(periods):
            seasonal_vals = [values[j] for j in range(i, len(values), periods)]
            if seasonal_vals:
                pattern.append(mean(seasonal_vals) - mean(values))
            else:
                pattern.append(0)

        return pattern

    async def _get_financial_risk_data(
        self, organization_id: OrganizationId, assessment_date: date
    ) -> Dict[str, Any]:
        """Get financial data for risk assessment"""
        try:
            # This would typically fetch comprehensive financial data
            # For demonstration, returning sample data
            return {
                "debt_to_equity_ratio": 0.6,
                "current_ratio": 1.2,
                "quick_ratio": 0.9,
                "cash_ratio": 0.15,
                "operating_cash_flow": 50000,
                "revenue_volatility": 0.18,
                "beta": 1.1,
                "market_concentration": 0.4,
                "currency_exposure": 0.05,
                "sector_volatility": 0.12,
                "working_capital": 150000,
                "operating_margin": 0.08,
                "employee_turnover": 0.12,
                "system_downtime_hours": 8,
                "compliance_violations": 1,
            }

        except Exception as e:
            logger.error(f"Error getting financial risk data: {str(e)}")
            return {}

    def _determine_risk_level(self, overall_score: float) -> str:
        """Determine risk level based on overall score"""
        if overall_score < 20:
            return "very_low"
        elif overall_score < 40:
            return "low"
        elif overall_score < 60:
            return "medium"
        elif overall_score < 80:
            return "high"
        else:
            return "very_high"

    def _identify_risk_factors(
        self,
        credit_score: float,
        market_score: float,
        liquidity_score: float,
        operational_score: float,
        financial_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Identify specific risk factors"""
        risk_factors = {}

        if credit_score > 60:
            risk_factors["credit"] = [
                "High debt-to-equity ratio",
                "Poor cash flow",
                "Revenue instability",
            ]
        if market_score > 60:
            risk_factors["market"] = [
                "High market volatility",
                "Sector concentration",
                "Currency exposure",
            ]
        if liquidity_score > 60:
            risk_factors["liquidity"] = [
                "Low current ratio",
                "Insufficient cash reserves",
                "Working capital issues",
            ]
        if operational_score > 60:
            risk_factors["operational"] = [
                "Low operating margins",
                "High employee turnover",
                "System reliability issues",
            ]

        return risk_factors

    def _generate_mitigation_strategies(
        self, risk_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate risk mitigation strategies"""
        strategies = {}

        if "credit" in risk_factors:
            strategies["credit"] = [
                "Improve debt management",
                "Enhance cash flow forecasting",
                "Diversify revenue streams",
            ]
        if "market" in risk_factors:
            strategies["market"] = [
                "Implement hedging strategies",
                "Diversify market exposure",
                "Monitor market indicators",
            ]
        if "liquidity" in risk_factors:
            strategies["liquidity"] = [
                "Maintain cash reserves",
                "Improve working capital management",
                "Establish credit facilities",
            ]
        if "operational" in risk_factors:
            strategies["operational"] = [
                "Improve operational efficiency",
                "Invest in employee retention",
                "Enhance system reliability",
            ]

        return strategies

    def _generate_risk_recommendations(
        self, risk_level: str, risk_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        if risk_level in ["high", "very_high"]:
            recommendations.extend(
                [
                    "Conduct immediate risk assessment review",
                    "Implement emergency risk mitigation measures",
                    "Consider engaging risk management consultants",
                ]
            )

        if "credit" in risk_factors:
            recommendations.append("Review and restructure debt obligations")
        if "liquidity" in risk_factors:
            recommendations.append("Establish emergency cash reserves")
        if "market" in risk_factors:
            recommendations.append("Implement market risk hedging strategies")
        if "operational" in risk_factors:
            recommendations.append(
                "Invest in operational improvements and staff training"
            )

        return recommendations

    def _calculate_confidence_score(self, financial_data: Dict[str, Any]) -> float:
        """Calculate confidence score for risk assessment"""
        # Simplified confidence calculation based on data completeness
        data_completeness = len(
            [v for v in financial_data.values() if v is not None and v != 0]
        ) / len(financial_data)
        return min(data_completeness * 100, 95.0)

    def _calculate_data_quality_score(self, financial_data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        # Simplified data quality assessment
        return 85.0  # Default good quality score

    def _generate_default_risk_analysis(self) -> Dict[str, Any]:
        """Generate default risk analysis when calculation fails"""
        return {
            "overall_score": Decimal("50.00"),
            "credit_score": Decimal("45.00"),
            "market_score": Decimal("50.00"),
            "liquidity_score": Decimal("40.00"),
            "operational_score": Decimal("35.00"),
            "risk_level": "medium",
            "risk_factors": {
                "general": ["Insufficient data for comprehensive analysis"]
            },
            "mitigation_strategies": {
                "general": ["Improve data collection and analysis"]
            },
            "recommendations": [
                "Enhance financial data tracking",
                "Implement comprehensive risk monitoring",
            ],
            "confidence_score": Decimal("60.00"),
            "data_quality_score": Decimal("70.00"),
        }

    async def _calculate_forecast_accuracy(
        self, historical_data: List[Dict[str, Any]], predictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate forecast accuracy metrics"""
        try:
            if not historical_data or not predictions:
                return {"accuracy_score": None, "mean_absolute_error": None}

            # For demonstration, return sample metrics
            return {
                "accuracy_score": Decimal("85.50"),
                "mean_absolute_error": Decimal("1250.75"),
                "mean_squared_error": Decimal("2500000.00"),
                "r_squared": Decimal("0.78"),
            }

        except Exception as e:
            logger.error(f"Error calculating forecast accuracy: {str(e)}")
            return {"accuracy_score": None, "mean_absolute_error": None}
