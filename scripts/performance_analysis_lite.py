#!/usr/bin/env python3
"""
CC02 v33.0 パフォーマンス分析ツール - Light Version
Performance Analysis Tool without external dependencies
"""

import time
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter
import ast


class PerformanceAnalysisLite:
    """軽量版パフォーマンス分析ツール"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.output_path = project_root / "scripts" / "performance_analysis_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # Performance patterns to analyze
        self.performance_patterns = {
            "sync_operations": r"def\s+\w+\([^)]*\):\s*\n(?:.*\n)*?.*(?:requests\.|urllib|http)",
            "database_queries": r"session\.query\(|db\.query\(|\.filter\(|\.join\(",
            "file_operations": r"open\(|with open|\.read\(\)|\.write\(",
            "json_operations": r"json\.loads\(|json\.dumps\(|\.json\(\)",
            "loop_operations": r"for\s+\w+\s+in\s+.*:",
            "nested_loops": r"for\s+\w+\s+in\s+.*:\s*\n(?:\s+.*\n)*?\s+for\s+\w+\s+in",
            "recursive_functions": r"def\s+(\w+)\([^)]*\):(?:.*\n)*?.*\1\(",
            "large_data_processing": r"\.all\(\)|len\(.*\.query|\.count\(\)"
        }
        
        # Performance anti-patterns
        self.anti_patterns = {
            "synchronous_io": {
                "pattern": r"requests\.(get|post|put|delete)\((?!.*timeout)",
                "severity": "high",
                "description": "Synchronous HTTP requests without timeout"
            },
            "unbounded_queries": {
                "pattern": r"\.all\(\)\s*$",
                "severity": "high", 
                "description": "Database queries without pagination or limits"
            },
            "n_plus_1_queries": {
                "pattern": r"for\s+\w+\s+in\s+.*\.all\(\):.*\.query\(",
                "severity": "high",
                "description": "Potential N+1 query pattern"
            },
            "inefficient_filtering": {
                "pattern": r"\[.*for.*in.*if.*\]",
                "severity": "medium",
                "description": "List comprehension with filtering instead of database filtering"
            },
            "unnecessary_json_parsing": {
                "pattern": r"json\.loads\(.*json\.dumps\(",
                "severity": "low",
                "description": "Unnecessary JSON serialization/deserialization"
            },
            "string_concatenation_loops": {
                "pattern": r"for\s+.*:\s*\n\s*.*\s*\+=\s*.*str",
                "severity": "medium",
                "description": "String concatenation in loops (use join instead)"
            }
        }
        
        # Code complexity indicators
        self.complexity_indicators = {
            "high_cyclomatic": r"if\s+.*:|elif\s+.*:|for\s+.*:|while\s+.*:|try:|except.*:|with\s+.*:",
            "deep_nesting": r"^\s{12,}",  # 3+ levels of indentation
            "long_functions": r"def\s+\w+\([^)]*\):",
            "many_parameters": r"def\s+\w+\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*\):"  # 5+ parameters
        }
    
    def analyze_codebase_performance(self) -> Dict[str, Any]:
        """コードベース全体のパフォーマンス分析"""
        print("🔍 Analyzing codebase performance patterns...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "file_analysis": {},
            "performance_hotspots": [],
            "anti_pattern_summary": defaultdict(int),
            "complexity_analysis": {},
            "optimization_opportunities": []
        }
        
        # Analyze Python files
        python_files = list(self.backend_path.glob("**/*.py"))
        
        for file_path in python_files:
            if file_path.name.startswith("__") or "migrations" in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_analysis = self._analyze_file_performance(content, file_path)
                
                if file_analysis["issues"]:
                    analysis["file_analysis"][str(file_path)] = file_analysis
                
                # Aggregate anti-patterns
                for issue in file_analysis["issues"]:
                    analysis["anti_pattern_summary"][issue["type"]] += 1
                
                # Add to hotspots if significant issues found
                if len(file_analysis["issues"]) >= 3:
                    analysis["performance_hotspots"].append({
                        "file": str(file_path),
                        "issue_count": len(file_analysis["issues"]),
                        "severity_score": sum(3 if i["severity"] == "high" else 2 if i["severity"] == "medium" else 1 
                                            for i in file_analysis["issues"])
                    })
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
        
        # Generate complexity analysis
        analysis["complexity_analysis"] = self._analyze_code_complexity(python_files)
        
        # Generate optimization opportunities
        analysis["optimization_opportunities"] = self._generate_optimization_opportunities(analysis)
        
        return analysis
    
    def _analyze_file_performance(self, content: str, file_path: Path) -> Dict[str, Any]:
        """個別ファイルのパフォーマンス分析"""
        analysis = {
            "file": str(file_path),
            "lines_of_code": len(content.split('\n')),
            "issues": [],
            "performance_patterns": {},
            "complexity_metrics": {}
        }
        
        lines = content.split('\n')
        
        # Check for anti-patterns
        for pattern_name, pattern_info in self.anti_patterns.items():
            matches = list(re.finditer(pattern_info["pattern"], content, re.MULTILINE))
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                analysis["issues"].append({
                    "type": pattern_name,
                    "severity": pattern_info["severity"],
                    "line": line_num,
                    "description": pattern_info["description"],
                    "code": lines[line_num - 1].strip() if line_num <= len(lines) else "",
                    "suggestion": self._get_optimization_suggestion(pattern_name)
                })
        
        # Analyze performance patterns
        for pattern_name, pattern_regex in self.performance_patterns.items():
            matches = len(re.findall(pattern_regex, content, re.MULTILINE))
            if matches > 0:
                analysis["performance_patterns"][pattern_name] = matches
        
        # Calculate complexity metrics
        analysis["complexity_metrics"] = self._calculate_complexity_metrics(content)
        
        return analysis
    
    def _calculate_complexity_metrics(self, content: str) -> Dict[str, Any]:
        """コード複雑度メトリクスを計算"""
        lines = content.split('\n')
        
        metrics = {
            "lines_of_code": len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            "total_lines": len(lines),
            "function_count": len(re.findall(r'def\s+\w+\(', content)),
            "class_count": len(re.findall(r'class\s+\w+', content)),
            "cyclomatic_complexity": len(re.findall(self.complexity_indicators["high_cyclomatic"], content)),
            "max_nesting_level": self._calculate_max_nesting(content),
            "average_function_length": 0
        }
        
        # Calculate average function length
        function_lengths = self._calculate_function_lengths(content)
        if function_lengths:
            metrics["average_function_length"] = sum(function_lengths) / len(function_lengths)
        
        return metrics
    
    def _calculate_max_nesting(self, content: str) -> int:
        """最大ネスト深度を計算"""
        lines = content.split('\n')
        max_indent = 0
        
        for line in lines:
            if line.strip():
                indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indentation
                max_indent = max(max_indent, indent_level)
        
        return max_indent
    
    def _calculate_function_lengths(self, content: str) -> List[int]:
        """関数の長さを計算"""
        try:
            tree = ast.parse(content)
            function_lengths = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        length = node.end_lineno - node.lineno + 1
                        function_lengths.append(length)
            
            return function_lengths
        except:
            return []
    
    def _analyze_code_complexity(self, python_files: List[Path]) -> Dict[str, Any]:
        """コード複雑度の全体分析"""
        complexity_summary = {
            "total_files": len(python_files),
            "high_complexity_files": [],
            "average_metrics": defaultdict(list),
            "complexity_distribution": defaultdict(int)
        }
        
        for file_path in python_files:
            if file_path.name.startswith("__"):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metrics = self._calculate_complexity_metrics(content)
                
                # Collect metrics for averaging
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        complexity_summary["average_metrics"][key].append(value)
                
                # Identify high complexity files
                complexity_score = (
                    metrics["cyclomatic_complexity"] +
                    metrics["max_nesting_level"] * 2 +
                    (metrics["average_function_length"] / 10 if metrics["average_function_length"] else 0)
                )
                
                if complexity_score > 20:  # Threshold for high complexity
                    complexity_summary["high_complexity_files"].append({
                        "file": str(file_path),
                        "complexity_score": complexity_score,
                        "metrics": metrics
                    })
                
                # Complexity distribution
                if complexity_score > 30:
                    complexity_summary["complexity_distribution"]["very_high"] += 1
                elif complexity_score > 20:
                    complexity_summary["complexity_distribution"]["high"] += 1
                elif complexity_score > 10:
                    complexity_summary["complexity_distribution"]["medium"] += 1
                else:
                    complexity_summary["complexity_distribution"]["low"] += 1
                
            except Exception as e:
                print(f"Warning: Could not analyze complexity for {file_path}: {e}")
        
        # Calculate averages
        final_averages = {}
        for key, values in complexity_summary["average_metrics"].items():
            if values:
                final_averages[key] = sum(values) / len(values)
        
        complexity_summary["average_metrics"] = final_averages
        
        return complexity_summary
    
    def _get_optimization_suggestion(self, pattern_name: str) -> str:
        """最適化提案を取得"""
        suggestions = {
            "synchronous_io": "Use async/await with aiohttp or add timeout parameters",
            "unbounded_queries": "Add .limit() or implement pagination",
            "n_plus_1_queries": "Use .joinedload() or .selectinload() for eager loading",
            "inefficient_filtering": "Move filtering to database query with .filter()",
            "unnecessary_json_parsing": "Avoid redundant JSON operations",
            "string_concatenation_loops": "Use ''.join() for string concatenation in loops"
        }
        return suggestions.get(pattern_name, "Optimize this pattern for better performance")
    
    def _generate_optimization_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """最適化機会を生成"""
        opportunities = []
        
        # High priority issues
        high_severity_count = sum(1 for file_data in analysis["file_analysis"].values() 
                                 for issue in file_data["issues"] if issue["severity"] == "high")
        
        if high_severity_count > 0:
            opportunities.append({
                "category": "critical_performance_issues",
                "priority": "high",
                "issue_count": high_severity_count,
                "description": f"{high_severity_count} high-severity performance issues detected",
                "recommendation": "Address synchronous I/O, unbounded queries, and N+1 patterns immediately",
                "estimated_impact": "30-50% performance improvement"
            })
        
        # Code complexity issues
        high_complexity_files = analysis["complexity_analysis"].get("high_complexity_files", [])
        if len(high_complexity_files) > 0:
            opportunities.append({
                "category": "code_complexity_reduction",
                "priority": "medium",
                "issue_count": len(high_complexity_files),
                "description": f"{len(high_complexity_files)} files with high complexity detected",
                "recommendation": "Refactor complex functions, reduce nesting, and break down large functions",
                "estimated_impact": "Improved maintainability and performance"
            })
        
        # Pattern-specific opportunities
        anti_pattern_summary = analysis["anti_pattern_summary"]
        
        if anti_pattern_summary["unbounded_queries"] > 5:
            opportunities.append({
                "category": "database_query_optimization",
                "priority": "high",
                "issue_count": anti_pattern_summary["unbounded_queries"],
                "description": "Multiple unbounded database queries detected",
                "recommendation": "Implement pagination and query limits across the application",
                "estimated_impact": "Significant reduction in database load and memory usage"
            })
        
        if anti_pattern_summary["n_plus_1_queries"] > 0:
            opportunities.append({
                "category": "eager_loading_implementation",
                "priority": "high",
                "issue_count": anti_pattern_summary["n_plus_1_queries"],
                "description": "N+1 query patterns detected",
                "recommendation": "Implement eager loading with SQLAlchemy joinedload/selectinload",
                "estimated_impact": "Dramatic reduction in database round trips"
            })
        
        return opportunities
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """包括的パフォーマンスレポートを生成"""
        print("🚀 CC02 v33.0 Performance Analysis (Lite)")
        print("=" * 60)
        
        analysis = self.analyze_codebase_performance()
        
        # Generate executive summary
        total_issues = sum(len(file_data["issues"]) for file_data in analysis["file_analysis"].values())
        high_severity_issues = sum(1 for file_data in analysis["file_analysis"].values() 
                                  for issue in file_data["issues"] if issue["severity"] == "high")
        
        executive_summary = {
            "total_files_analyzed": len(analysis["file_analysis"]),
            "total_performance_issues": total_issues,
            "high_severity_issues": high_severity_issues,
            "performance_hotspots": len(analysis["performance_hotspots"]),
            "optimization_opportunities": len(analysis["optimization_opportunities"]),
            "estimated_improvement_potential": "20-40% performance gain with recommended optimizations"
        }
        
        # Create comprehensive report
        comprehensive_report = {
            "report_timestamp": datetime.now().isoformat(),
            "executive_summary": executive_summary,
            "detailed_analysis": analysis,
            "action_plan": self._create_action_plan(analysis),
            "performance_monitoring_recommendations": self._get_monitoring_recommendations()
        }
        
        # Save report
        report_file = self.output_path / f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Analysis complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_performance_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _create_action_plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アクションプランを作成"""
        action_plan = []
        
        # Phase 1: Critical issues
        high_severity_count = sum(1 for file_data in analysis["file_analysis"].values() 
                                 for issue in file_data["issues"] if issue["severity"] == "high")
        
        if high_severity_count > 0:
            action_plan.append({
                "phase": 1,
                "priority": "critical",
                "timeline": "1-2 weeks",
                "tasks": [
                    "Fix all synchronous I/O operations",
                    "Add limits to unbounded database queries",
                    "Implement eager loading for N+1 queries",
                    "Add proper timeout handling"
                ],
                "success_criteria": "Zero high-severity performance issues"
            })
        
        # Phase 2: Medium priority optimization
        action_plan.append({
            "phase": 2,
            "priority": "optimization",
            "timeline": "2-4 weeks",
            "tasks": [
                "Refactor high complexity functions",
                "Implement database connection pooling",
                "Add caching for frequently accessed data",
                "Optimize string operations and loops"
            ],
            "success_criteria": "20% improvement in average response times"
        })
        
        # Phase 3: Long-term improvements
        action_plan.append({
            "phase": 3,
            "priority": "enhancement",
            "timeline": "1-2 months",
            "tasks": [
                "Implement comprehensive performance monitoring",
                "Set up automated performance testing",
                "Create performance budgets for new features",
                "Establish performance review processes"
            ],
            "success_criteria": "Continuous performance monitoring and optimization"
        })
        
        return action_plan
    
    def _get_monitoring_recommendations(self) -> List[Dict[str, Any]]:
        """モニタリング推奨事項を取得"""
        return [
            {
                "category": "application_monitoring",
                "tools": ["New Relic", "Datadog", "Prometheus + Grafana"],
                "metrics": ["Response times", "Throughput", "Error rates", "Memory usage"],
                "implementation": "Add APM integration to FastAPI application"
            },
            {
                "category": "database_monitoring",
                "tools": ["pg_stat_statements", "pgAdmin", "Custom query logging"],
                "metrics": ["Query execution time", "Query frequency", "Lock waits", "Index usage"],
                "implementation": "Enable PostgreSQL query statistics and create monitoring dashboard"
            },
            {
                "category": "infrastructure_monitoring",
                "tools": ["System metrics", "Docker stats", "Resource utilization"],
                "metrics": ["CPU usage", "Memory consumption", "Disk I/O", "Network latency"],
                "implementation": "Set up system-level monitoring with alerting thresholds"
            }
        ]
    
    def _print_performance_summary(self, report: Dict[str, Any]):
        """パフォーマンス分析サマリーを出力"""
        print("\n" + "=" * 60)
        print("📊 Performance Analysis Summary")
        print("=" * 60)
        
        summary = report["executive_summary"]
        print(f"Files analyzed: {summary['total_files_analyzed']}")
        print(f"Performance issues: {summary['total_performance_issues']}")
        print(f"High severity issues: {summary['high_severity_issues']}")
        print(f"Performance hotspots: {summary['performance_hotspots']}")
        print(f"Optimization opportunities: {summary['optimization_opportunities']}")
        
        # Top issues
        analysis = report["detailed_analysis"]
        print("\n🔥 Performance Hotspots:")
        hotspots = sorted(analysis["performance_hotspots"], key=lambda x: x["severity_score"], reverse=True)
        for i, hotspot in enumerate(hotspots[:5], 1):
            file_name = Path(hotspot["file"]).name
            print(f"  {i}. {file_name}: {hotspot['issue_count']} issues (score: {hotspot['severity_score']})")
        
        # Anti-pattern summary
        print("\n⚠️ Most Common Anti-patterns:")
        sorted_patterns = sorted(analysis["anti_pattern_summary"].items(), key=lambda x: x[1], reverse=True)
        for i, (pattern, count) in enumerate(sorted_patterns[:5], 1):
            print(f"  {i}. {pattern}: {count} occurrences")
        
        # Action plan
        print("\n📋 Action Plan:")
        for phase in report["action_plan"]:
            print(f"  Phase {phase['phase']} ({phase['timeline']}): {phase['priority']}")
            for task in phase["tasks"][:2]:  # Show first 2 tasks
                print(f"    - {task}")
        
        print(f"\n🎯 Estimated Impact: {summary['estimated_improvement_potential']}")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    analyzer = PerformanceAnalysisLite(project_root)
    report = analyzer.generate_performance_report()
    
    return report


if __name__ == "__main__":
    main()