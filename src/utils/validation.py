"""
Input validation utilities for ADK Multi-Agent Code Review MVP.

This module provides comprehensive validation for API inputs, file content,
and configuration data with proper error reporting and security checks.
"""

import re
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from datetime import datetime

from .config_loader import get_config
from ..utils.exceptions import ValidationError, SecurityError
from .types import (
    ValidationResult, SupportedLanguage, EXTENSION_TO_LANGUAGE, CodeFile
)
from .constants import (
    MAX_FILE_SIZE_BYTES, MAX_FILES_PER_REQUEST, MAX_FILENAME_LENGTH, MAX_FILE_CONTENT_LENGTH
)


class FileValidator:
    """Validator for code files and file uploads."""
    
    # Dangerous file extensions that should be blocked
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.dll',
        '.vbs', '.js', '.jar', '.app', '.deb', '.pkg', '.dmg'
    }
    
    # Maximum nesting levels for archives
    MAX_ARCHIVE_NESTING = 3
    
    def __init__(self):
        self.config = get_config()
    
    def validate_filename(self, filename: str) -> ValidationResult:
        """Validate a filename for security and format."""
        if not filename:
            return False, "Filename cannot be empty"
        
        if len(filename) > MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {MAX_FILENAME_LENGTH} characters)"
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/') or '\\' in filename:
            return False, "Filename contains invalid path characters"
        
        # Check for dangerous characters
        dangerous_chars = {'<', '>', ':', '"', '|', '?', '*', '\0'}
        if any(char in filename for char in dangerous_chars):
            return False, f"Filename contains invalid characters: {dangerous_chars & set(filename)}"
        
        # Check file extension
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension in self.DANGEROUS_EXTENSIONS:
            return False, f"File type not allowed: {extension}"
        
        return True, None
    
    def validate_file_content(self, content: str, filename: str) -> ValidationResult:
        """Validate file content for size and safety."""
        if not content:
            return False, "File content cannot be empty"
        
        # Check content length
        if len(content) > MAX_FILE_CONTENT_LENGTH:
            return False, f"File content too large (max {MAX_FILE_CONTENT_LENGTH} characters)"
        
        # Try to detect encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            return False, "File content contains invalid UTF-8 characters"
        
        # Check for binary content indicators
        if '\0' in content:
            return False, "Binary files are not supported"
        
        # Language-specific validation
        language = self.detect_language(filename)
        if language:
            return self._validate_language_specific(content, language)
        
        return True, None
    
    def validate_file_size(self, size_bytes: int) -> ValidationResult:
        """Validate file size limits."""
        if size_bytes <= 0:
            return False, "File size must be greater than 0"
        
        if size_bytes > MAX_FILE_SIZE_BYTES:
            return False, f"File too large (max {MAX_FILE_SIZE_BYTES // (1024*1024)}MB)"
        
        return True, None
    
    def detect_language(self, filename: str) -> Optional[SupportedLanguage]:
        """Detect programming language from filename."""
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(extension)
    
    def validate_code_file(self, file_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[CodeFile]]:
        """Validate a complete code file object."""
        try:
            # Required fields
            if 'filename' not in file_data:
                return False, "filename is required", None
            if 'content' not in file_data:
                return False, "content is required", None
            
            filename = file_data['filename']
            content = file_data['content']
            
            # Validate filename
            valid, error = self.validate_filename(filename)
            if not valid:
                return False, f"Invalid filename: {error}", None
            
            # Validate content
            valid, error = self.validate_file_content(content, filename)
            if not valid:
                return False, f"Invalid content: {error}", None
            
            # Validate size
            content_bytes = len(content.encode('utf-8'))
            valid, error = self.validate_file_size(content_bytes)
            if not valid:
                return False, error, None
            
            # Detect language
            language = self.detect_language(filename)
            if not language:
                return False, f"Unsupported file type: {Path(filename).suffix}", None
            
            # Create validated CodeFile
            code_file: CodeFile = {
                'filename': filename,
                'language': language,
                'content': content,
                'size_bytes': content_bytes,
                'encoding': 'utf-8'
            }
            
            return True, None, code_file
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None
    
    def _validate_language_specific(self, content: str, language: SupportedLanguage) -> ValidationResult:
        """Perform language-specific validation."""
        # Check for extremely long lines (potential minified code)
        lines = content.split('\n')
        max_line_length = 1000
        
        for i, line in enumerate(lines):
            if len(line) > max_line_length:
                return False, f"Line {i+1} is too long (max {max_line_length} characters)"
        
        # Check for suspicious patterns based on language
        if language == SupportedLanguage.PYTHON:
            return self._validate_python_content(content)
        elif language in [SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT]:
            return self._validate_javascript_content(content)
        
        return True, None
    
    def _validate_python_content(self, content: str) -> ValidationResult:
        """Validate Python-specific content."""
        # Check for basic syntax indicators
        if not any(keyword in content for keyword in ['def ', 'class ', 'import ', 'from ']):
            # Might be a script, check for basic Python patterns
            if not any(pattern in content for pattern in ['=', 'print(', 'if ', 'for ', 'while ']):
                return False, "Content doesn't appear to be valid Python code"
        
        return True, None
    
    def _validate_javascript_content(self, content: str) -> ValidationResult:
        """Validate JavaScript/TypeScript content."""
        # Very basic validation - check for common JS patterns
        js_patterns = ['function', 'var ', 'let ', 'const ', '=>', 'console.log']
        if not any(pattern in content for pattern in js_patterns):
            return False, "Content doesn't appear to be valid JavaScript/TypeScript code"
        
        return True, None


class SecurityValidator:
    """Validator for security-related checks."""
    
    # Patterns that might indicate malicious content
    SUSPICIOUS_PATTERNS = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'subprocess\.call',
        r'os\.system',
        r'shell=True',
        r'__import__\s*\(',
        r'getattr\s*\(',
        r'setattr\s*\(',
        r'delattr\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
    ]
    
    # Common secret patterns
    SECRET_PATTERNS = [
        r'[\'"](?:password|pwd)[\'"]?\s*[:=]\s*[\'"][^\'"]+[\'"]',
        r'[\'"](?:api_key|apikey)[\'"]?\s*[:=]\s*[\'"][^\'"]+[\'"]',
        r'[\'"](?:secret|token)[\'"]?\s*[:=]\s*[\'"][^\'"]+[\'"]',
        r'[\'"](?:private_key|privatekey)[\'"]?\s*[:=]\s*[\'"][^\'"]+[\'"]',
        r'-----BEGIN (?:RSA )?PRIVATE KEY-----',
        r'-----BEGIN CERTIFICATE-----',
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key
        r'ya29\.[0-9A-Za-z\-_]+',  # Google OAuth
    ]
    
    def __init__(self):
        self.config = get_config()
    
    def scan_for_secrets(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Scan content for potential secrets."""
        findings = []
        
        if not self.config.security.scan_for_secrets:
            return findings
        
        lines = content.split('\n')
        
        for pattern in self.SECRET_PATTERNS:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                matches = compiled_pattern.finditer(line)
                for match in matches:
                    findings.append({
                        'type': 'secret',
                        'pattern': pattern,
                        'filename': filename,
                        'line_number': line_num,
                        'column': match.start(),
                        'matched_text': match.group()[:50] + '...' if len(match.group()) > 50 else match.group(),
                        'severity': 'high'
                    })
        
        return findings
    
    def scan_for_malicious_patterns(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Scan content for potentially malicious patterns."""
        findings = []
        
        if not self.config.security.scan_for_malicious_patterns:
            return findings
        
        lines = content.split('\n')
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                matches = compiled_pattern.finditer(line)
                for match in matches:
                    findings.append({
                        'type': 'suspicious_pattern',
                        'pattern': pattern,
                        'filename': filename,
                        'line_number': line_num,
                        'column': match.start(),
                        'matched_text': match.group(),
                        'severity': 'medium'
                    })
        
        return findings
    
    def validate_safe_content(self, content: str, filename: str) -> ValidationResult:
        """Validate that content is safe for processing."""
        # Scan for secrets
        secret_findings = self.scan_for_secrets(content, filename)
        if secret_findings:
            high_severity_secrets = [f for f in secret_findings if f['severity'] == 'high']
            if high_severity_secrets:
                return False, f"Potential secrets detected in {filename}"
        
        # Scan for malicious patterns
        malicious_findings = self.scan_for_malicious_patterns(content, filename)
        if malicious_findings:
            # Allow some patterns but warn
            critical_patterns = ['eval(', 'exec(', 'os.system']
            for finding in malicious_findings:
                if any(pattern in finding['matched_text'] for pattern in critical_patterns):
                    return False, f"Potentially dangerous pattern detected: {finding['matched_text']}"
        
        return True, None


class APIValidator:
    """Validator for API requests and responses."""
    
    def __init__(self):
        self.config = get_config()
        self.file_validator = FileValidator()
        self.security_validator = SecurityValidator()
    
    def validate_analysis_request(self, request_data: Dict[str, Any]) -> ValidationResult:
        """Validate an analysis request."""
        try:
            # Check required fields
            if 'files' not in request_data:
                return False, "files field is required"
            
            files = request_data['files']
            if not isinstance(files, list):
                return False, "files must be a list"
            
            if not files:
                return False, "at least one file is required"
            
            if len(files) > MAX_FILES_PER_REQUEST:
                return False, f"too many files (max {MAX_FILES_PER_REQUEST})"
            
            # Validate each file
            total_size = 0
            validated_files = []
            
            for i, file_data in enumerate(files):
                if not isinstance(file_data, dict):
                    return False, f"file {i} must be an object"
                
                valid, error, code_file = self.file_validator.validate_code_file(file_data)
                if not valid:
                    return False, f"file {i}: {error}"
                
                # Security scan
                if code_file:
                    security_valid, security_error = self.security_validator.validate_safe_content(
                        code_file['content'], code_file['filename']
                    )
                    if not security_valid:
                        return False, f"file {i}: {security_error}"
                    
                    total_size += code_file['size_bytes']
                    validated_files.append(code_file)
            
            # Check total size
            max_total_size = self.config.security.max_files_per_request * MAX_FILE_SIZE_BYTES
            if total_size > max_total_size:
                return False, f"total size too large (max {max_total_size // (1024*1024)}MB)"
            
            return True, None
            
        except Exception as e:
            return False, f"validation error: {str(e)}"
    
    def validate_session_id(self, session_id: str) -> ValidationResult:
        """Validate a session ID format."""
        if not session_id:
            return False, "session_id is required"
        
        if not isinstance(session_id, str):
            return False, "session_id must be a string"
        
        # Check format (UUID-like)
        if not re.match(r'^[a-f0-9\-]{36}$', session_id):
            return False, "session_id must be a valid UUID"
        
        return True, None
    
    def validate_correlation_id(self, correlation_id: str) -> ValidationResult:
        """Validate a correlation ID format."""
        if not correlation_id:
            return False, "correlation_id is required"
        
        if not isinstance(correlation_id, str):
            return False, "correlation_id must be a string"
        
        if len(correlation_id) > 100:
            return False, "correlation_id too long (max 100 characters)"
        
        # Allow alphanumeric and common separators
        if not re.match(r'^[a-zA-Z0-9\-_]+$', correlation_id):
            return False, "correlation_id contains invalid characters"
        
        return True, None
    
    def validate_pagination_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate pagination parameters."""
        try:
            page = params.get('page', 1)
            page_size = params.get('page_size', 20)
            
            if not isinstance(page, int) or page < 1:
                return False, "page must be a positive integer"
            
            if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
                return False, "page_size must be between 1 and 100"
            
            return True, None
            
        except Exception as e:
            return False, f"pagination validation error: {str(e)}"


def validate_email(email: str) -> ValidationResult:
    """Validate email address format."""
    if not email:
        return False, "email is required"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "invalid email format"
    
    return True, None


def validate_url(url: str) -> ValidationResult:
    """Validate URL format."""
    if not url:
        return False, "URL is required"
    
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        return False, "invalid URL format"
    
    return True, None


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> ValidationResult:
    """Basic JSON schema validation."""
    try:
        # This is a simplified validation - in production, use jsonschema library
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})
        
        if not isinstance(data, dict):
            return False, "data must be an object"
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"required field '{field}' is missing"
        
        # Check field types
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type and not _check_type(value, expected_type):
                    return False, f"field '{field}' must be of type {expected_type}"
        
        return True, None
        
    except Exception as e:
        return False, f"schema validation error: {str(e)}"


def _check_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected JSON schema type."""
    type_mapping = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    expected_python_type = type_mapping.get(expected_type)
    if expected_python_type is None:
        return True  # Unknown type, allow it
    
    return isinstance(value, expected_python_type)


# Create global validator instances
file_validator = FileValidator()
security_validator = SecurityValidator()
api_validator = APIValidator()

# Export public interface
__all__ = [
    "FileValidator",
    "SecurityValidator", 
    "APIValidator",
    "validate_email",
    "validate_url",
    "validate_json_schema",
    "file_validator",
    "security_validator",
    "api_validator",
]
