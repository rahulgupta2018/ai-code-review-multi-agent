# ADK Session Management Upgrade - Phase 1 Implementation Guide

## Overview

This document outlines the transition from our custom Phase 0 session management to proper Google ADK SessionService patterns, based on the [ADK Agent Team Tutorial](https://google.github.io/adk-docs/tutorials/agent-team/).

## Key Changes Required

### 1. Session Management Architecture

**❌ Phase 0 (Custom Implementation):**
```python
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
```

**✅ Phase 1 (ADK-Compliant):**
```python
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

class CodeReviewSessionService:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.APP_NAME = "agentic_code_review_system"
```

### 2. Proper ADK Session Creation

**ADK Pattern (from tutorial):**
```python
# Create session with proper ADK triplet: app_name, user_id, session_id
session = await session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    state=initial_state  # Optional initial state
)
```

### 3. Runner Integration with SessionService

**ADK Pattern:**
```python
runner = Runner(
    agent=orchestrator_agent,
    app_name=APP_NAME,
    session_service=session_service
)
```

### 4. Agent Execution with Proper Context

**ADK Pattern:**
```python
# Execute agent with proper session context
async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=content
):
    if event.is_final_response():
        final_response = event.content.parts[0].text
        break
```

## Implementation Plan

### Phase 1.1: Core Session Service ✅ COMPLETED
- [x] Replace custom SessionManager with ADK InMemorySessionService
- [x] Implement proper app_name/user_id/session_id patterns
- [x] Add ADK Runner creation methods
- [x] Implement ADK-compliant agent calling patterns

### Phase 1.2: Agent Integration ✅ COMPLETED
- [x] Update orchestrator agent to use Runner with ModelService integration
- [x] Integrate ToolContext for sub-agents to access session state
- [x] Add proper output_key configuration for automatic state storage
- [x] Connect existing ModelService to all agents for dynamic model selection
- [ ] Implement callback patterns for guardrails (Phase 1.3)

### Phase 1.3: State Management
- [ ] Replace manual state updates with ToolContext.state patterns
- [ ] Add session state for agent progress tracking
- [ ] Implement analysis result persistence in session state
- [ ] Add user preferences storage in session state

### Phase 1.4: Tool Integration ⚠️ ARCHITECTURE CORRECTION NEEDED
- ❌ **INCORRECT PATTERN**: Separate `adk_setup.py` service (as shown in current plan)
- ✅ **CORRECT PATTERN**: Runner setup integrated directly in agent code
- [ ] Update tools to accept ToolContext parameter
- [ ] Enable tools to read/write session state via ToolContext.state
- [ ] Add tool-level session state management
- [ ] Implement state-aware tool behavior

## Required Dependencies

Add to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
google-adk = "^1.0.0"
google-genai = "^0.8.0"
```

## Migration Strategy

### 1. Backward Compatibility
- Keep existing SessionManager interface during transition
- Add ADK wrapper that maintains current API
- Gradual migration of components to ADK patterns

### 2. Testing Strategy
- Unit tests for ADK SessionService integration
- Integration tests for Runner execution
- End-to-end tests for agent delegation
- Session state persistence testing

### 3. Configuration Updates
- Update agent configurations to include proper ADK patterns
- Add session service configuration
- Update runner configuration for orchestrator

## Benefits of ADK Compliance

### 1. **Proper Session Management**
- Automatic session lifecycle management
- Built-in state persistence patterns
- Proper user/session isolation

### 2. **Tool Integration**
- Automatic ToolContext injection
- Session state access for tools
- State-aware tool behavior

### 3. **Agent Coordination**
- Proper sub-agent delegation patterns
- Automatic output_key state storage
- Built-in callback patterns for guardrails

### 4. **Scalability**
- Support for persistent session storage
- Horizontal scaling capabilities
- Production-ready session management

## Implementation Notes

### Current Status
- ✅ **services/session.py**: Updated to ADK-compliant patterns
- ✅ **Agent Integration**: Orchestrator and sub-agents use ADK Runner patterns
- ✅ **ModelService Integration**: All agents connected to existing ModelService
- ✅ **Session State**: Sub-agents update session state via ToolContext patterns
- ✅ **Dynamic Model Selection**: Context-aware model routing per agent type
- ❌ **Tool Context**: Tools don't have ToolContext access yet (Phase 1.3)
- ❌ **Callback Patterns**: Guardrails not implemented yet (Phase 1.3)

### Next Steps
1. Install ADK dependencies
2. Update orchestrator to use Runner patterns
3. Modify sub-agents to use ToolContext
4. Update tools to support session state
5. Add proper callback patterns

### Critical Architecture Corrections

### ❌ **INCORRECT**: Separate ADK Setup Service
The current phased plan (1.4) shows this incorrect pattern:
```python
# services/adk_setup.py - ❌ WRONG APPROACH
class ADKSetup:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.runners = {}
```

**Why this is wrong:**
- Violates ADK's intended architecture
- Creates unnecessary abstraction layer
- Goes against Google ADK tutorial patterns
- Separates Runner from agent execution context

### ✅ **CORRECT**: Runner Integration in Agent Code
Following Google ADK tutorial patterns:
```python
# In actual agent execution code
async def run_conversation():
    session_service = InMemorySessionService()
    
    # Create session
    session = await session_service.create_session(
        app_name="agentic_code_review_system",
        user_id="user_1",
        session_id="session_001"
    )
    
    # Create runner directly in execution context
    runner = Runner(
        agent=orchestrator_agent,
        app_name="agentic_code_review_system",
        session_service=session_service
    )
    
    # Execute agent
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            return event.content.parts[0].text
```

### Known Issues
- Import errors until ADK package is installed
- Type annotations may need adjustment
- Async/await patterns throughout the codebase
- Configuration updates required for ADK patterns
- **CRITICAL**: Remove planned `adk_setup.py` service approach

## Reference Implementation

Based on Google ADK tutorial Step 4 patterns:
```python
# Proper ADK session with state
session = await session_service.create_session(
    app_name="agentic_code_review_system",
    user_id="user_1",
    session_id="session_001",
    state={
        "analysis_results": {},
        "current_step": "initialized",
        "agent_progress": {},
        "review_preferences": {
            "focus_areas": ["quality", "security", "practices"],
            "detail_level": "comprehensive"
        }
    }
)

# Agent with proper state access and output_key
orchestrator_agent = Agent(
    name="code_review_orchestrator",
    model="gemini-2.0-flash",
    description="Code review orchestrator with session state management",
    instruction="...",
    sub_agents=[code_quality_agent, security_agent, engineering_practices_agent],
    output_key="orchestrator_response"  # Auto-saves response to session state
)

# Runner with SessionService
runner = Runner(
    agent=orchestrator_agent,
    app_name="agentic_code_review_system",
    session_service=session_service
)
```

This upgrade will make the system fully ADK-compliant and enable proper multi-agent orchestration with session state management.