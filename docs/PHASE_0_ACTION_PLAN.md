# Phase 0: Foundation Setup - Immediate Action Plan

**Status:** Ready to Execute  
**Duration:** 1 week  
**Priority:** Critical  

---

## 🚨 **Critical Issues to Fix First**

Based on the code review, here are the immediate blocking issues that need to be addressed:

### **1. ADK Installation Issue**
```bash
# Current Error: "adk: command not found"
# Terminal shows: Exit Code: 127

# Solution:
cd /Users/rahulgupta/Documents/Coding/agentic-code-review-system
docker-compose exec ai-code-review-adk bash
pip install google-adk
# or
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **2. Agent Import Syntax Error**
```python
# BROKEN CODE in code_review_orchestrator/agent.py:
from .sub_agents import code_quality_agent import code_quality_analyst
#                                         ^^^^^^ SYNTAX ERROR

# FIX:
from .sub_agents.code_quality_agent.agent import root_agent as code_quality_agent
```

### **3. Empty Agent Files**
```bash
# These files are empty and need basic implementation:
- code_review_orchestrator/sub_agents/security_agent/agent.py
- code_review_orchestrator/sub_agents/engineering_practices_agent/agent.py
- services/config_service.py
- services/model_service.py
- services/session.py
```

---

## 📝 **Step-by-Step Action Plan**

### **Step 1: Fix Environment Setup (Day 1)**

#### **1.1 Check Current Python Environment**
```bash
cd /Users/rahulgupta/Documents/Coding/agentic-code-review-system
python3 --version  # Should show Python 3.11+
which python3
```

#### **1.2 Install Google ADK**
```bash
# Option A: Install directly
pip3 install google-adk

# Option B: Use container (recommended)
docker-compose build --no-cache ai-code-review-adk
docker-compose up -d ai-code-review-adk
docker-compose exec ai-code-review-adk pip install google-adk

# Verify installation
docker-compose exec ai-code-review-adk python -c "import google.adk; print('ADK installed successfully')"
```

#### **1.3 Test Basic Container Functionality**
```bash
# Test container startup
docker-compose logs ai-code-review-adk

# Test health check
curl -f http://localhost:8000/health

# Test ADK dev portal
curl -f http://localhost:8200
```

### **Step 2: Fix Agent Import Errors (Day 1-2)**

#### **2.1 Fix Orchestrator Agent**
Create this file: `code_review_orchestrator/__init__.py`
```python
# Empty init file for proper module structure
```

Fix `code_review_orchestrator/agent.py`:
```python
from google.adk.agents import Agent

# Import sub-agents (fix syntax error)
from .sub_agents.code_quality_agent.agent import root_agent as code_quality_agent

root_agent = Agent(
    name="code_review_orchestrator",
    model="gemini-2.0-flash",
    description="Code review orchestrator agent that manages code quality analysis tasks.",
    instruction="""
    You are a helpful assistant that reviews code for quality and best practices.
    Ask for the user's name and greet them by name.
    Delegate specific analysis tasks to specialized sub-agents.
    """,
    sub_agents=[code_quality_agent],
)
```

#### **2.2 Fix Code Quality Agent**
Update `code_review_orchestrator/sub_agents/code_quality_agent/agent.py`:
```python
from google.adk.agents import Agent

root_agent = Agent(
    name="code_quality_agent",
    model="gemini-2.0-flash",
    description="Code quality agent that reviews code for quality and best practices.",
    instruction="""
    You are a code quality specialist. Analyze the provided code and provide feedback on:
    - Code complexity and maintainability
    - Coding best practices
    - Potential improvements
    - Code structure and organization
    
    Use the available tools to perform detailed analysis.
    """,
    tools=[],  # Will add tools in Phase 1
)
```

### **Step 3: Create Minimal Agent Implementations (Day 2-3)**

#### **3.1 Security Agent**
Create `code_review_orchestrator/sub_agents/security_agent/agent.py`:
```python
from google.adk.agents import Agent

root_agent = Agent(
    name="security_agent",
    model="gemini-2.0-flash",
    description="Security analysis agent that identifies potential security vulnerabilities.",
    instruction="""
    You are a security specialist. Analyze the provided code for:
    - Common security vulnerabilities (OWASP Top 10)
    - Authentication and authorization issues
    - Data handling and input validation problems
    - Cryptographic implementation issues
    
    Provide specific, actionable security recommendations.
    """,
    tools=[],  # Will add security tools in Phase 3
)
```

#### **3.2 Engineering Practices Agent**
Create `code_review_orchestrator/sub_agents/engineering_practices_agent/agent.py`:
```python
from google.adk.agents import Agent

root_agent = Agent(
    name="engineering_practices_agent",
    model="gemini-2.0-flash",
    description="Engineering practices agent that evaluates adherence to software engineering best practices.",
    instruction="""
    You are an engineering practices specialist. Analyze the provided code for:
    - SOLID principles adherence
    - Test coverage and quality
    - Documentation completeness
    - Code organization and structure
    - CI/CD configuration quality
    
    Focus on maintainability and team collaboration aspects.
    """,
    tools=[],  # Will add engineering tools in Phase 3
)
```

### **Step 4: Create Minimal Service Implementations (Day 3-4)**

#### **4.1 Basic Config Service**
Create `services/config_service.py`:
```python
"""
Basic Configuration Service - Phase 0 Implementation
Will be enhanced in Phase 1
"""
import yaml
import os
from typing import Dict, Any, Optional


class ConfigurationService:
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
        self.config_dir = "config"
        
    def load_config(self) -> Dict[str, Any]:
        """Load basic configuration - minimal implementation for Phase 0"""
        if self.config_cache:
            return self.config_cache
            
        # Basic fallback configuration
        self.config_cache = {
            "llm": {
                "default_provider": "ollama",
                "providers": {
                    "ollama": {
                        "base_url": "http://host.docker.internal:11434",
                        "models": {
                            "llama3_1_8b": {
                                "name": "llama3.1:8b",
                                "max_tokens": 8192
                            }
                        }
                    }
                }
            }
        }
        return self.config_cache
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        config = self.load_config()
        return config.get("llm", {})
```

#### **4.2 Basic Model Service**
Create `services/model_service.py`:
```python
"""
Basic Model Service - Phase 0 Implementation
Will be enhanced in Phase 1 with ADK Runner integration
"""
from typing import Dict, Any, Optional
from .config_service import ConfigurationService


class ModelService:
    def __init__(self, config_service: Optional[ConfigurationService] = None):
        self.config_service = config_service or ConfigurationService()
        self.config = self.config_service.get_llm_config()
        
    def get_model(self, model_name: Optional[str] = None) -> str:
        """Get model name - basic implementation for Phase 0"""
        if model_name:
            return model_name
            
        # Return default model
        default_provider = self.config.get("default_provider", "ollama")
        providers = self.config.get("providers", {})
        
        if default_provider in providers:
            models = providers[default_provider].get("models", {})
            if models:
                first_model = next(iter(models.values()))
                return first_model.get("name", "gemini-2.0-flash")
                
        return "gemini-2.0-flash"  # Final fallback
```

#### **4.3 Basic Session Management with ADK Preparation**
Create `services/session.py`:
```python
"""
Basic Session Management - Phase 0 Implementation
Will be enhanced in Phase 1 with proper ADK SessionService and Runner
"""
from typing import Dict, Any, Optional
import uuid
import time


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    def create_session(self, session_id: Optional[str] = None, user_id: str = "default_user") -> str:
        """Create a new session - preparing for ADK SessionService patterns"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        self.sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "app_name": "code_review_system",  # ADK pattern
            "created_at": time.time(),
            "state": {},  # Will become ADK session state
            "history": []
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data - compatible with ADK patterns"""
        return self.sessions.get(session_id)
    
    def update_session_state(self, session_id: str, key: str, value: Any):
        """Update session state - mimics ToolContext.state pattern"""
        if session_id in self.sessions:
            self.sessions[session_id]["state"][key] = value
            
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get session state dict - for ADK ToolContext compatibility"""
        session = self.sessions.get(session_id)
        return session["state"] if session else {}
```

### **Step 5: Test Basic Functionality (Day 4-5)**

#### **5.1 Create Test Script**
Create `scripts/test_phase0.py`:
```python
#!/usr/bin/env python3
"""
Phase 0 Testing Script
Tests basic functionality after fixes
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all imports work"""
    try:
        import google.adk
        print("✅ Google ADK imported successfully")
        
        from services.config_service import ConfigurationService
        print("✅ ConfigurationService imported successfully")
        
        from services.model_service import ModelService
        print("✅ ModelService imported successfully")
        
        from services.session import SessionManager
        print("✅ SessionManager imported successfully")
        
        # Test agent imports
        from code_review_orchestrator.agent import root_agent
        print("✅ Orchestrator agent imported successfully")
        
        from code_review_orchestrator.sub_agents.code_quality_agent.agent import root_agent as cq_agent
        print("✅ Code quality agent imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_services():
    """Test basic service functionality"""
    try:
        # Test config service
        config_service = ConfigurationService()
        config = config_service.load_config()
        print("✅ Configuration service working")
        
        # Test model service
        model_service = ModelService(config_service)
        model_name = model_service.get_model()
        print(f"✅ Model service working, default model: {model_name}")
        
        # Test session manager
        session_manager = SessionManager()
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)
        print(f"✅ Session manager working, created session: {session_id}")
        
        return True
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

def test_adk_basic():
    """Test basic ADK functionality with ToolContext patterns"""
    try:
        from google.adk.agents import Agent
        from google.adk.tools.tool_context import ToolContext
        
        # Test basic tool with ToolContext (preparing for Phase 1)
        def test_tool(message: str, tool_context: ToolContext) -> dict:
            """Test tool with ToolContext integration."""
            # Access session state
            previous_messages = tool_context.state.get("previous_messages", [])
            previous_messages.append(message)
            
            # Update session state
            tool_context.state["previous_messages"] = previous_messages
            tool_context.state["last_message"] = message
            
            return {"message": f"Processed: {message}", "count": len(previous_messages)}
        
        # Create a simple test agent with ToolContext-aware tool
        test_agent = Agent(
            name="test_agent",
            model="gemini-2.0-flash",
            description="Test agent for Phase 0 validation with ToolContext patterns",
            instruction="You are a test agent. Use the test_tool to process messages.",
            tools=[test_tool],
            output_key="test_result"  # ADK pattern for automatic state saving
        )
        
        print("✅ Basic ADK agent creation with ToolContext successful")
        return True
    except Exception as e:
        print(f"❌ ADK test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Phase 0 Testing - Foundation Setup Validation")
    print("=" * 50)
    
    all_tests_passed = True
    
    print("\n1. Testing Imports...")
    all_tests_passed &= test_imports()
    
    print("\n2. Testing Services...")
    all_tests_passed &= test_services()
    
    print("\n3. Testing ADK Basic Functionality...")
    all_tests_passed &= test_adk_basic()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All Phase 0 tests passed! Ready for Phase 1.")
    else:
        print("❌ Some tests failed. Please fix issues before proceeding.")
        sys.exit(1)
```

#### **5.2 Run Tests**
```bash
# Make script executable
chmod +x scripts/test_phase0.py

# Run tests
cd /Users/rahulgupta/Documents/Coding/agentic-code-review-system
python3 scripts/test_phase0.py

# Or run in container
docker-compose exec ai-code-review-adk python scripts/test_phase0.py
```

### **Step 6: Validate ADK Integration (Day 5-7)**

#### **6.1 Test ADK Web Server**
```bash
# Test if ADK can discover agents
docker-compose exec ai-code-review-adk adk web --port 8000

# Should be accessible at http://localhost:8000
```

#### **6.2 Test ADK Dev Portal**
```bash
# Start ADK dev portal
docker-compose exec ai-code-review-adk adk dev-portal --port 8200

# Should be accessible at http://localhost:8200
```

#### **6.3 Create Basic End-to-End Test**
Create `scripts/test_e2e_phase0.py`:
```python
#!/usr/bin/env python3
"""
End-to-end test for Phase 0
Tests complete workflow with minimal functionality
"""
import requests
import json

def test_basic_agent_interaction():
    """Test basic agent interaction through ADK"""
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return False
            
        # Test basic agent endpoint (if available)
        # This will be implemented once ADK web server is working
        print("✅ Basic E2E test structure ready")
        return True
        
    except Exception as e:
        print(f"❌ E2E test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Phase 0 End-to-End Testing")
    success = test_basic_agent_interaction()
    if success:
        print("🚀 Phase 0 complete! Ready to start Phase 1.")
    else:
        print("❌ E2E test failed. Check configuration.")
```

---

## 📋 **Phase 0 Completion Checklist**

### **Environment Setup**
- [ ] Google ADK installed successfully
- [ ] Container environment working
- [ ] Python environment validated
- [ ] Basic health checks passing

### **Code Fixes**
- [ ] Agent import syntax errors fixed
- [ ] All empty files have basic implementations
- [ ] No critical syntax errors remain
- [ ] Module imports working correctly

### **Basic Services**
- [ ] ConfigurationService loads basic config
- [ ] ModelService returns model names
- [ ] SessionManager creates and manages sessions
- [ ] All services can be imported and instantiated

### **ADK Integration**
- [ ] Basic agents can be created with ToolContext patterns
- [ ] Tools properly utilize ToolContext for state access
- [ ] Agent output_key patterns working
- [ ] ADK web server can start
- [ ] Agent discovery working
- [ ] No ADK-related errors in logs

### **Testing**
- [ ] All unit tests pass
- [ ] Import tests successful
- [ ] Service tests working
- [ ] Basic E2E test structure ready

---

## 🎯 **Success Criteria for Phase 0**

When Phase 0 is complete, you should have:

1. **✅ Working Development Environment**
   - Container starts without errors
   - All Python imports work
   - ADK is properly installed

2. **✅ Basic Agent Structure**
   - Orchestrator agent loads without errors
   - Sub-agents have minimal implementations
   - Agent hierarchy follows ADK patterns

3. **✅ Foundation Services**
   - Configuration can be loaded
   - Model service returns model information
   - Session management works

4. **✅ ADK Integration with Best Practices**
   - `adk web` command works
   - Agents use ToolContext patterns correctly
   - Agent output_key for automatic state saving
   - Agents are discoverable
   - Basic agent interaction possible
   - Foundation ready for Runner/SessionService in Phase 1

---

## 🚀 **Next Steps After Phase 0**

Once Phase 0 is complete:

1. **Validate Everything Works**
   - Run all tests and verify they pass
   - Test ADK web server functionality
   - Ensure no blocking errors remain

2. **Document Current State**
   - Update README with current capabilities
   - Document any workarounds or limitations
   - Note any remaining issues for Phase 1

3. **Plan Phase 1 Execution**
   - Review Phase 1 requirements (ADK SessionService, Runner setup)
   - Set up development workflow
   - Begin implementing proper ADK SessionService integration
   - Add callback patterns for production safety

**Ready to get started? Begin with Step 1 and work through systematically!**