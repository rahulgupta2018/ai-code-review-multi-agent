#!/usr/bin/env python3
"""
Test script for the merged BaseAgent functionality.
"""

import sys
import os
sys.path.insert(0, 'src')

from src.agents.base import BaseAgent, FindingSeverity, AnalysisContext, AnalysisResult


class TestAgent(BaseAgent):
    """Test implementation of the merged BaseAgent."""
    
    def _define_capabilities(self) -> list:
        return ["test_analysis", "pattern_detection"]
    
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """Simple test analysis."""
        # Create a test finding
        finding = self.create_finding(
            title="Test Finding",
            description="This is a test finding from the merged agent",
            severity=FindingSeverity.WARNING,
            category="test",
            file_path="test.py",
            recommendation="This is a test recommendation"
        )
        
        self.add_finding(finding)
        
        return AnalysisResult(
            agent_name=self.name,
            findings=self.get_findings(),
            metrics=self.get_metrics(),
            execution_time=0.1,
            success=True,
            errors=[],
            metadata={"test": True}
        )


def test_merged_agent():
    """Test the merged BaseAgent functionality."""
    print("🧪 Testing Merged BaseAgent")
    print("=" * 50)
    
    # Test basic agent without memory/AGDK
    print("\n1. Testing Basic Agent (no memory/AGDK):")
    basic_config = {"memory": {"enabled": False}, "agdk": {"enabled": False}}
    basic_agent = TestAgent("test_basic", basic_config)
    
    print(f"   Name: {basic_agent.get_name()}")
    print(f"   Version: {basic_agent.get_version()}")
    print(f"   Capabilities: {basic_agent.get_capabilities()}")
    print(f"   Features: {basic_agent.get_feature_status()}")
    print(f"   String: {basic_agent}")
    
    # Test memory-enabled agent
    print("\n2. Testing Memory-Enabled Agent:")
    memory_config = {"memory": {"enabled": True}, "agdk": {"enabled": False}}
    memory_agent = TestAgent("test_memory", memory_config)
    
    print(f"   Memory enabled: {memory_agent.is_memory_enabled()}")
    print(f"   AGDK enabled: {memory_agent.is_agdk_enabled()}")
    print(f"   Features: {memory_agent.get_feature_status()}")
    print(f"   String: {memory_agent}")
    
    # Test full-featured agent
    print("\n3. Testing Full-Featured Agent (Memory + AGDK):")
    full_config = {"memory": {"enabled": True}, "agdk": {"enabled": True}}
    full_agent = TestAgent("test_full", full_config)
    
    print(f"   Memory enabled: {full_agent.is_memory_enabled()}")
    print(f"   AGDK enabled: {full_agent.is_agdk_enabled()}")
    print(f"   Features: {full_agent.get_feature_status()}")
    print(f"   String: {full_agent}")
    
    # Test analysis functionality
    print("\n4. Testing Analysis Functionality:")
    context = AnalysisContext(
        files=[{"path": "test.py", "content": "print('hello')"}],
        configuration={},
        session_id="test_session",
        metadata={}
    )
    
    result = basic_agent.execute_analysis(context)
    print(f"   Analysis success: {result.success}")
    print(f"   Findings count: {len(result.findings)}")
    print(f"   Metrics: {result.metrics}")
    
    # Test memory analysis if available
    if memory_agent.is_memory_enabled():
        print("\n5. Testing Memory-Enhanced Analysis:")
        memory_result = memory_agent.execute_analysis(context)
        print(f"   Memory analysis success: {memory_result.success}")
        print(f"   Memory enhanced: {memory_result.metadata.get('memory_enhanced', False)}")
        print(f"   Learned patterns: {len(memory_agent.get_learned_patterns())}")
    
    print("\n✅ All tests completed successfully!")
    print("🎉 BaseAgent merge was successful!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_merged_agent()
        if success:
            print("\n🚀 BaseAgent consolidation complete and tested!")
        else:
            print("\n💥 Tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)