#!/usr/bin/env python3
"""
CC02 v33.0 コード品質最適化ツール - Infinite Loop Cycle 3
Code Quality Optimizer for Comprehensive Code Analysis and Improvement
"""

import ast
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict


@dataclass
class CodeQualityIssue:
    """コード品質問題データクラス"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggestion: str
    code_snippet: str
    complexity_score: int = 0


@dataclass
class FileQualityMetrics:
    """ファイル品質メトリクス"""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    code_duplication_score: float
    test_coverage: float
    issues_count: int
    quality_grade: str


class CodeQualityOptimizer:
    """コード品質最適化ツール"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.output_path = project_root / "scripts" / "code_quality_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # Code quality rules
        self.quality_rules = {
            "complexity_rules": {
                "max_function_length": 50,
                "max_class_length": 300,
                "max_cyclomatic_complexity": 10,
                "max_nesting_depth": 4,
                "max_parameters": 5
            },
            "naming_conventions": {
                "function_pattern": r"^[a-z_][a-z0-9_]*$",
                "class_pattern": r"^[A-Z][a-zA-Z0-9]*$",
                "constant_pattern": r"^[A-Z][A-Z0-9_]*$",
                "variable_pattern": r"^[a-z_][a-z0-9_]*$"
            },
            "code_smells": {
                "long_parameter_list": r"def\s+\w+\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*,[^)]*\):",
                "duplicate_code": r"(.{20,})\n(?:.*\n)*?\1",
                "magic_numbers": r"\b(?<![\w.])[2-9]\d+(?![\w.])\b",
                "god_class": r"class\s+\w+.*?(?=\nclass\s|\ndef\s|\Z)",
                "feature_envy": r"self\.\w+\.\w+\.\w+",
                "data_clumps": r"def\s+\w+\([^)]*(\w+),\s*(\w+),\s*(\w+)[^)]*\):",
                "dead_code": r"def\s+\w+\([^)]*\):(?:\s*#.*\n)*\s*pass\s*$"
            },
            "security_patterns": {
                "sql_injection_risk": r"['\"].*\+.*['\"]",
                "hardcoded_secrets": r"(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]",
                "unsafe_eval": r"eval\s*\(",
                "shell_injection": r"os\.system\(|subprocess\.call\(",
                "unsafe_deserialization": r"pickle\.loads?\(|yaml\.load\("
            }
        }
        
        # Quality metrics thresholds
        self.quality_thresholds = {
            "maintainability_index": {
                "excellent": 85,
                "good": 70,
                "acceptable": 50,
                "poor": 25
            },
            "complexity_score": {
                "simple": 10,
                "moderate": 20,
                "complex": 50,
                "very_complex": 100
            }
        }
        
        # Code improvement templates
        self.improvement_templates = {
            "extract_method": self._generate_extract_method_refactoring,
            "simplify_conditionals": self._generate_conditional_simplification,
            "reduce_parameters": self._generate_parameter_reduction,
            "eliminate_duplication": self._generate_duplication_elimination,
            "improve_naming": self._generate_naming_improvements
        }
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """包括的コード品質分析"""
        print("🔍 Analyzing code quality across the codebase...")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "file_metrics": {},
            "quality_issues": [],
            "code_smells": defaultdict(list),
            "security_issues": [],
            "refactoring_opportunities": [],
            "quality_summary": {}
        }
        
        python_files = list(self.backend_path.glob("**/*.py"))
        total_files = len([f for f in python_files if not f.name.startswith("__")])
        
        print(f"  📊 Analyzing {total_files} Python files...")
        
        for file_path in python_files:
            if file_path.name.startswith("__") or "migrations" in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze individual file
                file_analysis = self._analyze_file_quality(content, file_path)
                
                if file_analysis:
                    rel_path = str(file_path.relative_to(self.project_root))
                    analysis_results["file_metrics"][rel_path] = file_analysis["metrics"]
                    analysis_results["quality_issues"].extend(file_analysis["issues"])
                    
                    # Aggregate code smells
                    for smell_type, smells in file_analysis["code_smells"].items():
                        analysis_results["code_smells"][smell_type].extend(smells)
                    
                    analysis_results["security_issues"].extend(file_analysis["security_issues"])
                    analysis_results["refactoring_opportunities"].extend(file_analysis["refactoring_opportunities"])
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
        
        # Generate quality summary
        analysis_results["quality_summary"] = self._generate_quality_summary(analysis_results)
        
        return analysis_results
    
    def _analyze_file_quality(self, content: str, file_path: Path) -> Dict[str, Any]:
        """個別ファイルの品質分析"""
        analysis = {
            "metrics": None,
            "issues": [],
            "code_smells": defaultdict(list),
            "security_issues": [],
            "refactoring_opportunities": []
        }
        
        try:
            # Parse AST for detailed analysis
            tree = ast.parse(content)
            
            # Calculate metrics
            metrics = self._calculate_file_metrics(content, tree, file_path)
            analysis["metrics"] = asdict(metrics)
            
            # Detect quality issues
            analysis["issues"] = self._detect_quality_issues(content, tree, file_path)
            
            # Detect code smells
            analysis["code_smells"] = self._detect_code_smells(content, file_path)
            
            # Security analysis
            analysis["security_issues"] = self._detect_security_issues(content, file_path)
            
            # Refactoring opportunities
            analysis["refactoring_opportunities"] = self._identify_refactoring_opportunities(content, tree, file_path)
            
        except SyntaxError as e:
            analysis["issues"].append(CodeQualityIssue(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type="syntax_error",
                severity="critical",
                description=f"Syntax error: {e.msg}",
                suggestion="Fix syntax error to enable further analysis",
                code_snippet="",
                complexity_score=0
            ))
        
        return analysis
    
    def _calculate_file_metrics(self, content: str, tree: ast.AST, file_path: Path) -> FileQualityMetrics:
        """ファイルメトリクス計算"""
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(tree)
        
        # Calculate maintainability index (simplified version)
        maintainability = self._calculate_maintainability_index(content, complexity)
        
        # Calculate code duplication score
        duplication_score = self._calculate_duplication_score(content)
        
        # Get test coverage (mock value for now)
        test_coverage = 0.0  # Would integrate with coverage.py in real implementation
        
        # Count issues
        issues_count = len(self._detect_quality_issues(content, tree, file_path))
        
        # Determine quality grade
        quality_grade = self._determine_quality_grade(maintainability, complexity, issues_count)
        
        return FileQualityMetrics(
            file_path=str(file_path),
            lines_of_code=len(code_lines),
            cyclomatic_complexity=complexity,
            maintainability_index=maintainability,
            code_duplication_score=duplication_score,
            test_coverage=test_coverage,
            issues_count=issues_count,
            quality_grade=quality_grade
        )
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """循環的複雑度計算"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability_index(self, content: str, complexity: int) -> float:
        """保守性指数計算（簡易版）"""
        lines = content.split('\n')
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        if code_lines == 0:
            return 100.0
        
        # Simplified maintainability index
        # Real formula: MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        base_score = 100
        complexity_penalty = complexity * 2
        length_penalty = max(0, (code_lines - 50) * 0.1)
        
        return max(0, base_score - complexity_penalty - length_penalty)
    
    def _calculate_duplication_score(self, content: str) -> float:
        """コード重複スコア計算"""
        lines = content.split('\n')
        code_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if len(code_lines) == 0:
            return 0.0
        
        # Find duplicate lines
        line_counts = Counter(code_lines)
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        
        return (duplicate_lines / len(code_lines)) * 100
    
    def _determine_quality_grade(self, maintainability: float, complexity: int, issues_count: int) -> str:
        """品質グレード決定"""
        if maintainability >= 85 and complexity <= 10 and issues_count <= 2:
            return "A"
        elif maintainability >= 70 and complexity <= 20 and issues_count <= 5:
            return "B"
        elif maintainability >= 50 and complexity <= 50 and issues_count <= 10:
            return "C"
        elif maintainability >= 25:
            return "D"
        else:
            return "F"
    
    def _detect_quality_issues(self, content: str, tree: ast.AST, file_path: Path) -> List[CodeQualityIssue]:
        """品質問題検出"""
        issues = []
        lines = content.split('\n')
        
        # Analyze functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                issues.extend(self._analyze_function_quality(node, content, file_path, lines))
            elif isinstance(node, ast.ClassDef):
                issues.extend(self._analyze_class_quality(node, content, file_path, lines))
        
        # Check naming conventions
        issues.extend(self._check_naming_conventions(tree, file_path, lines))
        
        return issues
    
    def _analyze_function_quality(self, node: ast.FunctionDef, content: str, file_path: Path, lines: List[str]) -> List[CodeQualityIssue]:
        """関数品質分析"""
        issues = []
        
        # Function length check
        if hasattr(node, 'end_lineno'):
            function_length = node.end_lineno - node.lineno + 1
            if function_length > self.quality_rules["complexity_rules"]["max_function_length"]:
                issues.append(CodeQualityIssue(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_type="long_function",
                    severity="medium",
                    description=f"Function '{node.name}' is too long ({function_length} lines)",
                    suggestion="Consider breaking this function into smaller, more focused functions",
                    code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                    complexity_score=function_length
                ))
        
        # Parameter count check
        param_count = len(node.args.args)
        if param_count > self.quality_rules["complexity_rules"]["max_parameters"]:
            issues.append(CodeQualityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                issue_type="too_many_parameters",
                severity="medium",
                description=f"Function '{node.name}' has too many parameters ({param_count})",
                suggestion="Consider using a data class or dictionary to group related parameters",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                complexity_score=param_count
            ))
        
        # Complexity check
        complexity = self._calculate_function_complexity(node)
        if complexity > self.quality_rules["complexity_rules"]["max_cyclomatic_complexity"]:
            issues.append(CodeQualityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                issue_type="high_complexity",
                severity="high",
                description=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                suggestion="Simplify the function by extracting complex logic into separate methods",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                complexity_score=complexity
            ))
        
        return issues
    
    def _analyze_class_quality(self, node: ast.ClassDef, content: str, file_path: Path, lines: List[str]) -> List[CodeQualityIssue]:
        """クラス品質分析"""
        issues = []
        
        # Class length check
        if hasattr(node, 'end_lineno'):
            class_length = node.end_lineno - node.lineno + 1
            if class_length > self.quality_rules["complexity_rules"]["max_class_length"]:
                issues.append(CodeQualityIssue(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_type="large_class",
                    severity="medium",
                    description=f"Class '{node.name}' is too large ({class_length} lines)",
                    suggestion="Consider splitting this class into smaller, more focused classes",
                    code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                    complexity_score=class_length
                ))
        
        # Method count check
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        if method_count > 20:
            issues.append(CodeQualityIssue(
                file_path=str(file_path),
                line_number=node.lineno,
                issue_type="too_many_methods",
                severity="medium",
                description=f"Class '{node.name}' has too many methods ({method_count})",
                suggestion="Consider using composition or breaking the class into smaller classes",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                complexity_score=method_count
            ))
        
        return issues
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """関数の循環的複雑度計算"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CodeQualityIssue]:
        """命名規則チェック"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(self.quality_rules["naming_conventions"]["function_pattern"], node.name):
                    issues.append(CodeQualityIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="naming_convention_violation",
                        severity="low",
                        description=f"Function name '{node.name}' doesn't follow snake_case convention",
                        suggestion="Use snake_case for function names (e.g., my_function)",
                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                        complexity_score=1
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(self.quality_rules["naming_conventions"]["class_pattern"], node.name):
                    issues.append(CodeQualityIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="naming_convention_violation",
                        severity="low",
                        description=f"Class name '{node.name}' doesn't follow PascalCase convention",
                        suggestion="Use PascalCase for class names (e.g., MyClass)",
                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                        complexity_score=1
                    ))
        
        return issues
    
    def _detect_code_smells(self, content: str, file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """コードスメル検出"""
        code_smells = defaultdict(list)
        lines = content.split('\n')
        
        for smell_type, pattern in self.quality_rules["code_smells"].items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                code_smells[smell_type].append({
                    "file": str(file_path),
                    "line": line_num,
                    "match": match.group()[:100],  # Truncate long matches
                    "suggestion": self._get_code_smell_suggestion(smell_type)
                })
        
        return code_smells
    
    def _detect_security_issues(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """セキュリティ問題検出"""
        security_issues = []
        lines = content.split('\n')
        
        for issue_type, pattern in self.quality_rules["security_patterns"].items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                security_issues.append({
                    "type": issue_type,
                    "file": str(file_path),
                    "line": line_num,
                    "severity": "high" if issue_type in ["sql_injection_risk", "unsafe_eval"] else "medium",
                    "description": f"Potential {issue_type.replace('_', ' ')} detected",
                    "code": lines[line_num - 1].strip() if line_num <= len(lines) else "",
                    "suggestion": self._get_security_suggestion(issue_type)
                })
        
        return security_issues
    
    def _identify_refactoring_opportunities(self, content: str, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """リファクタリング機会の特定"""
        opportunities = []
        
        # Long functions that can be extracted
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno'):
                    function_length = node.end_lineno - node.lineno + 1
                    if function_length > 30:
                        opportunities.append({
                            "type": "extract_method",
                            "file": str(file_path),
                            "line": node.lineno,
                            "function": node.name,
                            "description": f"Long function ({function_length} lines) can be refactored",
                            "priority": "medium",
                            "estimated_effort": "2-4 hours"
                        })
        
        # Complex conditionals
        complex_conditions = re.finditer(r'if\s+.*and.*and.*:', content)
        for match in complex_conditions:
            line_num = content[:match.start()].count('\n') + 1
            opportunities.append({
                "type": "simplify_conditionals",
                "file": str(file_path),
                "line": line_num,
                "description": "Complex conditional can be simplified",
                "priority": "low",
                "estimated_effort": "1-2 hours"
            })
        
        return opportunities
    
    def _get_code_smell_suggestion(self, smell_type: str) -> str:
        """コードスメル改善提案"""
        suggestions = {
            "long_parameter_list": "Use a data class or configuration object to group parameters",
            "duplicate_code": "Extract common code into a shared function or method",
            "magic_numbers": "Define named constants for magic numbers",
            "god_class": "Split large class into smaller, focused classes",
            "feature_envy": "Move method to the class that owns the data it uses",
            "data_clumps": "Create a data class to group related parameters",
            "dead_code": "Remove unused code or implement the missing functionality"
        }
        return suggestions.get(smell_type, "Consider refactoring this code pattern")
    
    def _get_security_suggestion(self, issue_type: str) -> str:
        """セキュリティ改善提案"""
        suggestions = {
            "sql_injection_risk": "Use parameterized queries or ORM to prevent SQL injection",
            "hardcoded_secrets": "Use environment variables or secure key management",
            "unsafe_eval": "Avoid eval() - use safer alternatives like ast.literal_eval()",
            "shell_injection": "Use subprocess with shell=False and validate inputs",
            "unsafe_deserialization": "Use safe serialization formats like JSON"
        }
        return suggestions.get(issue_type, "Review this code for security implications")
    
    def _generate_extract_method_refactoring(self, opportunity: Dict[str, Any]) -> str:
        """メソッド抽出リファクタリング生成"""
        return f"""
# Refactoring suggestion for {opportunity['file']}:{opportunity['line']}
# Extract method refactoring for function: {opportunity.get('function', 'unknown')}

def extracted_method(self, parameters):
    '''
    Extracted method from long function.
    TODO: Implement the extracted logic here.
    '''
    pass

# Usage in original function:
# result = self.extracted_method(params)
"""
    
    def _generate_conditional_simplification(self, opportunity: Dict[str, Any]) -> str:
        """条件文簡略化生成"""
        return f"""
# Conditional simplification for {opportunity['file']}:{opportunity['line']}
# Before: if condition1 and condition2 and condition3:
# After:
def is_valid_condition(self, obj):
    '''Check if all conditions are met'''
    return (
        self.check_condition1(obj) and
        self.check_condition2(obj) and
        self.check_condition3(obj)
    )

# Usage: if self.is_valid_condition(obj):
"""
    
    def _generate_parameter_reduction(self, opportunity: Dict[str, Any]) -> str:
        """パラメータ削減生成"""
        return "# Consider using a configuration object to reduce parameter count"
    
    def _generate_duplication_elimination(self, opportunity: Dict[str, Any]) -> str:
        """重複除去生成"""
        return "# Extract common code into a shared utility function"
    
    def _generate_naming_improvements(self, opportunity: Dict[str, Any]) -> str:
        """命名改善生成"""
        return "# Use more descriptive and conventional names"
    
    def _generate_quality_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """品質サマリー生成"""
        file_metrics = analysis_results["file_metrics"]
        quality_issues = analysis_results["quality_issues"]
        
        if not file_metrics:
            return {"error": "No files analyzed"}
        
        # Calculate aggregate metrics
        total_files = len(file_metrics)
        total_loc = sum(metrics["lines_of_code"] for metrics in file_metrics.values())
        avg_complexity = sum(metrics["cyclomatic_complexity"] for metrics in file_metrics.values()) / total_files
        avg_maintainability = sum(metrics["maintainability_index"] for metrics in file_metrics.values()) / total_files
        
        # Grade distribution
        grades = [metrics["quality_grade"] for metrics in file_metrics.values()]
        grade_distribution = Counter(grades)
        
        # Issue severity breakdown
        severity_counts = Counter(issue.severity for issue in quality_issues)
        
        # Top problematic files
        problematic_files = sorted(
            [(path, metrics) for path, metrics in file_metrics.items()],
            key=lambda x: x[1]["issues_count"],
            reverse=True
        )[:10]
        
        return {
            "total_files_analyzed": total_files,
            "total_lines_of_code": total_loc,
            "average_cyclomatic_complexity": round(avg_complexity, 2),
            "average_maintainability_index": round(avg_maintainability, 2),
            "overall_quality_grade": self._calculate_overall_grade(grade_distribution),
            "grade_distribution": dict(grade_distribution),
            "issue_severity_breakdown": dict(severity_counts),
            "total_quality_issues": len(quality_issues),
            "code_smells_found": sum(len(smells) for smells in analysis_results["code_smells"].values()),
            "security_issues_found": len(analysis_results["security_issues"]),
            "refactoring_opportunities": len(analysis_results["refactoring_opportunities"]),
            "most_problematic_files": [
                {"file": path, "issues": metrics["issues_count"], "grade": metrics["quality_grade"]}
                for path, metrics in problematic_files
            ]
        }
    
    def _calculate_overall_grade(self, grade_distribution: Counter) -> str:
        """全体品質グレード計算"""
        total_files = sum(grade_distribution.values())
        if total_files == 0:
            return "N/A"
        
        # Weight grades: A=4, B=3, C=2, D=1, F=0
        grade_weights = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        weighted_score = sum(grade_weights.get(grade, 0) * count for grade, count in grade_distribution.items())
        avg_score = weighted_score / total_files
        
        if avg_score >= 3.5:
            return "A"
        elif avg_score >= 2.5:
            return "B"
        elif avg_score >= 1.5:
            return "C"
        elif avg_score >= 0.5:
            return "D"
        else:
            return "F"
    
    def generate_improvement_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """改善推奨事項生成"""
        print("📊 Generating code quality improvement recommendations...")
        
        recommendations = []
        quality_summary = analysis_results["quality_summary"]
        
        # Critical issues
        critical_issues = len([issue for issue in analysis_results["quality_issues"] if issue.severity == "critical"])
        if critical_issues > 0:
            recommendations.append({
                "category": "critical_fixes",
                "priority": "immediate",
                "issue_count": critical_issues,
                "description": f"{critical_issues} critical issues require immediate attention",
                "action_plan": [
                    "Fix all syntax errors and critical bugs",
                    "Address security vulnerabilities",
                    "Resolve import and dependency issues"
                ],
                "estimated_effort": f"{critical_issues * 2} hours",
                "impact": "System stability and security"
            })
        
        # High complexity functions
        high_complexity_issues = len([issue for issue in analysis_results["quality_issues"] if issue.issue_type == "high_complexity"])
        if high_complexity_issues > 0:
            recommendations.append({
                "category": "complexity_reduction",
                "priority": "high",
                "issue_count": high_complexity_issues,
                "description": f"{high_complexity_issues} functions with high cyclomatic complexity",
                "action_plan": [
                    "Break down complex functions into smaller methods",
                    "Extract nested logic into separate functions",
                    "Use early returns to reduce nesting"
                ],
                "estimated_effort": f"{high_complexity_issues * 4} hours",
                "impact": "Code maintainability and bug reduction"
            })
        
        # Code smells
        total_smells = sum(len(smells) for smells in analysis_results["code_smells"].values())
        if total_smells > 10:
            recommendations.append({
                "category": "code_smell_elimination",
                "priority": "medium",
                "issue_count": total_smells,
                "description": f"{total_smells} code smells detected across the codebase",
                "action_plan": [
                    "Eliminate duplicate code through extraction",
                    "Replace magic numbers with named constants",
                    "Refactor god classes into focused classes"
                ],
                "estimated_effort": f"{total_smells} hours",
                "impact": "Code readability and maintainability"
            })
        
        # Security issues
        security_issues = len(analysis_results["security_issues"])
        if security_issues > 0:
            recommendations.append({
                "category": "security_hardening",
                "priority": "high",
                "issue_count": security_issues,
                "description": f"{security_issues} potential security vulnerabilities found",
                "action_plan": [
                    "Replace hardcoded secrets with environment variables",
                    "Use parameterized queries to prevent SQL injection",
                    "Implement proper input validation and sanitization"
                ],
                "estimated_effort": f"{security_issues * 3} hours",
                "impact": "Application security and compliance"
            })
        
        # Overall quality improvement
        if quality_summary.get("overall_quality_grade", "A") in ["C", "D", "F"]:
            recommendations.append({
                "category": "overall_quality_improvement",
                "priority": "medium",
                "description": f"Overall code quality grade is {quality_summary.get('overall_quality_grade')}",
                "action_plan": [
                    "Implement code review processes",
                    "Set up automated code quality checks",
                    "Establish coding standards and guidelines",
                    "Provide team training on best practices"
                ],
                "estimated_effort": "2-4 weeks",
                "impact": "Long-term code quality and team productivity"
            })
        
        return recommendations
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的コード品質分析実行"""
        print("🚀 CC02 v33.0 Code Quality Optimization - Cycle 3")
        print("=" * 60)
        
        # Run analysis
        analysis_results = self.analyze_code_quality()
        
        # Generate recommendations
        recommendations = self.generate_improvement_recommendations(analysis_results)
        
        # Create comprehensive report
        comprehensive_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "analysis_results": analysis_results,
            "improvement_recommendations": recommendations,
            "quality_metrics": analysis_results["quality_summary"],
            "next_steps": [
                "Address critical and high-priority issues first",
                "Implement automated code quality checks in CI/CD",
                "Schedule regular code quality reviews",
                "Create coding standards documentation",
                "Set up code quality monitoring dashboard"
            ]
        }
        
        # Save report
        report_file = self.output_path / f"code_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Code quality analysis complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_analysis_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _print_analysis_summary(self, report: Dict[str, Any]):
        """分析サマリー出力"""
        print("\n" + "=" * 60)
        print("📊 Code Quality Analysis Summary")
        print("=" * 60)
        
        metrics = report["quality_metrics"]
        print(f"Files analyzed: {metrics.get('total_files_analyzed', 0)}")
        print(f"Total lines of code: {metrics.get('total_lines_of_code', 0)}")
        print(f"Overall quality grade: {metrics.get('overall_quality_grade', 'N/A')}")
        print(f"Average complexity: {metrics.get('average_cyclomatic_complexity', 0)}")
        print(f"Average maintainability: {metrics.get('average_maintainability_index', 0):.1f}")
        
        # Issues breakdown
        print(f"\n📋 Issues Found:")
        print(f"Quality issues: {metrics.get('total_quality_issues', 0)}")
        print(f"Code smells: {metrics.get('code_smells_found', 0)}")
        print(f"Security issues: {metrics.get('security_issues_found', 0)}")
        print(f"Refactoring opportunities: {metrics.get('refactoring_opportunities', 0)}")
        
        # Grade distribution
        grade_dist = metrics.get('grade_distribution', {})
        print(f"\n🎯 Quality Grade Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_dist.get(grade, 0)
            if count > 0:
                print(f"  Grade {grade}: {count} files")
        
        # Top problematic files
        problematic = metrics.get('most_problematic_files', [])[:5]
        if problematic:
            print(f"\n🔥 Most Problematic Files:")
            for i, file_info in enumerate(problematic, 1):
                file_name = Path(file_info['file']).name
                print(f"  {i}. {file_name}: {file_info['issues']} issues (grade {file_info['grade']})")
        
        # Recommendations
        recommendations = report["improvement_recommendations"]
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec['category']}: {rec['description']}")
        
        print(f"\n📈 Next Steps:")
        for step in report["next_steps"][:3]:
            print(f"  - {step}")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🔬 CC02 v33.0 Code Quality Optimizer")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    optimizer = CodeQualityOptimizer(project_root)
    report = optimizer.run_comprehensive_analysis()
    
    return report


if __name__ == "__main__":
    main()