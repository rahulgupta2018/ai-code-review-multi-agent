# Ollama Model Parameter Tuning Guide

This guide explains how to tune model parameters to improve code analysis quality.

## Key Parameters

### 1. **Temperature** (0.0 - 2.0)
Controls randomness/creativity in responses.

- **0.0-0.3**: Very focused, deterministic
  - ✅ Best for: Code analysis, structured output, JSON generation
  - ❌ May be: Repetitive, less creative
  
- **0.4-0.7**: Balanced
  - ✅ Best for: General tasks, explanations
  
- **0.8-2.0**: Creative, random
  - ❌ Not recommended for code analysis (too unpredictable)

**Recommendation for code review: 0.2 - 0.4**

### 2. **Top-P** (Nucleus Sampling, 0.0 - 1.0)
Controls diversity by limiting cumulative probability.

- **0.1-0.5**: Very focused, conservative
- **0.6-0.9**: Balanced (default: 0.9)
- **0.95-1.0**: More diverse

**Recommendation for code review: 0.85 - 0.95**

### 3. **Top-K** (10 - 100)
Limits vocabulary to top K most likely tokens.

- **10-20**: Very focused
- **30-50**: Balanced (default: 40)
- **60-100**: More diverse

**Recommendation for code review: 30 - 50**

### 4. **Repeat Penalty** (1.0 - 2.0)
Penalizes token repetition.

- **1.0**: No penalty
- **1.1-1.3**: Light penalty (recommended)
- **1.5+**: Strong penalty (may affect quality)

**Recommendation for code review: 1.1 - 1.2**

## Usage Examples

### Example 1: High Precision (Structured JSON Output)
```bash
python tests/unit/test_ollama_model_eval.py \
  --models gemma3:latest \
  --temperature 0.2 \
  --top-p 0.85 \
  --top-k 30 \
  --repeat-penalty 1.1
```

### Example 2: Balanced Quality
```bash
python tests/unit/test_ollama_model_eval.py \
  --models gemma3:latest granite4:latest \
  --temperature 0.3 \
  --top-p 0.9 \
  --top-k 40 \
  --repeat-penalty 1.15
```

### Example 3: More Detailed Analysis
```bash
python tests/unit/test_ollama_model_eval.py \
  --models gemma3:latest \
  --temperature 0.4 \
  --top-p 0.92 \
  --top-k 50 \
  --repeat-penalty 1.2
```

## Comparative Testing

To find optimal parameters, run multiple tests:

```bash
# Test 1: Very focused
python tests/unit/test_ollama_model_eval.py --models gemma3:latest \
  --temperature 0.2 --top-p 0.8 --top-k 30

# Test 2: Balanced
python tests/unit/test_ollama_model_eval.py --models gemma3:latest \
  --temperature 0.3 --top-p 0.9 --top-k 40

# Test 3: More creative
python tests/unit/test_ollama_model_eval.py --models gemma3:latest \
  --temperature 0.5 --top-p 0.95 --top-k 50
```

Compare outputs in `tests/unit/outputs/` directory.

## Expected Improvements

With optimized parameters (temp=0.2-0.3), you should see:

1. ✅ More consistent JSON structure
2. ✅ Better adherence to requested format
3. ✅ More focused, relevant analysis
4. ✅ Fewer hallucinations
5. ✅ More deterministic results (reproducible)

## Integration with Agent Framework

To use these parameters in your agents, update `util/llm_model.py`:

```python
from google.adk.models.lite_llm import LiteLlm

agent_model = LiteLlm(
    model=OLLAMA_MODEL,
    endpoint=OLLAMA_ENDPOINT,
    temperature=0.3,      # Add this
    top_p=0.9,            # Add this
    max_tokens=2048,      # Add this
)
```

**Note**: Check LiteLlm documentation for exact parameter names as they may differ from Ollama's native API.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Too repetitive | Increase temperature (0.3 → 0.4) or repeat_penalty (1.1 → 1.3) |
| Too random/creative | Decrease temperature (0.5 → 0.3) or top_p (0.95 → 0.85) |
| Incomplete responses | Increase num_predict (2048 → 4096) |
| JSON formatting issues | Lower temperature (0.4 → 0.2), lower top_k (50 → 30) |

## Performance vs Quality Trade-off

- **Lower temperature** = Faster responses (fewer tokens considered)
- **Higher temperature** = Slower responses (more exploration)

For production code review, prioritize **quality over speed** with conservative parameters.
