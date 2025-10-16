"""
Constants for API components.

This module contains constants specific to API operations,
HTTP handling, and request/response processing.
"""

from enum import Enum

# HTTP Headers
CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"

# Content Types
JSON_CONTENT_TYPE = "application/json"
TEXT_CONTENT_TYPE = "text/plain"
YAML_CONTENT_TYPE = "application/x-yaml"

# Default headers for API responses
DEFAULT_RESPONSE_HEADERS = {
    "Content-Type": JSON_CONTENT_TYPE,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
}

# HTTP Methods (already defined in types.py, this is for string constants)
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Status Code Groups
INFORMATIONAL_STATUS_CODES = range(100, 200)
SUCCESS_STATUS_CODES = range(200, 300)
REDIRECTION_STATUS_CODES = range(300, 400)
CLIENT_ERROR_STATUS_CODES = range(400, 500)
SERVER_ERROR_STATUS_CODES = range(500, 600)

# Common HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_502_BAD_GATEWAY = 502
HTTP_503_SERVICE_UNAVAILABLE = 503
HTTP_504_GATEWAY_TIMEOUT = 504

# Response messages
RESPONSE_MESSAGES = {
    "success": "Operation completed successfully",
    "created": "Resource created successfully",
    "updated": "Resource updated successfully",
    "deleted": "Resource deleted successfully",
    "not_found": "Resource not found",
    "bad_request": "Invalid request format",
    "unauthorized": "Authentication required",
    "forbidden": "Access denied",
    "conflict": "Resource conflict",
    "validation_error": "Request validation failed",
    "rate_limit_exceeded": "Rate limit exceeded",
    "internal_error": "Internal server error",
    "service_unavailable": "Service temporarily unavailable",
    "timeout": "Request timeout"
}

# Timeout constants (seconds)
DEFAULT_API_TIMEOUT = 30
DEFAULT_REQUEST_TIMEOUT = 60
LONG_RUNNING_REQUEST_TIMEOUT = 300

# Rate limiting constants
DEFAULT_RATE_LIMIT = 1000  # requests per hour
DEFAULT_RATE_LIMIT_WINDOW = 3600  # seconds

# Request size limits (bytes)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_JSON_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# API versioning
API_VERSION_HEADER = "API-Version"
SUPPORTED_API_VERSIONS = ["v1"]
DEFAULT_API_VERSION = "v1"

# CORS settings
CORS_MAX_AGE = 86400  # 24 hours
CORS_ALLOW_CREDENTIALS = True

# Request context constants
MAX_CORRELATION_ID_LENGTH = 36  # UUID length
MAX_USER_AGENT_LENGTH = 500