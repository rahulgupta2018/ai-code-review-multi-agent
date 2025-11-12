#!/usr/bin/env python3
"""
Test ADK Tools Implementation
Verify that the converted tools follow the proper ADK ToolContext pattern
"""

import asyncio
from typing import Dict, Any

# Mock ToolContext for testing since we don't have ADK installed
class MockSession:
    def __init__(self):
        self.id = "test_session_123"
        self.state = {}

class MockToolContext:
    def __init__(self, parameters: Dict[str, Any] = None):
        self.session = MockSession()
        self._parameters = parameters if parameters is not None else {}
    
    def get_session_parameters(self) -> Dict[str, Any]:
        return self._parameters

async def test_complexity_analyzer():
    """Test the complexity analyzer tool with ADK pattern"""
    print("🔧 Testing analyze_code_complexity with ADK ToolContext...")
    
    try:
        from tools.complexity_analyzer_tool import analyze_code_complexity
        
        # Create mock context with test code
        test_code = """
def complex_function(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0

class TestClass:
    def method1(self):
        pass
    
    def method2(self):
        for i in range(10):
            if i % 2 == 0:
                print(i)
"""
        
        tool_context = MockToolContext({
            'code': test_code,
            'language': 'python'
        })
        
        result = await analyze_code_complexity(tool_context)
        
        if result['status'] == 'success':
            print("✅ analyze_code_complexity executed successfully!")
            print(f"   - Cyclomatic complexity: {result['results']['cyclomatic_complexity']}")
            print(f"   - Function count: {result['results']['function_count']}")
            print(f"   - Class count: {result['results']['class_count']}")
            print(f"   - Session stored: {'last_complexity_analysis' in tool_context.session.state}")
            return True
        else:
            print(f"❌ analyze_code_complexity failed: {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ analyze_code_complexity test failed: {e}")
        return False

async def test_static_analyzer():
    """Test the static analyzer tool with ADK pattern"""
    print("\n🔧 Testing analyze_static_code with ADK ToolContext...")
    
    try:
        from tools.static_analyzer_tool import analyze_static_code
        
        # Create mock context with test code containing security issues
        test_code = """
import os
password = "hardcoded_password_123"
api_key = "sk-test123456789"

def unsafe_query(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    # TODO: Fix this security issue
    return query

def debug_function():
    print("Debug information")
    return True
"""
        
        tool_context = MockToolContext({
            'code': test_code,
            'language': 'python'
        })
        
        result = await analyze_static_code(tool_context)
        
        if result['status'] == 'success':
            print("✅ analyze_static_code executed successfully!")
            print(f"   - Security findings: {len(result['results']['security_findings'])}")
            print(f"   - Code quality issues: {len(result['results']['code_quality_issues'])}")
            print(f"   - Total issues: {result['summary']['total_issues']}")
            print(f"   - Session stored: {'last_static_analysis' in tool_context.session.state}")
            return True
        else:
            print(f"❌ analyze_static_code failed: {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ analyze_static_code test failed: {e}")
        return False

async def test_tree_sitter():
    """Test the tree-sitter tool with ADK pattern"""
    print("\n🔧 Testing parse_code_ast with ADK ToolContext...")
    
    try:
        from tools.tree_sitter_tool import parse_code_ast
        
        # Create mock context with test code
        test_code = """
def example_function():
    x = 10
    y = 20
    return x + y

class ExampleClass:
    def __init__(self):
        self.value = 0
"""
        
        tool_context = MockToolContext({
            'code': test_code,
            'language': 'python'
        })
        
        result = await parse_code_ast(tool_context)
        
        if result['status'] == 'success':
            print("✅ parse_code_ast executed successfully!")
            print(f"   - AST nodes count: {result['results']['ast_nodes_count']}")
            print(f"   - Line count: {result['results']['complexity_indicators']['line_count']}")
            print(f"   - Session stored: {'last_ast_analysis' in tool_context.session.state}")
            return True
        else:
            print(f"❌ parse_code_ast failed: {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ parse_code_ast test failed: {e}")
        return False

async def main():
    """Run all ADK tool tests"""
    print("🚀 Testing ADK ToolContext Pattern Implementation")
    print("=" * 50)
    
    results = []
    results.append(await test_complexity_analyzer())
    results.append(await test_static_analyzer())
    results.append(await test_tree_sitter())
    
    print("\n" + "=" * 50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All ADK tools are working correctly!")
        return True
    else:
        print("❌ Some tests failed - check the implementation")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)