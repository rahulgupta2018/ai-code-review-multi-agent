"""
Engineering Practices Evaluator Tool Implementation for ADK Code Review System.

This tool evaluates software engineering best practices, SOLID principles, and development workflows.
"""

import time
import re
from typing import Dict, Any, List, Optional

from google.adk.tools.tool_context import ToolContext


def evaluate_engineering_practices(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Evaluate engineering practices and software development best practices.
    
    Args:
        tool_context: ADK ToolContext containing session state and parameters
        
    Returns:
        dict: Engineering practices evaluation results with scores and recommendations
    """
    execution_start = time.time()
    
    try:
        # Get code from tool context
        code = tool_context.state.get('code', '')
        language = tool_context.state.get('language', 'python')
        file_path = tool_context.state.get('file_path', 'unknown')
        project_structure = tool_context.state.get('project_structure', {})
        
        # Check parameters if not in state
        if not code and hasattr(tool_context, 'parameters'):
            code = getattr(tool_context, 'parameters', {}).get('code', '')
            language = getattr(tool_context, 'parameters', {}).get('language', 'python')
            file_path = getattr(tool_context, 'parameters', {}).get('file_path', 'unknown')
        
        if not code:
            return {
                'status': 'error',
                'error_message': 'No code provided for engineering practices evaluation',
                'tool_name': 'evaluate_engineering_practices'
            }
        
        # Perform comprehensive engineering practices evaluation
        practices_result = {
            'status': 'success',
            'tool_name': 'evaluate_engineering_practices',
            'file_path': file_path,
            'language': language,
            'analysis_type': 'engineering_practices_evaluation',
            'solid_principles': {
                'single_responsibility': _evaluate_single_responsibility(code, language),
                'open_closed': _evaluate_open_closed(code, language),
                'liskov_substitution': _evaluate_liskov_substitution(code, language),
                'interface_segregation': _evaluate_interface_segregation(code, language),
                'dependency_inversion': _evaluate_dependency_inversion(code, language)
            },
            'code_organization': {
                'modularity_score': _assess_modularity(code, language),
                'separation_of_concerns': _assess_separation_of_concerns(code, language),
                'naming_conventions': _evaluate_naming_conventions(code, language),
                'code_structure': _evaluate_code_structure(code, language)
            },
            'documentation_quality': {
                'docstring_coverage': _assess_docstring_coverage(code, language),
                'comment_quality': _assess_comment_quality(code, language),
                'readme_indicators': _check_readme_indicators(code),
                'api_documentation': _check_api_documentation(code, language)
            },
            'testing_practices': {
                'test_indicators': _assess_testing_practices(code, language),
                'test_coverage_hints': _assess_test_coverage_hints(code, language),
                'test_quality': _assess_test_quality(code, language),
                'testing_patterns': _identify_testing_patterns(code, language)
            },
            'error_handling': {
                'exception_handling': _evaluate_exception_handling(code, language),
                'error_recovery': _evaluate_error_recovery(code, language),
                'logging_practices': _evaluate_logging_practices(code, language)
            },
            'performance_considerations': {
                'algorithm_efficiency': _assess_algorithm_efficiency(code, language),
                'resource_management': _assess_resource_management(code, language),
                'caching_strategies': _identify_caching_strategies(code, language)
            },
            'overall_scores': {},
            'recommendations': [],
            'timestamp': time.time()
        }
        
        # Calculate overall scores
        practices_result['overall_scores'] = _calculate_overall_scores(practices_result)
        
        # Generate recommendations
        practices_result['recommendations'] = _generate_engineering_recommendations(practices_result)
        
        execution_time = time.time() - execution_start
        practices_result['execution_time_seconds'] = execution_time
        
        # Store results in session state
        current_analysis = tool_context.state.get('engineering_practices_analysis', {})
        current_analysis[file_path] = practices_result
        tool_context.state['engineering_practices_analysis'] = current_analysis
        
        # Update analysis progress
        analysis_progress = tool_context.state.get('analysis_progress', {})
        analysis_progress['engineering_practices_completed'] = True
        analysis_progress['engineering_practices_timestamp'] = time.time()
        tool_context.state['analysis_progress'] = analysis_progress
        
        return practices_result
        
    except Exception as e:
        execution_time = time.time() - execution_start
        error_result = {
            'status': 'error',
            'tool_name': 'evaluate_engineering_practices',
            'error_message': str(e),
            'error_type': type(e).__name__,
            'execution_time_seconds': execution_time
        }
        
        tool_context.state['engineering_practices_error'] = error_result
        return error_result


def _evaluate_single_responsibility(code: str, language: str) -> Dict[str, Any]:
    """Evaluate Single Responsibility Principle adherence."""
    functions = _extract_functions(code, language)
    classes = _extract_classes(code, language)
    
    # Check function length as indicator of multiple responsibilities
    long_functions = [f for f in functions if f['line_count'] > 50]
    
    # Check class method count as indicator
    classes_with_many_methods = []
    for cls in classes:
        method_count = len(cls['methods'])
        if method_count > 10:
            classes_with_many_methods.append(cls)
    
    score = 100
    if long_functions:
        score -= len(long_functions) * 10
    if classes_with_many_methods:
        score -= len(classes_with_many_methods) * 15
    
    return {
        'score': max(0, score),
        'grade': _get_grade(score),
        'issues': {
            'long_functions': len(long_functions),
            'classes_with_many_methods': len(classes_with_many_methods)
        },
        'details': {
            'long_function_names': [f['name'] for f in long_functions[:3]],
            'complex_class_names': [c['name'] for c in classes_with_many_methods[:3]]
        }
    }


def _evaluate_open_closed(code: str, language: str) -> Dict[str, Any]:
    """Evaluate Open/Closed Principle adherence."""
    # Look for extensibility patterns
    inheritance_usage = len(re.findall(r'class\s+\w+\([^)]+\)', code))
    interface_usage = len(re.findall(r'(abstract|interface)', code, re.IGNORECASE))
    composition_patterns = len(re.findall(r'self\.\w+\s*=\s*\w+\(', code))
    
    score = 50  # Base score
    score += min(inheritance_usage * 10, 30)
    score += min(interface_usage * 15, 30)
    score += min(composition_patterns * 5, 20)
    
    return {
        'score': min(100, score),
        'grade': _get_grade(score),
        'extensibility_indicators': {
            'inheritance_usage': inheritance_usage,
            'interface_usage': interface_usage,
            'composition_patterns': composition_patterns
        }
    }


def _evaluate_liskov_substitution(code: str, language: str) -> Dict[str, Any]:
    """Evaluate Liskov Substitution Principle adherence."""
    # Look for potential LSP violations
    inheritance_chains = _analyze_inheritance_chains(code, language)
    method_overrides = _detect_method_overrides(code, language)
    
    # Check for type checking in methods (potential LSP violation)
    type_checks = len(re.findall(r'isinstance\s*\(|type\s*\(.*\)\s*==', code))
    
    score = 85  # Start with good score
    if type_checks > 3:
        score -= type_checks * 5
    
    return {
        'score': max(50, score),
        'grade': _get_grade(score),
        'potential_violations': {
            'excessive_type_checking': type_checks > 3,
            'type_check_count': type_checks
        },
        'inheritance_analysis': {
            'inheritance_chains': len(inheritance_chains),
            'method_overrides': len(method_overrides)
        }
    }


def _evaluate_interface_segregation(code: str, language: str) -> Dict[str, Any]:
    """Evaluate Interface Segregation Principle adherence."""
    classes = _extract_classes(code, language)
    
    # Look for fat interfaces (classes/interfaces with many methods)
    fat_interfaces = []
    for cls in classes:
        if len(cls['methods']) > 15:
            fat_interfaces.append(cls)
    
    # Check for abstract methods/interfaces
    abstract_methods = len(re.findall(r'@abstractmethod|abstract\s+def', code, re.IGNORECASE))
    
    score = 80  # Base score
    score -= len(fat_interfaces) * 15
    score += min(abstract_methods * 5, 20)
    
    return {
        'score': max(0, score),
        'grade': _get_grade(score),
        'interface_analysis': {
            'fat_interfaces_count': len(fat_interfaces),
            'abstract_methods_count': abstract_methods,
            'fat_interface_names': [fi['name'] for fi in fat_interfaces[:3]]
        }
    }


def _evaluate_dependency_inversion(code: str, language: str) -> Dict[str, Any]:
    """Evaluate Dependency Inversion Principle adherence."""
    # Look for dependency injection patterns
    constructor_injection = len(re.findall(r'def __init__\([^)]*\w+[^)]*\):', code))
    factory_patterns = len(re.findall(r'Factory|factory|create_\w+', code))
    abstract_dependencies = len(re.findall(r'ABC|Abstract|Interface', code))
    
    # Check for direct instantiation in methods (DIP violation)
    direct_instantiations = len(re.findall(r'= \w+\(', code)) - constructor_injection
    
    score = 60  # Base score
    score += min(constructor_injection * 8, 25)
    score += min(factory_patterns * 10, 20)
    score += min(abstract_dependencies * 15, 25)
    score -= min(direct_instantiations * 3, 30)
    
    return {
        'score': max(0, min(100, score)),
        'grade': _get_grade(score),
        'dependency_patterns': {
            'constructor_injection': constructor_injection,
            'factory_patterns': factory_patterns,
            'abstract_dependencies': abstract_dependencies,
            'direct_instantiations': direct_instantiations
        }
    }


def _assess_modularity(code: str, language: str) -> Dict[str, Any]:
    """Assess code modularity."""
    imports = len(re.findall(r'^import |^from .* import', code, re.MULTILINE))
    functions = len(_extract_functions(code, language))
    classes = len(_extract_classes(code, language))
    lines_of_code = len(code.split('\n'))
    
    # Calculate modularity indicators
    functions_per_loc = functions / max(lines_of_code, 1) * 100
    classes_per_loc = classes / max(lines_of_code, 1) * 100
    imports_ratio = imports / max(lines_of_code / 100, 1)
    
    # Score based on reasonable modularity
    score = 50
    if 0.5 <= functions_per_loc <= 3:
        score += 20
    if 0.1 <= classes_per_loc <= 1:
        score += 15
    if 1 <= imports_ratio <= 10:
        score += 15
    
    return {
        'score': min(100, score),
        'grade': _get_grade(score),
        'metrics': {
            'functions_count': functions,
            'classes_count': classes,
            'imports_count': imports,
            'functions_per_100_loc': round(functions_per_loc, 2),
            'classes_per_100_loc': round(classes_per_loc, 2)
        }
    }


def _assess_separation_of_concerns(code: str, language: str) -> Dict[str, Any]:
    """Assess separation of concerns."""
    # Look for mixed concerns indicators
    mixed_concerns_indicators = {
        'ui_and_logic': len(re.findall(r'print\(.*business|logic.*print\(', code, re.IGNORECASE)),
        'data_and_presentation': len(re.findall(r'html.*data|json.*render', code, re.IGNORECASE)),
        'multiple_responsibilities': len(re.findall(r'def \w*(save|load|process|validate|render)\w*', code))
    }
    
    total_mixed_concerns = sum(mixed_concerns_indicators.values())
    score = max(0, 100 - total_mixed_concerns * 10)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'mixed_concerns_indicators': mixed_concerns_indicators,
        'separation_quality': 'good' if score >= 80 else 'needs_improvement' if score >= 60 else 'poor'
    }


def _evaluate_naming_conventions(code: str, language: str) -> Dict[str, Any]:
    """Evaluate naming conventions."""
    functions = _extract_functions(code, language)
    classes = _extract_classes(code, language)
    variables = _extract_variables(code, language)
    
    naming_issues = {
        'snake_case_functions': 0,
        'pascal_case_classes': 0,
        'descriptive_names': 0,
        'abbreviations': 0
    }
    
    # Check function naming (should be snake_case in Python)
    if language.lower() == 'python':
        for func in functions:
            if not re.match(r'^[a-z_][a-z0-9_]*$', func['name']):
                naming_issues['snake_case_functions'] += 1
    
    # Check class naming (should be PascalCase)
    for cls in classes:
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', cls['name']):
            naming_issues['pascal_case_classes'] += 1
    
    # Check for descriptive names (length > 3)
    short_names = [name for name in variables if len(name) <= 2 and name not in ['i', 'j', 'k', 'x', 'y', 'z']]
    naming_issues['descriptive_names'] = len(short_names)
    
    # Check for excessive abbreviations
    abbreviations = len([name for name in variables if len(name) <= 5 and name.count('_') == 0 and name.islower()])
    naming_issues['abbreviations'] = abbreviations
    
    total_issues = sum(naming_issues.values())
    score = max(0, 100 - total_issues * 5)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'naming_issues': naming_issues,
        'conventions_followed': score >= 80
    }


def _evaluate_code_structure(code: str, language: str) -> Dict[str, Any]:
    """Evaluate overall code structure."""
    lines = code.split('\n')
    
    structure_metrics = {
        'empty_lines_ratio': len([line for line in lines if not line.strip()]) / max(len(lines), 1),
        'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
        'average_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
        'max_line_length': max(len(line) for line in lines) if lines else 0,
        'indentation_consistency': _check_indentation_consistency(lines)
    }
    
    score = 100
    # Penalize for poor structure
    if structure_metrics['empty_lines_ratio'] < 0.05 or structure_metrics['empty_lines_ratio'] > 0.3:
        score -= 10
    if structure_metrics['average_line_length'] > 100:
        score -= 15
    if structure_metrics['max_line_length'] > 120:
        score -= 10
    if not structure_metrics['indentation_consistency']:
        score -= 20
    
    return {
        'score': max(0, score),
        'grade': _get_grade(score),
        'structure_metrics': structure_metrics
    }


def _assess_docstring_coverage(code: str, language: str) -> Dict[str, Any]:
    """Assess docstring coverage."""
    functions = _extract_functions(code, language)
    classes = _extract_classes(code, language)
    
    functions_with_docstrings = 0
    classes_with_docstrings = 0
    
    # Count functions with docstrings
    for func in functions:
        if '"""' in func.get('body', '') or "'''" in func.get('body', ''):
            functions_with_docstrings += 1
    
    # Count classes with docstrings
    for cls in classes:
        if '"""' in cls.get('body', '') or "'''" in cls.get('body', ''):
            classes_with_docstrings += 1
    
    total_items = len(functions) + len(classes)
    documented_items = functions_with_docstrings + classes_with_docstrings
    
    coverage_percentage = (documented_items / max(total_items, 1)) * 100
    
    return {
        'coverage_percentage': round(coverage_percentage, 2),
        'grade': _get_grade(coverage_percentage),
        'documented_functions': functions_with_docstrings,
        'total_functions': len(functions),
        'documented_classes': classes_with_docstrings,
        'total_classes': len(classes)
    }


def _assess_comment_quality(code: str, language: str) -> Dict[str, Any]:
    """Assess comment quality."""
    lines = code.split('\n')
    comment_lines = [line for line in lines if line.strip().startswith('#')]
    
    # Analyze comment quality
    quality_indicators = {
        'explanatory_comments': len([c for c in comment_lines if len(c.strip()) > 20]),
        'todo_comments': len([c for c in comment_lines if 'TODO' in c.upper()]),
        'inline_comments': len([line for line in lines if '#' in line and not line.strip().startswith('#')]),
        'commented_code': len([c for c in comment_lines if any(keyword in c for keyword in ['def ', 'class ', 'import ', 'return '])])
    }
    
    total_comments = len(comment_lines)
    good_comments = quality_indicators['explanatory_comments']
    
    if total_comments == 0:
        quality_score = 0
    else:
        quality_score = (good_comments / total_comments) * 100
    
    return {
        'quality_score': round(quality_score, 2),
        'grade': _get_grade(quality_score),
        'quality_indicators': quality_indicators,
        'total_comments': total_comments
    }


def _check_readme_indicators(code: str) -> Dict[str, Any]:
    """Check for README and documentation indicators."""
    readme_indicators = {
        'has_main_guard': '__name__ == "__main__"' in code,
        'has_module_docstring': code.strip().startswith('"""') or code.strip().startswith("'''"),
        'has_usage_examples': 'example' in code.lower() or 'usage' in code.lower(),
        'has_version_info': '__version__' in code or 'version' in code.lower()
    }
    
    score = sum(readme_indicators.values()) * 25
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'indicators': readme_indicators
    }


def _check_api_documentation(code: str, language: str) -> Dict[str, Any]:
    """Check for API documentation patterns."""
    api_patterns = {
        'type_hints': len(re.findall(r':\s*\w+', code)),
        'return_annotations': len(re.findall(r'->\s*\w+:', code)),
        'docstring_parameters': len(re.findall(r'Args:|Parameters:|Param:', code)),
        'docstring_returns': len(re.findall(r'Returns:|Return:', code))
    }
    
    total_patterns = sum(api_patterns.values())
    score = min(100, total_patterns * 5)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'api_patterns': api_patterns
    }


def _assess_testing_practices(code: str, language: str) -> Dict[str, Any]:
    """Assess testing practices."""
    test_indicators = {
        'test_functions': len(re.findall(r'def test_\w+', code)),
        'assert_statements': len(re.findall(r'assert\s+', code)),
        'test_imports': len(re.findall(r'import (unittest|pytest|nose)', code)),
        'mock_usage': len(re.findall(r'mock|Mock|patch', code)),
        'fixture_usage': len(re.findall(r'@pytest\.fixture|setUp|tearDown', code))
    }
    
    total_test_indicators = sum(test_indicators.values())
    score = min(100, total_test_indicators * 10)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'test_indicators': test_indicators,
        'has_tests': total_test_indicators > 0
    }


def _assess_test_coverage_hints(code: str, language: str) -> Dict[str, Any]:
    """Assess test coverage hints."""
    functions = _extract_functions(code, language)
    test_functions = [f for f in functions if f['name'].startswith('test_')]
    regular_functions = [f for f in functions if not f['name'].startswith('test_')]
    
    if len(regular_functions) == 0:
        coverage_hint = 100
    else:
        coverage_hint = (len(test_functions) / len(regular_functions)) * 100
    
    return {
        'coverage_hint_percentage': min(100, round(coverage_hint, 2)),
        'grade': _get_grade(coverage_hint),
        'test_functions': len(test_functions),
        'regular_functions': len(regular_functions)
    }


def _assess_test_quality(code: str, language: str) -> Dict[str, Any]:
    """Assess test quality."""
    test_quality_indicators = {
        'descriptive_test_names': len([m.group() for m in re.finditer(r'def test_\w{10,}', code)]),
        'test_docstrings': len([m.group() for m in re.finditer(r'def test_.*?""".*?"""', code, re.DOTALL)]),
        'setup_teardown': len(re.findall(r'setUp|tearDown|setup_method|teardown_method', code)),
        'parameterized_tests': len(re.findall(r'@pytest\.mark\.parametrize|@parameterized', code))
    }
    
    total_quality = sum(test_quality_indicators.values())
    score = min(100, total_quality * 15)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'quality_indicators': test_quality_indicators
    }


def _identify_testing_patterns(code: str, language: str) -> List[str]:
    """Identify testing patterns used."""
    patterns = []
    
    if 'unittest' in code:
        patterns.append('unittest')
    if 'pytest' in code:
        patterns.append('pytest')
    if 'mock' in code.lower():
        patterns.append('mocking')
    if '@pytest.fixture' in code:
        patterns.append('fixtures')
    if 'setUp' in code or 'tearDown' in code:
        patterns.append('setup_teardown')
    
    return patterns


def _evaluate_exception_handling(code: str, language: str) -> Dict[str, Any]:
    """Evaluate exception handling practices."""
    exception_patterns = {
        'try_blocks': len(re.findall(r'try:', code)),
        'except_blocks': len(re.findall(r'except\s+\w+:', code)),
        'generic_except': len(re.findall(r'except:', code)),
        'finally_blocks': len(re.findall(r'finally:', code)),
        'raise_statements': len(re.findall(r'raise\s+\w+', code))
    }
    
    # Score based on good exception handling practices
    score = 50
    if exception_patterns['try_blocks'] > 0:
        score += 20
    if exception_patterns['except_blocks'] > exception_patterns['generic_except']:
        score += 20
    if exception_patterns['finally_blocks'] > 0:
        score += 10
    
    # Penalize for bad practices
    if exception_patterns['generic_except'] > 0:
        score -= exception_patterns['generic_except'] * 10
    
    return {
        'score': max(0, min(100, score)),
        'grade': _get_grade(score),
        'exception_patterns': exception_patterns
    }


def _evaluate_error_recovery(code: str, language: str) -> Dict[str, Any]:
    """Evaluate error recovery mechanisms."""
    recovery_patterns = {
        'retry_logic': len(re.findall(r'retry|attempt', code, re.IGNORECASE)),
        'fallback_mechanisms': len(re.findall(r'fallback|default|backup', code, re.IGNORECASE)),
        'circuit_breaker': len(re.findall(r'circuit.*breaker', code, re.IGNORECASE)),
        'timeout_handling': len(re.findall(r'timeout|deadline', code, re.IGNORECASE))
    }
    
    total_recovery = sum(recovery_patterns.values())
    score = min(100, total_recovery * 20)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'recovery_patterns': recovery_patterns
    }


def _evaluate_logging_practices(code: str, language: str) -> Dict[str, Any]:
    """Evaluate logging practices."""
    logging_patterns = {
        'logging_imports': len(re.findall(r'import logging|from logging', code)),
        'log_statements': len(re.findall(r'log\.\w+\(|logging\.\w+\(', code)),
        'log_levels': len(re.findall(r'(debug|info|warning|error|critical)', code, re.IGNORECASE)),
        'structured_logging': len(re.findall(r'extra=|exc_info=', code))
    }
    
    total_logging = sum(logging_patterns.values())
    score = min(100, total_logging * 15)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'logging_patterns': logging_patterns
    }


def _assess_algorithm_efficiency(code: str, language: str) -> Dict[str, Any]:
    """Assess algorithm efficiency indicators."""
    efficiency_patterns = {
        'nested_loops': len(re.findall(r'for.*for', code, re.DOTALL)),
        'recursive_calls': len(re.findall(r'def \w+.*\1\(', code)),
        'list_comprehensions': len(re.findall(r'\[.*for.*in.*\]', code)),
        'generator_expressions': len(re.findall(r'\(.*for.*in.*\)', code)),
        'builtin_functions': len(re.findall(r'(map|filter|reduce|sorted|min|max)\(', code))
    }
    
    # Score based on efficiency indicators
    score = 70  # Base score
    score -= efficiency_patterns['nested_loops'] * 10  # Nested loops reduce efficiency
    score += efficiency_patterns['list_comprehensions'] * 5
    score += efficiency_patterns['generator_expressions'] * 5
    score += efficiency_patterns['builtin_functions'] * 3
    
    return {
        'score': max(0, min(100, score)),
        'grade': _get_grade(score),
        'efficiency_patterns': efficiency_patterns
    }


def _assess_resource_management(code: str, language: str) -> Dict[str, Any]:
    """Assess resource management practices."""
    resource_patterns = {
        'context_managers': len(re.findall(r'with\s+\w+', code)),
        'file_operations': len(re.findall(r'open\(', code)),
        'connection_handling': len(re.findall(r'connect\(|connection', code, re.IGNORECASE)),
        'memory_optimization': len(re.findall(r'del\s+\w+|gc\.collect', code))
    }
    
    # Score based on proper resource management
    score = 50
    if resource_patterns['context_managers'] > 0 and resource_patterns['file_operations'] > 0:
        score += 25  # Using context managers with file operations
    if resource_patterns['connection_handling'] > 0:
        score += 15
    score += resource_patterns['memory_optimization'] * 10
    
    return {
        'score': min(100, score),
        'grade': _get_grade(score),
        'resource_patterns': resource_patterns
    }


def _identify_caching_strategies(code: str, language: str) -> Dict[str, Any]:
    """Identify caching strategies."""
    caching_patterns = {
        'lru_cache': len(re.findall(r'@lru_cache|@cache', code)),
        'memoization': len(re.findall(r'memo|cache', code, re.IGNORECASE)),
        'redis_cache': len(re.findall(r'redis|Redis', code)),
        'in_memory_cache': len(re.findall(r'cache.*dict|dict.*cache', code, re.IGNORECASE))
    }
    
    total_caching = sum(caching_patterns.values())
    score = min(100, total_caching * 25)
    
    return {
        'score': score,
        'grade': _get_grade(score),
        'caching_patterns': caching_patterns,
        'has_caching': total_caching > 0
    }


# Helper functions

def _extract_functions(code: str, language: str) -> List[Dict[str, Any]]:
    """Extract function information from code."""
    functions = []
    if language.lower() == 'python':
        pattern = r'def\s+(\w+)\s*\([^)]*\):'
        matches = re.finditer(pattern, code)
        for match in matches:
            func_start = match.start()
            func_name = match.group(1)
            # Rough estimate of function body
            remaining_code = code[func_start:]
            lines = remaining_code.split('\n')
            func_lines = []
            indent_level = len(lines[0]) - len(lines[0].lstrip())
            
            for i, line in enumerate(lines[1:], 1):
                if line.strip() and len(line) - len(line.lstrip()) <= indent_level and line[0] not in [' ', '\t']:
                    break
                func_lines.append(line)
            
            functions.append({
                'name': func_name,
                'line_count': len(func_lines),
                'body': '\n'.join(func_lines)
            })
    
    return functions


def _extract_classes(code: str, language: str) -> List[Dict[str, Any]]:
    """Extract class information from code."""
    classes = []
    if language.lower() == 'python':
        pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        matches = re.finditer(pattern, code)
        for match in matches:
            class_name = match.group(1)
            class_start = match.start()
            # Find methods in class
            remaining_code = code[class_start:]
            methods = re.findall(r'def\s+(\w+)\s*\([^)]*\):', remaining_code)
            
            classes.append({
                'name': class_name,
                'methods': methods,
                'body': remaining_code[:500]  # First 500 chars for analysis
            })
    
    return classes


def _extract_variables(code: str, language: str) -> List[str]:
    """Extract variable names from code."""
    # Simple variable extraction
    variables = []
    if language.lower() == 'python':
        # Find assignment patterns
        assignments = re.findall(r'(\w+)\s*=\s*', code)
        variables.extend(assignments)
        
        # Find function parameters
        func_params = re.findall(r'def\s+\w+\s*\(([^)]*)\)', code)
        for params in func_params:
            param_names = re.findall(r'(\w+)(?:\s*=|,|$)', params)
            variables.extend(param_names)
    
    return list(set(variables))  # Remove duplicates


def _analyze_inheritance_chains(code: str, language: str) -> List[Dict[str, Any]]:
    """Analyze inheritance chains."""
    chains = []
    if language.lower() == 'python':
        pattern = r'class\s+(\w+)\s*\(([^)]+)\):'
        matches = re.finditer(pattern, code)
        for match in matches:
            child_class = match.group(1)
            parent_classes = [p.strip() for p in match.group(2).split(',')]
            chains.append({
                'child': child_class,
                'parents': parent_classes
            })
    
    return chains


def _detect_method_overrides(code: str, language: str) -> List[str]:
    """Detect method overrides."""
    overrides = []
    if language.lower() == 'python':
        # Look for common override patterns
        override_patterns = [
            r'def __init__\(',
            r'def __str__\(',
            r'def __repr__\(',
            r'def __eq__\(',
            r'def __hash__\('
        ]
        
        for pattern in override_patterns:
            matches = re.findall(pattern, code)
            overrides.extend(matches)
    
    return overrides


def _check_indentation_consistency(lines: List[str]) -> bool:
    """Check if indentation is consistent."""
    indents = []
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                indents.append(indent)
    
    if not indents:
        return True
    
    # Check if all indentations are multiples of the smallest indent
    min_indent = min(indents)
    if min_indent == 0:
        return True
    
    return all(indent % min_indent == 0 for indent in indents)


def _calculate_overall_scores(practices_result: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall scores from all evaluations."""
    solid_scores = []
    for principle, data in practices_result['solid_principles'].items():
        if isinstance(data, dict) and 'score' in data:
            solid_scores.append(data['score'])
    
    overall_solid_score = sum(solid_scores) / len(solid_scores) if solid_scores else 0
    
    org_scores = []
    for aspect, data in practices_result['code_organization'].items():
        if isinstance(data, dict) and 'score' in data:
            org_scores.append(data['score'])
    
    overall_organization_score = sum(org_scores) / len(org_scores) if org_scores else 0
    
    # Calculate weighted overall score
    overall_score = (
        overall_solid_score * 0.3 +
        overall_organization_score * 0.25 +
        practices_result['documentation_quality']['docstring_coverage']['coverage_percentage'] * 0.2 +
        practices_result['testing_practices']['score'] * 0.25
    )
    
    return {
        'overall_engineering_score': round(overall_score, 2),
        'solid_principles_score': round(overall_solid_score, 2),
        'code_organization_score': round(overall_organization_score, 2),
        'overall_grade': _get_grade(overall_score)
    }


def _generate_engineering_recommendations(practices_result: Dict[str, Any]) -> List[str]:
    """Generate engineering practice recommendations."""
    recommendations = []
    
    # SOLID principles recommendations
    solid_scores = practices_result['solid_principles']
    if solid_scores['single_responsibility']['score'] < 70:
        recommendations.append("Break down large functions and classes to follow Single Responsibility Principle")
    
    if solid_scores['dependency_inversion']['score'] < 70:
        recommendations.append("Implement dependency injection to improve testability and flexibility")
    
    # Documentation recommendations
    doc_coverage = practices_result['documentation_quality']['docstring_coverage']['coverage_percentage']
    if doc_coverage < 50:
        recommendations.append("Add docstrings to functions and classes to improve code documentation")
    
    # Testing recommendations
    if practices_result['testing_practices']['score'] < 60:
        recommendations.append("Implement comprehensive unit tests to improve code reliability")
    
    # Code organization recommendations
    if practices_result['code_organization']['naming_conventions']['score'] < 70:
        recommendations.append("Follow consistent naming conventions (snake_case for functions, PascalCase for classes)")
    
    # Error handling recommendations
    if practices_result['error_handling']['exception_handling']['score'] < 60:
        recommendations.append("Implement proper exception handling with specific exception types")
    
    if not recommendations:
        recommendations.append("Engineering practices are well-implemented - maintain current quality standards")
    
    return recommendations


def _get_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'