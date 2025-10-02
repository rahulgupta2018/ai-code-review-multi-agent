"""
Language Configuration Manager

Language-specific AST mappings and patterns for code analysis.
Supports Tree-sitter parsing for multiple programming languages.
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LanguageConfig:
    """Configuration for language-specific analysis settings."""
    
    def __init__(self):
        """Initialize language configuration."""
        self._language_mappings: Dict[str, Dict[str, Any]] = {}
        self._default_config = self._get_default_config()
        
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get configuration for a specific programming language."""
        return self._language_mappings.get(language.lower(), self._default_config)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return [
            "python", "javascript", "typescript", "java", "go", 
            "rust", "cpp", "csharp", "swift", "kotlin", "sql"
        ]
    
    def get_file_extensions(self, language: str) -> List[str]:
        """Get file extensions for a programming language."""
        extension_map = {
            "python": [".py", ".pyw"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "go": [".go"],
            "rust": [".rs"],
            "cpp": [".cpp", ".cxx", ".cc", ".c", ".h", ".hpp"],
            "csharp": [".cs"],
            "swift": [".swift"],
            "kotlin": [".kt", ".kts"],
            "sql": [".sql"]
        }
        return extension_map.get(language.lower(), [])
    
    def get_tree_sitter_grammar(self, language: str) -> Optional[str]:
        """Get Tree-sitter grammar name for a language."""
        grammar_map = {
            "python": "tree-sitter-python",
            "javascript": "tree-sitter-javascript",
            "typescript": "tree-sitter-typescript",
            "java": "tree-sitter-java",
            "go": "tree-sitter-go",
            "rust": "tree-sitter-rust",
            "cpp": "tree-sitter-cpp",
            "csharp": "tree-sitter-c-sharp",
            "swift": "tree-sitter-swift",
            "kotlin": "tree-sitter-kotlin",
            "sql": "tree-sitter-sql"
        }
        return grammar_map.get(language.lower())
    
    def get_ast_node_patterns(self, language: str) -> Dict[str, List[str]]:
        """Get AST node patterns for complexity analysis."""
        patterns = {
            "python": {
                "functions": ["function_definition", "async_function_definition"],
                "classes": ["class_definition"],
                "loops": ["for_statement", "while_statement"],
                "conditionals": ["if_statement", "elif_clause"],
                "try_catch": ["try_statement", "except_clause"]
            },
            "javascript": {
                "functions": ["function_declaration", "arrow_function", "function_expression"],
                "classes": ["class_declaration"],
                "loops": ["for_statement", "for_in_statement", "while_statement"],
                "conditionals": ["if_statement"],
                "try_catch": ["try_statement", "catch_clause"]
            },
            "typescript": {
                "functions": ["function_declaration", "arrow_function", "method_definition"],
                "classes": ["class_declaration", "interface_declaration"],
                "loops": ["for_statement", "for_in_statement", "while_statement"],
                "conditionals": ["if_statement"],
                "try_catch": ["try_statement", "catch_clause"]
            },
            "java": {
                "functions": ["method_declaration", "constructor_declaration"],
                "classes": ["class_declaration", "interface_declaration"],
                "loops": ["for_statement", "enhanced_for_statement", "while_statement"],
                "conditionals": ["if_statement", "switch_statement"],
                "try_catch": ["try_statement", "catch_clause"]
            }
        }
        return patterns.get(language.lower(), self._get_default_patterns())
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for unsupported languages."""
        return {
            "supported": False,
            "complexity_threshold": 10,
            "patterns": self._get_default_patterns(),
            "extensions": [],
            "grammar": None
        }
    
    def _get_default_patterns(self) -> Dict[str, List[str]]:
        """Get default AST patterns."""
        return {
            "functions": [],
            "classes": [],
            "loops": [],
            "conditionals": [],
            "try_catch": []
        }
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported for analysis."""
        return language.lower() in self.get_supported_languages()
    
    def detect_language_from_extension(self, file_extension: str) -> Optional[str]:
        """Detect programming language from file extension."""
        for language in self.get_supported_languages():
            if file_extension.lower() in self.get_file_extensions(language):
                return language
        return None


# Global language configuration instance
language_config = LanguageConfig()