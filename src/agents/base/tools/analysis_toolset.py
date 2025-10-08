"""
ADK-native BaseToolset implementation for code analysis tools.

This module provides the core BaseToolset that all analysis tools extend from,
following Google ADK patterns for tool discovery and registration.
"""

from typing import List, Dict, Any, Optional, Callable
from abc import abstractmethod
import logging

from google.adk.tools import BaseTool, FunctionTool, ToolContext
ADK_AVAILABLE = True


logger = logging.getLogger(__name__)


class AnalysisToolset:
    """
    Base toolset for all code analysis tools following ADK patterns.
    
    This toolset provides:
    - Dynamic tool discovery and registration
    - Unified tool interface for LLM agents
    - Proper resource management and cleanup
    - Context sharing between tools
    """
    
    def __init__(self, name: str = "analysis_toolset"):
        """Initialize the analysis toolset with ADK patterns."""
        self.name = name
        self._tools: List[Any] = []
        self._registered_tools: Dict[str, Any] = {}
        self._tool_context: Optional[ToolContext] = None
        self._setup_core_tools()
        logger.info(f"Initialized {name} with {len(self.get_tools())} tools")
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to this toolset."""
        self._tools.append(tool)
    
    def _setup_core_tools(self) -> None:
        """Setup core analysis tools that are always available."""
        # Language detection tool
        self.add_tool(FunctionTool(self._detect_language))
        
        # File analysis tool
        self.add_tool(FunctionTool(self._analyze_file_structure))
    
    def register_analysis_tool(self, tool_name: str, tool_function: Callable[..., Any], 
                             description: str) -> None:
        """
        Register a new analysis tool dynamically.
        
        Args:
            tool_name: Unique name for the tool
            tool_function: Function that performs the analysis
            description: Description for LLM understanding
        """
        tool = FunctionTool(tool_function)
        
        self.add_tool(tool)
        self._registered_tools[tool_name] = tool
        logger.info(f"Registered analysis tool: {tool_name}")
    
    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        return self._registered_tools.get(name)
    
    def list_available_tools(self) -> List[Dict[str, str]]:
        """List all available tools with descriptions."""
        result = []
        for tool in self.get_tools():
            tool_info = {
                "name": getattr(tool, 'name', str(tool)),
                "description": getattr(tool, 'description', f"Tool: {type(tool).__name__}")
            }
            result.append(tool_info)
        return result
    
    def set_context(self, context: ToolContext) -> None:
        """Set the tool context for state management."""
        self._tool_context = context
    
    def _detect_language(self, code: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect programming language from code or filename.
        
        Args:
            code: Source code to analyze
            filename: Optional filename for extension-based detection
            
        Returns:
            Dictionary with language detection results
        """
        # Extension-based detection
        if filename:
            ext_mapping = {
                '.py': 'python',
                '.js': 'javascript', 
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp'
            }
            
            for ext, lang in ext_mapping.items():
                if filename.endswith(ext):
                    return {
                        "language": lang,
                        "confidence": 0.9,
                        "detection_method": "extension",
                        "filename": filename
                    }
        
        # Content-based detection (basic patterns)
        content_patterns = {
            'python': ['def ', 'import ', 'from ', 'class '],
            'javascript': ['function ', 'var ', 'let ', 'const '],
            'typescript': ['interface ', 'type ', 'enum '],
            'java': ['public class', 'private ', 'public static void main']
        }
        
        scores: Dict[str, float] = {}
        for lang, patterns in content_patterns.items():
            score = sum(1 for pattern in patterns if pattern in code)
            if score > 0:
                scores[lang] = score / len(patterns)
        
        if scores:
            best_lang = max(scores.keys(), key=lambda x: scores[x])
            return {
                "language": best_lang,
                "confidence": scores[best_lang],
                "detection_method": "content_analysis"
            }
        
        return {
            "language": "unknown",
            "confidence": 0.0,
            "detection_method": "failed"
        }
    
    def _analyze_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze file and directory structure.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            Dictionary with structure analysis
        """
        import os
        
        if not os.path.exists(file_path):
            return {
                "error": f"Path does not exist: {file_path}",
                "exists": False
            }
        
        result: Dict[str, Any] = {
            "path": file_path,
            "exists": True,
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path)
        }
        
        if os.path.isfile(file_path):
            # File analysis
            stat = os.stat(file_path)
            result.update({
                "size_bytes": stat.st_size,
                "extension": os.path.splitext(file_path)[1],
                "basename": os.path.basename(file_path)
            })
        elif os.path.isdir(file_path):
            # Directory analysis
            try:
                contents = os.listdir(file_path)
                files = [f for f in contents if os.path.isfile(os.path.join(file_path, f))]
                dirs = [d for d in contents if os.path.isdir(os.path.join(file_path, d))]
                
                result.update({
                    "total_items": len(contents),
                    "file_count": len(files),
                    "directory_count": len(dirs),
                    "files": files[:10],  # Limit to first 10
                    "directories": dirs[:10]  # Limit to first 10
                })
            except PermissionError:
                result["error"] = "Permission denied accessing directory"
        
        return result
    
    def get_tools(self) -> List[Any]:
        """
        Return list of tools provided by this toolset
        Override in specialized toolsets
        """
        return self._tools if hasattr(self, '_tools') else []
    
    def close(self) -> None:
        """Clean up resources when toolset is no longer needed"""
        logger.info(f"Closing toolset: {self.name}")
        self._registered_tools.clear()
        self._tool_context = None