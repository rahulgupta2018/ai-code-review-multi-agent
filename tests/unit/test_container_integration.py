#!/usr/bin/env python3
"""
Integration test for the containerized agentic code review system.
Tests the ModelService integration and agent functionality.
"""

import requests
import json
import time

def test_api_health():
    """Test if the API is accessible."""
    try:
        response = requests.get("http://localhost:8080/docs", timeout=10)
        print(f"✓ API accessible: Status {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API not accessible: {e}")
        return False

def test_agent_discovery():
    """Test agent discovery endpoint."""
    try:
        response = requests.get("http://localhost:8080/agents", timeout=10)
        if response.status_code == 200:
            agents = response.json()
            print(f"✓ Agent discovery working: Found {len(agents)} agents")
            for agent in agents:
                print(f"  - {agent.get('name', 'Unknown agent')}")
            return True
        else:
            print(f"✗ Agent discovery failed: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Agent discovery error: {e}")
        return False

def test_code_review_endpoint():
    """Test the code review functionality."""
    try:
        test_request = {
            "code": """
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
""",
            "language": "python",
            "analysis_type": "comprehensive"
        }
        
        response = requests.post(
            "http://localhost:8080/analyze", 
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Code review endpoint working")
            print(f"  Response keys: {list(result.keys())}")
            return True
        else:
            print(f"✗ Code review failed: Status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Code review error: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint for interactive queries."""
    try:
        test_query = "Please analyze this Python function for code quality issues: def add(a, b): return a + b"
        
        response = requests.post(
            "http://localhost:8080/chat",
            json={"message": test_query},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Chat endpoint working")
            print(f"  Response keys: {list(result.keys())}")
            return True
        else:
            print(f"✗ Chat endpoint failed: Status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Chat endpoint error: {e}")
        return False

def main():
    """Run integration tests for the containerized system."""
    print("🧪 Testing Containerized Agentic Code Review System")
    print("=" * 60)
    
    # Wait for container to be fully ready
    print("⏳ Waiting for container to be ready...")
    time.sleep(5)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Agent Discovery", test_agent_discovery),
        ("Code Review Endpoint", test_code_review_endpoint),
        ("Chat Endpoint", test_chat_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
        
        if not success:
            print("⚠️  Test failed, but continuing with other tests...")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The system is working correctly.")
        return 0
    elif passed > 0:
        print("⚠️  Some tests passed. The system is partially functional.")
        return 1
    else:
        print("❌ All tests failed. There may be issues with the system.")
        return 2

if __name__ == "__main__":
    exit(main())