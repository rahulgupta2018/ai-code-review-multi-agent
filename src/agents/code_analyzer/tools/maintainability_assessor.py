"""
Maintainability Assessment Tool for Code Analysis
Enhanced with LLM-powered insights for better maintainability assessment
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from agents.base.tools.analysis_toolset import AnalysisToolset
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest

logger = logging.getLogger(__name__)


class MaintainabilityAssessor:
    """Assess code maintainability with multiple metrics and LLM insights"""
    
    def __init__(self):
        self.analysis_toolset = AnalysisToolset()
        self.llm_provider = None
        try:
            self.llm_provider = get_llm_provider()
        except Exception as e:
            logger.warning(f"LLM provider not available for maintainability assessment: {e}")
    
    async def assess_maintainability(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive maintainability assessment
        
        Args:
            file_path: Path to the code file
            content: Optional file content (will read from file if not provided)
        
        Returns:
            Dict containing maintainability metrics and insights
        """
        try:
            if content is None:
                content = Path(file_path).read_text(encoding='utf-8')
            
            # Basic maintainability metrics
            metrics = self._calculate_basic_metrics(content, file_path)
            
            # Code structure analysis
            structure_analysis = self._analyze_code_structure(content, file_path)
            
            # Naming conventions check
            naming_analysis = self._analyze_naming_conventions(content, file_path)
            
            # Documentation assessment
            documentation_analysis = self._assess_documentation(content, file_path)
            
            # Calculate overall maintainability score
            overall_score = self._calculate_overall_score(metrics, structure_analysis, naming_analysis, documentation_analysis)
            
            result = {
                'file_path': file_path,
                'maintainability_score': overall_score,
                'metrics': metrics,
                'structure_analysis': structure_analysis,
                'naming_analysis': naming_analysis,
                'documentation_analysis': documentation_analysis,
                'recommendations': self._generate_recommendations(metrics, structure_analysis, naming_analysis, documentation_analysis)
            }
            
            # Add LLM-enhanced insights if available
            if self.llm_provider:
                try:
                    llm_insights = await self._generate_llm_insights(result, content)
                    result['llm_insights'] = llm_insights
                except Exception as e:
                    logger.warning(f"Failed to generate LLM insights: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in maintainability assessment for {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'maintainability_score': 0.0
            }
    
    def _calculate_basic_metrics(self, content: str, file_path: str) -> Dict[str, Any]:
        """Calculate basic maintainability metrics"""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Basic counts
        total_lines = len(lines)
        code_lines = len(non_empty_lines)
        comment_lines = len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')])
        
        # Calculate ratios
        comment_ratio = comment_lines / max(code_lines, 1)
        
        # Function/method count estimation
        function_count = len([line for line in lines if 'def ' in line or 'function ' in line])
        
        # Class count estimation
        class_count = len([line for line in lines if 'class ' in line])
        
        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'comment_ratio': round(comment_ratio, 3),
            'function_count': function_count,
            'class_count': class_count,
            'avg_lines_per_function': round(code_lines / max(function_count, 1), 2)
        }
    
    def _analyze_code_structure(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code structure for maintainability"""
        lines = content.split('\n')
        
        # Analyze indentation consistency
        indentation_levels = []
        for line in lines:
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indentation_levels.append(leading_spaces)
        
        # Check for consistent indentation
        consistent_indentation = len(set(indentation_levels)) <= 10  # Reasonable threshold
        
        # Long lines detection
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
        
        # Nested complexity estimation
        max_nesting = 0
        current_nesting = 0
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if ', 'for ', 'while ', 'with ', 'try:']):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped.startswith(('else', 'elif', 'except', 'finally')):
                continue
            elif not stripped or stripped.startswith('#'):
                continue
            else:
                # Rough estimation of nesting decrease
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces == 0:
                    current_nesting = 0
        
        return {
            'consistent_indentation': consistent_indentation,
            'long_lines_count': len(long_lines),
            'long_lines': long_lines[:10],  # First 10 long lines
            'max_nesting_level': max_nesting,
            'structure_score': self._calculate_structure_score(consistent_indentation, len(long_lines), max_nesting)
        }
    
    def _analyze_naming_conventions(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze naming conventions"""
        import re
        
        # Extract identifiers
        function_names = re.findall(r'def\s+(\w+)', content)
        class_names = re.findall(r'class\s+(\w+)', content)
        variable_names = re.findall(r'(\w+)\s*=', content)
        
        # Check naming conventions
        snake_case_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')
        pascal_case_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
        camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
        
        function_naming_score = sum(1 for name in function_names if snake_case_pattern.match(name)) / max(len(function_names), 1)
        class_naming_score = sum(1 for name in class_names if pascal_case_pattern.match(name)) / max(len(class_names), 1)
        
        return {
            'function_count': len(function_names),
            'class_count': len(class_names),
            'function_naming_score': round(function_naming_score, 3),
            'class_naming_score': round(class_naming_score, 3),
            'overall_naming_score': round((function_naming_score + class_naming_score) / 2, 3)
        }
    
    def _assess_documentation(self, content: str, file_path: str) -> Dict[str, Any]:
        """Assess code documentation quality"""
        lines = content.split('\n')
        
        # Count docstrings
        docstring_count = content.count('"""') // 2 + content.count("'''") // 2
        
        # Function documentation ratio
        function_count = len([line for line in lines if 'def ' in line])
        
        # Class documentation ratio
        class_count = len([line for line in lines if 'class ' in line])
        
        # Inline comments
        inline_comments = len([line for line in lines if '#' in line])
        
        # Calculate documentation score
        total_documentable = function_count + class_count
        documentation_ratio = docstring_count / max(total_documentable, 1)
        
        return {
            'docstring_count': docstring_count,
            'function_count': function_count,
            'class_count': class_count,
            'inline_comments': inline_comments,
            'documentation_ratio': round(documentation_ratio, 3),
            'documentation_score': min(documentation_ratio, 1.0)
        }
    
    def _calculate_structure_score(self, consistent_indentation: bool, long_lines_count: int, max_nesting: int) -> float:
        """Calculate structure quality score"""
        score = 1.0
        
        if not consistent_indentation:
            score -= 0.2
        
        # Penalize long lines
        if long_lines_count > 0:
            score -= min(0.3, long_lines_count * 0.02)
        
        # Penalize deep nesting
        if max_nesting > 4:
            score -= min(0.3, (max_nesting - 4) * 0.1)
        
        return max(0.0, score)
    
    def _calculate_overall_score(self, metrics: Dict, structure: Dict, naming: Dict, documentation: Dict) -> float:
        """Calculate overall maintainability score"""
        # Weight different aspects
        structure_weight = 0.3
        naming_weight = 0.2
        documentation_weight = 0.2
        metrics_weight = 0.3
        
        # Normalize metrics score
        comment_score = min(metrics['comment_ratio'] * 2, 1.0)  # Target 50% comment ratio
        function_size_score = max(0, 1.0 - (metrics['avg_lines_per_function'] - 20) / 50)  # Penalize functions > 20 lines
        metrics_score = (comment_score + function_size_score) / 2
        
        overall_score = (
            structure['structure_score'] * structure_weight +
            naming['overall_naming_score'] * naming_weight +
            documentation['documentation_score'] * documentation_weight +
            metrics_score * metrics_weight
        )
        
        return round(overall_score, 3)
    
    def _generate_recommendations(self, metrics: Dict, structure: Dict, naming: Dict, documentation: Dict) -> List[str]:
        """Generate maintainability improvement recommendations"""
        recommendations = []
        
        # Structure recommendations
        if not structure['consistent_indentation']:
            recommendations.append("Standardize indentation (use 4 spaces consistently)")
        
        if structure['long_lines_count'] > 0:
            recommendations.append(f"Break down {structure['long_lines_count']} long lines (>100 characters)")
        
        if structure['max_nesting_level'] > 4:
            recommendations.append("Reduce nesting complexity by extracting methods or using early returns")
        
        # Documentation recommendations
        if documentation['documentation_ratio'] < 0.5:
            recommendations.append("Add docstrings to functions and classes")
        
        if metrics['comment_ratio'] < 0.1:
            recommendations.append("Add more inline comments to explain complex logic")
        
        # Function size recommendations
        if metrics['avg_lines_per_function'] > 30:
            recommendations.append("Consider breaking down large functions into smaller ones")
        
        # Naming recommendations
        if naming['function_naming_score'] < 0.8:
            recommendations.append("Use snake_case for function names")
        
        if naming['class_naming_score'] < 0.8:
            recommendations.append("Use PascalCase for class names")
        
        return recommendations
    
    async def _generate_llm_insights(self, analysis_result: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Generate LLM-powered maintainability insights"""
        if not self.llm_provider:
            return {}
        
        # Prepare analysis summary for LLM
        summary = f"""
        Code Maintainability Analysis:
        - Overall Score: {analysis_result['maintainability_score']}
        - Lines of Code: {analysis_result['metrics']['code_lines']}
        - Functions: {analysis_result['metrics']['function_count']}
        - Classes: {analysis_result['metrics']['class_count']}
        - Comment Ratio: {analysis_result['metrics']['comment_ratio']}
        - Documentation Score: {analysis_result['documentation_analysis']['documentation_score']}
        - Structure Issues: {len(analysis_result['recommendations'])} identified
        """
        
        prompt = f"""
        As a senior software engineer, analyze this code maintainability report and provide:
        1. Key maintainability strengths
        2. Critical areas for improvement
        3. Specific refactoring suggestions
        4. Long-term maintenance considerations
        
        Analysis Data:
        {summary}
        
        Provide actionable insights focused on improving code maintainability.
        """
        
        try:
            request = LLMRequest(
                prompt=prompt,
                system_prompt="You are a senior software engineer focused on code maintainability and best practices.",
                temperature=0.1,
                max_tokens=1024
            )
            
            response = await self.llm_provider.generate_response(request)
            
            return {
                'llm_summary': response.content,
                'confidence': getattr(response, 'confidence', 0.8),
                'provider': self.llm_provider.__class__.__name__
            }
            
        except Exception as e:
            logger.warning(f"Failed to generate LLM insights: {e}")
            return {'error': str(e)}


async def maintainability_assessment(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Maintainability assessment function for Google ADK integration
    
    Args:
        file_path: Path to the code file
        content: Optional file content
    
    Returns:
        Comprehensive maintainability assessment results
    """
    assessor = MaintainabilityAssessor()
    return await assessor.assess_maintainability(file_path, content)

# Create assessor instance for tool functions
_maintainability_assessor = MaintainabilityAssessor()

def maintainability_assessor_tool(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """Assess code maintainability with detailed qualitative analysis"""
    import asyncio
    return asyncio.run(_maintainability_assessor.assess_maintainability(file_path, content))

# Backward compatibility wrapper
async def enhanced_maintainability_analysis(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatibility wrapper for maintainability_assessment"""
    return await maintainability_assessment(file_path, content)


# Export for tool registration
__all__ = ['MaintainabilityAssessor', 'maintainability_assessment', 'maintainability_assessor_tool', 'enhanced_maintainability_analysis']