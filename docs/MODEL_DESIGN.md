
[BRAIN] Thinking & Reasoning Frameworks

Built-in Thinking (Native Model Capability)

# Gemini 2.0+ thinking
thinking_agent = Agent(
    name="reasoning_assistant",
    model="gemini-2.0-flash",
    instruction="Solve complex problems with clear reasoning",
    thinking_config=ThinkingConfig(
        include_thoughts=True,  # Show reasoning in response
        max_thoughts=10
    )
)

# Thinking appears in response:
# "Let me think about this step by step:
# 1. First, I need to understand the problem...
# 2. Then, I should consider the constraints...
# 3. Finally, I'll provide the solution..."


Plan-ReAct Pattern (Structured Reasoning)

from google.adk.planners import PlanReActPlanner

# Structured reasoning agent
reasoning_agent = Agent(
    name="strategic_planner",
    model="gemini-2.5-flash",
    planner=PlanReActPlanner(),
    tools=[research_tool, analysis_tool],
    instruction="Plan and execute complex multi-step tasks"
)

# Execution pattern:
# [PLANNING] 1. Research topic 2. Analyze data 3. Create report
# [REASONING] I should start with research to gather facts...
# [ACTION] Call research_tool("quantum computing")
# [OBSERVATION] Found 15 relevant papers...
# [REPLANNING] Now analyze the data...


[FLOW] Multi-Turn Conversations
Context Management

# State-aware agent
conversational_agent = Agent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="""
    You are a helpful assistant. Previous conversation:
    {conversation_history}

    Current user: {user:name}
    Current task: {current_task}
    """,
    output_key="response"
)

# State tracks conversation flow
state['conversation_history'] += f"User: {user_input}\nAssistant: {response}\n"
state['current_task'] = extract_task(user_input)

Tool Call Chains
# Multi-tool agent
research_agent = Agent(
    name="comprehensive_researcher",
    model="gemini-2.5-flash",
    tools=[web_search, database_query, analysis_tool],
    instruction="""
    Research thoroughly using all available tools:
    1. Search the web for current information
    2. Query internal databases for company data
    3. Analyze and synthesize findings
    """
)

# LLM can generate multiple tool calls:
# 1. web_search("topic overview")
# 2. database_query("internal data")
# 3. analysis_tool("combine results")


## Fan-Out/Gather (Parallel + Sequential)
from google.adk.agents import ParallelAgent, SequentialAgent

# PARALLEL: Gather from multiple sources
parallel_search = ParallelAgent(
    name="DataGathering",
    sub_agents=[web_searcher, database_lookup, api_query]
)

# SEQUENTIAL: Synthesize results
synthesizer = Agent(
    name="synthesizer",
    instruction="Combine the gathered data into summary"
)

# COMBINE: Parallel gather + Sequential synthesis
fan_out_gather = SequentialAgent(
    name="FanOutGather",
    sub_agents=[parallel_search, synthesizer]
)

root_agent = fan_out_gather





### Advanced Prompting Techniques
# Explicit reasoning steps
reasoning_instruction = """
Solve this problem step by step:

1. Understand the problem: What is being asked?
2. Identify key information: What data do I have?
3. Consider approaches: What methods could work?
4. Evaluate options: Which approach is best?
5. Execute solution: Implement the chosen approach
6. Verify result: Does this make sense?

Show your work at each step.
"""

### Few-Shot Learning
# Example-based instruction
few_shot_instruction = """
Classify the sentiment of text as positive, negative, or neutral.

Examples:
Text: "I love this product!" → positive
Text: "This is terrible quality" → negative
Text: "It's okay, nothing special" → neutral

Now classify: "{user_text}"
"""

### Meta-Prompting
# Self-improving prompts
meta_instruction = """
First, analyze what type of question this is:
- Factual: Look for specific information
- Analytical: Break down components
- Creative: Generate novel ideas
- Advisory: Provide recommendations

Then, choose the appropriate response strategy:
- Factual: Cite sources, be precise
- Analytical: Structure with sections
- Creative: Brainstorm multiple options
- Advisory: Consider pros/cons, provide rationale

Question: {user_question}
"""

# Observability & Monitoring

## Events
# Enable event logging
runner = Runner(
    event_service=LoggingEventService(level="DEBUG")
)

# Events captured:
# - AGENT_START/COMPLETE
# - TOOL_CALL_START/RESULT
# - LLM_REQUEST/RESPONSE
# - STATE_CHANGE

# Tracing (Why It Happened) 
# Detailed execution traces
runner = Runner(
    trace_service=CloudTraceService(project="my-project")
)

# View in Cloud Trace console
# Performance bottlenecks
# Error root causes

### Callbacks (Custom Monitoring)

def monitor_agent(context, result):
    # Custom metrics
    log_performance(result.execution_time)
    alert_on_errors(result.errors)

agent = Agent(
    name="monitored_agent",
    callbacks=[monitor_agent]
)

### Performance Evaluation (Quality Metrics)
# Automated testing
adk eval agent_name --test-set my_tests.evalset.json

# Metrics:
# - tool_trajectory_avg_score (0-1)
# - response_match_score (0-1)
# - Custom LLM-as-judge metrics



