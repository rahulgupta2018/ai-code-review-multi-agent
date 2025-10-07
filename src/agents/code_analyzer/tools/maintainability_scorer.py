"""
Maintainability Scorer Tool for Google ADK
Holistic code quality scoring combining complexity, duplication, and other metrics with LLM enhancement
"""

from google.adk.tools import FunctionTool
from typing import Any, Dict, List, Optional, Union
import logging
import yaml
import re
import time
import asyncio
import json
from pathlib import Path
from .complexity_analyzer import ComplexityAnalyzer
from .duplication_detector import DuplicationDetector

# LLM provider integration
from agents.base.tools.llm_provider import get_llm_provider, LLMRequest

logger = logging.getLogger(__name__)


class MaintainabilityScorer:
    """
    Holistic maintainability scoring tool that combines multiple quality metrics.
    
    Analyzes:
    - Code complexity (cyclomatic, cognitive, nesting)
    - Code duplication (across files)
    - Documentation coverage and quality
    - Naming conventions compliance
    - Code structure (file/function/class sizes)
    - Test coverage estimation
    
    Provides weighted scoring and actionable recommendations.
    """
    
    def __init__(self):
        self.config = {}
        self.complexity_analyzer = ComplexityAnalyzer()
        self.duplication_detector = DuplicationDetector()
        self._load_configuration()
        
    def _load_configuration(self):
        """Load maintainability scorer configuration from YAML file"""
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
            raise FileNotFoundError(f"Configuration file not found in any of these locations: {[str(p) for p in config_paths]}")
        
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded maintainability scorer configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension using configuration"""
        file_ext = Path(file_path).suffix.lower()
        language_map = self.config.get("language_detection", {})
        return language_map.get(file_ext)
    
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
        """Score documentation coverage and quality"""
        doc_config = self.config.get("documentation_scoring", {})
        
        # Count documentation elements
        docstring_count = self._count_docstrings(content, language)
        comment_count = self._count_comments(content)
        
        # Estimate documentation coverage
        total_functions = len(re.findall(self._get_function_pattern(language), content))
        total_classes = len(re.findall(self._get_class_pattern(language), content))
        total_elements = total_functions + total_classes
        
        if total_elements == 0:
            coverage = 100.0  # No functions/classes to document
        else:
            coverage = min(100.0, (docstring_count / total_elements) * 100)
        
        # Score based on coverage thresholds
        doc_score = self._score_threshold(coverage, doc_config.get("coverage_thresholds", {}))
        
        # Quality assessment
        quality_indicators = self._assess_documentation_quality(content, language)
        quality_bonus = len(quality_indicators) * 2  # Up to 10 point bonus
        
        final_doc_score = min(100.0, doc_score + quality_bonus)
        
        return {
            "documentation_score": final_doc_score,
            "documentation_details": {
                "coverage_percentage": coverage,
                "docstring_count": docstring_count,
                "comment_count": comment_count,
                "total_elements": total_elements,
                "quality_indicators": quality_indicators,
                "base_score": doc_score,
                "quality_bonus": quality_bonus
            }
        }
    
    def _score_naming(self, content: str, language: str) -> Dict[str, Any]:
        """Score naming convention compliance"""
        naming_config = self.config.get("naming_scoring", {})
        conventions = naming_config.get("convention_checks", {}).get(language, {})
        
        if not conventions:
            return {"naming_score": 75.0, "naming_details": {"message": "No naming conventions defined for language"}}
        
        violations = 0
        total_names = 0
        violation_details = {}
        
        # Check function names
        functions = re.findall(self._get_function_pattern(language), content)
        for func_match in functions:
            func_name = self._extract_function_name(func_match, language)
            if func_name:
                total_names += 1
                expected_style = conventions.get("functions", "")
                if not self._check_naming_style(func_name, expected_style):
                    violations += 1
                    violation_details.setdefault("functions", []).append(func_name)
        
        # Check class names
        classes = re.findall(self._get_class_pattern(language), content)
        for class_match in classes:
            class_name = self._extract_class_name(class_match, language)
            if class_name:
                total_names += 1
                expected_style = conventions.get("classes", "")
                if not self._check_naming_style(class_name, expected_style):
                    violations += 1
                    violation_details.setdefault("classes", []).append(class_name)
        
        # Check variable names (basic heuristic)
        variable_pattern = self.config.get("regex_patterns", {}).get("variable_patterns", {}).get("assignment", r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=')
        variables = re.findall(variable_pattern, content)
        for var_name in variables[:10]:  # Limit to first 10 to avoid noise
            if var_name not in ['self', 'this', 'super']:
                total_names += 1
                expected_style = conventions.get("variables", "")
                if not self._check_naming_style(var_name, expected_style):
                    violations += 1
                    violation_details.setdefault("variables", []).append(var_name)
        
        # Calculate compliance percentage
        if total_names == 0:
            compliance = 100.0
        else:
            compliance = ((total_names - violations) / total_names) * 100
        
        # Score based on compliance
        naming_score = self._score_threshold(compliance, naming_config.get("naming_quality_thresholds", {}))
        
        return {
            "naming_score": naming_score,
            "naming_details": {
                "compliance_percentage": compliance,
                "total_names_checked": total_names,
                "violations": violations,
                "violation_details": violation_details,
                "conventions_used": conventions
            }
        }
    
    def _score_structure(self, content: str, file_path: str, language: str) -> Dict[str, Any]:
        """Score code structure (file, function, class sizes)"""
        structure_config = self.config.get("structure_scoring", {})
        
        # File size scoring
        line_count = len(content.split('\n'))
        file_score = self._score_threshold(
            line_count, 
            structure_config.get("file_size_thresholds", {}), 
            reverse=True
        )
        
        # Function size scoring
        functions = re.findall(self._get_function_pattern(language), content, re.MULTILINE | re.DOTALL)
        function_scores = []
        large_functions = []
        
        for func_match in functions:
            func_lines = len(func_match.split('\n'))
            func_score = self._score_threshold(
                func_lines, 
                structure_config.get("function_size_thresholds", {}), 
                reverse=True
            )
            function_scores.append(func_score)
            
            if func_lines > structure_config.get("function_size_thresholds", {}).get("good", 40):
                func_name = self._extract_function_name(func_match, language)
                large_functions.append({"name": func_name, "lines": func_lines})
        
        avg_function_score = sum(function_scores) / len(function_scores) if function_scores else 100.0
        
        # Class size scoring
        classes = re.findall(self._get_class_pattern(language), content, re.MULTILINE | re.DOTALL)
        class_scores = []
        large_classes = []
        
        for class_match in classes:
            class_lines = len(class_match.split('\n'))
            class_score = self._score_threshold(
                class_lines, 
                structure_config.get("class_size_thresholds", {}), 
                reverse=True
            )
            class_scores.append(class_score)
            
            if class_lines > structure_config.get("class_size_thresholds", {}).get("good", 400):
                class_name = self._extract_class_name(class_match, language)
                large_classes.append({"name": class_name, "lines": class_lines})
        
        avg_class_score = sum(class_scores) / len(class_scores) if class_scores else 100.0
        
        # Combined structure score
        structure_score = (file_score + avg_function_score + avg_class_score) / 3
        
        return {
            "structure_score": structure_score,
            "structure_details": {
                "file_lines": line_count,
                "file_score": file_score,
                "total_functions": len(functions),
                "avg_function_score": avg_function_score,
                "large_functions": large_functions,
                "total_classes": len(classes),
                "avg_class_score": avg_class_score,
                "large_classes": large_classes
            }
        }
    
    def _score_test_coverage(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Estimate test coverage based on heuristics"""
        test_config = self.config.get("test_coverage_scoring", {})
        test_patterns = test_config.get("test_file_patterns", [])
        
        # Count test files
        test_files = 0
        total_files = len(files)
        
        for file_info in files:
            file_path = file_info["path"]
            file_name = Path(file_path).name
            
            if any(self._matches_pattern(file_name, pattern) for pattern in test_patterns):
                test_files += 1
        
        # Estimate coverage based on test file ratio
        if total_files == 0:
            test_ratio = 0.0
        else:
            test_ratio = (test_files / total_files) * 100
        
        # Basic heuristic: assume test ratio correlates with coverage
        estimated_coverage = min(100.0, test_ratio * 3)  # Rough estimation
        
        # Score based on estimated coverage
        test_score = self._score_threshold(estimated_coverage, test_config.get("coverage_thresholds", {}))
        
        return {
            "test_coverage_score": test_score,
            "test_coverage_details": {
                "test_files": test_files,
                "total_files": total_files,
                "test_file_ratio": test_ratio,
                "estimated_coverage": estimated_coverage,
                "test_patterns_used": test_patterns
            }
        }
    
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
    
    def _get_function_pattern(self, language: str) -> str:
        """Get regex pattern for function definitions by language from configuration"""
        patterns = self.config.get("regex_patterns", {}).get("function_patterns", {})
        return patterns.get(language, r'(\w+)\s*\([^)]*\)')
    
    def _get_class_pattern(self, language: str) -> str:
        """Get regex pattern for class definitions by language from configuration"""
        patterns = self.config.get("regex_patterns", {}).get("class_patterns", {})
        return patterns.get(language, r'class\s+(\w+)')
    
    def _extract_function_name(self, func_match: str, language: str) -> str:
        """Extract function name from regex match using configuration patterns"""
        patterns = self.config.get("regex_patterns", {}).get("function_name_patterns", {})
        pattern = patterns.get(language, r'(\w+)')
        match = re.search(pattern, func_match)
        return match.group(1) if match else ""
    
    def _extract_class_name(self, class_match: str, language: str) -> str:
        """Extract class name from regex match using configuration patterns"""
        patterns = self.config.get("regex_patterns", {}).get("class_name_patterns", {})
        pattern = patterns.get(language, r'class\s+(\w+)')
        match = re.search(pattern, class_match)
        return match.group(1) if match else ""
    
    def _count_docstrings(self, content: str, language: str) -> int:
        """Count docstrings in code using configuration patterns"""
        patterns_config = self.config.get("regex_patterns", {}).get("docstring_patterns", {})
        patterns = patterns_config.get(language, [])
        
        total_count = 0
        for pattern in patterns:
            total_count += len(re.findall(pattern, content, re.DOTALL))
        
        return total_count
    
    def _count_comments(self, content: str) -> int:
        """Count inline comments using configuration patterns"""
        comment_patterns = self.config.get("regex_patterns", {}).get("comment_patterns", {})
        single_line_patterns = comment_patterns.get("single_line", ["#.*", "//.*"])
        
        total_count = 0
        for pattern in single_line_patterns:
            total_count += len(re.findall(pattern, content))
        
        return total_count
    
    def _assess_documentation_quality(self, content: str, language: str) -> List[str]:
        """Assess documentation quality indicators using configuration patterns"""
        indicators = []
        quality_patterns = self.config.get("regex_patterns", {}).get("documentation_quality_patterns", {})
        
        # Check for examples
        examples_pattern = quality_patterns.get("examples", "example|>>> ")
        if re.search(examples_pattern, content, re.IGNORECASE):
            indicators.append("contains_examples")
        
        # Check for parameter documentation
        params_pattern = quality_patterns.get("parameters", "@param|:param|@parameter")
        if re.search(params_pattern, content, re.IGNORECASE):
            indicators.append("contains_parameters")
        
        # Check for return documentation
        returns_pattern = quality_patterns.get("returns", "@return|:return|@returns")
        if re.search(returns_pattern, content, re.IGNORECASE):
            indicators.append("contains_return_info")
        
        # Check for raises/throws documentation
        raises_pattern = quality_patterns.get("raises", "@raises|:raises|@throws")
        if re.search(raises_pattern, content, re.IGNORECASE):
            indicators.append("contains_raises_info")
        
        return indicators
    
    def _check_naming_style(self, name: str, expected_style: str) -> bool:
        """Check if name follows expected naming style using configuration patterns"""
        style_patterns = self.config.get("regex_patterns", {}).get("naming_style_patterns", {})
        pattern = style_patterns.get(expected_style, "")
        
        if not pattern:
            return True  # Unknown style, assume valid
        
        return re.match(pattern, name) is not None
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob-like pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
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
    
    def _generate_recommendations(self, scores: Dict[str, float], details: Dict) -> List[str]:
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
    
    def score_maintainability(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Score maintainability across multiple files
        
        Args:
            files: List of dictionaries with 'path' and 'content' keys
            
        Returns:
            Dictionary containing maintainability analysis results
        """
        start_time = time.time()
        
        try:
            if not files:
                return {"error": "No files provided for analysis", "analysis_type": "maintainability"}
            
            # Analyze complexity across all files
            complexity_result = self.complexity_analyzer.analyze_complexity(
                files[0]["content"], 
                self._detect_language(files[0]["path"]) or "python"
            )
            
            # Analyze duplication across all files
            duplication_result = self.duplication_detector.detect_duplications(files)
            
            # Score individual metrics
            complexity_scores = self._score_complexity(complexity_result)
            duplication_scores = self._score_duplication(duplication_result)
            
            # For multi-file analysis, we'll analyze the first file for other metrics
            primary_file = files[0]
            language = self._detect_language(primary_file["path"])
            
            if not language:
                return {"error": f"Unsupported file type: {primary_file['path']}", "analysis_type": "maintainability"}
            
            documentation_scores = self._score_documentation(primary_file["content"], language)
            naming_scores = self._score_naming(primary_file["content"], language)
            structure_scores = self._score_structure(primary_file["content"], primary_file["path"], language)
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
            recommendations = self._generate_recommendations(all_scores, {
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


# Create scorer instance
_maintainability_scorer = MaintainabilityScorer()

def maintainability_scorer_tool(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """Score code maintainability with holistic metrics combining complexity, duplication, and other factors"""
    return _maintainability_scorer.score_maintainability(files)

async def maintainability_scoring(files: List[Dict[str, str]], include_llm_insights: bool = True) -> Dict[str, Any]:
    """
    Maintainability scoring with LLM insights
    
    Args:
        files: List of dictionaries with 'path' and 'content' keys
        include_llm_insights: Whether to include LLM-generated insights
        
    Returns:
        Dictionary containing comprehensive maintainability scoring
    """
    try:
        # Get base scoring results
        base_result = _maintainability_scorer.score_maintainability(files)
        
        if not include_llm_insights:
            return base_result
        
        # Add LLM insights if enabled
        if "error" in base_result:
            return base_result
        
        llm_provider = get_llm_provider()
        
        # Prepare analysis summary for LLM insights
        analysis_summary = {
            "maintainability_index": base_result.get("maintainability_index", 0),
            "quality_level": base_result.get("quality_level", "unknown"),
            "scores": base_result.get("scores", {}),
            "primary_language": base_result.get("primary_language", "unknown"),
            "total_files": base_result.get("total_files_analyzed", 0)
        }
        
        # Generate LLM insights
        language = _maintainability_scorer._detect_language(files[0]["path"]) or "python"  # Default to python
        
        prompt = f"""
Analyze this code maintainability scoring result and provide insights:

Language: {language}
Maintainability Index: {analysis_summary['maintainability_index']}/100
Quality Level: {analysis_summary['quality_level']}

Detailed Scores:
{json.dumps(analysis_summary['scores'], indent=2)}

Provide:
1. Key strengths and weaknesses
2. Specific improvement recommendations
3. Priority areas for refactoring
4. Long-term maintainability outlook
"""
        
        try:
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt="You are a code quality expert providing maintainability insights.",
                temperature=0.3,
                max_tokens=1024
            )
            
            llm_response = await llm_provider.generate_response(llm_request)
            base_result["llm_insights"] = {
                "analysis": llm_response.content if hasattr(llm_response, 'content') else str(llm_response),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"Failed to generate LLM insights: {e}")
            base_result["llm_insights"] = {"error": f"LLM insights unavailable: {str(e)}"}
        
        return base_result
        
    except Exception as e:
        logger.error(f"Enhanced maintainability scoring failed: {e}")
        return {
            "error": str(e),
            "analysis_type": "maintainability",
            "processing_time": 0
        }

def enhanced_maintainability_scorer_tool(files: List[Dict[str, str]], include_llm_insights: bool = True) -> Dict[str, Any]:
    """
    Enhanced maintainability scorer tool with LLM integration
    """
    return asyncio.run(maintainability_scoring(files, include_llm_insights))

# ADK FunctionTool for maintainability scoring
MaintainabilityScorerTool = FunctionTool(maintainability_scorer_tool)

# Enhanced ADK FunctionTool with LLM integration
EnhancedMaintainabilityScorerTool = FunctionTool(enhanced_maintainability_scorer_tool)

# Backward compatibility wrapper  
async def enhanced_maintainability_analysis(files: List[Dict[str, str]], include_llm_insights: bool = True) -> Dict[str, Any]:
    """Backward compatibility wrapper for maintainability_scoring"""
    # The main function is now called maintainability_scoring
    # Call it directly since it's the new name
    return await maintainability_scoring(files, include_llm_insights)