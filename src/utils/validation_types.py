"""
Validation-specific types and constants.

This module provides types and constants used specifically for validation.
These will eventually be moved to more appropriate domain modules.
"""

from typing import Tuple, TypedDict, Optional
from enum import Enum

# Validation result type
ValidationResult = Tuple[bool, Optional[str]]

# File validation constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_REQUEST = 50
MAX_FILENAME_LENGTH = 255
MAX_FILE_CONTENT_LENGTH = 1024 * 1024  # 1MB

class SupportedLanguage(Enum):
    """Supported programming languages for analysis."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"

# Extension to language mapping
EXTENSION_TO_LANGUAGE = {
    ".py": SupportedLanguage.PYTHON,
    ".js": SupportedLanguage.JAVASCRIPT,
    ".ts": SupportedLanguage.TYPESCRIPT,
    ".tsx": SupportedLanguage.TYPESCRIPT,
    ".jsx": SupportedLanguage.JAVASCRIPT,
    ".java": SupportedLanguage.JAVA,
    ".cs": SupportedLanguage.CSHARP,
    ".cpp": SupportedLanguage.CPP,
    ".cc": SupportedLanguage.CPP,
    ".cxx": SupportedLanguage.CPP,
    ".c": SupportedLanguage.CPP,
    ".h": SupportedLanguage.CPP,
    ".hpp": SupportedLanguage.CPP,
    ".go": SupportedLanguage.GO,
    ".rs": SupportedLanguage.RUST,
    ".php": SupportedLanguage.PHP,
    ".rb": SupportedLanguage.RUBY,
}

class CodeFile(TypedDict):
    """Code file structure for validation."""
    filename: str
    content: str
    language: SupportedLanguage
    size_bytes: int
    line_count: int
    encoding: str