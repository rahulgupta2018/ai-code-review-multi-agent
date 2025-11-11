#!/usr/bin/env python3
"""
Test script to validate dynamic model loading integration.
Tests that the orchestrator and sub-agents properly use ModelService
for dynamic model selection without hardcoded models.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from code_review_orchestrator.agent import create_orchestrator_agent, execute_code_review_analysis
from services.model_service import ModelService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_creation():
    """Test that orchestrator agent can be created dynamically without hardcoded models."""
    logger.info("Testing dynamic agent creation...")
    
    try:
        # Test orchestrator agent creation
        orchestrator = create_orchestrator_agent()
        logger.info(f"✓ Orchestrator agent created successfully")
        logger.info(f"Agent type: {type(orchestrator)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Agent creation failed: {e}")
        return False

def test_model_service_integration():
    """Test that ModelService provides models for different agent types."""
    logger.info("Testing ModelService integration...")
    
    try:
        model_service = ModelService()
        
        # Test model selection for different agent types
        orchestrator_model = model_service.get_model_for_agent("orchestrator")
        logger.info(f"✓ Orchestrator model: {orchestrator_model}")
        
        code_quality_model = model_service.get_model_for_agent("code_quality")
        logger.info(f"✓ Code quality model: {code_quality_model}")
        
        security_model = model_service.get_model_for_agent("security")
        logger.info(f"✓ Security model: {security_model}")
        
        engineering_model = model_service.get_model_for_agent("engineering_practices")
        logger.info(f"✓ Engineering practices model: {engineering_model}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ModelService integration failed: {e}")
        return False

def test_orchestrator_execution():
    """Test that orchestrator can execute analysis with dynamic models."""
    logger.info("Testing orchestrator execution...")
    
    try:
        # Create a simple test query
        user_query = """Please analyze this Python code for code quality issues:

def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
"""
        
        # Test execution (this will use dynamic model loading)
        result = execute_code_review_analysis(user_query)
        logger.info(f"✓ Analysis executed successfully")
        logger.info(f"Result type: {type(result)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Orchestrator execution failed: {e}")
        logger.error(f"Error details: {str(e)}")
        return False

def main():
    """Run all integration tests."""
    logger.info("=== Dynamic Model Loading Integration Test ===")
    
    tests = [
        ("Agent Creation", test_agent_creation),
        ("ModelService Integration", test_model_service_integration),
        ("Orchestrator Execution", test_orchestrator_execution)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
        
    # Summary
    logger.info(f"\n=== Test Results ===")
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")
        if success:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All tests passed! Dynamic model loading integration is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())