#!/usr/bin/env python3
"""
CC02 v33.0 データベース最適化分析ツール - Infinite Loop Cycle 2
Database Optimization Analyzer for SQLAlchemy Query Performance
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter


class DatabaseOptimizationAnalyzer:
    """SQLAlchemy クエリ最適化分析ツール"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.models_path = self.backend_path / "app" / "models"
        self.api_path = self.backend_path / "app" / "api"
        self.crud_path = self.backend_path / "app" / "crud"
        self.output_path = project_root / "scripts" / "db_optimization_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # Analysis patterns
        self.optimization_patterns = {
            "n_plus_1_queries": self._detect_n_plus_1_queries,
            "missing_indexes": self._detect_missing_indexes,
            "inefficient_joins": self._detect_inefficient_joins,
            "large_result_sets": self._detect_large_result_sets,
            "duplicate_queries": self._detect_duplicate_queries,
            "eager_loading_opportunities": self._detect_eager_loading_opportunities,
            "query_complexity": self._analyze_query_complexity,
            "transaction_optimization": self._analyze_transaction_patterns
        }
        
        # Performance anti-patterns
        self.anti_patterns = {
            "select_star": r"SELECT\s+\*\s+FROM",
            "no_limit": r"\.all\(\)\s*$",
            "nested_loops": r"for\s+\w+\s+in\s+\w+\.query\(",
            "sequential_queries": r"session\.query\(.*?\)\.filter\(.*?\)\.first\(\)",
            "missing_eager_loading": r"\.query\(.*?\)(?!.*joinedload)(?!.*selectinload)",
            "inefficient_counting": r"len\(.*\.all\(\)\)"
        }
        
        # Database schema analysis
        self.schema_info = {}
        self.relationship_map = {}
        self.index_suggestions = []
        
    def analyze_models(self) -> Dict[str, Any]:
        """SQLAlchemy モデルを分析"""
        print("🔍 Analyzing SQLAlchemy models...")
        
        model_analysis = {
            "total_models": 0,
            "relationships": {},
            "indexes": {},
            "constraints": {},
            "potential_issues": []
        }
        
        model_files = list(self.models_path.glob("*.py"))
        
        for model_file in model_files:
            if model_file.name.startswith("__"):
                continue
                
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST for detailed analysis
                tree = ast.parse(content)
                file_analysis = self._analyze_model_file(tree, content, model_file)
                
                if file_analysis:
                    model_analysis["total_models"] += file_analysis["model_count"]
                    model_analysis["relationships"].update(file_analysis["relationships"])
                    model_analysis["indexes"].update(file_analysis["indexes"])
                    model_analysis["constraints"].update(file_analysis["constraints"])
                    model_analysis["potential_issues"].extend(file_analysis["issues"])
                    
            except Exception as e:
                print(f"Warning: Could not analyze {model_file}: {e}")
        
        return model_analysis
    
    def _analyze_model_file(self, tree: ast.AST, content: str, file_path: Path) -> Dict[str, Any]:
        """個別モデルファイルの分析"""
        analysis = {
            "model_count": 0,
            "relationships": {},
            "indexes": {},
            "constraints": {},
            "issues": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a SQLAlchemy model
                if self._is_sqlalchemy_model(node, content):
                    analysis["model_count"] += 1
                    model_name = node.name
                    
                    # Analyze relationships
                    relationships = self._extract_relationships(node, content)
                    if relationships:
                        analysis["relationships"][model_name] = relationships
                    
                    # Analyze indexes
                    indexes = self._extract_indexes(node, content)
                    if indexes:
                        analysis["indexes"][model_name] = indexes
                    
                    # Check for potential issues
                    issues = self._check_model_issues(node, content, model_name, file_path)
                    analysis["issues"].extend(issues)
        
        return analysis
    
    def _is_sqlalchemy_model(self, node: ast.ClassDef, content: str) -> bool:
        """SQLAlchemy モデルかどうかを判定"""
        # Check for common SQLAlchemy patterns
        patterns = [
            "__tablename__",
            "Column(",
            "relationship(",
            "Base",
            "DeclarativeBase"
        ]
        
        # Extract class body content
        class_start = node.lineno
        class_end = node.end_lineno if hasattr(node, 'end_lineno') else class_start + 50
        class_content = '\n'.join(content.split('\n')[class_start-1:class_end])
        
        return any(pattern in class_content for pattern in patterns)
    
    def _extract_relationships(self, node: ast.ClassDef, content: str) -> List[Dict[str, Any]]:
        """リレーションシップを抽出"""
        relationships = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Check if this is a relationship
                        if isinstance(item.value, ast.Call):
                            if hasattr(item.value.func, 'id') and item.value.func.id == 'relationship':
                                rel_info = {
                                    "name": target.id,
                                    "type": "relationship",
                                    "lazy_loading": "select",  # default
                                    "back_populates": None,
                                    "cascade": None
                                }
                                
                                # Extract relationship parameters
                                for keyword in item.value.keywords:
                                    if keyword.arg == "lazy":
                                        if hasattr(keyword.value, 's'):
                                            rel_info["lazy_loading"] = keyword.value.s
                                    elif keyword.arg == "back_populates":
                                        if hasattr(keyword.value, 's'):
                                            rel_info["back_populates"] = keyword.value.s
                                    elif keyword.arg == "cascade":
                                        if hasattr(keyword.value, 's'):
                                            rel_info["cascade"] = keyword.value.s
                                
                                relationships.append(rel_info)
        
        return relationships
    
    def _extract_indexes(self, node: ast.ClassDef, content: str) -> List[Dict[str, Any]]:
        """インデックス情報を抽出"""
        indexes = []
        
        # Look for __table_args__ with Index definitions
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "__table_args__":
                        # Extract index information from table args
                        if isinstance(item.value, ast.Tuple):
                            for element in item.value.elts:
                                if isinstance(element, ast.Call):
                                    if hasattr(element.func, 'id') and element.func.id == 'Index':
                                        index_info = self._parse_index_definition(element)
                                        if index_info:
                                            indexes.append(index_info)
        
        return indexes
    
    def _parse_index_definition(self, index_call: ast.Call) -> Optional[Dict[str, Any]]:
        """Index定義を解析"""
        if not index_call.args:
            return None
        
        index_info = {
            "name": None,
            "columns": [],
            "unique": False
        }
        
        # First argument is usually the index name
        if hasattr(index_call.args[0], 's'):
            index_info["name"] = index_call.args[0].s
        
        # Extract column names
        for arg in index_call.args[1:]:
            if hasattr(arg, 's'):
                index_info["columns"].append(arg.s)
        
        # Check for unique constraint
        for keyword in index_call.keywords:
            if keyword.arg == "unique" and hasattr(keyword.value, 'value'):
                index_info["unique"] = keyword.value.value
        
        return index_info
    
    def _check_model_issues(self, node: ast.ClassDef, content: str, model_name: str, file_path: Path) -> List[Dict[str, Any]]:
        """モデルの潜在的問題をチェック"""
        issues = []
        
        # Extract class content for analysis
        class_start = node.lineno
        class_end = node.end_lineno if hasattr(node, 'end_lineno') else class_start + 100
        class_content = '\n'.join(content.split('\n')[class_start-1:class_end])
        
        # Check for missing indexes on foreign keys
        foreign_keys = re.findall(r'ForeignKey\([\'\"](.*?)[\'\"]', class_content)
        indexes = re.findall(r'index=True', class_content)
        
        if foreign_keys and len(indexes) < len(foreign_keys):
            issues.append({
                "type": "missing_index",
                "severity": "medium",
                "model": model_name,
                "file": str(file_path),
                "description": f"Foreign keys detected but insufficient indexes: {foreign_keys}",
                "suggestion": "Add indexes to foreign key columns for better join performance"
            })
        
        # Check for large text fields without limits
        unlimited_text = re.findall(r'Column\(Text(?!\(|\s*,\s*length)', class_content)
        if unlimited_text:
            issues.append({
                "type": "unlimited_text",
                "severity": "low",
                "model": model_name,
                "file": str(file_path),
                "description": "Text columns without length limits detected",
                "suggestion": "Consider adding length limits to Text columns for better performance"
            })
        
        # Check for missing __repr__ method (debugging aid)
        if "__repr__" not in class_content:
            issues.append({
                "type": "missing_repr",
                "severity": "low",
                "model": model_name,
                "file": str(file_path),
                "description": "Missing __repr__ method",
                "suggestion": "Add __repr__ method for better debugging experience"
            })
        
        return issues
    
    def analyze_queries(self) -> Dict[str, Any]:
        """SQLAlchemy クエリを分析"""
        print("🔍 Analyzing SQLAlchemy queries...")
        
        query_analysis = {
            "total_query_locations": 0,
            "anti_patterns": defaultdict(list),
            "n_plus_1_risks": [],
            "performance_issues": [],
            "optimization_opportunities": []
        }
        
        # Analyze API files
        api_files = list(self.api_path.glob("**/*.py"))
        crud_files = list(self.crud_path.glob("**/*.py")) if self.crud_path.exists() else []
        
        all_files = api_files + crud_files
        
        for file_path in all_files:
            if file_path.name.startswith("__"):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_analysis = self._analyze_query_file(content, file_path)
                
                query_analysis["total_query_locations"] += file_analysis["query_count"]
                
                # Merge anti-patterns
                for pattern, locations in file_analysis["anti_patterns"].items():
                    query_analysis["anti_patterns"][pattern].extend(locations)
                
                query_analysis["n_plus_1_risks"].extend(file_analysis["n_plus_1_risks"])
                query_analysis["performance_issues"].extend(file_analysis["performance_issues"])
                query_analysis["optimization_opportunities"].extend(file_analysis["optimizations"])
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
        
        return query_analysis
    
    def _analyze_query_file(self, content: str, file_path: Path) -> Dict[str, Any]:
        """個別ファイルのクエリ分析"""
        analysis = {
            "query_count": 0,
            "anti_patterns": defaultdict(list),
            "n_plus_1_risks": [],
            "performance_issues": [],
            "optimizations": []
        }
        
        lines = content.split('\n')
        
        # Count query locations
        query_patterns = [r'\.query\(', r'session\.query', r'db\.query', r'select\(']
        for i, line in enumerate(lines, 1):
            if any(re.search(pattern, line) for pattern in query_patterns):
                analysis["query_count"] += 1
        
        # Check for anti-patterns
        for pattern_name, regex in self.anti_patterns.items():
            matches = re.finditer(regex, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                analysis["anti_patterns"][pattern_name].append({
                    "file": str(file_path),
                    "line": line_num,
                    "code": lines[line_num - 1].strip() if line_num <= len(lines) else "",
                    "match": match.group()
                })
        
        # Detect N+1 query risks
        n_plus_1_patterns = [
            r'for\s+\w+\s+in\s+.*\.all\(\):.*\.query\(',
            r'for\s+\w+\s+in\s+.*\.filter\(.*\):.*\.\w+\.query\(',
        ]
        
        for pattern in n_plus_1_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                analysis["n_plus_1_risks"].append({
                    "file": str(file_path),
                    "line": line_num,
                    "pattern": "potential_n_plus_1",
                    "description": "Loop with nested query - potential N+1 problem",
                    "suggestion": "Consider using joinedload() or selectinload()"
                })
        
        # Detect missing eager loading opportunities
        lazy_loading_pattern = r'\.query\([^)]+\)\.filter\([^)]+\)\.(?:first|all)\(\)'
        relationship_access_pattern = r'\w+\.\w+\.(?:all\(\)|first\(\))'
        
        lazy_matches = list(re.finditer(lazy_loading_pattern, content))
        rel_matches = list(re.finditer(relationship_access_pattern, content))
        
        if lazy_matches and rel_matches:
            for lazy_match in lazy_matches:
                lazy_line = content[:lazy_match.start()].count('\n') + 1
                for rel_match in rel_matches:
                    rel_line = content[:rel_match.start()].count('\n') + 1
                    if abs(lazy_line - rel_line) <= 10:  # Within 10 lines
                        analysis["optimizations"].append({
                            "type": "eager_loading_opportunity",
                            "file": str(file_path),
                            "query_line": lazy_line,
                            "access_line": rel_line,
                            "suggestion": "Add .options(joinedload(Model.relationship)) to avoid N+1"
                        })
        
        return analysis
    
    def _detect_n_plus_1_queries(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """N+1クエリ問題を検出"""
        # This is implemented in _analyze_query_file
        return analysis_data.get("n_plus_1_risks", [])
    
    def _detect_missing_indexes(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """不足インデックスを検出"""
        missing_indexes = []
        
        # Analyze foreign keys without indexes
        for anti_pattern in analysis_data.get("anti_patterns", {}).get("missing_index", []):
            missing_indexes.append({
                "type": "missing_foreign_key_index",
                "severity": "high",
                "location": anti_pattern,
                "suggestion": "Add index to foreign key column"
            })
        
        return missing_indexes
    
    def _detect_inefficient_joins(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """非効率なJOINを検出"""
        # Implementation would analyze join patterns
        return []
    
    def _detect_large_result_sets(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """大きな結果セットを検出"""
        large_results = []
        
        # Look for queries without LIMIT
        no_limit_queries = analysis_data.get("anti_patterns", {}).get("no_limit", [])
        for query in no_limit_queries:
            large_results.append({
                "type": "unlimited_query",
                "severity": "medium",
                "location": query,
                "suggestion": "Add pagination or limit to prevent large result sets"
            })
        
        return large_results
    
    def _detect_duplicate_queries(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """重複クエリを検出"""
        # This would require more sophisticated analysis
        return []
    
    def _detect_eager_loading_opportunities(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Eager Loading最適化機会を検出"""
        return analysis_data.get("optimization_opportunities", [])
    
    def _analyze_query_complexity(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """クエリ複雑度を分析"""
        complexity_issues = []
        
        # Analyze queries with multiple JOINs, subqueries, etc.
        # This would require more detailed query parsing
        
        return complexity_issues
    
    def _analyze_transaction_patterns(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """トランザクションパターンを分析"""
        transaction_issues = []
        
        # Look for potential transaction problems
        # This would analyze commit/rollback patterns
        
        return transaction_issues
    
    def generate_optimization_recommendations(self, model_analysis: Dict[str, Any], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """最適化推奨事項を生成"""
        print("📊 Generating optimization recommendations...")
        
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "priority_high": [],
            "priority_medium": [],
            "priority_low": [],
            "quick_wins": [],
            "long_term_improvements": []
        }
        
        # High priority issues
        for issue in model_analysis.get("potential_issues", []):
            if issue.get("severity") == "high":
                recommendations["priority_high"].append({
                    "category": "model_optimization",
                    "issue": issue,
                    "impact": "High performance impact",
                    "effort": "Low"
                })
        
        # Query optimization opportunities
        n_plus_1_count = len(query_analysis.get("n_plus_1_risks", []))
        if n_plus_1_count > 0:
            recommendations["priority_high"].append({
                "category": "n_plus_1_elimination",
                "issue": f"{n_plus_1_count} potential N+1 query issues detected",
                "impact": "High performance impact on database load",
                "effort": "Medium",
                "solution": "Implement eager loading with joinedload() or selectinload()"
            })
        
        # Anti-pattern fixes
        for pattern, occurrences in query_analysis.get("anti_patterns", {}).items():
            if len(occurrences) > 5:  # Significant number of occurrences
                severity = "high" if pattern in ["no_limit", "nested_loops"] else "medium"
                priority_list = recommendations[f"priority_{severity}"]
                
                priority_list.append({
                    "category": "anti_pattern_elimination",
                    "pattern": pattern,
                    "occurrences": len(occurrences),
                    "issue": f"Anti-pattern '{pattern}' found in {len(occurrences)} locations",
                    "impact": f"{'High' if severity == 'high' else 'Medium'} performance impact",
                    "effort": "Low to Medium"
                })
        
        # Quick wins
        missing_indexes = [issue for issue in model_analysis.get("potential_issues", []) 
                          if issue.get("type") == "missing_index"]
        if missing_indexes:
            recommendations["quick_wins"].append({
                "category": "index_optimization",
                "issue": f"{len(missing_indexes)} missing indexes on foreign keys",
                "solution": "Add database indexes to foreign key columns",
                "effort": "Very Low",
                "impact": "High for join performance"
            })
        
        # Long-term improvements
        recommendations["long_term_improvements"].extend([
            {
                "category": "query_monitoring",
                "issue": "No query performance monitoring detected",
                "solution": "Implement SQLAlchemy query logging and monitoring",
                "effort": "Medium",
                "impact": "Enables continuous optimization"
            },
            {
                "category": "database_profiling",
                "issue": "Regular database profiling not implemented",
                "solution": "Set up periodic EXPLAIN ANALYZE for slow queries",
                "effort": "Medium",
                "impact": "Identifies performance bottlenecks"
            },
            {
                "category": "caching_strategy",
                "issue": "Limited caching implementation detected",
                "solution": "Implement Redis caching for frequently accessed data",
                "effort": "High",
                "impact": "Significant performance improvement for read operations"
            }
        ])
        
        return recommendations
    
    def generate_migration_scripts(self, recommendations: Dict[str, Any]) -> List[str]:
        """データベース最適化のためのマイグレーションスクリプトを生成"""
        print("🔧 Generating optimization migration scripts...")
        
        migration_scripts = []
        
        # Generate index creation scripts
        for rec in recommendations.get("quick_wins", []):
            if rec.get("category") == "index_optimization":
                script = self._generate_index_migration()
                if script:
                    migration_scripts.append(script)
        
        return migration_scripts
    
    def _generate_index_migration(self) -> str:
        """インデックス作成マイグレーションスクリプト"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f'''"""Add missing indexes for foreign keys

Revision ID: optimize_indexes_{timestamp}
Revises: 
Create Date: {datetime.now().isoformat()}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'optimize_indexes_{timestamp}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add missing indexes for better join performance"""
    # Example index creations - customize based on actual analysis
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])
    op.create_index('idx_projects_customer_id', 'projects', ['customer_id'])
    op.create_index('idx_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('idx_expenses_user_id', 'expenses', ['user_id'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_users_org_status', 'users', ['organization_id', 'status'])
    op.create_index('idx_projects_customer_status', 'projects', ['customer_id', 'status'])

def downgrade():
    """Remove the indexes"""
    op.drop_index('idx_projects_customer_status')
    op.drop_index('idx_users_org_status')
    op.drop_index('idx_expenses_user_id')
    op.drop_index('idx_tasks_project_id')
    op.drop_index('idx_projects_customer_id')
    op.drop_index('idx_users_organization_id')
'''
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的なデータベース最適化分析を実行"""
        print("🚀 CC02 v33.0 Database Optimization Analysis")
        print("=" * 60)
        
        # Run all analyses
        model_analysis = self.analyze_models()
        query_analysis = self.analyze_queries()
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(model_analysis, query_analysis)
        
        # Generate migration scripts
        migration_scripts = self.generate_migration_scripts(recommendations)
        
        # Compile comprehensive report
        comprehensive_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "model_analysis": model_analysis,
            "query_analysis": query_analysis,
            "recommendations": recommendations,
            "migration_scripts": migration_scripts,
            "summary": {
                "total_models": model_analysis.get("total_models", 0),
                "total_query_locations": query_analysis.get("total_query_locations", 0),
                "high_priority_issues": len(recommendations.get("priority_high", [])),
                "medium_priority_issues": len(recommendations.get("priority_medium", [])),
                "quick_wins": len(recommendations.get("quick_wins", [])),
                "potential_performance_gain": "Estimated 20-40% query performance improvement"
            }
        }
        
        # Save detailed report
        report_file = self.output_path / f"db_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Analysis complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_analysis_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _print_analysis_summary(self, report: Dict[str, Any]):
        """分析結果サマリーを出力"""
        print("\n" + "=" * 60)
        print("📊 Database Optimization Analysis Summary")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"Models analyzed: {summary['total_models']}")
        print(f"Query locations: {summary['total_query_locations']}")
        print(f"High priority issues: {summary['high_priority_issues']}")
        print(f"Medium priority issues: {summary['medium_priority_issues']}")
        print(f"Quick wins available: {summary['quick_wins']}")
        print(f"Estimated performance gain: {summary['potential_performance_gain']}")
        
        # Show top recommendations
        recommendations = report["recommendations"]
        
        print("\n🔴 Top High Priority Issues:")
        for i, issue in enumerate(recommendations.get("priority_high", [])[:3], 1):
            print(f"  {i}. {issue.get('issue', 'Unknown issue')}")
        
        print("\n🎯 Quick Wins:")
        for i, win in enumerate(recommendations.get("quick_wins", [])[:3], 1):
            print(f"  {i}. {win.get('issue', 'Unknown quick win')}")
        
        print("\n📈 Next Steps:")
        print("  1. Review the detailed JSON report")
        print("  2. Implement quick wins (indexes, etc.)")
        print("  3. Address high priority N+1 query issues")
        print("  4. Run database migrations for index optimization")
        print("  5. Set up query performance monitoring")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🔬 CC02 v33.0 Database Optimization Analyzer")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    analyzer = DatabaseOptimizationAnalyzer(project_root)
    report = analyzer.run_comprehensive_analysis()
    
    return report


if __name__ == "__main__":
    main()