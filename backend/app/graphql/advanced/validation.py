"""Advanced GraphQL query validation and complexity analysis."""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import strawberry
from strawberry.extensions import SchemaExtension

from app.core.monitoring import monitor_performance


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    PERMISSIVE = "permissive"
    STANDARD = "standard" 
    STRICT = "strict"
    ENTERPRISE = "enterprise"


class ComplexityMetric(str, Enum):
    """Query complexity metrics."""
    DEPTH = "depth"
    FIELD_COUNT = "field_count"
    ARRAY_COUNT = "array_count"
    ARGUMENT_COUNT = "argument_count"
    FRAGMENT_COUNT = "fragment_count"
    DIRECTIVE_COUNT = "directive_count"


@dataclass
class ValidationRule:
    """Custom validation rule."""
    id: str
    name: str
    description: str
    pattern: str
    severity: str  # error, warning, info
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComplexityAnalysis:
    """Query complexity analysis result."""
    query_hash: str
    total_score: int
    depth: int
    field_count: int
    array_count: int
    argument_count: int
    fragment_count: int
    directive_count: int
    estimated_execution_time_ms: float
    memory_estimate_mb: float
    risk_level: str  # low, medium, high, critical
    violations: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Query validation result."""
    query_hash: str
    is_valid: bool
    complexity_analysis: ComplexityAnalysis
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    execution_recommendations: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    allow_execution: bool = True


class QueryComplexityAnalyzer:
    """Advanced query complexity analysis."""
    
    def __init__(self):
        """Initialize complexity analyzer."""
        self.field_weights = {
            "User": 5,
            "Organization": 10,
            "Task": 3,
            "Report": 50,
            "Analytics": 100,
            "Search": 20
        }
        self.operation_weights = {
            "query": 1.0,
            "mutation": 2.0,
            "subscription": 1.5
        }
        self.max_depth = 15
        self.max_field_count = 100
        self.max_complexity_score = 1000
    
    @monitor_performance("graphql.validation.complexity_analysis")
    def analyze_complexity(self, query: str, variables: Optional[Dict[str, Any]] = None) -> ComplexityAnalysis:
        """Perform comprehensive complexity analysis."""
        import hashlib
        
        # Generate query hash
        query_content = query + str(variables or {})
        query_hash = hashlib.md5(query_content.encode()).hexdigest()
        
        # Basic metrics
        depth = self._calculate_depth(query)
        field_count = self._count_fields(query)
        array_count = self._count_arrays(query)
        argument_count = self._count_arguments(query)
        fragment_count = self._count_fragments(query)
        directive_count = self._count_directives(query)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            depth, field_count, array_count, argument_count, fragment_count, directive_count, query
        )
        
        # Estimate execution time and memory
        execution_time = self._estimate_execution_time(complexity_score, field_count, array_count)
        memory_estimate = self._estimate_memory_usage(field_count, array_count, depth)
        
        # Determine risk level
        risk_level = self._assess_risk_level(complexity_score, depth, field_count, execution_time)
        
        # Check for violations
        violations = self._check_complexity_violations(
            complexity_score, depth, field_count, execution_time
        )
        
        return ComplexityAnalysis(
            query_hash=query_hash,
            total_score=complexity_score,
            depth=depth,
            field_count=field_count,
            array_count=array_count,
            argument_count=argument_count,
            fragment_count=fragment_count,
            directive_count=directive_count,
            estimated_execution_time_ms=execution_time,
            memory_estimate_mb=memory_estimate,
            risk_level=risk_level,
            violations=violations
        )
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate maximum query depth."""
        max_depth = 0
        current_depth = 0
        
        # Remove strings and comments to avoid false positives
        cleaned_query = self._clean_query(query)
        
        for char in cleaned_query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        
        return max_depth
    
    def _count_fields(self, query: str) -> int:
        """Count number of fields in query."""
        # Simplified field counting
        lines = query.split('\n')
        field_count = 0
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, comments, and structural elements
            if (stripped and 
                not stripped.startswith('#') and
                not stripped.startswith('{') and
                not stripped.startswith('}') and
                not stripped.startswith('query') and
                not stripped.startswith('mutation') and
                not stripped.startswith('subscription') and
                not stripped.startswith('fragment')):
                
                # Count field-like patterns
                if ':' not in stripped or stripped.count(':') == 1:
                    field_count += 1
        
        return field_count
    
    def _count_arrays(self, query: str) -> int:
        """Count array field references."""
        return query.count('[') + query.count(']')
    
    def _count_arguments(self, query: str) -> int:
        """Count field arguments."""
        # Count opening parentheses as argument indicators
        return query.count('(')
    
    def _count_fragments(self, query: str) -> int:
        """Count fragment usage."""
        return query.lower().count('fragment') + query.count('...')
    
    def _count_directives(self, query: str) -> int:
        """Count directive usage."""
        return query.count('@')
    
    def _calculate_complexity_score(
        self,
        depth: int,
        field_count: int,
        array_count: int,
        argument_count: int,
        fragment_count: int,
        directive_count: int,
        query: str
    ) -> int:
        """Calculate overall complexity score."""
        base_score = 0
        
        # Depth complexity (exponential)
        base_score += depth ** 2 * 10
        
        # Field count (linear)
        base_score += field_count * 5
        
        # Array complexity (higher weight)
        base_score += array_count * 15
        
        # Argument complexity
        base_score += argument_count * 8
        
        # Fragment complexity
        base_score += fragment_count * 12
        
        # Directive complexity
        base_score += directive_count * 6
        
        # Type-specific weights
        for type_name, weight in self.field_weights.items():
            if type_name.lower() in query.lower():
                base_score += weight * query.lower().count(type_name.lower())
        
        # Operation type multiplier
        query_lower = query.lower()
        if 'mutation' in query_lower:
            base_score = int(base_score * self.operation_weights['mutation'])
        elif 'subscription' in query_lower:
            base_score = int(base_score * self.operation_weights['subscription'])
        
        return base_score
    
    def _estimate_execution_time(self, complexity_score: int, field_count: int, array_count: int) -> float:
        """Estimate query execution time in milliseconds."""
        # Base time calculation
        base_time = complexity_score * 0.1  # 0.1ms per complexity point
        
        # Field resolution time
        field_time = field_count * 2  # 2ms per field
        
        # Array processing time
        array_time = array_count * 5  # 5ms per array operation
        
        # Database query estimation
        db_queries = max(1, field_count // 5)  # Assume batching
        db_time = db_queries * 10  # 10ms per DB query
        
        total_time = base_time + field_time + array_time + db_time
        
        return round(total_time, 2)
    
    def _estimate_memory_usage(self, field_count: int, array_count: int, depth: int) -> float:
        """Estimate memory usage in MB."""
        # Base memory for query processing
        base_memory = 0.5
        
        # Memory per field (approximate)
        field_memory = field_count * 0.001  # 1KB per field
        
        # Array memory (higher usage)
        array_memory = array_count * 0.01  # 10KB per array
        
        # Depth memory (stack usage)
        depth_memory = depth * 0.002  # 2KB per depth level
        
        total_memory = base_memory + field_memory + array_memory + depth_memory
        
        return round(total_memory, 3)
    
    def _assess_risk_level(
        self,
        complexity_score: int,
        depth: int,
        field_count: int,
        execution_time: float
    ) -> str:
        """Assess query risk level."""
        if (complexity_score > 800 or depth > 12 or 
            field_count > 80 or execution_time > 5000):
            return "critical"
        elif (complexity_score > 500 or depth > 10 or 
              field_count > 60 or execution_time > 2000):
            return "high"
        elif (complexity_score > 200 or depth > 8 or 
              field_count > 40 or execution_time > 1000):
            return "medium"
        else:
            return "low"
    
    def _check_complexity_violations(
        self,
        complexity_score: int,
        depth: int,
        field_count: int,
        execution_time: float
    ) -> List[str]:
        """Check for complexity violations."""
        violations = []
        
        if depth > self.max_depth:
            violations.append(f"Query depth {depth} exceeds maximum {self.max_depth}")
        
        if field_count > self.max_field_count:
            violations.append(f"Field count {field_count} exceeds maximum {self.max_field_count}")
        
        if complexity_score > self.max_complexity_score:
            violations.append(f"Complexity score {complexity_score} exceeds maximum {self.max_complexity_score}")
        
        if execution_time > 10000:  # 10 seconds
            violations.append(f"Estimated execution time {execution_time}ms exceeds 10 seconds")
        
        return violations
    
    def _clean_query(self, query: str) -> str:
        """Clean query of strings and comments."""
        # Remove string literals
        cleaned = re.sub(r'"[^"]*"', '', query)
        cleaned = re.sub(r"'[^']*'", '', cleaned)
        
        # Remove comments
        cleaned = re.sub(r'#.*$', '', cleaned, flags=re.MULTILINE)
        
        return cleaned


class QueryValidator:
    """Advanced GraphQL query validator."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize query validator."""
        self.validation_level = validation_level
        self.complexity_analyzer = QueryComplexityAnalyzer()
        self.custom_rules: List[ValidationRule] = []
        self.validation_history: List[ValidationResult] = []
        
        # Initialize default rules based on validation level
        self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> None:
        """Initialize validation rules based on level."""
        base_rules = [
            ValidationRule(
                id="no_introspection",
                name="Block Introspection",
                description="Prevent introspection queries in production",
                pattern=r"(__schema|__type)",
                severity="error"
            ),
            ValidationRule(
                id="no_dangerous_mutations",
                name="Block Dangerous Mutations",
                description="Prevent potentially dangerous mutations",
                pattern=r"(delete|remove|destroy).*all",
                severity="error"
            ),
            ValidationRule(
                id="require_authentication",
                name="Require Authentication",
                description="Ensure user is authenticated for sensitive operations",
                pattern=r"(user|admin|private)",
                severity="warning"
            )
        ]
        
        if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.ENTERPRISE]:
            base_rules.extend([
                ValidationRule(
                    id="limit_recursive_queries",
                    name="Limit Recursive Queries",
                    description="Prevent potentially infinite recursive queries",
                    pattern=r"(\w+\s*\{[^}]*\1)",
                    severity="error"
                ),
                ValidationRule(
                    id="no_expensive_operations",
                    name="Block Expensive Operations",
                    description="Prevent expensive search and analytics operations",
                    pattern=r"(analytics|search|report).*\{.*\{",
                    severity="warning"
                )
            ])
        
        self.custom_rules = base_rules
    
    @monitor_performance("graphql.validation.validate_query")
    def validate_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Perform comprehensive query validation."""
        # Perform complexity analysis
        complexity_analysis = self.complexity_analyzer.analyze_complexity(query, variables)
        
        # Initialize validation result
        result = ValidationResult(
            query_hash=complexity_analysis.query_hash,
            is_valid=True,
            complexity_analysis=complexity_analysis
        )
        
        # Apply custom validation rules
        self._apply_custom_rules(query, result)
        
        # Apply context-based validation
        if user_context:
            self._apply_context_validation(query, user_context, result)
        
        # Apply complexity-based validation
        self._apply_complexity_validation(complexity_analysis, result)
        
        # Calculate execution cost
        result.estimated_cost = self._calculate_execution_cost(complexity_analysis)
        
        # Generate recommendations
        result.execution_recommendations = self._generate_recommendations(complexity_analysis, result)
        
        # Final validation decision
        result.is_valid = len(result.validation_errors) == 0
        result.allow_execution = (
            result.is_valid and
            complexity_analysis.risk_level not in ["critical"] and
            len(complexity_analysis.violations) == 0
        )
        
        # Store validation history
        self.validation_history.append(result)
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-500:]
        
        return result
    
    def _apply_custom_rules(self, query: str, result: ValidationResult) -> None:
        """Apply custom validation rules."""
        for rule in self.custom_rules:
            if not rule.enabled:
                continue
            
            if re.search(rule.pattern, query, re.IGNORECASE):
                message = f"{rule.name}: {rule.description}"
                
                if rule.severity == "error":
                    result.validation_errors.append(message)
                elif rule.severity == "warning":
                    result.validation_warnings.append(message)
    
    def _apply_context_validation(
        self,
        query: str,
        user_context: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Apply context-based validation."""
        user_role = user_context.get("role", "anonymous")
        is_authenticated = user_context.get("is_authenticated", False)
        
        # Authentication requirements
        sensitive_patterns = ["user", "admin", "private", "internal"]
        if any(pattern in query.lower() for pattern in sensitive_patterns):
            if not is_authenticated:
                result.validation_errors.append("Authentication required for sensitive queries")
        
        # Role-based restrictions
        if user_role == "anonymous":
            admin_patterns = ["admin", "system", "internal"]
            if any(pattern in query.lower() for pattern in admin_patterns):
                result.validation_errors.append("Admin privileges required")
        
        # Rate limiting based on role
        if user_role in ["free", "basic"]:
            if result.complexity_analysis.total_score > 300:
                result.validation_warnings.append("Query complexity may be limited for your account tier")
    
    def _apply_complexity_validation(
        self,
        complexity_analysis: ComplexityAnalysis,
        result: ValidationResult
    ) -> None:
        """Apply complexity-based validation."""
        # Add complexity violations as errors
        for violation in complexity_analysis.violations:
            result.validation_errors.append(f"Complexity violation: {violation}")
        
        # Risk-based warnings
        if complexity_analysis.risk_level == "high":
            result.validation_warnings.append("High complexity query - consider optimizing")
        elif complexity_analysis.risk_level == "critical":
            result.validation_errors.append("Critical complexity query - execution blocked")
        
        # Performance warnings
        if complexity_analysis.estimated_execution_time_ms > 5000:
            result.validation_warnings.append(
                f"Query may take {complexity_analysis.estimated_execution_time_ms}ms to execute"
            )
        
        if complexity_analysis.memory_estimate_mb > 100:
            result.validation_warnings.append(
                f"Query may use {complexity_analysis.memory_estimate_mb}MB of memory"
            )
    
    def _calculate_execution_cost(self, complexity_analysis: ComplexityAnalysis) -> float:
        """Calculate estimated execution cost."""
        base_cost = 0.01  # Base cost per query
        
        # Complexity cost
        complexity_cost = complexity_analysis.total_score * 0.0001
        
        # Time cost
        time_cost = complexity_analysis.estimated_execution_time_ms * 0.00001
        
        # Memory cost
        memory_cost = complexity_analysis.memory_estimate_mb * 0.001
        
        return round(base_cost + complexity_cost + time_cost + memory_cost, 4)
    
    def _generate_recommendations(
        self,
        complexity_analysis: ComplexityAnalysis,
        result: ValidationResult
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if complexity_analysis.depth > 8:
            recommendations.append("Consider reducing query depth by breaking into multiple queries")
        
        if complexity_analysis.field_count > 50:
            recommendations.append("Consider selecting fewer fields or using pagination")
        
        if complexity_analysis.array_count > 10:
            recommendations.append("Consider limiting array field selections")
        
        if complexity_analysis.estimated_execution_time_ms > 2000:
            recommendations.append("Consider adding indexes or caching for better performance")
        
        if result.estimated_cost > 0.1:
            recommendations.append("Query has high execution cost - consider optimization")
        
        return recommendations
    
    def add_custom_rule(self, rule: ValidationRule) -> None:
        """Add custom validation rule."""
        self.custom_rules.append(rule)
    
    def remove_custom_rule(self, rule_id: str) -> bool:
        """Remove custom validation rule."""
        initial_count = len(self.custom_rules)
        self.custom_rules = [rule for rule in self.custom_rules if rule.id != rule_id]
        return len(self.custom_rules) < initial_count
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation system summary."""
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        recent_validations = self.validation_history[-100:]
        
        total_validations = len(recent_validations)
        successful_validations = len([v for v in recent_validations if v.is_valid])
        blocked_executions = len([v for v in recent_validations if not v.allow_execution])
        
        avg_complexity = sum(v.complexity_analysis.total_score for v in recent_validations) / total_validations
        avg_cost = sum(v.estimated_cost for v in recent_validations) / total_validations
        
        risk_distribution = defaultdict(int)
        for validation in recent_validations:
            risk_distribution[validation.complexity_analysis.risk_level] += 1
        
        return {
            "validation_level": self.validation_level.value,
            "total_validations": total_validations,
            "success_rate_percentage": (successful_validations / total_validations * 100) if total_validations > 0 else 0,
            "blocked_executions": blocked_executions,
            "average_complexity_score": round(avg_complexity, 2),
            "average_execution_cost": round(avg_cost, 4),
            "risk_distribution": dict(risk_distribution),
            "custom_rules_count": len(self.custom_rules),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global validator instances
standard_validator = QueryValidator(ValidationLevel.STANDARD)
strict_validator = QueryValidator(ValidationLevel.STRICT)
enterprise_validator = QueryValidator(ValidationLevel.ENTERPRISE)


# Health check for validation system
async def check_graphql_validation_health() -> Dict[str, Any]:
    """Check GraphQL validation system health."""
    standard_summary = standard_validator.get_validation_summary()
    
    # Determine health status
    health_status = "healthy"
    if standard_summary.get("success_rate_percentage", 100) < 90:
        health_status = "degraded"
    if standard_summary.get("blocked_executions", 0) > 50:
        health_status = "warning"
    
    return {
        "status": health_status,
        "validation_summary": standard_summary,
        "complexity_analyzer": {
            "max_depth": standard_validator.complexity_analyzer.max_depth,
            "max_field_count": standard_validator.complexity_analyzer.max_field_count,
            "max_complexity_score": standard_validator.complexity_analyzer.max_complexity_score
        },
        "available_levels": [level.value for level in ValidationLevel]
    }