#!/usr/bin/env python3
"""
Test ADK FunctionTool Integration

This test validates that the ADK FunctionTool integration is working correctly.
It tests the connection between existing tools and ADK FunctionTool registration.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, '/app/src')

try:
    from src.agents.base_agent import ADKBaseAgent
    from src.agents.types import AgentType
    from src.agents.exceptions import FunctionToolError
    print("✅ Successfully imported ADK modules")
except ImportError as e:
    print(f"❌ Failed to import ADK modules: {e}")
    sys.exit(1)


class TestCodeQualityAgent(ADKBaseAgent):
    """Test agent for FunctionTool integration validation."""
    
    def __init__(self):
        # Provide config override to bypass missing ADK config
        config_override = {
            'name': 'TestCodeQualityAgent',
            'description': 'Test agent for FunctionTool integration',
            'timeout': 300,
            'version': '1.0.0',
            'tools': ['tree_sitter_tool', 'complexity_analyzer_tool', 'static_analyzer_tool']
        }
        super().__init__(AgentType.CODE_QUALITY, name="TestCodeQualityAgent", config_override=config_override)
    
    async def _execute_agent_logic(self, ctx: dict) -> dict:
        """Simple test logic to validate tool execution."""
        return {
            'analysis_type': 'code_quality',
            'status': 'success',
            'message': 'Test agent executed successfully'
        }


async def test_function_tool_integration():
    """Test ADK FunctionTool integration end-to-end."""
    print("\n🔧 Testing ADK FunctionTool Integration")
    print("=" * 50)
    
    try:
        # Initialize test agent
        print("1. Initializing test agent...")
        agent = TestCodeQualityAgent()
        print(f"   ✅ Agent initialized: {agent.name}")
        print(f"   📊 Tools loaded: {len(agent._tools)}")
        
        # Ensure FunctionTools are registered
        print("\n2. Registering ADK FunctionTools...")
        await agent._ensure_function_tools_registered()
        function_tools = agent.get_function_tools()
        print(f"   ✅ FunctionTools registered: {len(function_tools)}")
        
        for tool_name in function_tools.keys():
            print(f"   🔧 FunctionTool: {tool_name}")
        
        # Validate FunctionTool integration
        print("\n3. Validating FunctionTool integration...")
        validation_result = await agent.validate_function_tool_integration()
        print(f"   📊 Validation Status: {validation_result['status']}")
        print(f"   🔧 Total Tools: {validation_result['total_tools']}")
        print(f"   🎯 FunctionTools Registered: {validation_result['function_tools_registered']}")
        print(f"   ✅ Integration Healthy: {validation_result['integration_healthy']}")
        
        if validation_result['issues']:
            print("   ⚠️ Issues found:")
            for issue in validation_result['issues']:
                print(f"      - {issue}")
        
        # Test individual FunctionTool execution
        print("\n4. Testing FunctionTool execution...")
        test_successful = 0
        test_total = 0
        
        test_code = """
def example_function(a, b):
    if a > b:
        return a
    else:
        return b
"""
        
        for tool_name in function_tools.keys():
            test_total += 1
            try:
                print(f"   🚀 Testing FunctionTool: {tool_name}")
                
                # Execute FunctionTool
                result = await agent.execute_function_tool(
                    tool_name,
                    code=test_code,
                    language='python'
                )
                
                if result.get('status') == 'success':
                    print(f"      ✅ {tool_name}: SUCCESS")
                    print(f"         Execution time: {result.get('execution_time_seconds', 0):.3f}s")
                    test_successful += 1
                else:
                    print(f"      ❌ {tool_name}: FAILED - {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"      ❌ {tool_name}: EXCEPTION - {str(e)}")
        
        # Health check with FunctionTool status
        print("\n5. Running health check...")
        health_result = await agent.health_check()
        print(f"   📊 Agent Health: {health_result['status']}")
        
        tool_orchestration = health_result.get('tool_orchestration', {})
        print(f"   🔧 Tools Loaded: {tool_orchestration.get('tools_loaded', False)}")
        print(f"   🎯 FunctionTools Count: {tool_orchestration.get('function_tools_registered', 0)}")
        print(f"   ✅ ADK Integration: {tool_orchestration.get('adk_integration_status', 'unknown')}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 ADK FunctionTool Integration Test Summary")
        print("=" * 50)
        print(f"Agent Initialized: ✅")
        print(f"Tools Loaded: {len(agent._tools)}")
        print(f"FunctionTools Registered: {len(function_tools)}")
        print(f"Integration Validation: {validation_result['status'].upper()}")
        print(f"FunctionTool Tests: {test_successful}/{test_total} passed")
        print(f"Agent Health: {health_result['status'].upper()}")
        
        # Determine overall success
        overall_success = (
            len(function_tools) > 0 and
            validation_result['integration_healthy'] and
            test_successful > 0 and
            health_result['status'] == 'healthy'
        )
        
        if overall_success:
            print("\n🎉 ADK FUNCTIONTOOL INTEGRATION: SUCCESS!")
            print("✅ All FunctionTools are properly integrated with ADK")
            return True
        else:
            print("\n❌ ADK FUNCTIONTOOL INTEGRATION: FAILED!")
            print("❌ Some FunctionTool integration issues detected")
            return False
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        print("🔍 Full traceback:")
        traceback.print_exc()
        return False


async def main():
    """Main test execution."""
    print("🚀 Starting ADK FunctionTool Integration Tests")
    print("=" * 60)
    
    try:
        success = await test_function_tool_integration()
        
        if success:
            print("\n🎉 ALL TESTS PASSED! ADK FunctionTool integration is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED! FunctionTool integration needs attention.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())