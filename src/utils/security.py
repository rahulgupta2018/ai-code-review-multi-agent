"""
Security utilities for ADK Multi-Agent Code Review MVP.

This module provides security functions including PII detection, input sanitization,
authentication helpers, and secure data handling for production systems.
"""

import hashlib
import hmac
import secrets
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
import base64
import json

from ..core.config import get_config
from ..core.exceptions import SecurityError, AuthenticationError, AuthorizationError
from ..core.constants import CORRELATION_ID_HEADER


class PIIDetector:
    """Detect and handle Personally Identifiable Information (PII)."""
    
    # Common PII patterns
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone_us': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
        'ssn_us': r'\b(?!000|666|9\d{2})\d{3}[-.\s]?(?!00)\d{2}[-.\s]?(?!0000)\d{4}\b',
        'credit_card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'mac_address': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
        'postal_code_us': r'\b\d{5}(?:-\d{4})?\b',
    }
    
    # Sensitive keywords that might indicate PII
    SENSITIVE_KEYWORDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
        'login', 'credential', 'private', 'confidential', 'personal',
        'name', 'address', 'phone', 'email', 'ssn', 'social'
    }
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PII_PATTERNS.items()
        }
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text and return findings."""
        findings = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                findings.append({
                    'type': pii_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': self._calculate_confidence(pii_type, match.group())
                })
        
        # Check for sensitive keywords in variable names or strings
        sensitive_findings = self._detect_sensitive_keywords(text)
        findings.extend(sensitive_findings)
        
        return findings
    
    def sanitize_pii(self, text: str, mask_char: str = '*') -> str:
        """Sanitize PII in text by replacing with mask characters."""
        sanitized = text
        
        for pii_type, pattern in self.compiled_patterns.items():
            def replace_match(match):
                original = match.group()
                if pii_type == 'email':
                    # Keep first character and domain
                    parts = original.split('@')
                    if len(parts) == 2:
                        username = parts[0]
                        domain = parts[1]
                        masked_username = username[0] + mask_char * (len(username) - 1)
                        return f"{masked_username}@{domain}"
                elif pii_type in ['phone_us', 'ssn_us']:
                    # Keep last 4 digits
                    digits_only = re.sub(r'\D', '', original)
                    if len(digits_only) >= 4:
                        return mask_char * (len(original) - 4) + original[-4:]
                elif pii_type == 'credit_card':
                    # Keep last 4 digits
                    return mask_char * (len(original) - 4) + original[-4:]
                else:
                    # Full masking for other types
                    return mask_char * len(original)
                
                return mask_char * len(original)
            
            sanitized = pattern.sub(replace_match, sanitized)
        
        return sanitized
    
    def _calculate_confidence(self, pii_type: str, value: str) -> float:
        """Calculate confidence score for PII detection."""
        if pii_type == 'email':
            # Simple email validation
            return 0.9 if '@' in value and '.' in value.split('@')[-1] else 0.5
        elif pii_type == 'credit_card':
            # Luhn algorithm check
            return 0.9 if self._luhn_check(re.sub(r'\D', '', value)) else 0.3
        elif pii_type == 'ssn_us':
            # Basic SSN validation
            digits = re.sub(r'\D', '', value)
            return 0.8 if len(digits) == 9 else 0.4
        else:
            return 0.7
    
    def _luhn_check(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        if not card_number.isdigit():
            return False
        
        digits = [int(d) for d in card_number]
        checksum = 0
        
        for i in range(len(digits) - 2, -1, -1):
            if (len(digits) - i) % 2 == 0:
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] = digits[i] // 10 + digits[i] % 10
        
        return sum(digits) % 10 == 0
    
    def _detect_sensitive_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Detect sensitive keywords that might indicate PII."""
        findings = []
        
        # Look for variable assignments or object properties with sensitive names
        for keyword in self.SENSITIVE_KEYWORDS:
            # Pattern for variable assignments like "password = ..." or '"password": ...'
            patterns = [
                rf'\b{keyword}\s*[:=]\s*[\'"][^\'"]*[\'"]',
                rf'[\'"{keyword}[\'"]?\s*[:=]\s*[\'"][^\'"]*[\'"]'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'type': 'sensitive_keyword',
                        'keyword': keyword,
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.6
                    })
        
        return findings


class InputSanitizer:
    """Sanitize inputs to prevent injection attacks."""
    
    # Characters that might be used in injection attacks
    DANGEROUS_CHARS = {
        '<', '>', '"', "'", '&', '\x00', '\r', '\n'
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+set',
        r'exec\s*\(',
        r'xp_cmdshell',
        r'sp_executesql'
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onclick\s*=',
        r'onerror\s*='
    ]
    
    def __init__(self):
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
    
    def sanitize_string(self, value: str, allow_html: bool = False) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        sanitized = value.replace('\x00', '')
        
        # Handle HTML/XSS
        if not allow_html:
            sanitized = self._escape_html(sanitized)
        
        # Remove or escape dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in ['<', '>', '"', "'", '&'] and allow_html:
                continue  # Skip HTML-related chars if HTML is allowed
            sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    def check_sql_injection(self, value: str) -> bool:
        """Check if input contains SQL injection patterns."""
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True
        return False
    
    def check_xss(self, value: str) -> bool:
        """Check if input contains XSS patterns."""
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return True
        return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe storage."""
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            max_name_len = 255 - len(ext) - 1
            sanitized = name[:max_name_len] + ('.' + ext if ext else '')
        
        return sanitized
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters."""
        html_escape_table = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, escape in html_escape_table.items():
            text = text.replace(char, escape)
        
        return text


class TokenManager:
    """Manage authentication tokens and API keys."""
    
    def __init__(self):
        self.config = get_config()
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key."""
        if not self.config.security.api_key_required:
            return True
        
        if not api_key:
            return False
        
        # Hash the provided key and compare with stored hashes
        valid_keys = self.config.security.api_keys
        return api_key in valid_keys
    
    def generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    def generate_api_key(self) -> str:
        """Generate a new API key."""
        return secrets.token_urlsafe(48)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        salt = secrets.token_bytes(32)
        key_hash = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000)
        return base64.b64encode(salt + key_hash).decode('utf-8')
    
    def verify_api_key_hash(self, api_key: str, key_hash: str) -> bool:
        """Verify an API key against its hash."""
        try:
            decoded = base64.b64decode(key_hash.encode('utf-8'))
            salt = decoded[:32]
            stored_hash = decoded[32:]
            
            key_hash_computed = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000)
            return hmac.compare_digest(stored_hash, key_hash_computed)
        except Exception:
            return False
    
    def create_jwt_token(self, payload: Dict[str, Any], secret: str, expires_in: int = 3600) -> str:
        """Create a JWT token (simplified implementation)."""
        import jwt
        
        payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
        payload['iat'] = datetime.utcnow()
        
        return jwt.encode(payload, secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str, secret: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            import jwt
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")


class RateLimiter:
    """Rate limiting for API requests."""
    
    def __init__(self):
        self.config = get_config()
        self.request_counts: Dict[str, List[datetime]] = {}
        self._lock = {}
    
    def is_rate_limited(self, identifier: str, window_minutes: int = 1, max_requests: int = None) -> bool:
        """Check if an identifier is rate limited."""
        if not self.config.security.enable_rate_limiting:
            return False
        
        if max_requests is None:
            max_requests = self.config.security.requests_per_minute
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        if identifier in self.request_counts:
            self.request_counts[identifier] = [
                req_time for req_time in self.request_counts[identifier]
                if req_time > window_start
            ]
        else:
            self.request_counts[identifier] = []
        
        # Check if rate limit exceeded
        current_count = len(self.request_counts[identifier])
        if current_count >= max_requests:
            return True
        
        # Record this request
        self.request_counts[identifier].append(now)
        return False
    
    def get_rate_limit_info(self, identifier: str, window_minutes: int = 1, max_requests: int = None) -> Dict[str, Any]:
        """Get rate limit information for an identifier."""
        if max_requests is None:
            max_requests = self.config.security.requests_per_minute
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier in self.request_counts:
            recent_requests = [
                req_time for req_time in self.request_counts[identifier]
                if req_time > window_start
            ]
            current_count = len(recent_requests)
        else:
            current_count = 0
        
        return {
            'limit': max_requests,
            'remaining': max(0, max_requests - current_count),
            'reset_time': window_start + timedelta(minutes=window_minutes),
            'current_count': current_count
        }


class SecurityAuditor:
    """Security auditing and logging."""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.sanitizer = InputSanitizer()
    
    def audit_request(self, request_data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Audit an incoming request for security issues."""
        findings = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'security_findings': [],
            'risk_score': 0.0
        }
        
        # Check for PII in request data
        request_str = json.dumps(request_data)
        pii_findings = self.pii_detector.detect_pii(request_str)
        if pii_findings:
            findings['security_findings'].append({
                'type': 'pii_detected',
                'details': pii_findings,
                'severity': 'medium'
            })
            findings['risk_score'] += 0.3
        
        # Check for injection attempts
        if self.sanitizer.check_sql_injection(request_str):
            findings['security_findings'].append({
                'type': 'sql_injection_attempt',
                'severity': 'high'
            })
            findings['risk_score'] += 0.8
        
        if self.sanitizer.check_xss(request_str):
            findings['security_findings'].append({
                'type': 'xss_attempt',
                'severity': 'high'
            })
            findings['risk_score'] += 0.7
        
        return findings
    
    def sanitize_log_data(self, data: Any) -> Any:
        """Sanitize data before logging to remove PII."""
        if isinstance(data, str):
            return self.pii_detector.sanitize_pii(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_log_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_log_data(item) for item in data]
        else:
            return data


# Create global instances
pii_detector = PIIDetector()
input_sanitizer = InputSanitizer()
token_manager = TokenManager()
rate_limiter = RateLimiter()
security_auditor = SecurityAuditor()

# Utility functions
def get_client_ip(headers: Dict[str, str]) -> str:
    """Extract client IP from request headers."""
    # Check for forwarded IP first
    forwarded_for = headers.get('X-Forwarded-For', '').split(',')[0].strip()
    if forwarded_for:
        return forwarded_for
    
    # Check other common headers
    real_ip = headers.get('X-Real-IP', '').strip()
    if real_ip:
        return real_ip
    
    # Fallback to direct connection IP
    return headers.get('Remote-Addr', 'unknown')


def secure_hash(data: str, salt: Optional[str] = None) -> str:
    """Create a secure hash of data."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    hash_obj = hashlib.sha256()
    hash_obj.update((data + salt).encode('utf-8'))
    return f"{salt}:{hash_obj.hexdigest()}"


def verify_secure_hash(data: str, hash_with_salt: str) -> bool:
    """Verify data against a secure hash."""
    try:
        salt, expected_hash = hash_with_salt.split(':', 1)
        actual_hash = secure_hash(data, salt).split(':', 1)[1]
        return hmac.compare_digest(expected_hash, actual_hash)
    except ValueError:
        return False


# Export public interface
__all__ = [
    "PIIDetector",
    "InputSanitizer",
    "TokenManager",
    "RateLimiter",
    "SecurityAuditor",
    "pii_detector",
    "input_sanitizer",
    "token_manager",
    "rate_limiter",
    "security_auditor",
    "get_client_ip",
    "secure_hash",
    "verify_secure_hash",
]
