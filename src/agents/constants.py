"""
Constants for Agent components.

This module contains constants specific to agent operations,
workflows, sessions, and execution parameters.
"""

from enum import Enum

# Agent execution timeouts (seconds)
DEFAULT_AGENT_TIMEOUT = 300  # 5 minutes
QUICK_AGENT_TIMEOUT = 60   # 1 minute
LONG_AGENT_TIMEOUT = 900   # 15 minutes

# Workflow timeouts (seconds)
DEFAULT_WORKFLOW_TIMEOUT = 1800  # 30 minutes
QUICK_WORKFLOW_TIMEOUT = 300     # 5 minutes
LONG_WORKFLOW_TIMEOUT = 3600     # 1 hour

# Session timeouts (seconds)
DEFAULT_SESSION_TIMEOUT = 7200   # 2 hours
MAX_SESSION_TIMEOUT = 86400      # 24 hours

# Agent priority levels
AGENT_PRIORITY_CRITICAL = 1
AGENT_PRIORITY_HIGH = 2
AGENT_PRIORITY_MEDIUM = 3
AGENT_PRIORITY_LOW = 4

# Agent retry configuration
DEFAULT_RETRY_ATTEMPTS = 3
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 2  # exponential backoff multiplier

# Agent execution limits
MAX_CONCURRENT_AGENTS = 10
MAX_AGENTS_PER_WORKFLOW = 20
MAX_WORKFLOW_DEPTH = 5

# Agent result scoring
MIN_QUALITY_SCORE = 0.0
MAX_QUALITY_SCORE = 100.0
MIN_RISK_SCORE = 0.0
MAX_RISK_SCORE = 100.0

# Agent memory limits
MAX_AGENT_MEMORY_MB = 512
MAX_SESSION_MEMORY_MB = 2048

# Agent-specific analysis parameters
CODE_QUALITY_THRESHOLD = 70.0
SECURITY_RISK_THRESHOLD = 30.0
COMPLEXITY_THRESHOLD = 10
DOCUMENTATION_COVERAGE_THRESHOLD = 80.0

# Function tool limits
MAX_TOOL_EXECUTION_TIME = 60  # seconds
MAX_TOOL_OUTPUT_SIZE = 1024 * 1024  # 1MB
MAX_TOOLS_PER_AGENT = 50

# Agent metadata constants
AGENT_VERSION_KEY = "agent_version"
EXECUTION_CONTEXT_KEY = "execution_context"
PERFORMANCE_METRICS_KEY = "performance_metrics"

# Workflow execution states
WORKFLOW_STATE_PENDING = "pending"
WORKFLOW_STATE_RUNNING = "running"
WORKFLOW_STATE_COMPLETED = "completed"
WORKFLOW_STATE_FAILED = "failed"
WORKFLOW_STATE_CANCELLED = "cancelled"

# Agent health check constants
AGENT_HEALTH_CHECK_INTERVAL = 30  # seconds
AGENT_HEALTH_TIMEOUT = 10  # seconds
MAX_FAILED_HEALTH_CHECKS = 3

# Agent registry constants
MAX_AGENT_NAME_LENGTH = 100
MAX_AGENT_DESCRIPTION_LENGTH = 500
AGENT_CONFIG_VERSION = "1.0"

# Session management constants
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes
MAX_SESSIONS_PER_USER = 10

# Analysis result constants
MAX_FINDINGS_PER_AGENT = 1000
MAX_RECOMMENDATION_LENGTH = 1000
MAX_SUMMARY_LENGTH = 2000

# Agent communication constants
INTER_AGENT_MESSAGE_TIMEOUT = 30  # seconds
MAX_MESSAGE_SIZE = 10 * 1024  # 10KB
MAX_MESSAGES_PER_AGENT = 100