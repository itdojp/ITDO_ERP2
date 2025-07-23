#!/usr/bin/env python3
"""
CC02 v33.0 AI コードレビューアー - Infinite Loop Cycle 5
AI-Powered Code Reviewer for Intelligent Code Analysis and Improvement Suggestions
"""

import ast
import re
import json
import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict


@dataclass
class CodeReviewComment:
    """コードレビューコメント"""
    file_path: str
    line_number: int
    review_type: str
    severity: str
    title: str
    description: str
    suggestion: str
    code_example: Optional[str]
    confidence: float


@dataclass
class FileReviewSummary:
    """ファイルレビューサマリー"""
    file_path: str
    overall_score: float
    comment_count: int
    critical_issues: int
    improvement_suggestions: int
    code_smells: int
    best_practices: int


class AICodeReviewer:
    """AI コードレビューアー"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.output_path = project_root / "scripts" / "code_review_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # AI-like analysis patterns
        self.review_patterns = {
            "code_clarity": {
                "unclear_variable_names": r"\b[a-z]{1,2}\b\s*=",
                "magic_numbers": r"\b(?<![\w.])[2-9]\d+(?![\w.])\b",
                "complex_expressions": r".*\s+and\s+.*\s+or\s+.*",
                "nested_ternary": r".*\?.*\?.*:",
                "long_lines": lambda line: len(line) > 120
            },
            
            "maintainability": {
                "duplicate_logic": r"if\s+.*==.*:\s*\n\s*.*\n.*if\s+.*==.*:\s*\n\s*.*",
                "god_functions": lambda node: hasattr(node, 'end_lineno') and (node.end_lineno - node.lineno) > 50,
                "deep_nesting": r"^\s{16,}",  # 4+ levels of indentation
                "circular_imports": r"from\s+(\w+)\s+import.*\1",
                "unused_imports": r"import\s+(\w+)\n(?!.*\1)"
            },
            
            "performance": {
                "inefficient_loops": r"for\s+.*in\s+range\(len\(",
                "string_concatenation": r"\+=\s*['\"]",
                "repeated_calculations": r"(\w+\([^)]*\))\s*.*\1",
                "unnecessary_list_comprehensions": r"\[.*for.*in.*\][0]",
                "inefficient_membership_tests": r".*in\s+\[.*\]"
            },
            
            "error_handling": {
                "bare_except": r"except\s*:",
                "ignored_exceptions": r"except.*:\s*pass",
                "missing_finally": r"try:.*except.*:(?!.*finally)",
                "resource_leaks": r"open\([^)]*\)(?!.*with)",
                "unhandled_edge_cases": r"def\s+\w+\([^)]*\):(?!.*if.*is None)"
            },
            
            "security_concerns": {
                "eval_usage": r"\beval\s*\(",
                "exec_usage": r"\bexec\s*\(",
                "shell_injection": r"os\.system\(.*\+",
                "sql_concatenation": r"['\"].*SELECT.*['\"].*\+",
                "unsafe_deserialization": r"pickle\.loads?\("
            },
            
            "pythonic_style": {
                "enumerate_missing": r"for\s+\w+\s+in\s+range\(len\(",
                "zip_missing": r"for\s+\w+\s+in\s+range\(len\(.*\)\):\s*.*\[\w+\]",
                "list_comprehension_opportunity": r"result.*=.*\[\]\s*\n.*for.*:\s*\n.*result\.append",
                "dict_get_missing": r"\w+\[.*\]\s*if.*in\s+\w+\s*else",
                "with_statement_missing": r"file.*=.*open\("
            }
        }
        
        # AI knowledge base for suggestions
        self.knowledge_base = {
            "design_patterns": {
                "singleton_pattern": "Consider using dependency injection instead of singleton pattern",
                "factory_pattern": "Factory pattern can improve code flexibility here",
                "observer_pattern": "Observer pattern could decouple these components",
                "strategy_pattern": "Strategy pattern might simplify this conditional logic"
            },
            
            "architectural_improvements": {
                "separation_of_concerns": "Consider separating business logic from presentation logic",
                "dependency_inversion": "Depend on abstractions rather than concrete implementations",
                "single_responsibility": "This class/function has multiple responsibilities",
                "open_closed_principle": "Consider making this code open for extension but closed for modification"
            },
            
            "python_best_practices": {
                "pep8_compliance": "Follow PEP 8 naming conventions",
                "docstring_standards": "Add comprehensive docstrings following PEP 257",
                "type_hints": "Add type hints for better code documentation and IDE support",
                "context_managers": "Use context managers for resource management"
            }
        }
        
        # Scoring weights
        self.scoring_weights = {
            "critical": -10,
            "high": -5,
            "medium": -2,
            "low": -1,
            "info": 0,
            "improvement": 1,
            "best_practice": 2
        }
    
    def analyze_code_file(self, file_path: Path) -> List[CodeReviewComment]:
        """コードファイル分析"""
        if file_path.suffix != '.py':
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return []
            
            comments = []
            lines = content.split('\n')
            
            # Parse AST for structural analysis
            try:
                tree = ast.parse(content)
                comments.extend(self._analyze_ast_structure(tree, file_path, lines))
            except SyntaxError:
                comments.append(CodeReviewComment(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=1,
                    review_type="syntax_error",
                    severity="critical",
                    title="Syntax Error",
                    description="File contains syntax errors that prevent parsing",
                    suggestion="Fix syntax errors before proceeding with review",
                    code_example=None,
                    confidence=1.0
                ))
                return comments
            
            # Pattern-based analysis
            comments.extend(self._analyze_patterns(content, file_path, lines))
            
            # AI-style contextual analysis
            comments.extend(self._contextual_analysis(content, tree, file_path, lines))
            
            # Filter and rank comments
            comments = self._filter_and_rank_comments(comments)
            
            return comments
            
        except Exception as e:
            return [CodeReviewComment(
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=1,
                review_type="analysis_error",
                severity="info",
                title="Analysis Error",
                description=f"Could not analyze file: {str(e)}",
                suggestion="Check file accessibility and format",
                code_example=None,
                confidence=0.5
            )]
    
    def _analyze_ast_structure(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """AST構造分析"""
        comments = []
        
        for node in ast.walk(tree):
            # Analyze functions
            if isinstance(node, ast.FunctionDef):
                comments.extend(self._analyze_function(node, file_path, lines))
            
            # Analyze classes
            elif isinstance(node, ast.ClassDef):
                comments.extend(self._analyze_class(node, file_path, lines))
            
            # Analyze imports
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                comments.extend(self._analyze_import(node, file_path, lines))
            
            # Analyze error handling
            elif isinstance(node, ast.Try):
                comments.extend(self._analyze_error_handling(node, file_path, lines))
        
        return comments
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """関数分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Function length analysis
        if hasattr(node, 'end_lineno'):
            function_length = node.end_lineno - node.lineno + 1
            if function_length > 50:
                comments.append(CodeReviewComment(
                    file_path=rel_path,
                    line_number=node.lineno,
                    review_type="maintainability",
                    severity="medium",
                    title="Long Function",
                    description=f"Function '{node.name}' is {function_length} lines long",
                    suggestion="Consider breaking this function into smaller, more focused functions. Aim for functions under 30 lines.",
                    code_example=self._generate_refactoring_example("extract_method", node.name),
                    confidence=0.8
                ))
        
        # Parameter count analysis
        param_count = len(node.args.args)
        if param_count > 5:
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="maintainability",
                severity="medium",
                title="Too Many Parameters",
                description=f"Function '{node.name}' has {param_count} parameters",
                suggestion="Consider using a configuration object or data class to group related parameters.",
                code_example=self._generate_refactoring_example("parameter_object", node.name),
                confidence=0.7
            ))
        
        # Docstring analysis
        if not ast.get_docstring(node):
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="documentation",
                severity="low",
                title="Missing Docstring",
                description=f"Function '{node.name}' lacks documentation",
                suggestion="Add a comprehensive docstring explaining the function's purpose, parameters, and return value.",
                code_example=self._generate_docstring_example(node.name),
                confidence=0.9
            ))
        
        # Complexity analysis
        complexity = self._calculate_function_complexity(node)
        if complexity > 10:
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="complexity",
                severity="high",
                title="High Cyclomatic Complexity",
                description=f"Function '{node.name}' has cyclomatic complexity of {complexity}",
                suggestion="Reduce complexity by extracting nested logic into separate functions or using early returns.",
                code_example=self._generate_complexity_reduction_example(),
                confidence=0.9
            ))
        
        return comments
    
    def _analyze_class(self, node: ast.ClassDef, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """クラス分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Class length analysis
        if hasattr(node, 'end_lineno'):
            class_length = node.end_lineno - node.lineno + 1
            if class_length > 200:
                comments.append(CodeReviewComment(
                    file_path=rel_path,
                    line_number=node.lineno,
                    review_type="maintainability",
                    severity="medium",
                    title="Large Class",
                    description=f"Class '{node.name}' is {class_length} lines long",
                    suggestion="Consider splitting this class using composition or inheritance to improve maintainability.",
                    code_example=self._generate_class_splitting_example(node.name),
                    confidence=0.7
                ))
        
        # Method count analysis
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        if method_count > 15:
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="design",
                severity="medium",
                title="Too Many Methods",
                description=f"Class '{node.name}' has {method_count} methods",
                suggestion="Consider using composition to break down responsibilities into smaller classes.",
                code_example=self._generate_composition_example(),
                confidence=0.6
            ))
        
        # Inheritance analysis
        if len(node.bases) > 1:
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="design",
                severity="low",
                title="Multiple Inheritance",
                description=f"Class '{node.name}' uses multiple inheritance",
                suggestion="Consider using composition over multiple inheritance to avoid diamond problem and improve clarity.",
                code_example=self._generate_composition_over_inheritance_example(),
                confidence=0.5
            ))
        
        return comments
    
    def _analyze_import(self, node: ast.AST, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """インポート分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Star import analysis
        if isinstance(node, ast.ImportFrom) and any(alias.name == '*' for alias in (node.names or [])):
            comments.append(CodeReviewComment(
                file_path=rel_path,
                line_number=node.lineno,
                review_type="best_practice",
                severity="medium",
                title="Star Import",
                description="Using star import can pollute namespace",
                suggestion="Import specific items instead of using star imports to avoid namespace pollution.",
                code_example="from module import specific_function, specific_class",
                confidence=0.9
            ))
        
        return comments
    
    def _analyze_error_handling(self, node: ast.Try, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """エラーハンドリング分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Bare except analysis
        for handler in node.handlers:
            if handler.type is None:
                comments.append(CodeReviewComment(
                    file_path=rel_path,
                    line_number=handler.lineno,
                    review_type="error_handling",
                    severity="high",
                    title="Bare Except Clause",
                    description="Using bare except clause can hide important errors",
                    suggestion="Catch specific exceptions instead of using bare except clauses.",
                    code_example="except SpecificException as e:\n    logger.error(f'Specific error: {e}')",
                    confidence=0.9
                ))
        
        return comments
    
    def _analyze_patterns(self, content: str, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """パターン分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        for category, patterns in self.review_patterns.items():
            for pattern_name, pattern in patterns.items():
                if callable(pattern):
                    # Handle callable patterns
                    continue
                
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    comment = self._create_pattern_comment(
                        rel_path, line_num, category, pattern_name, 
                        lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    )
                    if comment:
                        comments.append(comment)
        
        return comments
    
    def _create_pattern_comment(self, file_path: str, line_num: int, category: str, 
                              pattern_name: str, code_line: str) -> Optional[CodeReviewComment]:
        """パターンコメント作成"""
        severity_map = {
            "code_clarity": "medium",
            "maintainability": "medium",
            "performance": "high",
            "error_handling": "high",
            "security_concerns": "critical",
            "pythonic_style": "low"
        }
        
        suggestions_map = {
            "unclear_variable_names": "Use descriptive variable names that clearly express intent",
            "magic_numbers": "Replace magic numbers with named constants",
            "complex_expressions": "Break complex expressions into multiple variables for clarity",
            "bare_except": "Catch specific exceptions instead of using bare except",
            "eval_usage": "Avoid eval() - use safer alternatives like ast.literal_eval()",
            "enumerate_missing": "Use enumerate() instead of range(len()) for cleaner code",
            "list_comprehension_opportunity": "Consider using list comprehension for more pythonic code"
        }
        
        title_map = {
            "unclear_variable_names": "Unclear Variable Name",
            "magic_numbers": "Magic Number",
            "complex_expressions": "Complex Expression",
            "bare_except": "Bare Except Clause",
            "eval_usage": "Dangerous eval() Usage",
            "enumerate_missing": "Missing enumerate()",
            "list_comprehension_opportunity": "List Comprehension Opportunity"
        }
        
        return CodeReviewComment(
            file_path=file_path,
            line_number=line_num,
            review_type=category,
            severity=severity_map.get(category, "medium"),
            title=title_map.get(pattern_name, pattern_name.replace('_', ' ').title()),
            description=f"Pattern '{pattern_name}' detected in code",
            suggestion=suggestions_map.get(pattern_name, "Consider refactoring this pattern"),
            code_example=self._generate_improvement_example(pattern_name, code_line),
            confidence=0.7
        )
    
    def _contextual_analysis(self, content: str, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CodeReviewComment]:
        """コンテキスト分析"""
        comments = []
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Analyze file-level patterns
        if "models" in str(file_path) and "class" in content:
            comments.extend(self._analyze_model_patterns(tree, rel_path, lines))
        
        if "api" in str(file_path) or "views" in str(file_path):
            comments.extend(self._analyze_api_patterns(tree, rel_path, lines))
        
        if "test" in str(file_path):
            comments.extend(self._analyze_test_patterns(tree, rel_path, lines))
        
        return comments
    
    def _analyze_model_patterns(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[CodeReviewComment]:
        """モデルパターン分析"""
        comments = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for missing __repr__ method
                has_repr = any(isinstance(n, ast.FunctionDef) and n.name == '__repr__' for n in node.body)
                if not has_repr:
                    comments.append(CodeReviewComment(
                        file_path=file_path,
                        line_number=node.lineno,
                        review_type="best_practice",
                        severity="low",
                        title="Missing __repr__ Method",
                        description=f"Model class '{node.name}' should have a __repr__ method",
                        suggestion="Add __repr__ method for better debugging and logging",
                        code_example=f"def __repr__(self):\n    return f'<{node.name}(id={{self.id}})>'",
                        confidence=0.8
                    ))
        
        return comments
    
    def _analyze_api_patterns(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[CodeReviewComment]:
        """APIパターン分析"""
        comments = []
        
        # Look for missing error handling in API endpoints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function looks like an API endpoint
                if any(decorator.id in ['app.route', 'api.route'] if hasattr(decorator, 'id') else False 
                      for decorator in node.decorator_list):
                    
                    # Check for try-except blocks
                    has_error_handling = any(isinstance(n, ast.Try) for n in ast.walk(node))
                    if not has_error_handling:
                        comments.append(CodeReviewComment(
                            file_path=file_path,
                            line_number=node.lineno,
                            review_type="error_handling",
                            severity="medium",
                            title="Missing Error Handling",
                            description=f"API endpoint '{node.name}' lacks error handling",
                            suggestion="Add try-except blocks to handle potential errors gracefully",
                            code_example="try:\n    # API logic here\nexcept Exception as e:\n    return {'error': str(e)}, 500",
                            confidence=0.7
                        ))
        
        return comments
    
    def _analyze_test_patterns(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[CodeReviewComment]:
        """テストパターン分析"""
        comments = []
        
        test_functions = [node for node in ast.walk(tree) 
                         if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
        
        # Check for assertion usage
        for func in test_functions:
            has_assertions = any(isinstance(n, ast.Call) and 
                               hasattr(n.func, 'id') and 
                               n.func.id.startswith('assert') 
                               for n in ast.walk(func))
            
            if not has_assertions:
                comments.append(CodeReviewComment(
                    file_path=file_path,
                    line_number=func.lineno,
                    review_type="testing",
                    severity="medium",
                    title="Missing Assertions",
                    description=f"Test function '{func.name}' has no assertions",
                    suggestion="Add assertions to verify expected behavior",
                    code_example="assert result == expected_value",
                    confidence=0.9
                ))
        
        return comments
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """関数複雑度計算"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _filter_and_rank_comments(self, comments: List[CodeReviewComment]) -> List[CodeReviewComment]:
        """コメントフィルタリングとランキング"""
        # Remove duplicates
        unique_comments = []
        seen = set()
        
        for comment in comments:
            key = (comment.file_path, comment.line_number, comment.review_type, comment.title)
            if key not in seen:
                seen.add(key)
                unique_comments.append(comment)
        
        # Sort by severity and confidence
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        
        return sorted(unique_comments, 
                     key=lambda c: (severity_order.get(c.severity, 5), -c.confidence))
    
    def _generate_refactoring_example(self, refactoring_type: str, function_name: str) -> str:
        """リファクタリング例生成"""
        examples = {
            "extract_method": f"""
# Before:
def {function_name}(self, data):
    # Long function with multiple responsibilities
    result = self.validate_data(data)
    processed = self.process_data(result)
    return self.save_data(processed)

# After:
def {function_name}(self, data):
    validated_data = self._validate_and_process(data)
    return self._save_processed_data(validated_data)

def _validate_and_process(self, data):
    result = self.validate_data(data)
    return self.process_data(result)
""",
            "parameter_object": f"""
# Before:
def {function_name}(self, name, age, email, phone, address):
    pass

# After:
@dataclass
class UserData:
    name: str
    age: int
    email: str
    phone: str
    address: str

def {function_name}(self, user_data: UserData):
    pass
"""
        }
        return examples.get(refactoring_type, "# Consider refactoring this code")
    
    def _generate_docstring_example(self, function_name: str) -> str:
        """Docstring例生成"""
        return f'''
def {function_name}(self, param1: str, param2: int) -> bool:
    """
    Brief description of what this function does.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter
    
    Returns:
        Description of what the function returns
    
    Raises:
        SpecificException: When this specific condition occurs
    """
    pass
'''
    
    def _generate_complexity_reduction_example(self) -> str:
        """複雑度削減例生成"""
        return '''
# Before (high complexity):
def process_data(self, data, config):
    if data is not None:
        if config.enabled:
            if data.type == "A":
                if data.value > 100:
                    return self.handle_large_a(data)
                else:
                    return self.handle_small_a(data)
            elif data.type == "B":
                return self.handle_b(data)
        else:
            return self.handle_disabled(data)
    return None

# After (reduced complexity):
def process_data(self, data, config):
    if not data:
        return None
    if not config.enabled:
        return self.handle_disabled(data)
    
    return self._process_by_type(data)

def _process_by_type(self, data):
    handlers = {
        "A": self._handle_type_a,
        "B": self._handle_type_b
    }
    handler = handlers.get(data.type)
    return handler(data) if handler else None

def _handle_type_a(self, data):
    return self.handle_large_a(data) if data.value > 100 else self.handle_small_a(data)
'''
    
    def _generate_class_splitting_example(self, class_name: str) -> str:
        """クラス分割例生成"""
        return f'''
# Before: Large {class_name} class
class {class_name}:
    # Too many responsibilities
    
# After: Split into focused classes
class {class_name}Data:
    """Handles data operations"""
    pass

class {class_name}Validator:
    """Handles validation logic"""
    pass

class {class_name}Processor:
    """Handles processing logic"""
    pass

class {class_name}:
    """Coordinates the components"""
    def __init__(self):
        self.data = {class_name}Data()
        self.validator = {class_name}Validator()
        self.processor = {class_name}Processor()
'''
    
    def _generate_composition_example(self) -> str:
        """コンポジション例生成"""
        return '''
# Use composition to reduce method count
class EmailService:
    def send_email(self, message): pass

class SMSService:
    def send_sms(self, message): pass

class NotificationManager:
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    def send_notification(self, message, method):
        if method == "email":
            self.email_service.send_email(message)
        elif method == "sms":
            self.sms_service.send_sms(message)
'''
    
    def _generate_composition_over_inheritance_example(self) -> str:
        """継承よりもコンポジション例生成"""
        return '''
# Instead of multiple inheritance:
# class Manager(Employee, Person, Serializable):

# Use composition:
class Manager:
    def __init__(self):
        self.employee_data = Employee()
        self.person_data = Person()
        self.serializer = Serializer()
    
    def serialize(self):
        return self.serializer.serialize({
            "employee": self.employee_data,
            "person": self.person_data
        })
'''
    
    def _generate_improvement_example(self, pattern_name: str, original_code: str) -> str:
        """改善例生成"""
        examples = {
            "enumerate_missing": f'''
# Instead of:
# {original_code}
for i, item in enumerate(items):
    print(f"{{i}}: {{item}}")
''',
            "magic_numbers": f'''
# Instead of:
# {original_code}
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
result = function_call(timeout=TIMEOUT_SECONDS, retries=MAX_RETRIES)
''',
            "list_comprehension_opportunity": f'''
# Instead of:
# {original_code}
result = [process(item) for item in items if item.is_valid()]
'''
        }
        return examples.get(pattern_name, f"# Improve: {original_code}")
    
    def calculate_file_score(self, comments: List[CodeReviewComment]) -> float:
        """ファイルスコア計算"""
        base_score = 100.0
        
        for comment in comments:
            weight = self.scoring_weights.get(comment.severity, -1)
            confidence_multiplier = comment.confidence
            base_score += weight * confidence_multiplier
        
        return max(0.0, min(100.0, base_score))
    
    def run_comprehensive_review(self) -> Dict[str, Any]:
        """包括的コードレビュー実行"""
        print("🚀 CC02 v33.0 AI Code Reviewer - Cycle 5")
        print("=" * 60)
        
        review_results = {
            "review_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "file_reviews": {},
            "overall_statistics": {},
            "top_issues": [],
            "improvement_roadmap": [],
            "ai_insights": []
        }
        
        # Get Python files to review
        python_files = list(self.backend_path.glob("**/*.py"))
        python_files = [f for f in python_files if not f.name.startswith("__") and "migrations" not in str(f)]
        
        print(f"  📊 Reviewing {len(python_files)} Python files...")
        
        all_comments = []
        file_summaries = []
        
        # Review each file
        for file_path in python_files:
            try:
                comments = self.analyze_code_file(file_path)
                
                if comments:
                    rel_path = str(file_path.relative_to(self.project_root))
                    file_score = self.calculate_file_score(comments)
                    
                    # Create file summary
                    summary = FileReviewSummary(
                        file_path=rel_path,
                        overall_score=file_score,
                        comment_count=len(comments),
                        critical_issues=len([c for c in comments if c.severity == "critical"]),
                        improvement_suggestions=len([c for c in comments if c.review_type in ["best_practice", "pythonic_style"]]),
                        code_smells=len([c for c in comments if c.review_type == "maintainability"]),
                        best_practices=len([c for c in comments if c.severity == "info"])
                    )
                    
                    review_results["file_reviews"][rel_path] = {
                        "summary": asdict(summary),
                        "comments": [asdict(c) for c in comments]
                    }
                    
                    all_comments.extend(comments)
                    file_summaries.append(summary)
                    
            except Exception as e:
                print(f"Warning: Could not review {file_path}: {e}")
        
        # Generate overall statistics
        review_results["overall_statistics"] = self._generate_overall_statistics(file_summaries, all_comments)
        
        # Identify top issues
        review_results["top_issues"] = self._identify_top_issues(all_comments)
        
        # Generate improvement roadmap
        review_results["improvement_roadmap"] = self._generate_improvement_roadmap(all_comments, file_summaries)
        
        # Generate AI insights
        review_results["ai_insights"] = self._generate_ai_insights(all_comments, file_summaries)
        
        # Save comprehensive report
        report_file = self.output_path / f"ai_code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(review_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ AI code review complete! Report saved to: {report_file}")
        
        # Print summary
        self._print_review_summary(review_results)
        
        return review_results
    
    def _generate_overall_statistics(self, file_summaries: List[FileReviewSummary], 
                                   all_comments: List[CodeReviewComment]) -> Dict[str, Any]:
        """全体統計生成"""
        if not file_summaries:
            return {}
        
        total_files = len(file_summaries)
        avg_score = sum(f.overall_score for f in file_summaries) / total_files
        
        severity_counts = Counter(c.severity for c in all_comments)
        review_type_counts = Counter(c.review_type for c in all_comments)
        
        return {
            "total_files_reviewed": total_files,
            "average_code_quality_score": round(avg_score, 2),
            "total_comments": len(all_comments),
            "severity_breakdown": dict(severity_counts),
            "review_type_breakdown": dict(review_type_counts),
            "files_needing_attention": len([f for f in file_summaries if f.overall_score < 70]),
            "high_quality_files": len([f for f in file_summaries if f.overall_score >= 90])
        }
    
    def _identify_top_issues(self, all_comments: List[CodeReviewComment]) -> List[Dict[str, Any]]:
        """トップ問題特定"""
        # Group by title and count occurrences
        issue_counts = Counter(c.title for c in all_comments)
        
        top_issues = []
        for title, count in issue_counts.most_common(10):
            relevant_comments = [c for c in all_comments if c.title == title]
            avg_severity = Counter(c.severity for c in relevant_comments).most_common(1)[0][0]
            
            top_issues.append({
                "title": title,
                "occurrences": count,
                "severity": avg_severity,
                "affected_files": len(set(c.file_path for c in relevant_comments)),
                "avg_confidence": round(sum(c.confidence for c in relevant_comments) / len(relevant_comments), 2)
            })
        
        return top_issues
    
    def _generate_improvement_roadmap(self, all_comments: List[CodeReviewComment], 
                                    file_summaries: List[FileReviewSummary]) -> List[Dict[str, Any]]:
        """改善ロードマップ生成"""
        roadmap = []
        
        # Phase 1: Critical issues
        critical_comments = [c for c in all_comments if c.severity == "critical"]
        if critical_comments:
            roadmap.append({
                "phase": 1,
                "title": "Address Critical Issues",
                "priority": "immediate",
                "timeline": "1-2 days",
                "issue_count": len(critical_comments),
                "focus_areas": list(set(c.review_type for c in critical_comments)),
                "expected_impact": "Prevent security vulnerabilities and system failures"
            })
        
        # Phase 2: High severity issues
        high_comments = [c for c in all_comments if c.severity == "high"]
        if high_comments:
            roadmap.append({
                "phase": 2,
                "title": "Fix High Priority Issues",
                "priority": "high",
                "timeline": "1 week",
                "issue_count": len(high_comments),
                "focus_areas": list(set(c.review_type for c in high_comments)),
                "expected_impact": "Improve code maintainability and performance"
            })
        
        # Phase 3: Refactoring and improvements
        medium_low_comments = [c for c in all_comments if c.severity in ["medium", "low"]]
        if medium_low_comments:
            roadmap.append({
                "phase": 3,
                "title": "Code Quality Improvements",
                "priority": "medium",
                "timeline": "2-4 weeks",
                "issue_count": len(medium_low_comments),
                "focus_areas": list(set(c.review_type for c in medium_low_comments)),
                "expected_impact": "Enhance code readability and maintainability"
            })
        
        return roadmap
    
    def _generate_ai_insights(self, all_comments: List[CodeReviewComment], 
                            file_summaries: List[FileReviewSummary]) -> List[Dict[str, Any]]:
        """AI洞察生成"""
        insights = []
        
        # Code quality trend analysis
        avg_score = sum(f.overall_score for f in file_summaries) / len(file_summaries) if file_summaries else 0
        if avg_score < 70:
            insights.append({
                "type": "quality_trend",
                "severity": "high",
                "title": "Below Average Code Quality",
                "description": f"Overall code quality score is {avg_score:.1f}/100, indicating room for improvement",
                "recommendation": "Focus on addressing high-severity issues and implementing coding standards"
            })
        
        # Pattern analysis
        maintainability_issues = len([c for c in all_comments if c.review_type == "maintainability"])
        if maintainability_issues > len(file_summaries) * 2:  # More than 2 issues per file on average
            insights.append({
                "type": "pattern_analysis",
                "severity": "medium",
                "title": "Maintainability Concerns",
                "description": f"High number of maintainability issues ({maintainability_issues}) detected",
                "recommendation": "Consider refactoring large functions and classes, implementing design patterns"
            })
        
        # Security analysis
        security_issues = len([c for c in all_comments if c.review_type == "security_concerns"])
        if security_issues > 0:
            insights.append({
                "type": "security_analysis",
                "severity": "critical",
                "title": "Security Vulnerabilities Detected",
                "description": f"{security_issues} potential security issues found",
                "recommendation": "Immediately review and fix all security-related issues"
            })
        
        # Best practices analysis
        pythonic_opportunities = len([c for c in all_comments if c.review_type == "pythonic_style"])
        if pythonic_opportunities > len(file_summaries):
            insights.append({
                "type": "best_practices",
                "severity": "low",
                "title": "Pythonic Code Opportunities",
                "description": f"{pythonic_opportunities} opportunities to make code more Pythonic",
                "recommendation": "Implement Python best practices for cleaner, more readable code"
            })
        
        return insights
    
    def _print_review_summary(self, review_results: Dict[str, Any]):
        """レビューサマリー出力"""
        print("\n" + "=" * 60)
        print("🧠 AI Code Review Summary")
        print("=" * 60)
        
        stats = review_results["overall_statistics"]
        print(f"Files reviewed: {stats.get('total_files_reviewed', 0)}")
        print(f"Average quality score: {stats.get('average_code_quality_score', 0)}/100")
        print(f"Total review comments: {stats.get('total_comments', 0)}")
        print(f"Files needing attention: {stats.get('files_needing_attention', 0)}")
        print(f"High quality files: {stats.get('high_quality_files', 0)}")
        
        # Severity breakdown
        severity_breakdown = stats.get('severity_breakdown', {})
        print(f"\n📊 Issue Severity Breakdown:")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = severity_breakdown.get(severity, 0)
            if count > 0:
                print(f"  {severity.capitalize()}: {count}")
        
        # Top issues
        top_issues = review_results.get("top_issues", [])[:5]
        if top_issues:
            print(f"\n🔥 Top Issues:")
            for i, issue in enumerate(top_issues, 1):
                print(f"  {i}. {issue['title']}: {issue['occurrences']} occurrences ({issue['severity']})")
        
        # AI insights
        ai_insights = review_results.get("ai_insights", [])
        if ai_insights:
            print(f"\n🧠 AI Insights:")
            for insight in ai_insights[:3]:
                print(f"  • {insight['title']}: {insight['description']}")
        
        # Improvement roadmap
        roadmap = review_results.get("improvement_roadmap", [])
        if roadmap:
            print(f"\n📋 Improvement Roadmap:")
            for phase in roadmap:
                print(f"  Phase {phase['phase']} ({phase['timeline']}): {phase['title']} - {phase['issue_count']} issues")


def main():
    """メイン実行関数"""
    project_root = Path.cwd()
    
    print("🔬 CC02 v33.0 AI Code Reviewer")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    reviewer = AICodeReviewer(project_root)
    report = reviewer.run_comprehensive_review()
    
    return report


if __name__ == "__main__":
    main()