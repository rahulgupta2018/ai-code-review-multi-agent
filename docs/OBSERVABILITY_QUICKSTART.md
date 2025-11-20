# Quick Start: ADK Observability & Tracing

## ✅ What ADK Provides Out-of-the-Box

Google ADK includes **built-in observability** that automatically tracks:

- ✅ **Agent executions** - Which agents were invoked
- ✅ **Tool calls** - Which tools were executed with what parameters
- ✅ **LLM interactions** - Model requests, responses, token usage
- ✅ **Agent routing** - Orchestrator delegation decisions
- ✅ **Performance metrics** - Execution times, latencies
- ✅ **Session state** - Conversation context and history

**No additional configuration required!** It works automatically when using ADK.

---

## 🎯 Quick Access Methods

### 1. Visual UI (Easiest)

**Access**: http://localhost:8800/dev-ui

1. Open the ADK Dev UI
2. Start a conversation (creates a session)
3. Click on any message
4. Click **"Event Graph"** button to see:
   - Agent execution flow
   - Tool invocations
   - LLM calls with token usage
   - Timing information

### 2. Command-Line Analyzer (Fastest)

```bash
# Analyze most recent session
python scripts/analyze_traces.py

# Analyze specific session
python scripts/analyze_traces.py <session_id>
```

**Example Output**:
```
📊 Session Analysis: e99cba69-3a14-4ae8-9b24-afa276d4331e

🤖 Agent Executions: 3
   1. orchestrator_agent (2348ms)
   2. orchestrator_agent (6774ms)
   3. carbon_emission_agent (5685ms)

🔧 Tool Executions: 5
   - transfer_to_agent (4 calls)

💬 LLM Interactions: 3
   Model: gemini-2.0-flash
   Total Tokens: 6,734 (5,887 in + 847 out)
   Average Latency: 4934ms per call

⏱️  Performance Summary:
   Total Time: 25.4s
   LLM Time: 14.8s (58.2% of total)
```

### 3. Direct API Access

```bash
# List all sessions
curl http://localhost:8800/apps/orchestrator_agent/users/user/sessions

# Get traces for a session
curl http://localhost:8800/debug/trace/session/{session_id} | python3 -m json.tool

# Example
curl http://localhost:8800/debug/trace/session/e99cba69-3a14-4ae8-9b24-afa276d4331e | python3 -m json.tool
```

---

## 📊 What You Can Track

### Agent Execution
- Which agents were called (orchestrator, sub-agents)
- Execution order and timing
- Agent delegation patterns

### Tool Usage
- Which tools were invoked
- Tool parameters and results
- Tool execution time

### LLM Calls
- Model used (gemini-2.0-flash)
- Input/output tokens
- Response latency
- Cost estimation

### Performance
- End-to-end response time
- Agent processing time
- LLM time vs total time
- Bottleneck identification

---

## 🔍 Common Use Cases

### Debug Routing Issues
**Problem**: "Why didn't my security agent get called?"

**Solution**: Check traces for `transfer_to_agent` calls:
```bash
python scripts/analyze_traces.py <session_id>
# Look at "Tool Executions" section
```

### Track API Costs
**Problem**: "How many tokens am I using?"

**Solution**: 
```bash
python scripts/analyze_traces.py <session_id>
# Check "💬 LLM Interactions" section
```

### Find Performance Bottlenecks
**Problem**: "Why is this so slow?"

**Solution**: Look at timing breakdown:
- If LLM time is high (>80%) → Model latency
- If Agent time is high → Tool execution issues
- Check individual agent durations

### Verify Tool Execution
**Problem**: "Did my tool actually run?"

**Solution**: Check "🔧 Tool Executions" section in trace output

---

## 📚 Key Files & URLs

| Resource | Location |
|----------|----------|
| **ADK Dev UI** | http://localhost:8800/dev-ui |
| **Trace API** | http://localhost:8800/debug/trace/session/{session_id} |
| **Session API** | http://localhost:8800/apps/orchestrator_agent/users/user/sessions |
| **Trace Analyzer** | `scripts/analyze_traces.py` |
| **Full Guide** | `docs/OBSERVABILITY_GUIDE.md` |
| **Server Logs** | `agent_workspace/adk_web.log` |

---

## 💡 Pro Tips

1. **Session IDs**: Every conversation creates a unique session - copy the ID from the UI or logs
2. **Real-time Monitoring**: Tail the log file during testing:
   ```bash
   tail -f agent_workspace/adk_web.log
   ```
3. **Token Tracking**: Use traces to estimate costs before production
4. **Performance Testing**: Compare traces across different model configurations
5. **Error Debugging**: Check `finish_reason` in LLM traces (should be "stop")

---

## 🚀 Quick Test

Try this now:

1. **Start a conversation**: http://localhost:8800/dev-ui
2. **Send a message**: "Review this code: `def add(a, b): return a + b`"
3. **Check traces**:
   ```bash
   python scripts/analyze_traces.py
   ```
4. **View in UI**: Click the message → "Event Graph"

You should see:
- Orchestrator agent execution
- Transfer to code_quality_agent
- Sub-agent analysis
- LLM calls with token counts
- Total execution time

---

**That's it!** ADK handles all the tracing automatically. No extra setup needed. 🎉

For detailed information, see `docs/OBSERVABILITY_GUIDE.md`
