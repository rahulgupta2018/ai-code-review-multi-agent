# Gemini Model Configuration Guide

## Overview

This document explains how to use the optimized generation parameters with Google Gemini models in the ADK framework.

## Configuration Structure

The `util/llm_model.py` module now provides:

### 1. Model Instances
- `get_agent_model()` - Returns Gemini model for orchestrator
- `get_sub_agent_model()` - Returns Gemini model for sub-agents

### 2. Generation Configs
- `get_orchestrator_config()` - Optimal parameters for orchestrator (temp=0.4)
- `get_subagent_config()` - Optimal parameters for sub-agents (temp=0.2)

## Why Separate Configs?

Google ADK's `Gemini` class doesn't accept generation_config in the constructor. Instead:
1. The model instance is created with just the model name
2. Generation parameters are applied when the agent makes API calls
3. ADK agents handle this automatically if you configure them properly

## Optimal Parameters Discovered

### Orchestrator (Temperature 0.4)
```python
{
    "temperature": 0.4,        # Balanced for routing decisions
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,
}
```
**Why?** Orchestrators need flexibility for routing decisions while staying consistent.

### Sub-Agents (Temperature 0.2)
```python
{
    "temperature": 0.2,        # Low temperature for precise analysis
    "top_p": 0.85,
    "top_k": 30,
    "max_output_tokens": 2048,
}
```
**Why?** Code analysis requires precision, consistency, and structured output.

## How Google ADK Handles Generation Config

Google ADK agents apply generation config in one of these ways:

### Option 1: Agent Instruction (Implicit)
ADK may use default parameters or those specified in the agent's system instruction.

### Option 2: Runtime Configuration
When calling the agent, you can pass generation config:

```python
from google.adk import Runner
from util.llm_model import get_agent_model, get_subagent_config

model = get_agent_model()
config = get_subagent_config()

# The agent will use the model with optimal config
runner = Runner(agent=your_agent, ...)
```

### Option 3: Model-Level Config (If Supported)
Some ADK versions may support passing config at model creation. Check your ADK version documentation.

## Comparison: Ollama vs Gemini

| Feature | Ollama (LiteLlm) | Gemini (Google ADK) |
|---------|------------------|---------------------|
| **Constructor Params** | ✅ Accepts temperature, top_p, etc. | ❌ Only accepts model name |
| **Config Location** | Model instance | Separate config dict |
| **Streaming** | Configurable | ADK-managed |
| **Repeat Penalty** | ✅ Supported | ❌ Not available |
| **Max Tokens** | `max_tokens` | `max_output_tokens` |

## Usage in Your Agents

Your agents automatically use the configured models:

```python
from util.llm_model import get_agent_model, get_sub_agent_model

# Orchestrator uses get_agent_model()
orchestrator_agent = LlmAgent(
    name="orchestrator",
    model=get_agent_model(),  # Uses gemini-2.0-flash with temp=0.4 (via config)
    # ... other params
)

# Sub-agents use get_sub_agent_model()
code_quality_agent = Agent(
    name="code_quality",
    model=get_sub_agent_model(),  # Uses gemini-2.0-flash with temp=0.2 (via config)
    # ... other params
)
```

## Testing Generation Parameters

To verify Gemini is respecting your parameters, test with:

```bash
# Run a test with your current config
cd /Users/rahulgupta/Documents/Coding/agentic-codereview
python -c "
from util.llm_model import get_agent_model, get_orchestrator_config
import json

model = get_agent_model()
config = get_orchestrator_config()

print(f'Model: {model.model}')
print(f'Config: {json.dumps(config, indent=2)}')
"
```

## Switching Between Ollama and Gemini

The commented-out Ollama configuration in `llm_model.py` shows how to use LiteLlm:

```python
# To use Ollama (uncomment these lines):
agent_model = LiteLlm(
    model=OLLAMA_MODEL, 
    endpoint=OLLAMA_ENDPOINT,
    temperature=0.4,
    top_p=0.9,
    top_k=40,
    repeat_penalty=1.15,
    max_tokens=2048,
    stream=True
)

# To use Gemini (current configuration):
agent_model = Gemini(model=GEMINI_MODEL)
# Config applied via get_orchestrator_config()
```

## Expected Behavior

With these optimized parameters, you should see:

### Orchestrator (temp=0.4)
- ✅ Consistent but flexible routing decisions
- ✅ Natural language responses
- ✅ Appropriate delegation to sub-agents
- ✅ Balanced creativity and precision

### Sub-Agents (temp=0.2)
- ✅ Highly consistent structured output (JSON)
- ✅ Focused, precise code analysis
- ✅ Better adherence to requested format
- ✅ Fewer hallucinations
- ✅ More reproducible results

## Troubleshooting

### Issue: Generation config not being applied
**Solution**: Check if your ADK version supports generation_config. You may need to pass it when creating the Runner or in the agent's instruction.

### Issue: Responses still too creative/random
**Solution**: Lower the temperature further (try 0.1 for sub-agents). Update `SUBAGENT_GENERATION_CONFIG` in `llm_model.py`.

### Issue: Responses too rigid/repetitive
**Solution**: Increase temperature slightly (try 0.3 for sub-agents, 0.5 for orchestrator).

## Further Reading

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Google ADK Agent Framework](https://github.com/google/adk)
- [Temperature Parameter Testing Results](../tests/unit/TEMPERATURE_COMPARISON_RESULTS.md)
- [Model Parameter Tuning Guide](../tests/unit/MODEL_PARAMETERS_GUIDE.md)

## Next Steps

1. **Test your agents** with the new Gemini configuration
2. **Monitor response quality** - are they more consistent?
3. **Adjust if needed** - modify `ORCHESTRATOR_GENERATION_CONFIG` and `SUBAGENT_GENERATION_CONFIG`
4. **Compare with Ollama** - which gives better results for your use case?
