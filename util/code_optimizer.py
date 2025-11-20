"""
Code Optimization Utilities for Token Reduction
Preprocess code to reduce token usage before sending to LLM
"""

import re
from typing import Tuple


def strip_comments_and_docstrings(code: str, language: str = "python") -> Tuple[str, int]:
    """
    Remove comments and docstrings to reduce token count.
    
    Args:
        code: Source code string
        language: Programming language (python, javascript, java, etc.)
    
    Returns:
        Tuple of (cleaned_code, tokens_saved_estimate)
    """
    original_length = len(code)
    cleaned = code
    
    if language.lower() in ["python", "py"]:
        # Remove single-line comments
        cleaned = re.sub(r'#.*$', '', cleaned, flags=re.MULTILINE)
        # Remove multi-line docstrings (""" or ''')
        cleaned = re.sub(r'"""[\s\S]*?"""', '', cleaned)
        cleaned = re.sub(r"'''[\s\S]*?'''", '', cleaned)
    
    elif language.lower() in ["javascript", "js", "typescript", "ts", "java", "c", "cpp", "go"]:
        # Remove single-line comments
        cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)
        # Remove multi-line comments
        cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)
    
    # Remove excessive blank lines (keep max 1 blank line)
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    tokens_saved = (original_length - len(cleaned)) // 4  # Rough estimate: 4 chars = 1 token
    
    return cleaned, tokens_saved


def should_optimize_code(code: str, threshold: int = 2000) -> bool:
    """
    Determine if code should be optimized based on size.
    
    Args:
        code: Source code string
        threshold: Character count threshold (default: 2000 chars ≈ 500 tokens)
    
    Returns:
        True if code exceeds threshold
    """
    return len(code) > threshold


def get_code_summary(code: str, language: str = "python", max_length: int = 1000) -> str:
    """
    Extract key parts of code (function signatures, class definitions) for large files.
    
    Args:
        code: Source code string
        language: Programming language
        max_length: Maximum length of summary
    
    Returns:
        Summarized code with key structures
    """
    if len(code) <= max_length:
        return code
    
    lines = code.split('\n')
    summary_lines = []
    
    if language.lower() in ["python", "py"]:
        for line in lines:
            # Keep function/class definitions, imports
            if any(keyword in line for keyword in ['def ', 'class ', 'import ', 'from ']):
                summary_lines.append(line)
            # Keep lines with potential issues (TODO, FIXME, etc.)
            elif any(marker in line for marker in ['TODO', 'FIXME', 'XXX', 'HACK']):
                summary_lines.append(line)
    
    summary = '\n'.join(summary_lines)
    
    if len(summary) > max_length:
        return summary[:max_length] + "\n... (truncated)"
    
    return summary if summary else code[:max_length] + "\n... (truncated)"
