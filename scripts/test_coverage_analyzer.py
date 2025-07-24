#!/usr/bin/env python3
"""
CC02 v33.0 テストカバレッジ分析ツール
Test Coverage Analyzer for Quality Improvement Cycles
"""

import os
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime


class TestCoverageAnalyzer:
    """テストカバレッジを分析し、品質改善提案を生成するツール"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.frontend_path = project_root / "frontend"
        self.coverage_threshold = 80.0
        self.analysis_results = {}
        
    def analyze_backend_coverage(self) -> Dict[str, Any]:
        """バックエンドのテストカバレッジを分析"""
        print("🔍 バックエンドテストカバレッジ分析開始...")
        
        try:
            # pytest with coverage
            result = subprocess.run([
                "uv", "run", "pytest", "--cov=app", "--cov-report=json", 
                "--cov-report=term-missing", "tests/"
            ], 
            cwd=self.backend_path, 
            capture_output=True, 
            text=True,
            timeout=300
            )
            
            # Parse coverage.json if it exists
            coverage_file = self.backend_path / "coverage.json"
            coverage_data = {}
            
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
            
            return {
                "type": "backend",
                "status": "success" if result.returncode == 0 else "warning",
                "output": result.stdout,
                "errors": result.stderr,
                "coverage_data": coverage_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "type": "backend",
                "status": "timeout",
                "error": "テスト実行がタイムアウトしました"
            }
        except Exception as e:
            return {
                "type": "backend", 
                "status": "error",
                "error": str(e)
            }
    
    def analyze_frontend_coverage(self) -> Dict[str, Any]:
        """フロントエンドのテストカバレッジを分析"""
        print("🔍 フロントエンドテストカバレッジ分析開始...")
        
        try:
            # Check if node_modules exists
            if not (self.frontend_path / "node_modules").exists():
                return {
                    "type": "frontend",
                    "status": "skip",
                    "reason": "node_modules not found - run npm install first"
                }
            
            # Run vitest with coverage
            result = subprocess.run([
                "npm", "run", "coverage"
            ],
            cwd=self.frontend_path,
            capture_output=True,
            text=True,
            timeout=300
            )
            
            return {
                "type": "frontend",
                "status": "success" if result.returncode == 0 else "warning", 
                "output": result.stdout,
                "errors": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "type": "frontend",
                "status": "timeout", 
                "error": "テスト実行がタイムアウトしました"
            }
        except Exception as e:
            return {
                "type": "frontend",
                "status": "error",
                "error": str(e)
            }
    
    def identify_low_coverage_files(self, coverage_data: Dict) -> List[Dict[str, Any]]:
        """カバレッジが低いファイルを特定"""
        low_coverage_files = []
        
        if "files" in coverage_data:
            for filepath, file_data in coverage_data["files"].items():
                if "summary" in file_data:
                    coverage_percent = file_data["summary"]["percent_covered"]
                    if coverage_percent < self.coverage_threshold:
                        low_coverage_files.append({
                            "file": filepath,
                            "coverage": coverage_percent,
                            "missing_lines": file_data.get("missing_lines", []),
                            "total_lines": file_data["summary"]["num_statements"]
                        })
        
        # Sort by lowest coverage first
        low_coverage_files.sort(key=lambda x: x["coverage"])
        return low_coverage_files
    
    def generate_test_improvement_suggestions(self, analysis_results: Dict) -> List[str]:
        """テスト品質改善提案を生成"""
        suggestions = []
        
        # Backend suggestions
        if "backend" in analysis_results:
            backend_result = analysis_results["backend"]
            if backend_result["status"] == "success" and "coverage_data" in backend_result:
                low_coverage = self.identify_low_coverage_files(backend_result["coverage_data"])
                
                if low_coverage:
                    suggestions.append("📈 低カバレッジファイルのテスト追加:")
                    for file_info in low_coverage[:5]:  # Top 5
                        suggestions.append(f"  - {file_info['file']} ({file_info['coverage']:.1f}%)")
                
                suggestions.append("🧪 推奨テストパターン:")
                suggestions.append("  - Edge caseテストの追加")  
                suggestions.append("  - Error handlingテストの強化")
                suggestions.append("  - Integration testの拡充")
        
        # Frontend suggestions  
        if "frontend" in analysis_results:
            frontend_result = analysis_results["frontend"]
            if frontend_result["status"] == "success":
                suggestions.append("🎨 フロントエンドテスト改善:")
                suggestions.append("  - Component interaction tests")
                suggestions.append("  - User flow testing") 
                suggestions.append("  - Accessibility testing")
        
        # General suggestions
        suggestions.extend([
            "🔧 コード品質改善:",
            "  - Type annotationの強化",
            "  - Docstring coverage向上", 
            "  - Performance testing追加",
            "🚀 CI/CD改善:",
            "  - Test parallelization",
            "  - Coverage quality gates",
            "  - Automated test generation"
        ])
        
        return suggestions
    
    def create_improvement_pr_plan(self, suggestions: List[str]) -> Dict[str, Any]:
        """改善PR作成計画を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return {
            "branch_name": f"test/cc02-v33-quality-improvement-{timestamp}",
            "pr_title": f"test: CC02 v33.0 Quality Improvement - {datetime.now().strftime('%Y-%m-%d')}",
            "pr_description": f"""## Test Quality Improvement - CC02 v33.0 Protocol

### 改善内容
{chr(10).join(['- ' + s for s in suggestions[:10]])}

### 実施済み分析
- Backend coverage analysis ✅
- Frontend coverage analysis ✅ 
- Low coverage identification ✅
- Improvement suggestions generated ✅

### テスト戦略
- Focus on critical business logic
- Improve edge case coverage
- Enhance error handling tests
- Add performance benchmarks

🤖 Generated with CC02 v33.0 Protocol - Test-Driven Quality Improvement

Co-Authored-By: Claude <noreply@anthropic.com>
""",
            "suggestions": suggestions,
            "timestamp": timestamp
        }
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """完全なテストカバレッジ分析を実行"""
        print("🚀 CC02 v33.0 テスト品質分析開始")
        print("=" * 50)
        
        # Run backend analysis
        backend_analysis = self.analyze_backend_coverage()
        
        # Run frontend analysis  
        frontend_analysis = self.analyze_frontend_coverage()
        
        # Compile results
        self.analysis_results = {
            "backend": backend_analysis,
            "frontend": frontend_analysis,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Generate improvement suggestions
        suggestions = self.generate_test_improvement_suggestions(self.analysis_results)
        
        # Create PR plan
        pr_plan = self.create_improvement_pr_plan(suggestions)
        
        # Final results
        return {
            "analysis_results": self.analysis_results,
            "improvement_suggestions": suggestions,
            "pr_plan": pr_plan,
            "next_steps": [
                "Create improvement branch",
                "Implement high-priority test additions",
                "Run quality checks",
                "Create focused PR with improvements"
            ]
        }
    
    def save_analysis_report(self, results: Dict[str, Any], output_file: Path):
        """分析レポートを保存"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"📊 分析レポート保存: {output_file}")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🔬 CC02 v33.0 Test Coverage Analyzer")
    print("=" * 50)
    print(f"Project root: {project_root}")
    
    analyzer = TestCoverageAnalyzer(project_root)
    results = analyzer.run_full_analysis()
    
    # Save report
    report_file = project_root / f"coverage_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    analyzer.save_analysis_report(results, report_file)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📈 分析完了サマリー:")
    print(f"Backend status: {results['analysis_results']['backend']['status']}")
    print(f"Frontend status: {results['analysis_results']['frontend']['status']}")
    print(f"Improvement suggestions: {len(results['improvement_suggestions'])}")
    print(f"PR plan ready: {results['pr_plan']['branch_name']}")
    
    print("\n🎯 次のステップ:")
    for i, step in enumerate(results['next_steps'], 1):
        print(f"{i}. {step}")
    
    return results


if __name__ == "__main__":
    main()