"""
Complexity Analysis Tool

AGDK tool for analyzing code complexity with memory integration.
Provides cyclomatic complexity analysis with historical context.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ComplexityAnalysisTool:
    """Tool for analyzing code complexity with memory awareness."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the complexity analysis tool."""
        self.config = config or {}
        self.complexity_threshold = self.config.get("complexity_threshold", 10)
        self.memory_enabled = self.config.get("memory_enabled", True)
        
    def analyze_complexity(self, code_content: str, file_path: str, 
                          memory_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Analyze complexity of code content."""
        try:
            # Calculate base complexity
            base_complexity = self._calculate_cyclomatic_complexity(code_content)
            
            # Apply memory-based threshold adjustment
            adjusted_threshold = self._adjust_threshold_with_memory(
                self.complexity_threshold, memory_context
            )
            
            # Determine if threshold is exceeded
            exceeds_threshold = base_complexity > adjusted_threshold
            
            result = {
                "complexity_score": base_complexity,
                "threshold": adjusted_threshold,
                "exceeds_threshold": exceeds_threshold,
                "file_path": file_path,
                "memory_enhanced": self.memory_enabled and memory_context is not None,
                "metadata": {
                    "base_threshold": self.complexity_threshold,
                    "memory_adjustments": self._get_memory_adjustments(memory_context)
                }
            }
            
            logger.debug(f"Complexity analysis for {file_path}: {base_complexity}")
            return result
            
        except Exception as e:
            logger.error(f"Complexity analysis failed for {file_path}: {e}")
            return {
                "complexity_score": 0,
                "threshold": self.complexity_threshold,
                "exceeds_threshold": False,
                "error": str(e)
            }
    
    def _calculate_cyclomatic_complexity(self, code_content: str) -> int:
        """Calculate cyclomatic complexity of code."""
        # TODO: Implement actual complexity calculation using AST
        # This is a simplified placeholder implementation
        
        # Count decision points (if, while, for, try, etc.)
        decision_keywords = [
            'if', 'elif', 'while', 'for', 'try', 'except',
            'and', 'or', '?', '&&', '||', 'case', 'default'
        ]
        
        complexity = 1  # Base complexity
        lines = code_content.lower().split('\n')
        
        for line in lines:
            for keyword in decision_keywords:
                complexity += line.count(keyword)
        
        return min(complexity, 50)  # Cap at reasonable maximum
    
    def _adjust_threshold_with_memory(self, base_threshold: int, 
                                    memory_context: Optional[List[Dict[str, Any]]]) -> int:
        """Adjust complexity threshold based on memory context."""
        if not memory_context or not self.memory_enabled:
            return base_threshold
        
        adjustment = 0
        
        for context_item in memory_context:
            if context_item.get("type") == "learned_threshold":
                if context_item.get("metric") == "complexity_score":
                    learned_threshold = context_item.get("threshold", base_threshold)
                    accuracy = context_item.get("accuracy", 0.5)
                    
                    # Adjust based on historical accuracy
                    if accuracy > 0.8:
                        adjustment = int((learned_threshold - base_threshold) * 0.5)
        
        return max(base_threshold + adjustment, 5)  # Minimum threshold of 5
    
    def _get_memory_adjustments(self, memory_context: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Get memory-based adjustments applied."""
        adjustments = []
        
        if memory_context:
            for context_item in memory_context:
                if context_item.get("type") == "learned_threshold":
                    adjustments.append({
                        "type": "threshold_adjustment",
                        "original_threshold": self.complexity_threshold,
                        "learned_threshold": context_item.get("threshold"),
                        "accuracy": context_item.get("accuracy")
                    })
        
        return adjustments
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about this tool."""
        return {
            "name": "ComplexityAnalysisTool",
            "version": "1.0.0",
            "capabilities": ["cyclomatic_complexity", "threshold_adjustment", "memory_integration"],
            "config": self.config
        }