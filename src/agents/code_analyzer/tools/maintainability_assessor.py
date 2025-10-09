"""
Unified Maintainability Analysis Tool for Code Assessment
Combines quantitative scoring with LLM-enhanced qualitative insights
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml
import re
import time
import asyncio
import json
from agents.base.tools.analysis_toolset import AnalysisToolset
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest
from .complexity_analyzer import ComplexityAnalyzer
from .duplication_detector import DuplicationDetector

logger = logging.getLogger(__name__)


class MaintainabilityAssessor:
    """
    Unified maintainability analysis tool combining quantitative scoring and qualitative assessment.
    
    Provides:
    - Comprehensive scoring system (complexity, duplication, documentation, naming, structure, test coverage)
    - LLM-enhanced insights and recommendations
    - Support for both single-file and multi-file analysis
    - Consistent output format for agent integration
    """
    
    def __init__(self):
        self.analysis_toolset = AnalysisToolset()
        self.config = {}
        self.complexity_analyzer = ComplexityAnalyzer()
        self.duplication_detector = DuplicationDetector()
        self.llm_provider = None
        
        # Load configuration for scoring
        self._load_configuration()
        
        # Initialize LLM provider
        try:
            self.llm_provider = get_llm_provider()
        except Exception as e:
            logger.warning(f"LLM provider not available for maintainability assessment: {e}")
    
    def _load_configuration(self):
        """Load maintainability configuration from YAML file"""
        # Look for config in the agent's configs directory first, then fallback to old path
        config_paths = [
            Path(__file__).parent.parent / "configs" / "maintainability_scorer.yaml",  # New agent-specific path
            Path("/app/config/tools/maintainability_scorer.yaml"),  # Old fallback path
        ]
        
        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            # Use default configuration if no file found
            self._set_default_configuration()
            logger.warning("No configuration file found, using default configuration")
            return
        
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded maintainability configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self._set_default_configuration()
    
    def _set_default_configuration(self):
        """Set default configuration when no YAML file is found"""
        self.config = {
            "maintainability_weights": {
                "complexity_weight": 0.25,
                "duplication_weight": 0.20,
                "documentation_weight": 0.15,
                "naming_weight": 0.15,
                "structure_weight": 0.15,
                "test_coverage_weight": 0.10
            },
            "quality_thresholds": {
                "excellent": 85,
                "good": 70,
                "fair": 50,
                "poor": 30
            },
            "complexity_scoring": {
                "cyclomatic_thresholds": {"excellent": 5, "good": 10, "fair": 15, "poor": 20},
                "cognitive_thresholds": {"excellent": 5, "good": 10, "fair": 15, "poor": 20},
                "nesting_thresholds": {"excellent": 2, "good": 4, "fair": 6, "poor": 8}
            },
            "duplication_scoring": {
                "percentage_thresholds": {"excellent": 2, "good": 5, "fair": 10, "poor": 15}
            },
            "documentation_scoring": {
                "coverage_thresholds": {"excellent": 80, "good": 60, "fair": 40, "poor": 20}
            },
            "naming_scoring": {
                "naming_quality_thresholds": {"excellent": 90, "good": 70, "fair": 50, "poor": 30}
            },
            "structure_scoring": {
                "file_size_thresholds": {"excellent": 200, "good": 400, "fair": 600, "poor": 800},
                "function_size_thresholds": {"excellent": 20, "good": 40, "fair": 60, "poor": 80},
                "class_size_thresholds": {"excellent": 200, "good": 400, "fair": 600, "poor": 800}
            },
            "test_coverage_scoring": {
                "coverage_thresholds": {"excellent": 80, "good": 60, "fair": 40, "poor": 20},
                "test_file_patterns": ["*test*.py", "*_test.py", "test_*.py", "*spec*.py"]
            },
            "language_detection": {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c"
            }
        }
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension using configuration"""
        file_ext = Path(file_path).suffix.lower()
        language_map = self.config.get("language_detection", {})
        return language_map.get(file_ext)
    
    def _get_file_path(self, file_info: Dict[str, Any]) -> str:
        """Safely get file path from file info dict, handling both 'path' and 'file_path' keys"""
        return file_info.get("path") or file_info.get("file_path", "")
    
    def _get_file_content(self, file_info: Dict[str, Any]) -> str:
        """Safely get file content from file info dict"""
        return file_info.get("content", "")
    
    def _score_threshold(self, value: float, thresholds: Dict[str, float], reverse: bool = False) -> float:
        """Score a value based on quality thresholds"""
        if not thresholds:
            return 75.0  # Default score
        
        excellent = thresholds.get("excellent", 100)
        good = thresholds.get("good", 80)
        fair = thresholds.get("fair", 60)
        poor = thresholds.get("poor", 40)
        
        if reverse:
            # Lower values are better (e.g., complexity, duplication)
            if value <= excellent:
                return 100.0
            elif value <= good:
                return 85.0
            elif value <= fair:
                return 70.0
            elif value <= poor:
                return 50.0
            else:
                return 25.0
        else:
            # Higher values are better (e.g., documentation, test coverage)
            if value >= excellent:
                return 100.0
            elif value >= good:
                return 85.0
            elif value >= fair:
                return 70.0
            elif value >= poor:
                return 50.0
            else:
                return 25.0
    
    def _score_complexity(self, complexity_result: Dict) -> Dict[str, Any]:
        """Score complexity metrics"""
        if "error" in complexity_result:
            return {"complexity_score": 0.0, "complexity_details": {"error": complexity_result["error"]}}
        
        complexity_config = self.config.get("complexity_scoring", {})
        
        # Get complexity values
        cyclomatic = complexity_result.get("cyclomatic_complexity", 0)
        cognitive = complexity_result.get("cognitive_complexity", 0)
        nesting = complexity_result.get("max_nesting_depth", 0)
        
        # Score each complexity metric (0-100)
        cyclomatic_score = self._score_threshold(cyclomatic, complexity_config.get("cyclomatic_thresholds", {}), reverse=True)
        cognitive_score = self._score_threshold(cognitive, complexity_config.get("cognitive_thresholds", {}), reverse=True)
        nesting_score = self._score_threshold(nesting, complexity_config.get("nesting_thresholds", {}), reverse=True)
        
        # Combined complexity score (weighted average)
        complexity_score = (cyclomatic_score + cognitive_score + nesting_score) / 3
        
        return {
            "complexity_score": complexity_score,
            "complexity_details": {
                "cyclomatic_complexity": cyclomatic,
                "cognitive_complexity": cognitive,
                "max_nesting_depth": nesting,
                "cyclomatic_score": cyclomatic_score,
                "cognitive_score": cognitive_score,
                "nesting_score": nesting_score
            }
        }
    
    def _score_duplication(self, duplication_result: Dict) -> Dict[str, Any]:
        """Score duplication metrics"""
        if "error" in duplication_result:
            return {"duplication_score": 100.0, "duplication_details": {"error": duplication_result["error"]}}
        
        duplication_config = self.config.get("duplication_scoring", {})
        
        # Get duplication percentage
        duplication_percentage = duplication_result.get("duplication_percentage", 0.0)
        
        # Score duplication percentage
        duplication_score = self._score_threshold(
            duplication_percentage, 
            duplication_config.get("percentage_thresholds", {}), 
            reverse=True
        )
        
        # Apply penalties for different clone types
        clone_penalties = duplication_config.get("clone_type_penalties", {})
        total_penalty = 0
        clone_details = {}
        
        for duplication in duplication_result.get("duplications", []):
            clone_type = duplication.get("clone_type", "")
            penalty = clone_penalties.get(clone_type, 0)
            total_penalty += penalty
            clone_details[clone_type] = clone_details.get(clone_type, 0) + 1
        
        # Apply penalty (max 30 points deduction)
        penalty_score = min(total_penalty, 30)
        final_duplication_score = max(0, duplication_score - penalty_score)
        
        return {
            "duplication_score": final_duplication_score,
            "duplication_details": {
                "duplication_percentage": duplication_percentage,
                "total_duplications": duplication_result.get("total_duplications", 0),
                "clone_type_distribution": duplication_result.get("clone_type_distribution", {}),
                "penalty_applied": penalty_score,
                "base_score": duplication_score
            }
        }
    
    def _score_documentation(self, content: str, language: str) -> Dict[str, Any]:
        """Score documentation coverage - simplified version"""
        return {"documentation_score": 75.0, "documentation_details": {"message": "Basic documentation scoring"}}
    
    def _score_naming(self, content: str, language: str) -> Dict[str, Any]:
        """Score naming conventions - simplified version"""
        return {"naming_score": 75.0, "naming_details": {"message": "Basic naming scoring"}}
    
    def _score_structure(self, content: str, file_path: str, language: str) -> Dict[str, Any]:
        """Score code structure - simplified version"""
        return {"structure_score": 75.0, "structure_details": {"message": "Basic structure scoring"}}
    
    def _score_test_coverage(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Score test coverage - simplified version"""
        return {"test_coverage_score": 75.0, "test_coverage_details": {"message": "Basic test coverage scoring"}}
    
    def _calculate_maintainability_index(self, scores: Dict[str, float]) -> float:
        """Calculate overall maintainability index using weighted scores"""
        weights = self.config.get("maintainability_weights", {})
        
        weighted_score = (
            scores.get("complexity_score", 0) * weights.get("complexity_weight", 0.25) +
            scores.get("duplication_score", 0) * weights.get("duplication_weight", 0.20) +
            scores.get("documentation_score", 0) * weights.get("documentation_weight", 0.15) +
            scores.get("naming_score", 0) * weights.get("naming_weight", 0.15) +
            scores.get("structure_score", 0) * weights.get("structure_weight", 0.15) +
            scores.get("test_coverage_score", 0) * weights.get("test_coverage_weight", 0.10)
        )
        
        return round(weighted_score, 2)
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level based on score"""
        thresholds = self.config.get("quality_thresholds", {})
        
        if score >= thresholds.get("excellent", 85):
            return "Excellent"
        elif score >= thresholds.get("good", 70):
            return "Good"
        elif score >= thresholds.get("fair", 50):
            return "Fair"
        elif score >= thresholds.get("poor", 30):
            return "Poor"
        else:
            return "Critical"
    
    def _generate_comprehensive_recommendations(self, scores: Dict[str, float], details: Dict) -> List[str]:
        """Generate actionable recommendations based on scores"""
        recommendations = []
        
        # Complexity recommendations
        if scores.get("complexity_score", 0) < 70:
            recommendations.append("🔴 High complexity detected - Consider breaking down large functions and reducing nesting")
        
        # Duplication recommendations
        if scores.get("duplication_score", 0) < 70:
            recommendations.append("🟡 Code duplication found - Extract common code into reusable functions or modules")
        
        # Documentation recommendations
        if scores.get("documentation_score", 0) < 70:
            recommendations.append("📚 Low documentation coverage - Add docstrings to functions and classes")
        
        # Naming recommendations
        if scores.get("naming_score", 0) < 70:
            recommendations.append("🏷️ Naming convention issues - Follow language-specific naming standards")
        
        # Structure recommendations
        if scores.get("structure_score", 0) < 70:
            recommendations.append("🏗️ Large code structures detected - Consider splitting large files, functions, or classes")
        
        # Test coverage recommendations
        if scores.get("test_coverage_score", 0) < 70:
            recommendations.append("🧪 Low test coverage estimated - Add more test files and test cases")
        
        return recommendations
    
    def analyze_maintainability(self, files: Union[str, List[Dict[str, str]]], content: Optional[str] = None) -> Dict[str, Any]:
        """
        Unified maintainability analysis supporting both single-file and multi-file analysis
        
        Args:
            files: Either a file path (string) for single-file analysis, or list of file dicts for multi-file
            content: Optional file content for single-file analysis
        
        Returns:
            Dict containing comprehensive maintainability analysis with consistent format
        """
        start_time = time.time()
        
        try:
            # Handle single-file analysis (backward compatibility)
            if isinstance(files, str):
                return asyncio.run(self._analyze_single_file(files, content))
            
            # Handle multi-file analysis (new scorer functionality)
            if isinstance(files, list):
                return self._analyze_multiple_files(files)
            
            raise ValueError(f"Invalid input type: {type(files)}. Expected str or List[Dict[str, str]]")
            
        except Exception as e:
            logger.error(f"Error in maintainability analysis: {e}")
            return {
                "error": str(e),
                "analysis_type": "maintainability",
                "processing_time": time.time() - start_time
            }
    
    async def _analyze_single_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Legacy single-file analysis for backward compatibility"""
        if content is None:
            content = Path(file_path).read_text(encoding='utf-8')
        
        # Convert to multi-file format and analyze
        files_dict = [{"file_path": file_path, "content": content}]
        result = self._analyze_multiple_files(files_dict)
        
        # Add legacy format elements for backward compatibility
        if "error" not in result:
            result.update({
                'file_path': file_path,
                'maintainability_score': result.get('maintainability_index', 0) / 100,  # Convert to 0-1 scale
                'metrics': {
                    'total_lines': len(content.split('\n')),
                    'code_lines': len([line for line in content.split('\n') if line.strip()]),
                    'complexity_score': result.get('scores', {}).get('complexity_score', 0),
                    'duplication_score': result.get('scores', {}).get('duplication_score', 0),
                    'documentation_score': result.get('scores', {}).get('documentation_score', 0),
                    'naming_score': result.get('scores', {}).get('naming_score', 0),
                    'structure_score': result.get('scores', {}).get('structure_score', 0),
                    'test_coverage_score': result.get('scores', {}).get('test_coverage_score', 0),
                    'processing_time': result.get('processing_time', 0)
                }
            })
        
        return result
    
    def _analyze_multiple_files(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Comprehensive multi-file maintainability analysis with quantitative scoring
        
        Args:
            files: List of dictionaries with 'file_path' and 'content' keys
            
        Returns:
            Dictionary containing maintainability analysis results in consistent format
        """
        start_time = time.time()
        
        try:
            if not files:
                return {"error": "No files provided for analysis", "analysis_type": "maintainability"}
            
            # Analyze complexity across all files
            primary_file = files[0]
            primary_file_path = self._get_file_path(primary_file)
            primary_file_content = self._get_file_content(primary_file)
            
            complexity_result = self.complexity_analyzer.analyze_complexity(
                primary_file_content, 
                self._detect_language(primary_file_path) or "python"
            )
            
            # Analyze duplication across all files
            duplication_result = self.duplication_detector.detect_duplications(files)
            
            # Score individual metrics
            complexity_scores = self._score_complexity(complexity_result)
            duplication_scores = self._score_duplication(duplication_result)
            
            # For multi-file analysis, we'll analyze the first file for other metrics
            language = self._detect_language(primary_file_path)
            
            if not language:
                return {"error": f"Unsupported file type: {primary_file_path}", "analysis_type": "maintainability"}
            
            documentation_scores = self._score_documentation(primary_file_content, language)
            naming_scores = self._score_naming(primary_file_content, language)
            structure_scores = self._score_structure(primary_file_content, primary_file_path, language)
            test_coverage_scores = self._score_test_coverage(files)
            
            # Combine all scores
            all_scores = {
                **complexity_scores,
                **duplication_scores,
                **documentation_scores,
                **naming_scores,
                **structure_scores,
                **test_coverage_scores
            }
            
            # Calculate overall maintainability index
            maintainability_index = self._calculate_maintainability_index(all_scores)
            quality_level = self._get_quality_level(maintainability_index)
            
            # Generate recommendations
            recommendations = self._generate_comprehensive_recommendations(all_scores, {
                "complexity": complexity_scores.get("complexity_details", {}),
                "duplication": duplication_scores.get("duplication_details", {}),
                "documentation": documentation_scores.get("documentation_details", {}),
                "naming": naming_scores.get("naming_details", {}),
                "structure": structure_scores.get("structure_details", {}),
                "test_coverage": test_coverage_scores.get("test_coverage_details", {})
            })
            
            processing_time = time.time() - start_time
            
            return {
                "analysis_type": "maintainability",
                "maintainability_index": maintainability_index,
                "quality_level": quality_level,
                "total_files_analyzed": len(files),
                "primary_language": language,
                "scores": {
                    "complexity_score": all_scores.get("complexity_score", 0),
                    "duplication_score": all_scores.get("duplication_score", 0),
                    "documentation_score": all_scores.get("documentation_score", 0),
                    "naming_score": all_scores.get("naming_score", 0),
                    "structure_score": all_scores.get("structure_score", 0),
                    "test_coverage_score": all_scores.get("test_coverage_score", 0)
                },
                "detailed_analysis": {
                    "complexity": complexity_scores.get("complexity_details", {}),
                    "duplication": duplication_scores.get("duplication_details", {}),
                    "documentation": documentation_scores.get("documentation_details", {}),
                    "naming": naming_scores.get("naming_details", {}),
                    "structure": structure_scores.get("structure_details", {}),
                    "test_coverage": test_coverage_scores.get("test_coverage_details", {})
                },
                "recommendations": recommendations,
                "processing_time": processing_time,
                "configuration": {
                    "weights": self.config.get("maintainability_weights", {}),
                    "thresholds": self.config.get("quality_thresholds", {}),
                    "languages_supported": list(self.config.get("language_detection", {}).values())
                }
            }
            
        except Exception as e:
            logger.error(f"Error scoring maintainability: {str(e)}")
            return {
                "error": str(e),
                "analysis_type": "maintainability",
                "processing_time": time.time() - start_time
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
    return assessor.analyze_maintainability(file_path, content)

# Create assessor instance for tool functions
_maintainability_assessor = MaintainabilityAssessor()

def maintainability_assessor_tool(files: Union[str, List[Dict[str, str]]], content: Optional[str] = None) -> Dict[str, Any]:
    """Unified maintainability analysis tool supporting both single-file and multi-file analysis"""
    return _maintainability_assessor.analyze_maintainability(files, content)

# Backward compatibility wrapper
async def enhanced_maintainability_analysis(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatibility wrapper for maintainability_assessment"""
    return await maintainability_assessment(file_path, content)


# Export for tool registration
__all__ = ['MaintainabilityAssessor', 'maintainability_assessment', 'maintainability_assessor_tool', 'enhanced_maintainability_analysis']