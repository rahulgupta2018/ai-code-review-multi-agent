#!/usr/bin/env python3
"""
Test script to verify BaseAgent AGDK integration implementation.

This script tests the BaseAgent AGDK integration without requiring 
actual Google Cloud credentials or services.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.base.base_agent import BaseAgent, AnalysisContext, FindingSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgent(BaseAgent):
    """Test agent implementation for AGDK integration testing."""
    
    def _define_capabilities(self):
        return ["test_analysis", "agdk_integration"]
    
    def analyze(self, context: AnalysisContext):
        from agents.base.base_agent import AnalysisResult
        
        # Create a test finding
        finding = self.create_finding(
            title="Test Finding",
            description="This is a test finding for AGDK integration",
            severity=FindingSeverity.INFO,
            category="test",
            file_path="test.py",
            recommendation="This is a test recommendation",
            confidence=0.85
        )
        
        self.add_finding(finding)
        
        return AnalysisResult(
            agent_name=self.name,
            findings=self.get_findings(),
            metrics=self.get_metrics(),
            execution_time=1.0,
            success=True,
            errors=[],
            metadata={}
        )


def test_baseagent_configuration_loading():
    """Test BaseAgent configuration loading."""
    print("\n=== Testing BaseAgent Configuration Loading ===")
    
    # Test with custom configuration
    test_config = {
        "behavior": {
            "confidence_threshold": 0.8,
            "enable_memory_integration": True,
            "enable_learning": True
        },
        "agdk": {
            "enabled": False  # Disabled for testing without Google Cloud
        },
        "quality_control": {
            "hallucination_prevention": {
                "enable_fact_checking": True
            }
        }
    }
    
    agent = TestAgent("test_agent", test_config)
    
    # Verify configuration loading
    config_summary = agent.get_configuration_summary()
    print(f"Agent: {config_summary['name']} v{config_summary['version']}")
    print(f"Memory enabled: {config_summary['memory_enabled']}")
    print(f"AGDK enabled: {config_summary['agdk_enabled']}")
    print(f"Learning enabled: {config_summary['learning_enabled']}")
    print(f"Confidence threshold: {config_summary['confidence_threshold']}")
    
    assert config_summary['confidence_threshold'] == 0.8
    assert config_summary['memory_enabled'] == True
    assert config_summary['agdk_enabled'] == False
    assert config_summary['learning_enabled'] == True
    
    print("✅ Configuration loading test passed!")
    return agent


def test_agdk_integration_methods():
    """Test AGDK integration methods."""
    print("\n=== Testing AGDK Integration Methods ===")
    
    # Create agent with AGDK disabled for testing
    test_config = {
        "agdk": {
            "enabled": False,
            "events": {
                "tool_execution_requested": {"enabled": True},
                "analysis_started": {"enabled": True}
            }
        }
    }
    
    agent = TestAgent("agdk_test_agent", test_config)
    
    # Test AGDK session methods (should handle gracefully when disabled)
    session_data = {
        "session_id": "test_session_123",
        "metadata": {"test": True}
    }
    
    # Test session start (should be no-op when AGDK disabled)
    agent.on_session_started(session_data)
    
    # Test event handling (should be no-op when AGDK disabled)
    event_data = {
        "tool_name": "test_tool",
        "parameters": {"test_param": "value"}
    }
    
    agent.handle_agdk_event("tool_execution_requested", event_data)
    
    # Test session finish (should be no-op when AGDK disabled)
    agent.on_session_finished(session_data)
    
    # Test AGDK info retrieval
    agdk_info = agent.get_agdk_session_info()
    print(f"AGDK session info: {agdk_info}")
    
    assert agdk_info['agdk_enabled'] == False
    assert agdk_info['session_active'] == False
    
    print("✅ AGDK integration methods test passed!")
    return agent


def test_feature_status():
    """Test feature status reporting."""
    print("\n=== Testing Feature Status ===")
    
    test_config = {
        "behavior": {
            "enable_memory_integration": True,
            "enable_learning": True
        },
        "agdk": {
            "enabled": False
        }
    }
    
    agent = TestAgent("feature_test_agent", test_config)
    
    # Test feature status
    feature_status = agent.get_feature_status()
    print(f"Feature status: {feature_status}")
    
    assert feature_status['memory_enabled'] == True
    assert feature_status['agdk_enabled'] == False
    assert feature_status['learning_active'] == False  # No patterns learned yet
    
    print("✅ Feature status test passed!")
    return agent


def test_agent_tools():
    """Test AGDK tools functionality."""
    print("\n=== Testing AGDK Tools ===")
    
    agent = TestAgent("tools_test_agent", {})
    
    # Test getting AGDK tools
    tools = agent.get_agdk_tools()
    print(f"Available AGDK tools: {tools}")
    
    expected_tools = ["base_quality_validator", "base_bias_checker", "base_evidence_validator"]
    assert tools == expected_tools
    
    print("✅ AGDK tools test passed!")
    return agent


def test_analysis_with_agdk_disabled():
    """Test analysis execution with AGDK disabled."""
    print("\n=== Testing Analysis with AGDK Disabled ===")
    
    agent = TestAgent("analysis_test_agent", {"agdk": {"enabled": False}})
    
    # Create test context
    context = AnalysisContext(
        files=[{"path": "test.py", "content": "print('hello')"}],
        configuration={},
        session_id="test_session",
        metadata={}
    )
    
    # Execute analysis
    result = agent.execute_analysis(context)
    
    print(f"Analysis result: Agent={result.agent_name}, Success={result.success}")
    print(f"Findings: {len(result.findings)}")
    print(f"Metrics: {result.metrics}")
    
    assert result.success == True
    assert len(result.findings) == 1
    assert result.agent_name == "analysis_test_agent"
    
    print("✅ Analysis execution test passed!")
    return agent


def main():
    """Run all BaseAgent AGDK integration tests."""
    print("🚀 Starting BaseAgent AGDK Integration Tests")
    print("=" * 60)
    
    try:
        # Run tests
        test_baseagent_configuration_loading()
        test_agdk_integration_methods()
        test_feature_status()
        test_agent_tools()
        test_analysis_with_agdk_disabled()
        
        print("\n" + "=" * 60)
        print("🎉 All BaseAgent AGDK Integration Tests Passed!")
        print("✅ Configuration loading works correctly")
        print("✅ AGDK integration methods handle disabled state gracefully")
        print("✅ Feature status reporting works")
        print("✅ AGDK tools framework is in place")
        print("✅ Analysis execution works with AGDK disabled")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)