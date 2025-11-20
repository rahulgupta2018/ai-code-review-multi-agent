#!/usr/bin/env python3
"""
ADK Trace Analyzer - Analyze agent execution, tool calls, and LLM usage
"""

import requests
import json
import sys
from datetime import datetime
from typing import List, Dict

def get_session_list() -> List[Dict]:
    """Get list of all sessions."""
    try:
        url = "http://localhost:8800/apps/orchestrator_agent/users/user/sessions"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        return []

def get_session_traces(session_id: str) -> List[Dict]:
    """Fetch traces for a specific session."""
    try:
        url = f"http://localhost:8800/debug/trace/session/{session_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching traces for session {session_id}: {e}")
        return []

def analyze_traces(traces: List[Dict], session_id: str):
    """Analyze and display trace information."""
    if not traces:
        print(f"⚠️  No traces found for session {session_id}")
        return
    
    agent_calls = []
    tool_calls = []
    llm_calls = []
    
    # Parse traces
    for span in traces:
        span_type = span.get('name', '')
        
        if 'invoke_agent' in span_type:
            agent_name = span.get('attributes', {}).get('gen_ai.agent.name', 'unknown')
            duration_ms = (span['end_time'] - span['start_time']) / 1_000_000
            agent_calls.append({
                'agent': agent_name,
                'duration_ms': duration_ms,
                'start_time': span['start_time'],
                'span_id': span['span_id']
            })
        
        elif 'execute_tool' in span_type:
            tool_name = span_type.replace('execute_tool ', '')
            duration_ms = (span['end_time'] - span['start_time']) / 1_000_000
            tool_calls.append({
                'tool': tool_name,
                'duration_ms': duration_ms,
                'start_time': span['start_time']
            })
        
        elif 'call_llm' in span_type:
            attrs = span.get('attributes', {})
            llm_calls.append({
                'model': attrs.get('gen_ai.request.model', 'unknown'),
                'input_tokens': attrs.get('gen_ai.usage.input_tokens', 0),
                'output_tokens': attrs.get('gen_ai.usage.output_tokens', 0),
                'duration_ms': (span['end_time'] - span['start_time']) / 1_000_000,
                'finish_reason': attrs.get('gen_ai.response.finish_reasons', ['unknown'])[0],
                'start_time': span['start_time']
            })
    
    # Sort by start time
    agent_calls.sort(key=lambda x: x['start_time'])
    tool_calls.sort(key=lambda x: x['start_time'])
    llm_calls.sort(key=lambda x: x['start_time'])
    
    # Display results
    print(f"\n{'='*80}")
    print(f"📊 Session Analysis: {session_id}")
    print(f"{'='*80}\n")
    
    # Agent execution summary
    print(f"🤖 Agent Executions: {len(agent_calls)}")
    if agent_calls:
        for i, call in enumerate(agent_calls, 1):
            print(f"   {i}. {call['agent']}")
            print(f"      Duration: {call['duration_ms']:.0f}ms")
            print(f"      Time: {datetime.fromtimestamp(call['start_time'] / 1_000_000_000).strftime('%H:%M:%S')}")
    else:
        print("   (No agent calls found)")
    
    # Tool execution summary
    print(f"\n🔧 Tool Executions: {len(tool_calls)}")
    if tool_calls:
        for i, call in enumerate(tool_calls, 1):
            print(f"   {i}. {call['tool']}")
            print(f"      Duration: {call['duration_ms']:.0f}ms")
    else:
        print("   (No tools executed)")
    
    # LLM call summary
    print(f"\n💬 LLM Interactions: {len(llm_calls)}")
    if llm_calls:
        total_input = sum(c['input_tokens'] for c in llm_calls)
        total_output = sum(c['output_tokens'] for c in llm_calls)
        total_duration = sum(c['duration_ms'] for c in llm_calls)
        
        print(f"   Model: {llm_calls[0]['model']}")
        print(f"   Total Calls: {len(llm_calls)}")
        print(f"   Input Tokens: {total_input:,}")
        print(f"   Output Tokens: {total_output:,}")
        print(f"   Total Tokens: {total_input + total_output:,}")
        print(f"   Total LLM Time: {total_duration:.0f}ms")
        print(f"   Average Latency: {total_duration / len(llm_calls):.0f}ms per call")
        
        print(f"\n   Detailed LLM Calls:")
        for i, call in enumerate(llm_calls, 1):
            print(f"      {i}. {call['duration_ms']:.0f}ms | "
                  f"In: {call['input_tokens']} tokens | "
                  f"Out: {call['output_tokens']} tokens | "
                  f"Status: {call['finish_reason']}")
    else:
        print("   (No LLM calls found)")
    
    # Performance metrics
    print(f"\n⏱️  Performance Summary:")
    total_time = max((span['end_time'] for span in traces)) - min((span['start_time'] for span in traces))
    print(f"   Total Session Time: {total_time / 1_000_000:.0f}ms")
    if agent_calls:
        print(f"   Agent Processing Time: {sum(c['duration_ms'] for c in agent_calls):.0f}ms")
    if llm_calls:
        llm_time = sum(c['duration_ms'] for c in llm_calls)
        llm_percentage = (llm_time / (total_time / 1_000_000)) * 100 if total_time > 0 else 0
        print(f"   LLM Time: {llm_time:.0f}ms ({llm_percentage:.1f}% of total)")
    
    print(f"\n{'='*80}\n")

def main():
    """Main function to analyze traces."""
    print("🔍 ADK Trace Analyzer")
    print("=" * 80)
    
    # Get session list
    print("\n📋 Fetching sessions...")
    sessions = get_session_list()
    
    if not sessions:
        print("❌ No sessions found or unable to connect to ADK server")
        print("   Make sure the server is running at http://localhost:8800")
        return 1
    
    print(f"✅ Found {len(sessions)} session(s)\n")
    
    # If session ID provided as argument, analyze that one
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        print(f"Analyzing session: {session_id}")
        traces = get_session_traces(session_id)
        analyze_traces(traces, session_id)
        return 0
    
    # Otherwise, show list and analyze most recent
    print("Recent Sessions:")
    for i, session in enumerate(sessions[-5:], 1):  # Show last 5
        session_id = session.get('id', 'unknown')
        last_update = session.get('lastUpdateTime', 0)
        if last_update:
            timestamp = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = 'unknown'
        print(f"   {i}. {session_id} (last update: {timestamp})")
    
    if sessions:
        latest_session_id = sessions[-1].get('id')
        if latest_session_id:
            print(f"\n🎯 Analyzing most recent session: {latest_session_id}")
            traces = get_session_traces(latest_session_id)
            analyze_traces(traces, latest_session_id)
        else:
            print("❌ Could not extract session ID")
    
    print("\n💡 Tip: Run with session ID to analyze specific session:")
    print(f"   python {sys.argv[0]} <session_id>")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
