# ADK Observability Guide - Agent & Tool Tracing

## Overview

Google ADK provides **built-in observability** for tracking agent executions, tool calls, and LLM interactions. This guide shows you how to access and use these traces.

## 🎯 Accessing Traces in ADK Web UI

### 1. **Web Interface (Recommended)**

Your ADK server at `http://localhost:8800/dev-ui` provides a visual trace viewer:

1. **Access the Dev UI**:
   ```
   http://localhost:8800/dev-ui
   ```

2. **Create/Select a Session**:
   - Each conversation creates a new session with a unique ID
   - Sessions are listed in the UI sidebar

3. **View Traces**:
   - Click on any message/interaction in the chat
   - The **"Event Graph"** button shows the execution flow
   - Traces display:
     - ✅ Agent invocations (`invoke_agent`)
     - ✅ Sub-agent transfers (`transfer_to_agent`)
     - ✅ Tool executions (`execute_tool`)
     - ✅ LLM calls (`call_llm`)
     - ✅ Timing information (start_time, end_time, duration)
     - ✅ Input/output payloads
     - ✅ Token usage statistics

### 2. **Direct API Access**

You can also access trace data programmatically:

#### Get Session Traces
```bash
# List all sessions
curl http://localhost:8800/apps/orchestrator_agent/users/user/sessions

# Get specific session traces
curl http://localhost:8800/debug/trace/session/{session_id} | python3 -m json.tool

# Example
curl http://localhost:8800/debug/trace/session/e99cba69-3a14-4ae8-9b24-afa276d4331e | python3 -m json.tool
```

#### Get Event-Specific Traces
```bash
# Get trace for a specific event/interaction
curl http://localhost:8800/debug/trace/{event_id} | python3 -m json.tool

# Get event graph (execution flow visualization data)
curl http://localhost:8800/apps/orchestrator_agent/users/user/sessions/{session_id}/events/{event_id}/graph
```

## 📊 Understanding Trace Data

### Trace Structure

Each trace span contains:

```json
{
  "name": "invoke_agent orchestrator_agent",
  "span_id": 11793420044709008278,
  "trace_id": 176662007179865700031775966572438849363,
  "start_time": 1763467186882784000,
  "end_time": 1763467189231215000,
  "attributes": {
    "gen_ai.operation.name": "invoke_agent",
    "gen_ai.agent.name": "orchestrator_agent",
    "gen_ai.agent.description": "An orchestrator agent...",
    "gen_ai.conversation.id": "e99cba69-3a14-4ae8-9b24-afa276d4331e"
  },
  "parent_span_id": 1544769913189085153
}
```

### Key Trace Types

1. **`invoke_agent`** - Agent execution
   - Attributes: `gen_ai.agent.name`, `gen_ai.agent.description`
   - Shows which agent handled the request

2. **`call_llm`** - LLM API calls
   - Attributes:
     - `gen_ai.request.model`: Model name (e.g., "gemini-2.0-flash")
     - `gcp.vertex.agent.llm_request`: Full request payload
     - `gcp.vertex.agent.llm_response`: Full response payload
     - `gen_ai.usage.input_tokens`: Input tokens consumed
     - `gen_ai.usage.output_tokens`: Output tokens generated
     - `gen_ai.response.finish_reasons`: Completion reason

3. **`execute_tool`** - Tool invocations
   - Shows tool name and parameters
   - Includes tool execution results

4. **`transfer_to_agent`** - Sub-agent delegation
   - Shows orchestrator routing decisions
   - Links parent agent to child agent spans

### Example: Full Trace Hierarchy

```
invocation (root)
└── invoke_agent orchestrator_agent
    ├── call_llm (orchestrator decides routing)
    │   └── LLM response: transfer_to_agent(code_quality_agent)
    └── invoke_agent code_quality_agent
        ├── execute_tool complexity_analyzer_tool
        │   └── Tool result: {complexity: 5}
        └── call_llm (sub-agent generates response)
            └── LLM response: "Code quality is good..."
```

## 🔍 What You Can Track

### Agent Execution Flow
- ✅ Which agents were called
- ✅ Orchestrator routing decisions
- ✅ Sub-agent delegation chain
- ✅ Agent execution order (sequential vs parallel)
- ✅ Agent response times

### Tool Usage
- ✅ Which tools were invoked
- ✅ Tool input parameters
- ✅ Tool execution results
- ✅ Tool execution duration
- ✅ Tool success/failure status

### LLM Interactions
- ✅ Model used (gemini-2.0-flash)
- ✅ System instructions sent
- ✅ User prompts and context
- ✅ Model responses
- ✅ Token usage (input/output)
- ✅ Finish reasons (stop, max_tokens, etc.)
- ✅ Response latency

### Session State
- ✅ Session ID and metadata
- ✅ Conversation history
- ✅ User interactions
- ✅ Event timestamps

## 💡 Practical Use Cases

### 1. Debug Agent Routing Issues

**Problem**: Orchestrator not calling the right sub-agent

**Solution**: Check traces for `transfer_to_agent` calls:
```bash
curl http://localhost:8800/debug/trace/session/{session_id} | \
  jq '.[] | select(.name | contains("transfer_to_agent"))'
```

### 2. Identify Performance Bottlenecks

**Problem**: Slow response times

**Solution**: Calculate duration from trace timestamps:
```python
duration_ms = (end_time - start_time) / 1_000_000
```

Look for:
- Long `call_llm` spans → Model latency
- Long `execute_tool` spans → Tool performance issues

### 3. Track Token Usage

**Problem**: High API costs

**Solution**: Extract token usage from LLM traces:
```bash
curl http://localhost:8800/debug/trace/session/{session_id} | \
  jq '[.[] | select(.name == "call_llm") | .attributes."gen_ai.usage.input_tokens", .attributes."gen_ai.usage.output_tokens"] | add'
```

### 4. Verify Tool Execution

**Problem**: Tool not being called

**Solution**: Search for `execute_tool` spans:
```bash
curl http://localhost:8800/debug/trace/session/{session_id} | \
  jq '.[] | select(.name | contains("execute_tool"))'
```

### 5. Analyze Conversation Flow

**Problem**: Understanding multi-turn interactions

**Solution**: View session traces in chronological order:
```bash
curl http://localhost:8800/debug/trace/session/{session_id} | \
  jq 'sort_by(.start_time) | .[] | {name, start_time, duration: (.end_time - .start_time)}'
```

## 🛠️ Programmatic Access Example

### Python Script to Analyze Traces

```python
import requests
import json
from datetime import datetime

def get_session_traces(session_id: str):
    """Fetch and analyze traces for a session."""
    url = f"http://localhost:8800/debug/trace/session/{session_id}"
    response = requests.get(url)
    traces = response.json()
    
    # Analyze traces
    agent_calls = []
    tool_calls = []
    llm_calls = []
    
    for span in traces:
        span_type = span.get('name', '')
        
        if 'invoke_agent' in span_type:
            agent_name = span['attributes'].get('gen_ai.agent.name', 'unknown')
            duration_ms = (span['end_time'] - span['start_time']) / 1_000_000
            agent_calls.append({
                'agent': agent_name,
                'duration_ms': duration_ms,
                'timestamp': datetime.fromtimestamp(span['start_time'] / 1_000_000_000)
            })
        
        elif 'execute_tool' in span_type:
            # Tool name is in the span name after "execute_tool "
            tool_name = span_type.replace('execute_tool ', '')
            duration_ms = (span['end_time'] - span['start_time']) / 1_000_000
            tool_calls.append({
                'tool': tool_name,
                'duration_ms': duration_ms
            })
        
        elif 'call_llm' in span_type:
            attrs = span['attributes']
            llm_calls.append({
                'model': attrs.get('gen_ai.request.model', 'unknown'),
                'input_tokens': attrs.get('gen_ai.usage.input_tokens', 0),
                'output_tokens': attrs.get('gen_ai.usage.output_tokens', 0),
                'duration_ms': (span['end_time'] - span['start_time']) / 1_000_000
            })
    
    # Print summary
    print(f"📊 Session {session_id} Analysis")
    print(f"\n🤖 Agents Called: {len(agent_calls)}")
    for call in agent_calls:
        print(f"   - {call['agent']}: {call['duration_ms']:.0f}ms")
    
    print(f"\n🔧 Tools Executed: {len(tool_calls)}")
    for call in tool_calls:
        print(f"   - {call['tool']}: {call['duration_ms']:.0f}ms")
    
    print(f"\n💬 LLM Calls: {len(llm_calls)}")
    total_input = sum(c['input_tokens'] for c in llm_calls)
    total_output = sum(c['output_tokens'] for c in llm_calls)
    print(f"   - Total Input Tokens: {total_input}")
    print(f"   - Total Output Tokens: {total_output}")
    print(f"   - Average LLM Latency: {sum(c['duration_ms'] for c in llm_calls) / len(llm_calls):.0f}ms")

# Example usage
if __name__ == "__main__":
    session_id = "e99cba69-3a14-4ae8-9b24-afa276d4331e"  # Replace with your session ID
    get_session_traces(session_id)
```

## 📝 Log File Traces

ADK also logs traces to the console/log file:

```bash
# View agent execution logs
tail -f /Users/rahulgupta/Documents/Coding/agentic-codereview/agent_workspace/adk_web.log
```

Look for:
- `INFO - google_llm.py:133 - Sending out request, model: gemini-2.0-flash`
- `INFO - google_llm.py:186 - Response received from the model`
- Session creation: `INFO - adk_web_server.py:605 - New session created`

## 🎯 Best Practices

1. **Use Session IDs**: Always track which session you're debugging
2. **Check Event Graphs**: Visual representation helps understand complex flows
3. **Monitor Token Usage**: Track costs via `gen_ai.usage.*` attributes
4. **Time Analysis**: Calculate durations to find bottlenecks
5. **Error Tracking**: Look for `finish_reason` != "stop" in LLM calls
6. **Tool Verification**: Ensure tools are called with correct parameters

## 🚀 Advanced: Custom Tracing

You can also add custom trace spans (future enhancement):

```python
from google.adk.tracing import trace_span

@trace_span("custom_operation")
async def my_custom_function():
    # Your code here
    pass
```

## 📚 Additional Resources

- [Google ADK Documentation](https://github.com/google/adk)
- [OpenTelemetry Trace Semantics](https://opentelemetry.io/docs/concepts/signals/traces/)
- ADK Dev UI: `http://localhost:8800/dev-ui`
- Trace API: `http://localhost:8800/debug/trace/`

---

## Quick Reference

| What to Track | Trace Type | Key Attributes |
|--------------|------------|----------------|
| Agent execution | `invoke_agent` | `gen_ai.agent.name` |
| Tool calls | `execute_tool` | Tool name in span name |
| LLM requests | `call_llm` | `gen_ai.request.model`, `gen_ai.usage.*` |
| Agent routing | `transfer_to_agent` | Agent name parameter |
| Token usage | `call_llm` | `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` |
| Response time | All spans | `end_time - start_time` |

**Server URL**: `http://localhost:8800`  
**Dev UI**: `http://localhost:8800/dev-ui`  
**Trace API**: `http://localhost:8800/debug/trace/session/{session_id}`
