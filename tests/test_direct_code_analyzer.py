#!/usr/bin/env python3
"""
Direct Code Analyzer Agent Test
Tests the code analyzer agent directly within the ADK container environment
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, '/app/src')

async def test_code_analyzer_directly():
    """Test the code analyzer agent by instantiating it directly"""
    
    print("🚀 Starting Direct Code Analyzer Agent Test")
    print("=" * 60)
    
    try:
        # Import the code analyzer agent
        from agents.code_analyzer.agent import CodeAnalyzerAgent
        print("✅ Successfully imported CodeAnalyzerAgent")
        
        # Check if we have the test file
        target_file = Path("/app/tests/input_files/AuthenticationAppService.ts")
        if not target_file.exists():
            print(f"❌ Target file not found: {target_file}")
            return False
            
        print(f"📂 Target file: {target_file}")
        print(f"📏 File size: {target_file.stat().st_size} bytes")
        
        # Read the file content
        with open(target_file, 'r') as f:
            file_content = f.read()
        
        lines_count = len(file_content.split('\n'))
        print(f"📄 Lines of code: {lines_count}")
        
        # Initialize the agent
        print(f"\n🤖 Initializing CodeAnalyzerAgent...")
        
        # Create agent with default configuration
        agent = CodeAnalyzerAgent()
        print(f"✅ Agent initialized with {len(agent.tools)} tools:")
        for tool in agent.tools:
            print(f"   - {tool.__name__ if hasattr(tool, '__name__') else type(tool).__name__}")
        
        # Prepare analysis request
        print(f"\n🔍 Starting analysis of {target_file.name}...")
        start_time = time.time()
        
        # Create a simple request context (mimicking what ADK would provide)
        from google.adk.agents import InvocationContext
        from google.adk.events import Event
        
        # Create an analysis event
        analysis_event = Event(
            event_type="code_analysis_request",
            data={
                "files": [str(target_file)],
                "analysis_type": "comprehensive",
                "output_format": "structured"
            }
        )
        
        # Create invocation context
        context = InvocationContext(
            agent_name="code_analyzer",
            event=analysis_event,
            config={}
        )
        
        # Run the agent
        print(f"🔄 Executing agent analysis...")
        result = await agent.ainvoke(context)
        
        execution_time = time.time() - start_time
        print(f"✅ Analysis completed in {execution_time:.2f}s")
        
        # Process results
        print(f"📊 Processing results...")
        
        # Setup output directory
        output_dir = Path("/app/src/outputs/code_analyzer")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (output_dir / "findings").mkdir(exist_ok=True)
        (output_dir / "metrics").mkdir(exist_ok=True)
        (output_dir / "reports").mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract findings and metrics from result
        if hasattr(result, 'data'):
            analysis_data = result.data
        elif hasattr(result, 'content'):
            analysis_data = result.content
        else:
            analysis_data = result
            
        print(f"🔍 Result type: {type(analysis_data)}")
        
        # Try to parse the result
        findings = []
        metrics = {}
        
        if isinstance(analysis_data, dict):
            findings = analysis_data.get('findings', [])
            metrics = analysis_data.get('metrics', {})
        elif isinstance(analysis_data, str):
            try:
                parsed_data = json.loads(analysis_data)
                findings = parsed_data.get('findings', [])
                metrics = parsed_data.get('metrics', {})
            except json.JSONDecodeError:
                print("⚠️  Result is string but not JSON, treating as raw output")
                findings = [{"message": "Raw analysis output", "details": analysis_data}]
        else:
            print(f"⚠️  Unexpected result format: {type(analysis_data)}")
            findings = [{"message": "Analysis completed", "details": str(analysis_data)}]
        
        # Save findings
        findings_file = output_dir / "findings" / f"auth_service_analysis_{timestamp}.json"
        findings_data = {
            "timestamp": timestamp,
            "agent": "code_analyzer",
            "file_analyzed": str(target_file),
            "findings_count": len(findings),
            "findings": findings,
            "execution_time": execution_time
        }
        
        with open(findings_file, 'w') as f:
            json.dump(findings_data, f, indent=2)
        
        # Save metrics
        metrics_file = output_dir / "metrics" / f"auth_service_metrics_{timestamp}.json"
        metrics_data = {
            "timestamp": timestamp,
            "execution_time": execution_time,
            "file_analyzed": str(target_file),
            "file_size": target_file.stat().st_size,
            "lines_of_code": lines_count,
            "agent_tools": len(agent.tools),
            "metrics": metrics
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Generate markdown report
        report_file = output_dir / "reports" / f"auth_service_report_{timestamp}.md"
        report_content = f"""# Code Analysis Report - AuthenticationAppService.ts
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Agent: CodeAnalyzerAgent (Google ADK)

## File Information
- **File**: {target_file}
- **Size**: {target_file.stat().st_size} bytes
- **Lines**: {lines_count}
- **Analysis Time**: {execution_time:.2f}s
- **Agent Tools**: {len(agent.tools)}

## Summary
- **Total Findings**: {len(findings)}
- **Analysis Type**: Comprehensive

## Tool Configuration
"""
        
        # Add tool information
        for i, tool in enumerate(agent.tools, 1):
            tool_name = tool.__name__ if hasattr(tool, '__name__') else type(tool).__name__
            report_content += f"{i}. **{tool_name}**\n"
        
        report_content += "\n"
        
        # Add findings
        if findings:
            # Group findings by category if available
            findings_by_category = {}
            for finding in findings:
                category = finding.get('category', 'general')
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append(finding)
            
            report_content += "## Findings by Category\n\n"
            for category, category_findings in findings_by_category.items():
                report_content += f"### {category.title()} ({len(category_findings)} issues)\n\n"
                for finding in category_findings:
                    title = finding.get('title', finding.get('message', 'Issue detected'))
                    line_num = finding.get('line_number', finding.get('line', 'N/A'))
                    severity = finding.get('severity', 'unknown')
                    description = finding.get('description', finding.get('details', ''))
                    
                    report_content += f"**{title}** ({severity})\n"
                    if line_num != 'N/A':
                        report_content += f"- Line: {line_num}\n"
                    if description:
                        report_content += f"- Description: {description}\n"
                    report_content += "\n"
        else:
            report_content += "## No Issues Found\n\nThe code analyzer found no issues with this file.\n\n"
        
        # Add metrics
        if metrics:
            report_content += "## Metrics\n\n"
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    if isinstance(metric_value, float):
                        report_content += f"- **{metric_name}**: {metric_value:.2f}\n"
                    else:
                        report_content += f"- **{metric_name}**: {metric_value}\n"
                else:
                    report_content += f"- **{metric_name}**: {metric_value}\n"
            report_content += "\n"
        
        # Add raw result for debugging
        report_content += f"## Raw Agent Output\n\n```json\n{json.dumps(analysis_data, indent=2)}\n```\n"
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n💾 Results saved:")
        print(f"   - Findings: {findings_file}")
        print(f"   - Metrics: {metrics_file}")
        print(f"   - Report: {report_file}")
        
        print(f"\n📊 Analysis Summary:")
        print(f"   - Agent tools: {len(agent.tools)}")
        print(f"   - Findings: {len(findings)}")
        print(f"   - Execution time: {execution_time:.2f}s")
        print(f"   - File analyzed: {target_file.name} ({lines_count} lines)")
        
        # Show findings summary
        if findings:
            print(f"\n🔍 Top Findings:")
            for i, finding in enumerate(findings[:5], 1):
                title = finding.get('title', finding.get('message', 'Issue'))
                line = finding.get('line_number', finding.get('line', 'N/A'))
                severity = finding.get('severity', 'unknown')
                print(f"   {i}. [{severity}] {title} (Line {line})")
            
            if len(findings) > 5:
                print(f"   ... and {len(findings) - 5} more findings")
        else:
            print(f"\n✅ No issues found in the code!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🏗️  Google ADK Code Analyzer Direct Test")
    print("📋 Testing AuthenticationAppService.ts with real agent")
    print("")
    
    success = await test_code_analyzer_directly()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📁 Check /app/src/outputs/code_analyzer/ for detailed results")
        print("🌐 You can also view results via:")
        print("   - File Manager: http://localhost:8082")
        print("   - ADK Portal: http://localhost:8200")
    else:
        print("\n❌ Test failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())