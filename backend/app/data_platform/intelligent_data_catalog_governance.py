"""
CC02 v79.0 Day 24: Enterprise Integrated Data Platform & Analytics
Module 4: Intelligent Data Catalog & Governance

AI-powered data catalog with automated discovery, intelligent classification,
lineage tracking, and comprehensive governance framework.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import numpy as np
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import networkx as nx
import re
import hashlib
import uuid
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from collections import defaultdict, Counter
import pickle
import time

from ..core.mobile_erp_sdk import MobileERPSDK


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class DataQualityStatus(Enum):
    """Data quality status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class GovernanceAction(Enum):
    """Governance action types"""
    CREATED = "created"
    ACCESSED = "accessed"
    MODIFIED = "modified"
    DELETED = "deleted"
    CLASSIFIED = "classified"
    APPROVED = "approved"
    REJECTED = "rejected"


class DataSensitivity(Enum):
    """Data sensitivity levels"""
    PII = "pii"                    # Personally Identifiable Information
    PHI = "phi"                    # Protected Health Information
    FINANCIAL = "financial"        # Financial data
    INTELLECTUAL_PROPERTY = "ip"   # Intellectual Property
    OPERATIONAL = "operational"    # Operational data
    PUBLIC = "public"              # Public data


@dataclass
class DataAsset:
    """Comprehensive data asset definition"""
    id: str
    name: str
    type: str  # table, file, api, stream, etc.
    source_system: str
    location: str
    schema: Dict[str, Any]
    classification: DataClassification
    sensitivity: DataSensitivity
    owner: str
    steward: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataLineage:
    """Data lineage tracking"""
    id: str
    source_asset_id: str
    target_asset_id: str
    transformation_type: str
    transformation_logic: str
    dependency_level: int
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernancePolicy:
    """Data governance policy"""
    id: str
    name: str
    description: str
    policy_type: str
    rules: List[Dict[str, Any]]
    scope: List[str]  # Asset IDs or patterns
    enforcement_level: str  # warning, blocking, monitoring
    enabled: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataQualityRule:
    """Data quality rule definition"""
    id: str
    name: str
    description: str
    rule_type: str  # completeness, accuracy, consistency, validity
    column: str
    condition: str
    threshold: float
    severity: str  # low, medium, high, critical
    enabled: bool = True


@dataclass
class GovernanceAuditLog:
    """Governance audit log entry"""
    id: str
    asset_id: str
    action: GovernanceAction
    user_id: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class IntelligentDataDiscovery:
    """AI-powered data discovery engine"""
    
    def __init__(self):
        self.discovered_assets: Dict[str, DataAsset] = {}
        self.classification_model = None
        self.nlp_model = None
        self.pattern_library: Dict[str, List[str]] = {}
        
        # Initialize NLP model
        try:
            self.nlp_model = spacy.load("en_core_web_sm")
        except OSError:
            logging.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp_model = None
            
        # Initialize pattern library
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Initialize data pattern recognition library"""
        self.pattern_library = {
            "email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            ],
            "phone": [
                r'\b\d{3}-\d{3}-\d{4}\b',
                r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
                r'\b\d{10}\b'
            ],
            "ssn": [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b'
            ],
            "credit_card": [
                r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',
                r'\b\d{16}\b'
            ],
            "ip_address": [
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ],
            "date": [
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b\d{2}/\d{2}/\d{4}\b',
                r'\b\d{2}-\d{2}-\d{4}\b'
            ],
            "currency": [
                r'\$\d+\.?\d*',
                r'\b\d+\.?\d*\s*(USD|EUR|GBP|JPY)\b'
            ]
        }
        
    async def discover_database_assets(self, connection_string: str) -> List[DataAsset]:
        """Discover data assets from database"""
        discovered_assets = []
        
        try:
            engine = create_engine(connection_string)
            
            # Get metadata about tables
            with engine.connect() as conn:
                # Get table names
                tables_query = """
                SELECT table_name, table_schema 
                FROM information_schema.tables 
                WHERE table_type = 'BASE TABLE'
                """
                
                tables_result = conn.execute(text(tables_query))
                tables = tables_result.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    schema_name = table[1]
                    
                    # Get column information
                    columns_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = '{schema_name}'
                    ORDER BY ordinal_position
                    """
                    
                    columns_result = conn.execute(text(columns_query))
                    columns = columns_result.fetchall()
                    
                    # Build schema information
                    schema_info = {}
                    for col in columns:
                        schema_info[col[0]] = {
                            "type": col[1],
                            "nullable": col[2] == "YES",
                            "default": col[3]
                        }
                        
                    # Sample data for classification
                    sample_query = f"SELECT * FROM {schema_name}.{table_name} LIMIT 100"
                    try:
                        sample_data = pd.read_sql(sample_query, conn)
                        
                        # Analyze and classify
                        classification = await self._classify_data_asset(sample_data, table_name, schema_info)
                        sensitivity = await self._detect_sensitivity(sample_data, schema_info)
                        
                    except Exception as e:
                        logging.warning(f"Could not sample data from {table_name}: {e}")
                        classification = DataClassification.INTERNAL
                        sensitivity = DataSensitivity.OPERATIONAL
                        
                    # Create data asset
                    asset = DataAsset(
                        id=f"db_{schema_name}_{table_name}",
                        name=f"{schema_name}.{table_name}",
                        type="database_table",
                        source_system="database",
                        location=f"{connection_string}/{schema_name}/{table_name}",
                        schema=schema_info,
                        classification=classification,
                        sensitivity=sensitivity,
                        owner="system",
                        steward="data_team",
                        description=f"Database table {table_name} in schema {schema_name}",
                        tags=["database", "table", schema_name]
                    )
                    
                    discovered_assets.append(asset)
                    self.discovered_assets[asset.id] = asset
                    
        except Exception as e:
            logging.error(f"Database discovery failed: {e}")
            
        return discovered_assets
        
    async def discover_file_assets(self, directory_path: str) -> List[DataAsset]:
        """Discover data assets from file system"""
        discovered_assets = []
        
        try:
            data_files = []
            
            # Supported file extensions
            supported_extensions = ['.csv', '.parquet', '.json', '.xlsx', '.xml']
            
            # Scan directory
            for ext in supported_extensions:
                data_files.extend(Path(directory_path).rglob(f"*{ext}"))
                
            for file_path in data_files:
                try:
                    # Load and analyze file
                    if file_path.suffix == '.csv':
                        sample_data = pd.read_csv(file_path, nrows=100)
                    elif file_path.suffix == '.parquet':
                        sample_data = pd.read_parquet(file_path)
                        if len(sample_data) > 100:
                            sample_data = sample_data.head(100)
                    elif file_path.suffix == '.json':
                        sample_data = pd.read_json(file_path, lines=True, nrows=100)
                    elif file_path.suffix == '.xlsx':
                        sample_data = pd.read_excel(file_path, nrows=100)
                    else:
                        continue
                        
                    # Build schema
                    schema_info = {}
                    for col in sample_data.columns:
                        schema_info[col] = {
                            "type": str(sample_data[col].dtype),
                            "nullable": sample_data[col].isnull().any(),
                            "sample_values": sample_data[col].dropna().head(5).tolist()
                        }
                        
                    # Classify asset
                    classification = await self._classify_data_asset(sample_data, file_path.name, schema_info)
                    sensitivity = await self._detect_sensitivity(sample_data, schema_info)
                    
                    # Create asset
                    asset = DataAsset(
                        id=f"file_{hashlib.md5(str(file_path).encode()).hexdigest()}",
                        name=file_path.name,
                        type="data_file",
                        source_system="filesystem",
                        location=str(file_path),
                        schema=schema_info,
                        classification=classification,
                        sensitivity=sensitivity,
                        owner="system",
                        steward="data_team",
                        description=f"Data file: {file_path.name}",
                        tags=["file", file_path.suffix[1:]]
                    )
                    
                    discovered_assets.append(asset)
                    self.discovered_assets[asset.id] = asset
                    
                except Exception as e:
                    logging.warning(f"Could not analyze file {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"File discovery failed: {e}")
            
        return discovered_assets
        
    async def _classify_data_asset(self, data: pd.DataFrame, asset_name: str, 
                                 schema: Dict[str, Any]) -> DataClassification:
        """Classify data asset based on content analysis"""
        
        # Check for sensitive patterns
        has_pii = await self._detect_pii_patterns(data)
        has_financial = await self._detect_financial_patterns(data)
        has_confidential_keywords = await self._detect_confidential_keywords(asset_name, data)
        
        if has_pii or "ssn" in asset_name.lower() or "personal" in asset_name.lower():
            return DataClassification.RESTRICTED
        elif has_financial or "payment" in asset_name.lower() or "transaction" in asset_name.lower():
            return DataClassification.CONFIDENTIAL
        elif has_confidential_keywords:
            return DataClassification.CONFIDENTIAL
        elif "public" in asset_name.lower() or "reference" in asset_name.lower():
            return DataClassification.PUBLIC
        else:
            return DataClassification.INTERNAL
            
    async def _detect_sensitivity(self, data: pd.DataFrame, 
                                schema: Dict[str, Any]) -> DataSensitivity:
        """Detect data sensitivity level"""
        
        # Check for PII patterns
        if await self._detect_pii_patterns(data):
            return DataSensitivity.PII
            
        # Check for financial patterns
        if await self._detect_financial_patterns(data):
            return DataSensitivity.FINANCIAL
            
        # Check for health information
        health_keywords = ['medical', 'health', 'patient', 'diagnosis', 'treatment']
        if any(keyword in str(data.columns).lower() for keyword in health_keywords):
            return DataSensitivity.PHI
            
        # Check for IP patterns
        ip_keywords = ['patent', 'proprietary', 'confidential', 'trade_secret']
        if any(keyword in str(data.columns).lower() for keyword in ip_keywords):
            return DataSensitivity.INTELLECTUAL_PROPERTY
            
        return DataSensitivity.OPERATIONAL
        
    async def _detect_pii_patterns(self, data: pd.DataFrame) -> bool:
        """Detect personally identifiable information patterns"""
        
        # Convert data to string for pattern matching
        data_str = data.astype(str).values.flatten()
        sample_data = ' '.join(data_str[:1000])  # Sample for performance
        
        # Check for email patterns
        for pattern in self.pattern_library["email"]:
            if re.search(pattern, sample_data):
                return True
                
        # Check for phone patterns
        for pattern in self.pattern_library["phone"]:
            if re.search(pattern, sample_data):
                return True
                
        # Check for SSN patterns
        for pattern in self.pattern_library["ssn"]:
            if re.search(pattern, sample_data):
                return True
                
        # Check column names for PII indicators
        pii_columns = ['email', 'phone', 'ssn', 'social_security', 'address', 'name']
        column_names = [col.lower() for col in data.columns]
        
        for pii_col in pii_columns:
            if any(pii_col in col_name for col_name in column_names):
                return True
                
        return False
        
    async def _detect_financial_patterns(self, data: pd.DataFrame) -> bool:
        """Detect financial data patterns"""
        
        # Convert data to string for pattern matching
        data_str = data.astype(str).values.flatten()
        sample_data = ' '.join(data_str[:1000])
        
        # Check for credit card patterns
        for pattern in self.pattern_library["credit_card"]:
            if re.search(pattern, sample_data):
                return True
                
        # Check for currency patterns
        for pattern in self.pattern_library["currency"]:
            if re.search(pattern, sample_data):
                return True
                
        # Check column names for financial indicators
        financial_columns = ['amount', 'price', 'cost', 'payment', 'salary', 'account']
        column_names = [col.lower() for col in data.columns]
        
        for fin_col in financial_columns:
            if any(fin_col in col_name for col_name in column_names):
                return True
                
        return False
        
    async def _detect_confidential_keywords(self, asset_name: str, data: pd.DataFrame) -> bool:
        """Detect confidential keywords"""
        
        confidential_keywords = [
            'confidential', 'secret', 'internal', 'private', 'restricted',
            'classified', 'sensitive', 'proprietary'
        ]
        
        # Check asset name
        name_lower = asset_name.lower()
        if any(keyword in name_lower for keyword in confidential_keywords):
            return True
            
        # Check column names
        columns_str = ' '.join(data.columns).lower()
        if any(keyword in columns_str for keyword in confidential_keywords):
            return True
            
        return False


class DataLineageTracker:
    """Automated data lineage tracking"""
    
    def __init__(self):
        self.lineage_graph = nx.DiGraph()
        self.lineage_records: Dict[str, DataLineage] = {}
        self.transformation_patterns: Dict[str, str] = {}
        
    def add_lineage_relationship(self, lineage: DataLineage):
        """Add data lineage relationship"""
        self.lineage_records[lineage.id] = lineage
        
        # Add to graph
        self.lineage_graph.add_edge(
            lineage.source_asset_id,
            lineage.target_asset_id,
            transformation=lineage.transformation_type,
            lineage_id=lineage.id
        )
        
        logging.info(f"Added lineage: {lineage.source_asset_id} -> {lineage.target_asset_id}")
        
    def trace_upstream_lineage(self, asset_id: str, max_depth: int = 10) -> Dict[str, Any]:
        """Trace upstream data lineage"""
        upstream_assets = []
        
        try:
            # Find all upstream paths
            for depth in range(1, max_depth + 1):
                for source in self.lineage_graph.nodes():
                    if nx.has_path(self.lineage_graph, source, asset_id):
                        try:
                            path = nx.shortest_path(self.lineage_graph, source, asset_id)
                            if len(path) == depth + 1:  # depth + 1 because path includes source and target
                                upstream_assets.append({
                                    "asset_id": source,
                                    "path": path,
                                    "depth": depth,
                                    "transformations": self._get_path_transformations(path)
                                })
                        except nx.NetworkXNoPath:
                            continue
                            
        except Exception as e:
            logging.error(f"Upstream lineage trace failed: {e}")
            
        return {
            "target_asset_id": asset_id,
            "upstream_assets": upstream_assets,
            "total_upstream": len(upstream_assets)
        }
        
    def trace_downstream_lineage(self, asset_id: str, max_depth: int = 10) -> Dict[str, Any]:
        """Trace downstream data lineage"""
        downstream_assets = []
        
        try:
            # Find all downstream paths
            for depth in range(1, max_depth + 1):
                for target in self.lineage_graph.nodes():
                    if nx.has_path(self.lineage_graph, asset_id, target):
                        try:
                            path = nx.shortest_path(self.lineage_graph, asset_id, target)
                            if len(path) == depth + 1:
                                downstream_assets.append({
                                    "asset_id": target,
                                    "path": path,
                                    "depth": depth,
                                    "transformations": self._get_path_transformations(path)
                                })
                        except nx.NetworkXNoPath:
                            continue
                            
        except Exception as e:
            logging.error(f"Downstream lineage trace failed: {e}")
            
        return {
            "source_asset_id": asset_id,
            "downstream_assets": downstream_assets,
            "total_downstream": len(downstream_assets)
        }
        
    def _get_path_transformations(self, path: List[str]) -> List[str]:
        """Get transformations along a lineage path"""
        transformations = []
        
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            
            if self.lineage_graph.has_edge(source, target):
                edge_data = self.lineage_graph[source][target]
                transformations.append(edge_data.get("transformation", "unknown"))
                
        return transformations
        
    def get_lineage_impact_analysis(self, asset_id: str) -> Dict[str, Any]:
        """Analyze impact of changes to an asset"""
        
        # Get all affected downstream assets
        downstream = self.trace_downstream_lineage(asset_id)
        
        # Calculate impact metrics
        total_affected = downstream["total_downstream"]
        max_depth = max([asset["depth"] for asset in downstream["downstream_assets"]], default=0)
        
        # Group by transformation type
        transformation_impact = defaultdict(int)
        for asset in downstream["downstream_assets"]:
            for transformation in asset["transformations"]:
                transformation_impact[transformation] += 1
                
        return {
            "source_asset_id": asset_id,
            "total_affected_assets": total_affected,
            "max_propagation_depth": max_depth,
            "transformation_impact": dict(transformation_impact),
            "affected_assets": downstream["downstream_assets"]
        }


class DataGovernanceEngine:
    """Comprehensive data governance engine"""
    
    def __init__(self):
        self.policies: Dict[str, GovernancePolicy] = {}
        self.quality_rules: Dict[str, DataQualityRule] = {}
        self.audit_logs: List[GovernanceAuditLog] = []
        self.access_controls: Dict[str, Dict[str, Any]] = {}
        self.compliance_reports: Dict[str, Dict[str, Any]] = {}
        
    def add_governance_policy(self, policy: GovernancePolicy):
        """Add data governance policy"""
        self.policies[policy.id] = policy
        logging.info(f"Added governance policy: {policy.name}")
        
    def add_quality_rule(self, rule: DataQualityRule):
        """Add data quality rule"""
        self.quality_rules[rule.id] = rule
        logging.info(f"Added quality rule: {rule.name}")
        
    async def evaluate_policy_compliance(self, asset: DataAsset, 
                                       action: GovernanceAction,
                                       user_id: str) -> Dict[str, Any]:
        """Evaluate policy compliance for asset action"""
        
        compliance_results = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check applicable policies
        applicable_policies = self._get_applicable_policies(asset)
        
        for policy in applicable_policies:
            if not policy.enabled:
                continue
                
            # Evaluate policy rules
            for rule in policy.rules:
                violation = await self._evaluate_policy_rule(asset, action, user_id, rule)
                
                if violation:
                    if policy.enforcement_level == "blocking":
                        compliance_results["compliant"] = False
                        compliance_results["violations"].append({
                            "policy_id": policy.id,
                            "policy_name": policy.name,
                            "rule": rule,
                            "severity": "blocking"
                        })
                    elif policy.enforcement_level == "warning":
                        compliance_results["warnings"].append({
                            "policy_id": policy.id,
                            "policy_name": policy.name,
                            "rule": rule,
                            "severity": "warning"
                        })
                        
        # Log compliance check
        await self._log_governance_action(asset.id, action, user_id, {
            "compliance_check": True,
            "compliant": compliance_results["compliant"],
            "violations_count": len(compliance_results["violations"])
        })
        
        return compliance_results
        
    def _get_applicable_policies(self, asset: DataAsset) -> List[GovernancePolicy]:
        """Get policies applicable to an asset"""
        applicable_policies = []
        
        for policy in self.policies.values():
            # Check if policy applies to this asset
            if self._policy_applies_to_asset(policy, asset):
                applicable_policies.append(policy)
                
        return applicable_policies
        
    def _policy_applies_to_asset(self, policy: GovernancePolicy, asset: DataAsset) -> bool:
        """Check if policy applies to asset"""
        
        for scope_pattern in policy.scope:
            # Simple pattern matching
            if scope_pattern == "*" or scope_pattern == asset.id:
                return True
            elif scope_pattern.endswith("*") and asset.id.startswith(scope_pattern[:-1]):
                return True
            elif asset.type in scope_pattern or asset.source_system in scope_pattern:
                return True
                
        return False
        
    async def _evaluate_policy_rule(self, asset: DataAsset, action: GovernanceAction,
                                  user_id: str, rule: Dict[str, Any]) -> bool:
        """Evaluate individual policy rule"""
        
        rule_type = rule.get("type", "")
        
        if rule_type == "classification_required":
            return asset.classification == DataClassification.PUBLIC  # Example: shouldn't be public
            
        elif rule_type == "owner_required":
            return not asset.owner or asset.owner == "system"
            
        elif rule_type == "access_control":
            required_role = rule.get("required_role", "")
            user_roles = self._get_user_roles(user_id)
            return required_role not in user_roles
            
        elif rule_type == "retention_period":
            max_age_days = rule.get("max_age_days", 365)
            asset_age = (datetime.now() - asset.created_at).days
            return asset_age > max_age_days
            
        elif rule_type == "sensitive_data_protection":
            if asset.sensitivity in [DataSensitivity.PII, DataSensitivity.PHI]:
                return action in [GovernanceAction.ACCESSED, GovernanceAction.MODIFIED]
                
        return False
        
    def _get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles (mock implementation)"""
        # In real implementation, would query user management system
        user_roles_map = {
            "admin": ["admin", "data_steward", "analyst"],
            "analyst": ["analyst"],
            "viewer": ["viewer"]
        }
        return user_roles_map.get(user_id, ["viewer"])
        
    async def evaluate_data_quality(self, asset: DataAsset, data: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate data quality against rules"""
        
        quality_results = {
            "overall_score": 100.0,
            "rule_results": [],
            "issues": [],
            "recommendations": []
        }
        
        # Get applicable quality rules
        applicable_rules = [
            rule for rule in self.quality_rules.values()
            if rule.enabled and (rule.column in data.columns or rule.column == "*")
        ]
        
        total_deductions = 0
        
        for rule in applicable_rules:
            result = await self._evaluate_quality_rule(data, rule)
            quality_results["rule_results"].append(result)
            
            if not result["passed"]:
                # Deduct points based on severity
                severity_weights = {"low": 5, "medium": 10, "high": 20, "critical": 30}
                deduction = severity_weights.get(rule.severity, 10)
                total_deductions += deduction
                
                quality_results["issues"].append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "severity": rule.severity,
                    "description": result["description"],
                    "affected_records": result.get("affected_records", 0)
                })
                
        # Calculate final score
        quality_results["overall_score"] = max(0, 100 - total_deductions)
        
        # Determine quality status
        score = quality_results["overall_score"]
        if score >= 95:
            quality_status = DataQualityStatus.EXCELLENT
        elif score >= 85:
            quality_status = DataQualityStatus.GOOD
        elif score >= 70:
            quality_status = DataQualityStatus.FAIR
        elif score >= 50:
            quality_status = DataQualityStatus.POOR
        else:
            quality_status = DataQualityStatus.CRITICAL
            
        quality_results["quality_status"] = quality_status.value
        
        return quality_results
        
    async def _evaluate_quality_rule(self, data: pd.DataFrame, rule: DataQualityRule) -> Dict[str, Any]:
        """Evaluate individual quality rule"""
        
        result = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "passed": True,
            "description": "",
            "metric_value": 0.0
        }
        
        try:
            if rule.rule_type == "completeness":
                # Check for missing values
                if rule.column == "*":
                    # Overall completeness
                    total_cells = data.shape[0] * data.shape[1]
                    missing_cells = data.isnull().sum().sum()
                    completeness = ((total_cells - missing_cells) / total_cells) * 100
                else:
                    # Column completeness
                    completeness = ((len(data) - data[rule.column].isnull().sum()) / len(data)) * 100
                    
                result["metric_value"] = completeness
                result["passed"] = completeness >= rule.threshold
                result["description"] = f"Completeness: {completeness:.2f}% (threshold: {rule.threshold}%)"
                
            elif rule.rule_type == "uniqueness":
                # Check for duplicate values
                if rule.column in data.columns:
                    unique_count = data[rule.column].nunique()
                    total_count = len(data[rule.column].dropna())
                    uniqueness = (unique_count / total_count) * 100 if total_count > 0 else 0
                    
                    result["metric_value"] = uniqueness
                    result["passed"] = uniqueness >= rule.threshold
                    result["description"] = f"Uniqueness: {uniqueness:.2f}% (threshold: {rule.threshold}%)"
                    
            elif rule.rule_type == "validity":
                # Check for valid values based on condition
                if rule.column in data.columns:
                    if "regex" in rule.condition:
                        pattern = rule.condition.split("regex:")[1]
                        valid_count = data[rule.column].astype(str).str.match(pattern).sum()
                        validity = (valid_count / len(data)) * 100
                        
                        result["metric_value"] = validity
                        result["passed"] = validity >= rule.threshold
                        result["description"] = f"Validity (regex): {validity:.2f}% (threshold: {rule.threshold}%)"
                        
            elif rule.rule_type == "consistency":
                # Check for consistent data across related columns
                if rule.condition and "=" in rule.condition:
                    # Example: column1 = column2
                    col1, col2 = rule.condition.split("=")
                    col1, col2 = col1.strip(), col2.strip()
                    
                    if col1 in data.columns and col2 in data.columns:
                        consistent_count = (data[col1] == data[col2]).sum()
                        consistency = (consistent_count / len(data)) * 100
                        
                        result["metric_value"] = consistency
                        result["passed"] = consistency >= rule.threshold
                        result["description"] = f"Consistency: {consistency:.2f}% (threshold: {rule.threshold}%)"
                        
        except Exception as e:
            result["passed"] = False
            result["description"] = f"Rule evaluation failed: {str(e)}"
            
        return result
        
    async def _log_governance_action(self, asset_id: str, action: GovernanceAction,
                                   user_id: str, details: Dict[str, Any]):
        """Log governance action"""
        
        log_entry = GovernanceAuditLog(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            action=action,
            user_id=user_id,
            timestamp=datetime.now(),
            details=details
        )
        
        self.audit_logs.append(log_entry)
        
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report"""
        
        # Filter audit logs for date range
        period_logs = [
            log for log in self.audit_logs
            if start_date <= log.timestamp <= end_date
        ]
        
        # Calculate metrics
        total_actions = len(period_logs)
        violations = len([log for log in period_logs 
                         if log.details.get("compliance_check") and not log.details.get("compliant")])
        
        # Group by action type
        actions_by_type = Counter([log.action.value for log in period_logs])
        
        # Group by asset
        actions_by_asset = Counter([log.asset_id for log in period_logs])
        
        # Group by user
        actions_by_user = Counter([log.user_id for log in period_logs])
        
        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_actions": total_actions,
                "policy_violations": violations,
                "compliance_rate": ((total_actions - violations) / total_actions * 100) if total_actions > 0 else 100
            },
            "actions_by_type": dict(actions_by_type),
            "top_accessed_assets": dict(actions_by_asset.most_common(10)),
            "top_active_users": dict(actions_by_user.most_common(10)),
            "active_policies": len([p for p in self.policies.values() if p.enabled]),
            "active_quality_rules": len([r for r in self.quality_rules.values() if r.enabled])
        }
        
        return report


class IntelligentDataCatalogSystem:
    """Main intelligent data catalog and governance system"""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self.discovery_engine = IntelligentDataDiscovery()
        self.lineage_tracker = DataLineageTracker()
        self.governance_engine = DataGovernanceEngine()
        
        # Asset registry
        self.data_assets: Dict[str, DataAsset] = {}
        self.asset_relationships: Dict[str, List[str]] = defaultdict(list)
        
        # Search and recommendation
        self.search_index: Dict[str, List[str]] = defaultdict(list)
        self.recommendation_cache: Dict[str, List[str]] = {}
        
        # System configuration
        self.catalog_enabled = True
        self.auto_discovery_enabled = True
        self.governance_enabled = True
        
        # Initialize default policies and rules
        self._initialize_default_governance()
        
        logging.info("Intelligent Data Catalog system initialized")
        
    def _initialize_default_governance(self):
        """Initialize default governance policies and rules"""
        
        # Default governance policies
        pii_policy = GovernancePolicy(
            id="pii_protection_policy",
            name="PII Protection Policy",
            description="Protect personally identifiable information",
            policy_type="data_protection",
            rules=[
                {
                    "type": "sensitive_data_protection",
                    "condition": "pii_data",
                    "action_restrictions": ["export", "share"]
                },
                {
                    "type": "access_control", 
                    "required_role": "data_steward",
                    "applies_to": "pii_assets"
                }
            ],
            scope=["*"],
            enforcement_level="blocking",
            created_by="system"
        )
        self.governance_engine.add_governance_policy(pii_policy)
        
        # Default quality rules
        completeness_rule = DataQualityRule(
            id="general_completeness",
            name="General Completeness Check",
            description="Ensure data completeness above 95%",
            rule_type="completeness",
            column="*",
            condition="not_null",
            threshold=95.0,
            severity="high"
        )
        self.governance_engine.add_quality_rule(completeness_rule)
        
        uniqueness_rule = DataQualityRule(
            id="id_uniqueness",
            name="ID Field Uniqueness",
            description="Ensure ID fields are unique",
            rule_type="uniqueness",
            column="id",
            condition="unique",
            threshold=100.0,
            severity="critical"
        )
        self.governance_engine.add_quality_rule(uniqueness_rule)
        
    async def register_data_asset(self, asset: DataAsset) -> bool:
        """Register data asset in catalog"""
        try:
            self.data_assets[asset.id] = asset
            
            # Update search index
            await self._update_search_index(asset)
            
            # Log registration
            await self.governance_engine._log_governance_action(
                asset.id, GovernanceAction.CREATED, asset.owner, 
                {"asset_type": asset.type, "classification": asset.classification.value}
            )
            
            logging.info(f"Registered data asset: {asset.name}")
            return True
            
        except Exception as e:
            logging.error(f"Asset registration failed: {e}")
            return False
            
    async def discover_assets_auto(self, sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """Automatically discover assets from multiple sources"""
        
        if not self.auto_discovery_enabled:
            return {"message": "Auto-discovery disabled"}
            
        discovery_results = {
            "total_discovered": 0,
            "by_source": {},
            "new_assets": [],
            "errors": []
        }
        
        for source in sources:
            source_type = source.get("type", "")
            source_location = source.get("location", "")
            
            try:
                if source_type == "database":
                    assets = await self.discovery_engine.discover_database_assets(source_location)
                elif source_type == "filesystem":
                    assets = await self.discovery_engine.discover_file_assets(source_location)
                else:
                    continue
                    
                # Register discovered assets
                new_assets = []
                for asset in assets:
                    if asset.id not in self.data_assets:
                        await self.register_data_asset(asset)
                        new_assets.append(asset.id)
                        
                discovery_results["by_source"][source_location] = {
                    "discovered": len(assets),
                    "new": len(new_assets)
                }
                discovery_results["new_assets"].extend(new_assets)
                discovery_results["total_discovered"] += len(assets)
                
            except Exception as e:
                discovery_results["errors"].append({
                    "source": source_location,
                    "error": str(e)
                })
                
        return discovery_results
        
    async def _update_search_index(self, asset: DataAsset):
        """Update search index for asset discovery"""
        
        # Index by name
        name_tokens = asset.name.lower().split()
        for token in name_tokens:
            self.search_index[token].append(asset.id)
            
        # Index by tags
        for tag in asset.tags:
            self.search_index[tag.lower()].append(asset.id)
            
        # Index by type and source
        self.search_index[asset.type].append(asset.id)
        self.search_index[asset.source_system].append(asset.id)
        
    async def search_assets(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search data assets"""
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Find matching assets
        matching_asset_ids = set()
        
        for token in query_tokens:
            if token in self.search_index:
                matching_asset_ids.update(self.search_index[token])
                
        # Apply filters
        if filters:
            filtered_assets = []
            for asset_id in matching_asset_ids:
                asset = self.data_assets.get(asset_id)
                if asset and self._asset_matches_filters(asset, filters):
                    filtered_assets.append(asset_id)
            matching_asset_ids = set(filtered_assets)
            
        # Build search results
        results = []
        for asset_id in matching_asset_ids:
            asset = self.data_assets.get(asset_id)
            if asset:
                results.append({
                    "asset_id": asset.id,
                    "name": asset.name,
                    "type": asset.type,
                    "source_system": asset.source_system,
                    "classification": asset.classification.value,
                    "sensitivity": asset.sensitivity.value,
                    "owner": asset.owner,
                    "description": asset.description,
                    "tags": asset.tags,
                    "quality_score": asset.quality_score,
                    "last_updated": asset.last_updated
                })
                
        # Sort by relevance (simplified scoring)
        results.sort(key=lambda x: len([t for t in query_tokens if t in x["name"].lower()]), reverse=True)
        
        return results
        
    def _asset_matches_filters(self, asset: DataAsset, filters: Dict[str, Any]) -> bool:
        """Check if asset matches search filters"""
        
        if "type" in filters and asset.type not in filters["type"]:
            return False
            
        if "classification" in filters and asset.classification.value not in filters["classification"]:
            return False
            
        if "sensitivity" in filters and asset.sensitivity.value not in filters["sensitivity"]:
            return False
            
        if "owner" in filters and asset.owner not in filters["owner"]:
            return False
            
        if "tags" in filters:
            filter_tags = set(filters["tags"])
            asset_tags = set(asset.tags)
            if not filter_tags.intersection(asset_tags):
                return False
                
        return True
        
    async def get_asset_recommendations(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get asset recommendations based on similarity"""
        
        if asset_id in self.recommendation_cache:
            return self.recommendation_cache[asset_id]
            
        asset = self.data_assets.get(asset_id)
        if not asset:
            return []
            
        recommendations = []
        
        # Find similar assets based on tags, type, and classification
        for other_id, other_asset in self.data_assets.items():
            if other_id == asset_id:
                continue
                
            similarity_score = 0
            
            # Type similarity
            if asset.type == other_asset.type:
                similarity_score += 0.3
                
            # Tag similarity
            common_tags = set(asset.tags).intersection(set(other_asset.tags))
            if asset.tags and other_asset.tags:
                tag_similarity = len(common_tags) / len(set(asset.tags).union(set(other_asset.tags)))
                similarity_score += tag_similarity * 0.4
                
            # Classification similarity
            if asset.classification == other_asset.classification:
                similarity_score += 0.2
                
            # Source system similarity
            if asset.source_system == other_asset.source_system:
                similarity_score += 0.1
                
            if similarity_score > 0.3:  # Threshold for recommendation
                recommendations.append({
                    "asset_id": other_asset.id,
                    "name": other_asset.name,
                    "similarity_score": similarity_score,
                    "common_tags": list(common_tags),
                    "reason": "Similar content and classification"
                })
                
        # Sort by similarity score
        recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Cache results
        self.recommendation_cache[asset_id] = recommendations[:10]  # Top 10
        
        return recommendations[:10]
        
    async def validate_asset_governance(self, asset_id: str, action: GovernanceAction,
                                      user_id: str) -> Dict[str, Any]:
        """Validate governance compliance for asset action"""
        
        asset = self.data_assets.get(asset_id)
        if not asset:
            return {"error": "Asset not found"}
            
        return await self.governance_engine.evaluate_policy_compliance(asset, action, user_id)
        
    async def assess_data_quality(self, asset_id: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality for asset"""
        
        asset = self.data_assets.get(asset_id)
        if not asset:
            return {"error": "Asset not found"}
            
        quality_results = await self.governance_engine.evaluate_data_quality(asset, data)
        
        # Update asset quality score
        asset.quality_score = quality_results["overall_score"]
        
        return quality_results
        
    def get_catalog_metrics(self) -> Dict[str, Any]:
        """Get catalog metrics and statistics"""
        
        total_assets = len(self.data_assets)
        
        # Group by type
        by_type = Counter([asset.type for asset in self.data_assets.values()])
        
        # Group by classification
        by_classification = Counter([asset.classification.value for asset in self.data_assets.values()])
        
        # Group by sensitivity
        by_sensitivity = Counter([asset.sensitivity.value for asset in self.data_assets.values()])
        
        # Calculate average quality score
        quality_scores = [asset.quality_score for asset in self.data_assets.values() if asset.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "timestamp": datetime.now(),
            "total_assets": total_assets,
            "assets_by_type": dict(by_type),
            "assets_by_classification": dict(by_classification),
            "assets_by_sensitivity": dict(by_sensitivity),
            "average_quality_score": avg_quality,
            "total_lineage_relationships": len(self.lineage_tracker.lineage_records),
            "active_policies": len([p for p in self.governance_engine.policies.values() if p.enabled]),
            "search_index_size": sum(len(assets) for assets in self.search_index.values())
        }
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        catalog_metrics = self.get_catalog_metrics()
        
        # Recent activity
        recent_logs = [
            log for log in self.governance_engine.audit_logs
            if log.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            "timestamp": datetime.now(),
            "catalog_enabled": self.catalog_enabled,
            "auto_discovery_enabled": self.auto_discovery_enabled,
            "governance_enabled": self.governance_enabled,
            "catalog_metrics": catalog_metrics,
            "recent_activity": {
                "actions_last_24h": len(recent_logs),
                "discovered_assets": len(self.discovery_engine.discovered_assets)
            }
        }


# Example usage and testing
async def main():
    """Example usage of the Intelligent Data Catalog & Governance system"""
    
    # Initialize SDK (mock)
    class MockMobileERPSDK:
        pass
    
    sdk = MockMobileERPSDK()
    
    # Create catalog system
    catalog_system = IntelligentDataCatalogSystem(sdk)
    
    # Get initial system status
    status = catalog_system.get_system_status()
    print(f"Initial Catalog Status: {json.dumps(status, indent=2, default=str)}")
    
    # Create sample data assets
    print("Creating sample data assets...")
    
    # Customer data asset
    customer_asset = DataAsset(
        id="customer_data_001",
        name="Customer Database",
        type="database_table",
        source_system="erp_database",
        location="postgresql://localhost/erp/customers",
        schema={
            "customer_id": {"type": "integer", "nullable": False},
            "first_name": {"type": "varchar", "nullable": False},
            "last_name": {"type": "varchar", "nullable": False},
            "email": {"type": "varchar", "nullable": True},
            "phone": {"type": "varchar", "nullable": True}
        },
        classification=DataClassification.CONFIDENTIAL,
        sensitivity=DataSensitivity.PII,
        owner="data_team",
        steward="john_doe",
        description="Main customer database with PII",
        tags=["customer", "pii", "database"]
    )
    
    await catalog_system.register_data_asset(customer_asset)
    
    # Transaction data asset
    transaction_asset = DataAsset(
        id="transaction_data_001",
        name="Transaction History",
        type="database_table",
        source_system="payment_system",
        location="postgresql://localhost/payments/transactions",
        schema={
            "transaction_id": {"type": "uuid", "nullable": False},
            "customer_id": {"type": "integer", "nullable": False},
            "amount": {"type": "decimal", "nullable": False},
            "timestamp": {"type": "timestamp", "nullable": False}
        },
        classification=DataClassification.CONFIDENTIAL,
        sensitivity=DataSensitivity.FINANCIAL,
        owner="finance_team",
        steward="jane_smith",
        description="Customer transaction history",
        tags=["transaction", "financial", "database"]
    )
    
    await catalog_system.register_data_asset(transaction_asset)
    
    # Add lineage relationship
    lineage = DataLineage(
        id="lineage_001",
        source_asset_id="customer_data_001",
        target_asset_id="transaction_data_001",
        transformation_type="join",
        transformation_logic="JOIN ON customer_id",
        dependency_level=1
    )
    
    catalog_system.lineage_tracker.add_lineage_relationship(lineage)
    
    # Search assets
    print("Searching for customer assets...")
    search_results = await catalog_system.search_assets("customer")
    print(f"Found {len(search_results)} assets matching 'customer'")
    
    for result in search_results:
        print(f"  - {result['name']} ({result['type']}) - {result['classification']}")
        
    # Get recommendations
    print("Getting asset recommendations...")
    recommendations = await catalog_system.get_asset_recommendations("customer_data_001")
    print(f"Found {len(recommendations)} recommendations")
    
    for rec in recommendations:
        print(f"  - {rec['name']} (similarity: {rec['similarity_score']:.2f})")
        
    # Test governance compliance
    print("Testing governance compliance...")
    compliance = await catalog_system.validate_asset_governance(
        "customer_data_001", 
        GovernanceAction.ACCESSED, 
        "analyst"
    )
    
    print(f"Compliance check: {'PASSED' if compliance['compliant'] else 'FAILED'}")
    if compliance['violations']:
        print(f"Violations: {len(compliance['violations'])}")
        
    # Test data quality assessment
    print("Testing data quality assessment...")
    
    # Create sample data for quality check
    sample_data = pd.DataFrame({
        'customer_id': range(1, 101),
        'first_name': ['John'] * 95 + [None] * 5,  # 5% missing
        'last_name': ['Doe'] * 100,
        'email': [f'user{i}@example.com' for i in range(100)],
        'phone': ['555-0123'] * 100
    })
    
    quality_results = await catalog_system.assess_data_quality("customer_data_001", sample_data)
    print(f"Data Quality Score: {quality_results['overall_score']:.1f}%")
    print(f"Quality Status: {quality_results['quality_status']}")
    
    if quality_results['issues']:
        print(f"Quality Issues: {len(quality_results['issues'])}")
        
    # Get lineage trace
    print("Tracing data lineage...")
    upstream = catalog_system.lineage_tracker.trace_upstream_lineage("transaction_data_001")
    print(f"Upstream assets: {upstream['total_upstream']}")
    
    downstream = catalog_system.lineage_tracker.trace_downstream_lineage("customer_data_001")
    print(f"Downstream assets: {downstream['total_downstream']}")
    
    # Generate compliance report
    print("Generating compliance report...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    compliance_report = catalog_system.governance_engine.generate_compliance_report(start_date, end_date)
    print(f"Compliance Rate: {compliance_report['summary']['compliance_rate']:.1f}%")
    print(f"Total Actions: {compliance_report['summary']['total_actions']}")
    
    # Get final system status
    final_status = catalog_system.get_system_status()
    print(f"Final Catalog Status: {json.dumps(final_status, indent=2, default=str)}")
    
    print("Intelligent Data Catalog demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())