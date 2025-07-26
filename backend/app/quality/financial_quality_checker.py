"""
ITDO ERP Backend - Financial Quality Checker
Day 27: Comprehensive quality assurance for financial management system

This module provides:
- Code quality validation
- Business logic verification
- Data integrity checks
- Performance validation
- Security compliance verification
- Integration testing validation
"""

from __future__ import annotations

import ast
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityIssue:
    """Represents a quality issue found during validation"""

    def __init__(
        self,
        issue_id: str,
        severity: str,
        category: str,
        description: str,
        file_path: str,
        line_number: Optional[int] = None,
        recommendation: str = "",
    ):
        self.issue_id = issue_id
        self.severity = severity  # critical, high, medium, low
        self.category = category
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.recommendation = recommendation
        self.detected_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "issue_id": self.issue_id,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "recommendation": self.recommendation,
            "detected_at": self.detected_at.isoformat(),
        }


class FinancialQualityChecker:
    """Comprehensive quality checker for financial management system"""

    def __init__(self, project_root: str = "/home/work/ITDO_ERP2"):
        self.project_root = Path(project_root)
        self.backend_root = self.project_root / "backend"
        self.frontend_root = self.project_root / "frontend"
        self.issues: List[QualityIssue] = []

    async def run_comprehensive_quality_check(self) -> Dict[str, Any]:
        """Run comprehensive quality check on financial management system"""
        logger.info("Starting comprehensive financial system quality check")

        quality_report = {
            "check_started_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "checks_performed": [],
            "issues": [],
            "summary": {},
            "recommendations": [],
            "overall_score": 0,
        }

        try:
            # 1. Code Quality Checks
            await self._check_code_quality()
            quality_report["checks_performed"].append("code_quality")

            # 2. Business Logic Validation
            await self._check_business_logic()
            quality_report["checks_performed"].append("business_logic")

            # 3. Data Integrity Checks
            await self._check_data_integrity()
            quality_report["checks_performed"].append("data_integrity")

            # 4. Performance Validation
            await self._check_performance_standards()
            quality_report["checks_performed"].append("performance")

            # 5. Security Validation
            await self._check_security_implementation()
            quality_report["checks_performed"].append("security")

            # 6. Integration Testing Validation
            await self._check_integration_tests()
            quality_report["checks_performed"].append("integration_tests")

            # 7. API Standards Validation
            await self._check_api_standards()
            quality_report["checks_performed"].append("api_standards")

            # 8. Documentation Quality
            await self._check_documentation_quality()
            quality_report["checks_performed"].append("documentation")

            # Generate final report
            quality_report["issues"] = [issue.to_dict() for issue in self.issues]
            quality_report["summary"] = self._generate_quality_summary()
            quality_report["recommendations"] = self._generate_quality_recommendations()
            quality_report["overall_score"] = self._calculate_overall_score()
            quality_report["check_completed_at"] = datetime.now().isoformat()

            logger.info(f"Quality check completed. Found {len(self.issues)} issues.")
            return quality_report

        except Exception as e:
            logger.error(f"Error during quality check: {str(e)}")
            quality_report["error"] = str(e)
            quality_report["status"] = "failed"
            return quality_report

    async def _check_code_quality(self) -> None:
        """Check code quality standards"""
        logger.debug("Checking code quality standards")

        # Check Python files in financial modules
        financial_modules = [
            "app/models/financial.py",
            "app/models/advanced_financial.py",
            "app/models/multi_currency.py",
            "app/api/v1/financial_integration_api.py",
            "app/services/cross_module_financial_service.py",
            "app/services/integrated_financial_dashboard_service.py",
            "app/utils/financial_performance_optimizer.py",
            "app/security/financial_security_audit.py",
        ]

        for module_path in financial_modules:
            file_path = self.backend_root / module_path
            if file_path.exists():
                await self._check_python_file_quality(file_path)

        # Check TypeScript files for financial frontend
        financial_frontend_files = [
            "src/components/financial/IntegratedFinancialDashboard.tsx",
        ]

        for file_path_str in financial_frontend_files:
            file_path = self.frontend_root / file_path_str
            if file_path.exists():
                await self._check_typescript_file_quality(file_path)

    async def _check_python_file_quality(self, file_path: Path) -> None:
        """Check quality of Python files"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.issues.append(
                    QualityIssue(
                        issue_id="SYNTAX_ERROR",
                        severity="critical",
                        category="Code Quality",
                        description=f"Syntax error in file: {e.msg}",
                        file_path=str(file_path),
                        line_number=e.lineno,
                        recommendation="Fix syntax error to ensure code can be parsed",
                    )
                )
                return

            # Check for docstrings
            if not self._has_module_docstring(tree):
                self.issues.append(
                    QualityIssue(
                        issue_id="MISSING_DOCSTRING",
                        severity="medium",
                        category="Code Quality",
                        description="Module missing docstring",
                        file_path=str(file_path),
                        recommendation="Add comprehensive module docstring explaining purpose and functionality",
                    )
                )

            # Check function complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        self.issues.append(
                            QualityIssue(
                                issue_id="HIGH_COMPLEXITY",
                                severity="high",
                                category="Code Quality",
                                description=f"Function '{node.name}' has high cyclomatic complexity: {complexity}",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                recommendation="Refactor function to reduce complexity (target: < 10)",
                            )
                        )

            # Check for hardcoded values
            self._check_hardcoded_values(content, file_path)

            # Check type annotations
            self._check_type_annotations(tree, file_path)

        except Exception as e:
            logger.warning(f"Error checking Python file {file_path}: {e}")

    async def _check_typescript_file_quality(self, file_path: Path) -> None:
        """Check quality of TypeScript files"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for TODO comments
            todo_pattern = r"//\s*TODO|//\s*FIXME|//\s*HACK"
            for line_num, line in enumerate(content.split("\n"), 1):
                if re.search(todo_pattern, line, re.IGNORECASE):
                    self.issues.append(
                        QualityIssue(
                            issue_id="TODO_COMMENT",
                            severity="low",
                            category="Code Quality",
                            description="TODO/FIXME comment found",
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Address TODO comment or convert to GitHub issue",
                        )
                    )

            # Check for console.log statements
            console_pattern = r"console\.(log|error|warn|debug)"
            for line_num, line in enumerate(content.split("\n"), 1):
                if re.search(console_pattern, line):
                    self.issues.append(
                        QualityIssue(
                            issue_id="CONSOLE_LOG",
                            severity="medium",
                            category="Code Quality",
                            description="Console log statement found",
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Remove console.log or replace with proper logging",
                        )
                    )

            # Check for any type usage
            any_pattern = r":\s*any\b|as\s+any\b"
            for line_num, line in enumerate(content.split("\n"), 1):
                if re.search(any_pattern, line):
                    self.issues.append(
                        QualityIssue(
                            issue_id="ANY_TYPE_USAGE",
                            severity="medium",
                            category="Code Quality",
                            description="'any' type usage found",
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Replace 'any' with specific type definitions",
                        )
                    )

        except Exception as e:
            logger.warning(f"Error checking TypeScript file {file_path}: {e}")

    async def _check_business_logic(self) -> None:
        """Check business logic implementation"""
        logger.debug("Checking business logic implementation")

        # Check financial calculation accuracy
        await self._check_financial_calculations()

        # Check workflow validation
        await self._check_workflow_implementation()

        # Check error handling
        await self._check_error_handling()

    async def _check_financial_calculations(self) -> None:
        """Check financial calculation implementations"""
        # Check for proper decimal usage in financial calculations
        financial_files = [
            self.backend_root / "app/services/cross_module_financial_service.py",
            self.backend_root
            / "app/services/integrated_financial_dashboard_service.py",
        ]

        for file_path in financial_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()

                # Check for float usage in financial calculations
                float_pattern = r"float\("
                for line_num, line in enumerate(content.split("\n"), 1):
                    if re.search(float_pattern, line) and "financial" in line.lower():
                        self.issues.append(
                            QualityIssue(
                                issue_id="FLOAT_IN_FINANCIAL",
                                severity="high",
                                category="Business Logic",
                                description="Float usage in financial calculation detected",
                                file_path=str(file_path),
                                line_number=line_num,
                                recommendation="Use Decimal type for financial calculations to ensure precision",
                            )
                        )

    async def _check_workflow_implementation(self) -> None:
        """Check workflow implementation"""
        # Check for proper transaction handling
        service_files = [
            self.backend_root / "app/services/cross_module_financial_service.py",
            self.backend_root / "app/api/v1/financial_integration_api.py",
        ]

        for file_path in service_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()

                # Check for database transaction handling
                if (
                    "await db.commit()" in content
                    and "await db.rollback()" not in content
                ):
                    self.issues.append(
                        QualityIssue(
                            issue_id="MISSING_ROLLBACK",
                            severity="high",
                            category="Business Logic",
                            description="Database commit without proper rollback handling",
                            file_path=str(file_path),
                            recommendation="Add proper rollback handling in exception cases",
                        )
                    )

    async def _check_error_handling(self) -> None:
        """Check error handling implementation"""
        # Check for bare except clauses
        python_files = list(self.backend_root.rglob("*.py"))

        for file_path in python_files:
            if "financial" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for bare except
                    bare_except_pattern = r"except\s*:"
                    for line_num, line in enumerate(content.split("\n"), 1):
                        if re.search(bare_except_pattern, line):
                            self.issues.append(
                                QualityIssue(
                                    issue_id="BARE_EXCEPT",
                                    severity="medium",
                                    category="Error Handling",
                                    description="Bare except clause found",
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    recommendation="Specify exception types for better error handling",
                                )
                            )
                except Exception:
                    continue

    async def _check_data_integrity(self) -> None:
        """Check data integrity implementation"""
        logger.debug("Checking data integrity")

        # Check model validations
        await self._check_model_validations()

        # Check data constraints
        await self._check_data_constraints()

    async def _check_model_validations(self) -> None:
        """Check model validation implementations"""
        model_files = [
            self.backend_root / "app/models/financial.py",
            self.backend_root / "app/models/advanced_financial.py",
            self.backend_root / "app/models/multi_currency.py",
        ]

        for file_path in model_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()

                # Check for validation decorators
                if "@validates" not in content and "def validate_" not in content:
                    self.issues.append(
                        QualityIssue(
                            issue_id="MISSING_VALIDATION",
                            severity="medium",
                            category="Data Integrity",
                            description="Model lacks validation methods",
                            file_path=str(file_path),
                            recommendation="Add validation methods for critical fields",
                        )
                    )

    async def _check_data_constraints(self) -> None:
        """Check data constraint implementations"""
        # Check for proper decimal constraints
        schema_files = list((self.backend_root / "app/schemas").rglob("*.py"))

        for file_path in schema_files:
            if "financial" in str(file_path) or "currency" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for decimal field constraints
                    if "Decimal" in content and "gt=Decimal(" not in content:
                        self.issues.append(
                            QualityIssue(
                                issue_id="MISSING_DECIMAL_CONSTRAINT",
                                severity="medium",
                                category="Data Integrity",
                                description="Decimal field without proper constraints",
                                file_path=str(file_path),
                                recommendation="Add min/max constraints for decimal fields",
                            )
                        )
                except Exception:
                    continue

    async def _check_performance_standards(self) -> None:
        """Check performance implementation"""
        logger.debug("Checking performance standards")

        # Check for database query optimization
        await self._check_database_queries()

        # Check for caching implementation
        await self._check_caching_usage()

    async def _check_database_queries(self) -> None:
        """Check database query optimization"""
        service_files = list((self.backend_root / "app/services").rglob("*.py"))

        for file_path in service_files:
            if "financial" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for N+1 query patterns
                    if "for " in content and "await db.execute" in content:
                        # Simple heuristic for potential N+1 queries
                        for_blocks = re.finditer(r"for\s+\w+\s+in\s+.*?:", content)
                        for match in for_blocks:
                            line_num = content[: match.start()].count("\n") + 1
                            self.issues.append(
                                QualityIssue(
                                    issue_id="POTENTIAL_N_PLUS_ONE",
                                    severity="medium",
                                    category="Performance",
                                    description="Potential N+1 query pattern detected",
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    recommendation="Consider using batch queries or eager loading",
                                )
                            )
                except Exception:
                    continue

    async def _check_caching_usage(self) -> None:
        """Check caching implementation"""
        # Check if performance optimizer is being used
        optimizer_file = (
            self.backend_root / "app/utils/financial_performance_optimizer.py"
        )
        if optimizer_file.exists():
            service_files = list((self.backend_root / "app/services").rglob("*.py"))

            for file_path in service_files:
                if "financial" in str(file_path):
                    try:
                        with open(file_path, "r") as f:
                            content = f.read()

                        if (
                            "from app.utils.financial_performance_optimizer"
                            not in content
                        ):
                            self.issues.append(
                                QualityIssue(
                                    issue_id="MISSING_PERFORMANCE_OPTIMIZATION",
                                    severity="low",
                                    category="Performance",
                                    description="Financial service not using performance optimization utilities",
                                    file_path=str(file_path),
                                    recommendation="Consider using financial performance optimizer for caching and optimization",
                                )
                            )
                    except Exception:
                        continue

    async def _check_security_implementation(self) -> None:
        """Check security implementation"""
        logger.debug("Checking security implementation")

        # Check for security headers
        await self._check_security_headers()

        # Check for input validation
        await self._check_input_validation()

    async def _check_security_headers(self) -> None:
        """Check security headers implementation"""
        # Check if security headers are implemented in main app
        main_file = self.backend_root / "app/main.py"
        if main_file.exists():
            with open(main_file, "r") as f:
                content = f.read()

            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
            ]
            for header in security_headers:
                if header not in content:
                    self.issues.append(
                        QualityIssue(
                            issue_id="MISSING_SECURITY_HEADER",
                            severity="medium",
                            category="Security",
                            description=f"Missing security header: {header}",
                            file_path=str(main_file),
                            recommendation=f"Add {header} security header",
                        )
                    )

    async def _check_input_validation(self) -> None:
        """Check input validation implementation"""
        api_files = list((self.backend_root / "app/api").rglob("*.py"))

        for file_path in api_files:
            if "financial" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for Pydantic validation
                    if "def " in content and "Field(" not in content:
                        function_matches = re.finditer(r"def\s+(\w+)", content)
                        for match in function_matches:
                            if (
                                "post" in match.group(1).lower()
                                or "put" in match.group(1).lower()
                            ):
                                line_num = content[: match.start()].count("\n") + 1
                                self.issues.append(
                                    QualityIssue(
                                        issue_id="MISSING_INPUT_VALIDATION",
                                        severity="high",
                                        category="Security",
                                        description="API endpoint lacks proper input validation",
                                        file_path=str(file_path),
                                        line_number=line_num,
                                        recommendation="Add Pydantic Field validation for input parameters",
                                    )
                                )
                except Exception:
                    continue

    async def _check_integration_tests(self) -> None:
        """Check integration test coverage"""
        logger.debug("Checking integration test coverage")

        test_file = self.backend_root / "tests/test_financial_integration.py"
        if not test_file.exists():
            self.issues.append(
                QualityIssue(
                    issue_id="MISSING_INTEGRATION_TESTS",
                    severity="high",
                    category="Testing",
                    description="Financial integration tests file missing",
                    file_path=str(test_file),
                    recommendation="Create comprehensive integration tests for financial module",
                )
            )
        else:
            # Check test coverage
            with open(test_file, "r") as f:
                content = f.read()

            test_count = len(re.findall(r"def test_", content))
            if test_count < 10:
                self.issues.append(
                    QualityIssue(
                        issue_id="INSUFFICIENT_TEST_COVERAGE",
                        severity="medium",
                        category="Testing",
                        description=f"Low test coverage: only {test_count} tests found",
                        file_path=str(test_file),
                        recommendation="Add more comprehensive test cases",
                    )
                )

    async def _check_api_standards(self) -> None:
        """Check API standards compliance"""
        logger.debug("Checking API standards")

        api_files = list((self.backend_root / "app/api").rglob("*.py"))

        for file_path in api_files:
            if "financial" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for proper HTTP status codes
                    if (
                        "HTTPException" in content
                        and "status_code=status." not in content
                    ):
                        self.issues.append(
                            QualityIssue(
                                issue_id="INCONSISTENT_STATUS_CODES",
                                severity="medium",
                                category="API Standards",
                                description="Inconsistent HTTP status code usage",
                                file_path=str(file_path),
                                recommendation="Use status module constants for HTTP status codes",
                            )
                        )

                    # Check for proper error responses
                    if "@router." in content and "try:" not in content:
                        self.issues.append(
                            QualityIssue(
                                issue_id="MISSING_ERROR_HANDLING",
                                severity="high",
                                category="API Standards",
                                description="API endpoint lacks error handling",
                                file_path=str(file_path),
                                recommendation="Add try-catch blocks for proper error handling",
                            )
                        )
                except Exception:
                    continue

    async def _check_documentation_quality(self) -> None:
        """Check documentation quality"""
        logger.debug("Checking documentation quality")

        # Check for API documentation
        api_files = list((self.backend_root / "app/api").rglob("*.py"))

        for file_path in api_files:
            if "financial" in str(file_path):
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for docstrings in API endpoints
                    router_matches = re.finditer(
                        r"@router\.(get|post|put|delete)", content
                    )
                    for match in router_matches:
                        # Look for docstring after the decorator
                        after_decorator = content[match.end() :]
                        if '"""' not in after_decorator[:200]:  # Check next 200 chars
                            line_num = content[: match.start()].count("\n") + 1
                            self.issues.append(
                                QualityIssue(
                                    issue_id="MISSING_API_DOCSTRING",
                                    severity="medium",
                                    category="Documentation",
                                    description="API endpoint missing docstring",
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    recommendation="Add comprehensive docstring for API endpoint",
                                )
                            )
                except Exception:
                    continue

    def _has_module_docstring(self, tree: ast.AST) -> bool:
        """Check if module has docstring"""
        return (
            isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        )

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith),
            ):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _check_hardcoded_values(self, content: str, file_path: Path) -> None:
        """Check for hardcoded values"""
        # Look for common hardcoded patterns
        patterns = [
            (r'\b(https?://[^\s\'"]+)', "Hardcoded URL"),
            (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "Hardcoded IP address"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        ]

        for pattern, description in patterns:
            for line_num, line in enumerate(content.split("\n"), 1):
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(
                        QualityIssue(
                            issue_id="HARDCODED_VALUE",
                            severity="medium",
                            category="Code Quality",
                            description=description,
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Move hardcoded value to configuration",
                        )
                    )

    def _check_type_annotations(self, tree: ast.AST, file_path: Path) -> None:
        """Check for type annotations"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has return type annotation
                if node.returns is None and node.name != "__init__":
                    self.issues.append(
                        QualityIssue(
                            issue_id="MISSING_RETURN_TYPE",
                            severity="low",
                            category="Code Quality",
                            description=f"Function '{node.name}' missing return type annotation",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            recommendation="Add return type annotation for better code clarity",
                        )
                    )

    def _generate_quality_summary(self) -> Dict[str, Any]:
        """Generate quality summary"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {}

        for issue in self.issues:
            severity_counts[issue.severity] += 1
            category = issue.category
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_issues": len(self.issues),
            "issues_by_severity": severity_counts,
            "issues_by_category": category_counts,
            "critical_issues": severity_counts["critical"],
            "high_issues": severity_counts["high"],
            "medium_issues": severity_counts["medium"],
            "low_issues": severity_counts["low"],
        }

    def _generate_quality_recommendations(self) -> List[Dict[str, Any]]:
        """Generate quality recommendations"""
        recommendations = []

        # Group issues by severity and provide recommendations
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        high_issues = [i for i in self.issues if i.severity == "high"]

        if critical_issues:
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "Critical Issues",
                    "recommendation": f"Address {len(critical_issues)} critical issues immediately",
                    "affected_files": list(set(i.file_path for i in critical_issues)),
                    "estimated_effort": "high",
                }
            )

        if high_issues:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "High Priority Issues",
                    "recommendation": f"Address {len(high_issues)} high priority issues",
                    "affected_files": list(set(i.file_path for i in high_issues)),
                    "estimated_effort": "medium",
                }
            )

        # Add general recommendations
        recommendations.extend(
            [
                {
                    "priority": "medium",
                    "category": "Code Quality",
                    "recommendation": "Implement automated code quality checks in CI/CD pipeline",
                    "estimated_effort": "medium",
                },
                {
                    "priority": "medium",
                    "category": "Testing",
                    "recommendation": "Increase test coverage to > 90% for financial modules",
                    "estimated_effort": "high",
                },
                {
                    "priority": "low",
                    "category": "Documentation",
                    "recommendation": "Add comprehensive API documentation with examples",
                    "estimated_effort": "medium",
                },
            ]
        )

        return recommendations

    def _calculate_overall_score(self) -> float:
        """Calculate overall quality score"""
        if not self.issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_weight = sum(severity_weights[issue.severity] for issue in self.issues)

        # Calculate score (100 - weighted issues)
        max_possible_weight = len(self.issues) * 10  # If all were critical
        score = max(0, 100 - (total_weight / max_possible_weight * 100))

        return round(score, 1)


async def run_financial_quality_check(
    project_root: str = "/home/work/ITDO_ERP2",
) -> Dict[str, Any]:
    """Run comprehensive quality check on financial management system"""
    checker = FinancialQualityChecker(project_root)
    return await checker.run_comprehensive_quality_check()
