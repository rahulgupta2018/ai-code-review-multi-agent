"""
This service provides callbacks and guardrails: pre- and post-processing hooks
for LLM interactions to ensure safety, compliance, and logging.

Use cases include:
- Guardrails: Block inappropriate content (before_model_callback)
- Validation: Check tool arguments (before_tool_callback)
- Logging: Track all operations (multiple callbacks)
- Modification: Add safety instructions (before_model_callback)
- Filtering: Remove PII from responses (after_model_callback)
- Metrics: Track usage statistics (state management)

Each callback function can inspect and modify the inputs/outputs as needed.
Example usage:
from util.callbacks_guardrails import (
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
    on_tool_error_callback,
    on_model_error_callback,
    initialize_state,
    finalize_state,
)
"""

import logging
from typing import Any, Dict, Optional
from google.adk.agents.callback_context import CallbackContext

# Setup logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def before_model_callback(input_data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-process input to the LLM model.
    Example: Add safety instructions or check for inappropriate content.
    """
    logger.debug("🔍 [before_model_callback] Pre-processing model input")
    # Example guardrail: Block inputs with banned words
    banned_words = state.get("banned_words", [])
    if any(word in input_data.get("prompt", "") for word in banned_words):
        raise ValueError("Input contains inappropriate content.")
    
    # Add safety instructions
    safety_instructions = "\nPlease ensure your response is safe and appropriate."
    input_data["prompt"] += safety_instructions
    return input_data

def after_model_callback(output_data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process output from the LLM model.
    Example: Filter out PII or log the response.
    """
    logger.debug("🔍 [after_model_callback] Post-processing model output")
    # Example filtering: Remove PII (simple example)
    pii_keywords = state.get("pii_keywords", [])
    for keyword in pii_keywords:
        output_data["response"] = output_data["response"].replace(keyword, "[REDACTED]")
    
    return output_data
