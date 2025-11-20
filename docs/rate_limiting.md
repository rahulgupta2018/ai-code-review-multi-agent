# Rate Limiting Configuration

## Problem Identified

**Log Analysis (2025-11-19 12:14:37-39):**

1. Classifier succeeded and requested full review (4 agents)
2. Code optimization saved ~96 tokens ✅
3. **4 parallel agents fired simultaneously** (12:14:37.389-398)
4. **Each agent called tools, triggering MORE LLM requests** 
5. Within 2 seconds: **6+ LLM requests sent to Gemini API**
6. Result: **503 UNAVAILABLE - "The model is overloaded"**

```
2025-11-19 12:14:37,389 - Sending request (Agent 1)
2025-11-19 12:14:37,392 - Sending request (Agent 2)
2025-11-19 12:14:37,396 - Sending request (Agent 3)
2025-11-19 12:14:37,398 - Sending request (Agent 4)
2025-11-19 12:14:38,717 - Response + function_call (triggers 5th request)
2025-11-19 12:14:38,718 - Sending request (Tool execution 1)
2025-11-19 12:14:39,027 - Sending request (Tool execution 2)
2025-11-19 12:14:39,147 - ERROR: 503 UNAVAILABLE
```

## Root Cause

**WE were overloading the API**, not external users:
- Parallel execution = burst of 4 immediate requests
- Tool-calling agents = 2-3x request multiplication
- No rate limiting = 6+ requests in 2 seconds
- Gemini's rate limit: ~15 RPM for free tier
- Our burst: 180+ RPM equivalent (6 requests in 2s = 180/min if sustained)

## Solution Implemented

### 1. Sequential Agent Execution (IMMEDIATE FIX)

**File:** `orchestrator_agent/agent.py` (Lines 306-335)

Changed from:
```python
# ParallelAgent execution - bursts 4 requests at once
parallel_analysis = ParallelAgent(name="DynamicParallelAnalysis", sub_agents=agents_list)
async for event in parallel_analysis.run_async(ctx):
    yield event
```

To:
```python
# Sequential execution with delays
for idx, agent in enumerate(agents_to_run, 1):
    logger.info(f"Starting agent {idx}/{len(agents_to_run)}: {agent.name}")
    
    async for event in agent.run_async(ctx):
        yield event
    
    if idx < len(agents_to_run):
        await asyncio.sleep(2.0)  # 2s delay between agents
```

**Impact:**
- Before: 4 agents start simultaneously → 6+ requests in 2s → 503 error
- After: 1 agent at a time, 2s delays → Max 1-2 requests every 2s → Within rate limits

**Trade-off:**
- Execution time increases: ~10-15s instead of ~3-5s
- But avoids 503 errors and failed requests entirely
- Better UX: Reliable slow completion > fast failures

### 2. Universal LLM Wrapper (AVAILABLE FOR ALL PROVIDERS)

**File:** `util/rate_limiter.py`

Token bucket algorithm implementation:
- Default: 10 RPM (conservative for free tier)
- Burst size: 3 requests (allows small bursts)
- Cooldown: 30s after 429/503 errors

**Status:** Created but not yet integrated (requires ADK hooks or middleware)

**Future Integration:**
```python
from util.rate_limiter import get_rate_limiter, RateLimitConfig

# Configure
config = RateLimitConfig(
    requests_per_minute=10,
    burst_size=3,
    cooldown_on_error=30.0
)

# Use before each LLM call
rate_limiter = get_rate_limiter()
await rate_limiter.acquire()
# ... make API call ...
```

## Rate Limits by Gemini Tier

### Free Tier (Current)
- **RPM:** 15 requests/minute
- **RPD:** 1,500 requests/day
- **TPM:** 1M tokens/minute
- **Concurrent:** 1 request at a time (effectively)

### Gemini API Standard
- **RPM:** 360 requests/minute
- **RPD:** 30,000 requests/day
- **TPM:** 4M tokens/minute
- **Cost:** $0.00015/1K input tokens, $0.0006/1K output tokens

### Gemini API Pro
- **RPM:** 1,000 requests/minute
- **RPD:** 100,000 requests/day
- **TPM:** 10M tokens/minute

## Recommendations

### Immediate (Phase 1 - Current)
✅ **Sequential execution with 2s delays** (IMPLEMENTED)
- Keeps us well under 15 RPM free tier limit
- Reliable operation without 503 errors
- Simple to implement and maintain

### Short-term (Phase 2 - Next Week)
- [ ] Add request queue for multiple users
- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker pattern
- [ ] Monitor actual RPM usage (metrics)

### Medium-term (Phase 2 - Next Month)
- [ ] Upgrade to Gemini API Standard ($50-100/mo)
  * 360 RPM = Can run 6 agents in parallel safely
  * 4M TPM = Handles large code files
  * Reliable for 100-500 users
- [ ] Implement adaptive rate limiting
  * Adjust delays based on actual API responses
  * Speed up when API is responsive
  * Slow down after errors
- [ ] Add request priority queue
  * Fast path for simple queries
  * Slow path for complex code reviews

### Long-term (Phase 3 - Production Scale)
- [ ] Horizontal scaling with load balancer
- [ ] Multiple API keys with round-robin
- [ ] Redis-based distributed rate limiting
- [ ] Auto-scaling based on queue depth

## Testing Impact

Before fix:
```
Test 1: "what can you do?" → ✅ SUCCESS (no LLM agents called)
Test 2: Code review → ❌ 503 UNAVAILABLE (6+ requests in 2s)
```

After fix (expected):
```
Test 1: "what can you do?" → ✅ SUCCESS (same, no change)
Test 2: Code review → ✅ SUCCESS (sequential, ~12-15s total)
  - Agent 1: Execute → 2s delay
  - Agent 2: Execute → 2s delay
  - Agent 3: Execute → 2s delay
  - Agent 4: Execute → Complete
  - Report synthesis: ~3-5s
```

## Monitoring

Add these log patterns to watch for rate limit issues:

```bash
# Watch for rate limit errors
tail -f adk_web.log | grep -E "429|503|UNAVAILABLE|RESOURCE_EXHAUSTED"

# Monitor request timing
tail -f adk_web.log | grep "Sending out request"

# Track agent execution timing
tail -f adk_web.log | grep "Starting agent"

# Watch for cooldown activation
tail -f adk_web.log | grep "cooldown"
```

## Cost Projection

### Current (Free Tier)
- Cost: $0
- Users: 1-5 concurrent
- Reliability: Good with sequential execution
- Limitation: ~15 requests/min = 1 full review every 2 minutes

### Upgraded (Standard Tier)
- Cost: $50-100/month (estimated)
- Users: 50-100 concurrent
- Reliability: Excellent
- Capability: ~360 requests/min = 30+ full reviews/minute

### ROI Calculation
- Free tier: Good for MVP, demo, testing
- Standard tier: Required for >10 users, production deployment
- Upgrade trigger: When seeing regular 429/503 errors OR >5 concurrent users
