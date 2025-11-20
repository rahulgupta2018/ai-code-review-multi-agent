# ADK Runner Features & Usage Guide

Complete reference for using Google ADK Runner in the Code Review System.

## 📋 Table of Contents

1. [Runner Constructor](#runner-constructor)
2. [Key Methods](#key-methods)
3. [Event Structure](#event-structure)
4. [RunConfig Options](#runconfig-options)
5. [Practical Examples](#practical-examples)
6. [Best Practices](#best-practices)

---

## Runner Constructor

```python
Runner(
    *,
    app: Optional[App] = None,
    app_name: Optional[str] = None,
    agent: Optional[BaseAgent] = None,
    plugins: Optional[List[BasePlugin]] = None,
    artifact_service: Optional[BaseArtifactService] = None,
    session_service: BaseSessionService,
    memory_service: Optional[BaseMemoryService] = None,
    credential_service: Optional[BaseCredentialService] = None
)
```

### Current Usage in main.py:
```python
runner = Runner(
    agent=orchestrator_agent,
    app_name="Code Review System",
    session_service=session_service,  # JSONFileSessionService
)
```

### Available Services You Can Add:

- **artifact_service**: Store files, images, code snippets, analysis reports
- **memory_service**: Long-term memory across sessions (remember user preferences, past issues)
- **credential_service**: Secure storage for API keys, tokens
- **plugins**: Extend functionality (logging, monitoring, custom processing)

---

## Key Methods

### 1. `run_async()` - Main Production Method ⭐

**Current usage in main.py - This is what you're using!**

```python
async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content
):
    # Process events as they stream in
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                print(part.text.strip())
```

**Full Signature:**
```python
runner.run_async(
    *,
    user_id: str,
    session_id: str,
    invocation_id: Optional[str] = None,      # Resume interrupted conversation
    new_message: Optional[types.Content] = None,
    state_delta: Optional[dict[str, Any]] = None,  # Update session state
    run_config: Optional[RunConfig] = None
) -> AsyncGenerator[Event, None]
```

**Advanced Features You Can Use:**

#### Resume Interrupted Conversations:
```python
# Save invocation_id from previous run
last_invocation_id = None
async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content
):
    last_invocation_id = event.invocation_id
    # Process event...

# Later, resume if interrupted:
async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    invocation_id=last_invocation_id  # Continue from here
):
    # Process remaining events...
```

#### Update Session State Dynamically:
```python
# Update user preferences mid-conversation
async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content,
    state_delta={
        "user_preferences": {
            "analysis_depth": "detailed",
            "focus_areas": ["security", "performance"]
        }
    }
):
    # State is merged into session automatically
```

### 2. `run_debug()` - Quick Testing Method 🧪

**Perfect for testing agents without session complexity!**

```python
# Simple one-liner testing
await runner.run_debug("Check this code for security issues")

# Multiple queries in sequence
await runner.run_debug([
    "Hello!",
    "What's my name?",
    "Analyze this code..."
])

# Continue a debug session
await runner.run_debug(
    "What did we discuss?",
    session_id="debug_session_1"  # Reuse same session
)

# Capture events for inspection
events = await runner.run_debug(
    "Analyze this code",
    verbose=True,  # Show tool calls
    quiet=False    # Show output
)

# Process captured events
for event in events:
    if event.content:
        print(f"Author: {event.author}")
        print(f"Content: {event.content}")
```

**Full Signature:**
```python
runner.run_debug(
    user_messages: str | list[str],
    *,
    user_id: str = 'debug_user_id',
    session_id: str = 'debug_session_id',
    run_config: RunConfig | None = None,
    quiet: bool = False,      # Suppress output
    verbose: bool = False     # Show tool calls
) -> list[Event]
```

**Use Cases:**
- ✅ Unit testing agents
- ✅ Quick prototyping
- ✅ Debugging agent behavior
- ✅ Testing without session setup
- ❌ NOT for production (use run_async instead)

### 3. `rewind_async()` - Undo Agent Actions ⏪

**Rollback to previous state if something goes wrong!**

```python
# Track invocation IDs during conversation
invocation_history = []

async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content
):
    invocation_history.append(event.invocation_id)
    # Process event...

# User says "undo that" or error occurs
if user_wants_undo:
    # Rewind to before last invocation
    await runner.rewind_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        rewind_before_invocation_id=invocation_history[-1]
    )
    print("✅ Undone! Session restored to previous state.")
```

**Use Cases:**
- User wants to undo analysis
- Agent made an error
- Wrong tool was called
- Rollback after failed operation

### 4. `run_live()` - Real-time Streaming 🔴 (Experimental)

**For advanced real-time audio/video applications.**

```python
from google.adk.runners import LiveRequestQueue

queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id=USER_ID,
    session_id=SESSION_ID,
    live_request_queue=queue,
    run_config=RunConfig(
        streaming_mode=StreamingMode.AUDIO,
        save_live_audio=True
    )
):
    # Process real-time events
```

**Note:** Experimental feature - best for voice/video agents.

---

## Event Structure

Every event from `run_async()` contains:

### Core Fields:
```python
event.content          # Agent response (text, images, etc.)
event.author           # Who created this event (user, agent, tool)
event.invocation_id    # Unique ID for this conversation turn
event.timestamp        # When this event occurred
event.id               # Unique event ID
```

### Status Fields:
```python
event.turn_complete    # Is this turn finished?
event.partial          # Is this a partial response?
event.interrupted      # Was this interrupted?
event.finish_reason    # Why did generation stop?
event.error_code       # Error code if failed
event.error_message    # Error description
```

### Actions & Metadata:
```python
event.actions              # Tools called, function results
event.usage_metadata       # Token counts, costs
event.custom_metadata      # Your custom data
event.grounding_metadata   # Search grounding info
event.citation_metadata    # Source citations
event.cache_metadata       # Context cache usage
```

### Example Event Processing:
```python
async for event in runner.run_async(...):
    # Check for errors
    if event.error_code:
        print(f"❌ Error: {event.error_message}")
        continue
    
    # Get agent responses
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text"):
                print(f"💬 {event.author}: {part.text}")
    
    # Track usage (costs)
    if event.usage_metadata:
        print(f"🪙 Tokens used: {event.usage_metadata.total_token_count}")
    
    # Check if turn is complete
    if event.turn_complete:
        print("✅ Turn finished")
    
    # Process tool calls
    if event.actions and event.actions.tool_calls:
        for tool_call in event.actions.tool_calls:
            print(f"🔧 Tool called: {tool_call.name}")
```

---

## RunConfig Options

Configure agent behavior at runtime:

### Basic Configuration:
```python
from google.adk.runners import RunConfig

run_config = RunConfig(
    max_llm_calls=100,              # Prevent infinite loops
    custom_metadata={                # Your custom tracking data
        "analysis_type": "security",
        "user_tier": "premium"
    }
)

async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content,
    run_config=run_config
):
    # Runner respects these configs
```

### Available Options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_llm_calls` | int | 500 | Max agent iterations (prevents loops) |
| `custom_metadata` | dict | None | Your tracking data (user tier, request type) |
| `save_input_blobs_as_artifacts` | bool | False | Save uploaded files (DEPRECATED: use plugin) |
| `streaming_mode` | StreamingMode | NONE | Enable streaming responses |
| `support_cfc` | bool | False | Enable controlled function calling |

---

## Practical Examples

### Example 1: Enhanced Error Handling

**Upgrade your main.py with better error handling:**

```python
# In main.py conversation loop
try:
    last_invocation_id = None
    
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
        run_config=RunConfig(max_llm_calls=100)  # Safety limit
    ):
        # Track invocation for undo
        last_invocation_id = event.invocation_id
        
        # Check for errors
        if event.error_code:
            print(f"❌ Analysis failed: {event.error_message}")
            
            # Offer to undo
            retry = input("Would you like to undo and try again? (y/n): ")
            if retry.lower() == 'y':
                await runner.rewind_async(
                    user_id=USER_ID,
                    session_id=SESSION_ID,
                    rewind_before_invocation_id=last_invocation_id
                )
                print("✅ Undone. Please try again.")
            continue
        
        # Process normal response
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text.strip())
        
        # Show progress
        if event.partial:
            print(".", end="", flush=True)
        elif event.turn_complete:
            print("\n✅ Analysis complete")
            
except KeyboardInterrupt:
    print("\n⚠️ Interrupted by user")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Example 2: Track Token Usage & Costs

```python
total_tokens = 0
total_cost = 0.0

async for event in runner.run_async(...):
    if event.usage_metadata:
        tokens = event.usage_metadata.total_token_count
        total_tokens += tokens
        
        # Estimate cost (example: $0.000001 per token)
        total_cost += tokens * 0.000001
        
        print(f"🪙 Tokens: {tokens} | Total: {total_tokens} | Cost: ${total_cost:.4f}")
    
    # Your response processing...

print(f"\n💰 Final cost: ${total_cost:.4f}")
```

### Example 3: Add Undo Command

```python
# Enhanced conversation loop with undo
conversation_history = []

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break
    
    # Special undo command
    if user_input.lower() in ["undo", "rollback"]:
        if conversation_history:
            last_invocation = conversation_history.pop()
            await runner.rewind_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                rewind_before_invocation_id=last_invocation
            )
            print("✅ Last action undone!")
        else:
            print("❌ Nothing to undo")
        continue
    
    # Normal processing
    content = types.Content(role="user", parts=[types.Part(text=user_input)])
    
    last_invocation_id = None
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        last_invocation_id = event.invocation_id
        # Process event...
    
    # Track for undo
    if last_invocation_id:
        conversation_history.append(last_invocation_id)
```

### Example 4: Unit Testing with run_debug

```python
# tests/unit/test_agents.py
import pytest
from google.adk.runners import Runner
from agent_workspace.orchestrator_agent.agent import orchestrator_agent

@pytest.mark.asyncio
async def test_code_quality_analysis():
    runner = Runner(
        agent=orchestrator_agent,
        app_name="Test App",
        session_service=InMemorySessionService()
    )
    
    test_code = """
    def calculate(x, y):
        return x + y
    """
    
    events = await runner.run_debug(
        f"Analyze this code for quality:\n{test_code}",
        quiet=True  # Suppress output in tests
    )
    
    # Assert we got responses
    assert len(events) > 0
    
    # Check for quality analysis
    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text"):
                    response_text += part.text
    
    assert "quality" in response_text.lower()
    assert len(response_text) > 50  # Got substantial response

@pytest.mark.asyncio
async def test_security_analysis():
    runner = Runner(
        agent=orchestrator_agent,
        app_name="Test App",
        session_service=InMemorySessionService()
    )
    
    vulnerable_code = """
    import sqlite3
    def login(username, password):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query)
        return cursor.fetchone()
    """
    
    events = await runner.run_debug(
        f"Check this code for security issues:\n{vulnerable_code}",
        verbose=True  # See what tools are called
    )
    
    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text"):
                    response_text += part.text
    
    # Should detect SQL injection
    assert any(word in response_text.lower() for word in ["injection", "sql", "vulnerability"])
```

### Example 5: Dynamic State Updates

```python
# Update user preferences mid-conversation
async for event in runner.run_async(
    user_id=USER_ID,
    session_id=SESSION_ID,
    new_message=content,
    state_delta={
        "user_preferences": {
            "analysis_depth": "comprehensive",
            "focus_areas": ["security", "performance", "maintainability"]
        },
        "quality_metrics": {
            "issues_analyzed": 50,
            "critical_issues": 2
        }
    }
):
    # State is automatically merged into session
    # Next agent calls will see updated preferences
```

---

## Best Practices

### ✅ DO:

1. **Use `run_async()` for production**
   ```python
   # Good: Proper async streaming
   async for event in runner.run_async(...):
       process_event(event)
   ```

2. **Use `run_debug()` for testing**
   ```python
   # Good: Quick testing
   events = await runner.run_debug("test query", quiet=True)
   ```

3. **Track invocation IDs for undo**
   ```python
   invocation_history = []
   async for event in runner.run_async(...):
       invocation_history.append(event.invocation_id)
   ```

4. **Set max_llm_calls safety limit**
   ```python
   run_config = RunConfig(max_llm_calls=100)
   ```

5. **Check for errors in events**
   ```python
   if event.error_code:
       handle_error(event.error_message)
   ```

### ❌ DON'T:

1. **Don't use `run_debug()` in production**
   ```python
   # Bad: Debug method in production
   await runner.run_debug(user_input)  # Use run_async instead!
   ```

2. **Don't ignore error events**
   ```python
   # Bad: No error handling
   async for event in runner.run_async(...):
       print(event.content)  # What if error_code is set?
   ```

3. **Don't forget to check turn_complete**
   ```python
   # Bad: Processing incomplete turns
   if event.content:
       save_to_database(event)  # Might be partial!
   
   # Good: Wait for complete turn
   if event.turn_complete:
       save_to_database(event)
   ```

4. **Don't create runner in loop**
   ```python
   # Bad: Creating runner repeatedly
   while True:
       runner = Runner(...)  # WASTE!
       await runner.run_async(...)
   
   # Good: Create once
   runner = Runner(...)
   while True:
       await runner.run_async(...)
   ```

---

## Summary: What You Can Add to Your Project

Based on your current `main.py`, here are **practical enhancements** you can implement:

### 🎯 Quick Wins (Easy to Add):

1. **Add undo command**
   - Track `invocation_id` from events
   - Call `rewind_async()` on user command

2. **Better error messages**
   - Check `event.error_code`
   - Show user-friendly error descriptions

3. **Token usage tracking**
   - Monitor `event.usage_metadata`
   - Display cost estimates

4. **Progress indicators**
   - Show "..." while `event.partial` is True
   - Show "✅" when `event.turn_complete`

### 🚀 Advanced Features:

5. **Session resumability**
   - Save `invocation_id` on interruption
   - Resume with `invocation_id` parameter

6. **Dynamic preferences**
   - Update session state with `state_delta`
   - User can change analysis depth mid-conversation

7. **Unit tests with run_debug()**
   - Test agents without session complexity
   - Validate responses automatically

8. **Artifact storage**
   - Save analysis reports
   - Store code snippets with issues

Your current implementation is solid! These are optional enhancements based on ADK Runner capabilities.
