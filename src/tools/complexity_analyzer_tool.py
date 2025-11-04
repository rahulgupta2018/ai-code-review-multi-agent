"""
Complexity Analyzer Tool Implementation for ADK Code Review System.

This tool provides code complexity analysis capabilities.
"""

import time
from typing import Dict, Any, Optional


class ComplexityAnalyzerTool:
    """Code complexity analysis tool."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **parameters):
        """Initialize the complexity analyzer tool with configuration."""
        self.config = config or {}
        self.parameters = parameters
        self.name = "ComplexityAnalyzerTool"
        self.description = "Code complexity analysis and metrics calculation"
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complexity analysis on the provided code context."""
        execution_start = time.time()
        
        try:
            # Extract code and language from context
            code = context.get('code', context.get('test_code', ''))
            language = context.get('language', 'python')
            
            if not code:
                return {
                    'status': 'error',
                    'error_message': 'No code provided for analysis',
                    'tool_name': self.name
                }
            
            # Calculate basic complexity metrics
            complexity_result = {
                'status': 'success',
                'tool_name': self.name,
                'language': language,
                'analysis_type': 'complexity_analysis',
                'results': {
                    'cyclomatic_complexity': self._calculate_cyclomatic_complexity(code),
                    'cognitive_complexity': self._calculate_cognitive_complexity(code),
                    'maintainability_index': self._calculate_maintainability_index(code),
                    'lines_of_code': len(code.split('\n')),
                    'code_metrics': {
                        'function_count': self._count_functions(code, language),
                        'class_count': self._count_classes(code, language),
                        'nesting_depth': self._calculate_nesting_depth(code),
                        'parameter_count': self._count_parameters(code, language)
                    }
                },
                'thresholds': {
                    'complexity_threshold': self.parameters.get('complexity_threshold', 10),
                    'maintainability_threshold': self.config.get('maintainability_threshold', 70)
                },
                'metadata': {
                    'tool_version': '1.0.0',
                    'analysis_timestamp': time.time(),
                    'configuration': self.config,
                    'parameters': self.parameters
                }
            }
            
            execution_time = time.time() - execution_start
            complexity_result['execution_time_seconds'] = execution_time
            
            return complexity_result
            
        except Exception as e:
            execution_time = time.time() - execution_start
            return {
                'status': 'error',
                'tool_name': self.name,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'execution_time_seconds': execution_time
            }
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculate basic cyclomatic complexity."""
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            complexity += code.count(f' {keyword} ') + code.count(f'\n{keyword} ')
        
        return complexity
    
    def _calculate_cognitive_complexity(self, code: str) -> int:
        """Calculate basic cognitive complexity."""
        # Simple heuristic for cognitive complexity
        nesting_penalty = self._calculate_nesting_depth(code) * 2
        decision_points = code.count('if ') + code.count('for ') + code.count('while ')
        return decision_points + nesting_penalty
    
    def _calculate_maintainability_index(self, code: str) -> float:
        """Calculate basic maintainability index."""
        lines = len(code.split('\n'))
        complexity = self._calculate_cyclomatic_complexity(code)
        
        # Simplified maintainability index calculation
        if lines == 0:
            return 100.0
        
        maintainability = 100 - (complexity * 2) - (lines / 10)
        return max(0.0, min(100.0, maintainability))
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.endswith(':') and any(keyword in stripped for keyword in ['if', 'for', 'while', 'try', 'def', 'class']):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif stripped in ['', 'pass'] or stripped.startswith('#'):
                continue
            elif len(line) - len(line.lstrip()) == 0 and stripped:
                current_depth = 0
        
        return max_depth
    
    def _count_functions(self, code: str, language: str) -> int:
        """Count functions in the code."""
        if language.lower() == 'python':
            return code.count('def ')
        elif language.lower() in ['javascript', 'typescript']:
            return code.count('function ') + code.count('=>')
        elif language.lower() == 'java':
            return code.count('public ') + code.count('private ') + code.count('protected ')
        else:
            return code.count('def ') + code.count('function ')
    
    def _count_classes(self, code: str, language: str) -> int:
        """Count classes in the code."""
        if language.lower() == 'python':
            return code.count('class ')
        elif language.lower() == 'java':
            return code.count('class ') + code.count('interface ')
        else:
            return code.count('class ')
    
    def _count_parameters(self, code: str, language: str) -> int:
        """Count total parameters across all functions."""
        # Simple heuristic: count commas in function definitions
        function_lines = [line for line in code.split('\n') if 'def ' in line or 'function' in line]
        total_params = 0
        
        for line in function_lines:
            if '(' in line and ')' in line:
                params_section = line[line.find('('):line.find(')')]
                total_params += params_section.count(',') + (1 if params_section.strip('()').strip() else 0)
        
        return total_params