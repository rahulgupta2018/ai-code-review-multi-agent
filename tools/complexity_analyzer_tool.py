"""
Complexity Analyzer Tool Implementation for ADK Code Review System.

This tool provides code complexity analysis capabilities using ADK ToolContext pattern.
"""

import time
from typing import Dict, Any

from google.adk.tools.tool_context import ToolContext


def analyze_code_complexity(tool_context: ToolContext) -> dict:
    """
    Analyze code complexity and store results in session state.
    
    This tool analyzes code complexity metrics including cyclomatic complexity,
    cognitive complexity, maintainability index, and other code quality metrics.
    
    Args:
        tool_context: ADK ToolContext containing session state and parameters
        
    Returns:
        dict: Analysis results with complexity metrics and quality scores
    """
    execution_start = time.time()
    
    try:
        # Get code from tool context (agent should provide this in parameters or state)
        code = tool_context.state.get('code', '')
        language = tool_context.state.get('language', 'python')
        file_path = tool_context.state.get('file_path', 'unknown')
        
        # Also check if code is provided in the current tool invocation
        if not code and hasattr(tool_context, 'parameters'):
            code = getattr(tool_context, 'parameters', {}).get('code', '')
            language = getattr(tool_context, 'parameters', {}).get('language', 'python')
            file_path = getattr(tool_context, 'parameters', {}).get('file_path', 'unknown')
        
        if not code:
            return {
                'status': 'error',
                'error_message': 'No code provided for complexity analysis',
                'tool_name': 'analyze_code_complexity'
            }
        
        # Calculate complexity metrics
        cyclomatic_complexity = _calculate_cyclomatic_complexity(code)
        cognitive_complexity = _calculate_cognitive_complexity(code)
        maintainability_index = _calculate_maintainability_index(code)
        nesting_depth = _calculate_nesting_depth(code)
        
        # Calculate code metrics
        lines_of_code = len(code.split('\n'))
        function_count = _count_functions(code, language)
        class_count = _count_classes(code, language)
        parameter_count = _count_parameters(code, language)
        
        # Build complexity analysis results
        complexity_result = {
            'status': 'success',
            'tool_name': 'analyze_code_complexity',
            'file_path': file_path,
            'language': language,
            'analysis_type': 'complexity_analysis',
            'metrics': {
                'cyclomatic_complexity': cyclomatic_complexity,
                'cognitive_complexity': cognitive_complexity,
                'maintainability_index': maintainability_index,
                'lines_of_code': lines_of_code,
                'function_count': function_count,
                'class_count': class_count,
                'nesting_depth': nesting_depth,
                'parameter_count': parameter_count
            },
            'quality_assessment': {
                'complexity_grade': _get_complexity_grade(cyclomatic_complexity),
                'maintainability_grade': _get_maintainability_grade(maintainability_index),
                'overall_score': _calculate_overall_score(cyclomatic_complexity, maintainability_index)
            },
            'recommendations': _generate_recommendations(
                cyclomatic_complexity, maintainability_index, nesting_depth, function_count
            ),
            'timestamp': time.time()
        }
        
        execution_time = time.time() - execution_start
        complexity_result['execution_time_seconds'] = execution_time
        
        # Store results in session state for other agents to access
        current_analysis = tool_context.state.get('complexity_analysis', {})
        current_analysis[file_path] = complexity_result
        tool_context.state['complexity_analysis'] = current_analysis
        
        # Update analysis progress
        analysis_progress = tool_context.state.get('analysis_progress', {})
        analysis_progress['complexity_analysis_completed'] = True
        analysis_progress['complexity_analysis_timestamp'] = time.time()
        tool_context.state['analysis_progress'] = analysis_progress
        
        return complexity_result
        
    except Exception as e:
        execution_time = time.time() - execution_start
        error_result = {
            'status': 'error',
            'tool_name': 'analyze_code_complexity',
            'error_message': str(e),
            'error_type': type(e).__name__,
            'execution_time_seconds': execution_time
        }
        
        # Store error in session state
        tool_context.state['complexity_analysis_error'] = error_result
        
        return error_result


def _calculate_cyclomatic_complexity(code: str) -> int:
    """Calculate basic cyclomatic complexity."""
    complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or', 'with']
    complexity = 1  # Base complexity
    
    for keyword in complexity_keywords:
        # Count keyword occurrences with proper word boundaries
        complexity += code.count(f' {keyword} ') + code.count(f'\n{keyword} ') + code.count(f'\t{keyword} ')
    
    return complexity


def _calculate_cognitive_complexity(code: str) -> int:
    """Calculate basic cognitive complexity."""
    nesting_penalty = _calculate_nesting_depth(code) * 2
    decision_points = code.count('if ') + code.count('for ') + code.count('while ') + code.count('try ')
    return decision_points + nesting_penalty


def _calculate_maintainability_index(code: str) -> float:
    """Calculate basic maintainability index."""
    lines = len(code.split('\n'))
    complexity = _calculate_cyclomatic_complexity(code)
    
    if lines == 0:
        return 100.0
    
    # Simplified maintainability index calculation
    maintainability = 100 - (complexity * 3) - (lines / 15)
    return max(0.0, min(100.0, maintainability))


def _calculate_nesting_depth(code: str) -> int:
    """Calculate maximum nesting depth."""
    max_depth = 0
    current_depth = 0
    
    for line in code.split('\n'):
        stripped = line.strip()
        # Calculate indentation level
        indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indentation
        
        if stripped.startswith(('if ', 'for ', 'while ', 'try:', 'with ', 'def ', 'class ')):
            current_depth = indent_level + 1
            max_depth = max(max_depth, current_depth)
    
    return max_depth


def _count_functions(code: str, language: str) -> int:
    """Count functions in the code."""
    if language.lower() == 'python':
        return code.count('def ')
    elif language.lower() in ['javascript', 'typescript']:
        return code.count('function ') + code.count(' => ')
    elif language.lower() == 'java':
        return code.count('public ') + code.count('private ') + code.count('protected ')
    else:
        return code.count('def ') + code.count('function ')


def _count_classes(code: str, language: str) -> int:
    """Count classes in the code."""
    if language.lower() == 'python':
        return code.count('class ')
    elif language.lower() == 'java':
        return code.count('class ') + code.count('interface ')
    else:
        return code.count('class ')


def _count_parameters(code: str, language: str) -> int:
    """Count total parameters across all functions."""
    function_lines = [line for line in code.split('\n') if 'def ' in line or 'function' in line]
    total_params = 0
    
    for line in function_lines:
        if '(' in line and ')' in line:
            params_section = line[line.find('('):line.find(')')]
            # Count commas + 1 if there are parameters
            param_count = params_section.count(',')
            if params_section.strip('()').strip():
                param_count += 1
            total_params += param_count
    
    return total_params


def _get_complexity_grade(complexity: int) -> str:
    """Get complexity grade based on cyclomatic complexity."""
    if complexity <= 5:
        return 'A'
    elif complexity <= 10:
        return 'B'
    elif complexity <= 15:
        return 'C'
    elif complexity <= 20:
        return 'D'
    else:
        return 'F'


def _get_maintainability_grade(maintainability: float) -> str:
    """Get maintainability grade based on maintainability index."""
    if maintainability >= 85:
        return 'A'
    elif maintainability >= 70:
        return 'B'
    elif maintainability >= 55:
        return 'C'
    elif maintainability >= 40:
        return 'D'
    else:
        return 'F'


def _calculate_overall_score(complexity: int, maintainability: float) -> float:
    """Calculate overall code quality score."""
    # Normalize complexity (lower is better)
    complexity_score = max(0, 100 - (complexity * 5))
    
    # Weighted average: 40% complexity, 60% maintainability
    overall = (complexity_score * 0.4) + (maintainability * 0.6)
    return round(overall, 2)


def _generate_recommendations(complexity: int, maintainability: float, nesting: int, functions: int) -> list:
    """Generate code improvement recommendations."""
    recommendations = []
    
    if complexity > 10:
        recommendations.append("Consider breaking down complex functions to reduce cyclomatic complexity")
    
    if maintainability < 70:
        recommendations.append("Improve code maintainability by adding comments and reducing complexity")
    
    if nesting > 4:
        recommendations.append("Reduce nesting depth by extracting nested logic into separate functions")
    
    if functions > 20:
        recommendations.append("Consider organizing functions into classes or modules for better structure")
    
    if not recommendations:
        recommendations.append("Code complexity is within acceptable limits")
    
    return recommendations