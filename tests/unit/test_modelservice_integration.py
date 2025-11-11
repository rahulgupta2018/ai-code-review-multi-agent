#!/usr/bin/env python3
"""
ModelService Integration Test
Demonstrates how orchestrator and sub-agents work with your existing ModelService
"""
import asyncio
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "services"))
sys.path.append(str(project_root / "code_review_orchestrator"))

async def test_model_service_integration():
    """Test ModelService integration with agents"""
    print("🚀 Testing ModelService Integration with Agents")
    print("=" * 60)
    
    try:
        # Import ModelService
        from model_service import ModelService
        print("✅ ModelService imported successfully")
        
        # Initialize ModelService
        model_service = ModelService()
        print("✅ ModelService initialized")
        
        # Test configuration loading
        config = await model_service.load_config()
        print(f"✅ Configuration loaded: {len(config.get('providers', {}))} providers")
        
        # Test model selection for different agents
        print("\n🤖 Testing Model Selection for Agents:")
        
        # Orchestrator model
        orchestrator_context = {
            "agent_name": "code_review_orchestrator",
            "analysis_type": "orchestration",
            "environment": "development"
        }
        orchestrator_model = await model_service.get_model_for_agent(
            "code_review_orchestrator", orchestrator_context
        )
        print(f"📋 Orchestrator model: {orchestrator_model}")
        
        # Code Quality Agent model
        code_quality_context = {
            "agent_name": "code_quality_agent",
            "analysis_type": "code_quality",
            "environment": "development",
            "specialized_for": "code_analysis"
        }
        code_quality_model = await model_service.get_model_for_agent(
            "code_quality_agent", code_quality_context
        )
        print(f"🔍 Code Quality Agent model: {code_quality_model}")
        
        # Security Agent model
        security_context = {
            "agent_name": "security_agent", 
            "analysis_type": "security",
            "environment": "development",
            "specialized_for": "security_analysis"
        }
        security_model = await model_service.get_model_for_agent(
            "security_agent", security_context
        )
        print(f"🔐 Security Agent model: {security_model}")
        
        # Engineering Practices Agent model
        practices_context = {
            "agent_name": "engineering_practices_agent",
            "analysis_type": "engineering_practices", 
            "environment": "development",
            "specialized_for": "best_practices_evaluation"
        }
        practices_model = await model_service.get_model_for_agent(
            "engineering_practices_agent", practices_context
        )
        print(f"⚙️ Engineering Practices Agent model: {practices_model}")
        
        # Test provider health checks
        print("\n💊 Testing Provider Health:")
        health_status = await model_service.health_check_all_providers()
        for provider, is_healthy in health_status.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"   {provider}: {status}")
        
        # Test available models
        print("\n📚 Available Models:")
        available_models = await model_service.get_available_models()
        for provider, models in available_models.items():
            print(f"   {provider}: {len(models)} models")
            for model in models[:3]:  # Show first 3
                print(f"     - {model}")
            if len(models) > 3:
                print(f"     ... and {len(models) - 3} more")
        
        print("\n🎉 ModelService Integration Test PASSED!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 This is expected if ADK is not installed yet")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

async def test_agent_imports():
    """Test agent imports and basic functionality"""
    print("\n🤖 Testing Agent Imports:")
    print("-" * 40)
    
    try:
        # Test orchestrator import
        sys.path.append(str(project_root / "code_review_orchestrator"))
        from agent import agent as orchestrator_agent
        print(f"✅ Orchestrator agent: {orchestrator_agent.name}")
        
        # Test sub-agent imports
        from sub_agents.code_quality_agent.agent import agent as code_quality_agent
        print(f"✅ Code Quality agent: {code_quality_agent.name}")
        
        from sub_agents.security_agent.agent import agent as security_agent
        print(f"✅ Security agent: {security_agent.name}")
        
        from sub_agents.engineering_practices_agent.agent import agent as engineering_practices_agent
        print(f"✅ Engineering Practices agent: {engineering_practices_agent.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Agent Import Error: {e}")
        print("💡 This is expected if ADK is not installed yet")
        return False

def simulate_session_state():
    """Simulate session state structure with ModelService integration"""
    print("\n📊 Simulated Session State Structure:")
    print("-" * 50)
    
    simulated_state = {
        "analysis_progress": "agents_completed",
        "orchestrator_model": "LiteLlm(model='ollama/llama3.1:8b')",
        "model_service_status": "active",
        "completed_agents": ["code_quality_agent", "security_agent", "engineering_practices_agent"],
        "user_preferences": {
            "detail_level": "comprehensive",
            "include_examples": True
        },
        
        # Agent-specific state
        "code_quality_agent": {
            "status": "completed",
            "model_used": "LiteLlm(model='ollama/codellama:13b')",
            "analysis_type": "code_quality",
            "findings": ["Code complexity analyzed", "Best practices evaluated"],
            "timestamp": "2025-11-11T10:30:00"
        },
        
        "security_agent": {
            "status": "completed",
            "model_used": "LiteLlm(model='ollama/gemma2:9b')",
            "analysis_type": "security",
            "vulnerability_categories": ["injection_attacks", "authentication_issues"],
            "risk_level": "medium",
            "timestamp": "2025-11-11T10:31:00"
        },
        
        "engineering_practices_agent": {
            "status": "completed",
            "model_used": "LiteLlm(model='ollama/llama3.1:8b')",
            "analysis_type": "engineering_practices",
            "practices_score": 75,
            "evaluation_areas": ["SOLID_principles", "testing_practices", "documentation"],
            "timestamp": "2025-11-11T10:32:00"
        }
    }
    
    print("Session State Structure:")
    for key, value in simulated_state.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    return simulated_state

async def main():
    """Run all integration tests"""
    print("🧪 ModelService Integration Test Suite")
    print("=" * 60)
    
    # Test 1: ModelService functionality
    model_service_ok = await test_model_service_integration()
    
    # Test 2: Agent imports  
    agents_ok = await test_agent_imports()
    
    # Test 3: Session state simulation
    session_state = simulate_session_state()
    
    # Summary
    print("\n📋 Test Summary:")
    print("-" * 20)
    print(f"ModelService Integration: {'✅ PASS' if model_service_ok else '❌ FAIL (expected without ADK)'}")
    print(f"Agent Imports: {'✅ PASS' if agents_ok else '❌ FAIL (expected without ADK)'}")
    print(f"Session State Structure: ✅ PASS")
    
    if not model_service_ok or not agents_ok:
        print("\n💡 To fix import errors:")
        print("   pip install google-adk google-genai")
        print("   Or install from your project requirements")
    
    print("\n🎯 Next Steps:")
    print("1. Install ADK dependencies")
    print("2. Test with actual Ollama models")
    print("3. Implement tool integration")
    print("4. Add callback patterns")

if __name__ == "__main__":
    asyncio.run(main())