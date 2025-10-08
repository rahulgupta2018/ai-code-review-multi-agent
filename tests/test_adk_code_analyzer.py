#!/usr/bin/env python3
"""
Google ADK Code Analyzer Agent Test
Tests the actual code analyzer agent within the ADK framework to analyze AuthenticationAppService.ts
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    # Import Google ADK components
    from google.adk.agents import invoke_agent
    from google.adk.events import Event
    print("✅ Google ADK imports successful")
except ImportError as e:
    print(f"❌ Google ADK not available: {e}")
    print("💡 Make sure you're running this within the ADK container environment")
    sys.exit(1)

async def test_code_analyzer_agent():
    """Test the code analyzer agent with the real AuthenticationAppService.ts file"""
    
    print("🚀 Starting Google ADK Code Analyzer Agent Test")
    print("=" * 60)
    
    # File to analyze
    target_file = Path(__file__).parent / "input_files" / "AuthenticationAppService.ts"
    if not target_file.exists():
        print(f"❌ Target file not found: {target_file}")
        return
    
    print(f"📂 Target file: {target_file}")
    print(f"📏 File size: {target_file.stat().st_size} bytes")
    
    # Read the file content
    with open(target_file, 'r') as f:
        file_content = f.read()
    
    lines_count = len(file_content.split('\n'))
    print(f"📄 Lines of code: {lines_count}")
    
    # Prepare the analysis request
    analysis_request = {
        "files": [str(target_file)],
        "analysis_type": "comprehensive",
        "output_format": "structured",
        "include_metrics": True,
        "include_recommendations": True
    }
    
    print(f"\n🤖 Invoking code analyzer agent...")
    print(f"📋 Request: {json.dumps(analysis_request, indent=2)}")
    
    try:
        start_time = time.time()
        
        # Create an event to trigger the agent
        analysis_event = Event(
            event_type="code_analysis_request",
            data=analysis_request,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "test_run": True,
                "file_path": str(target_file)
            }
        )
        
        # Invoke the code analyzer agent
        print(f"🔄 Calling agent: code_analyzer")
        
        # Use the ADK agent invocation system
        result = await invoke_agent(
            agent_name="code_analyzer",
            event=analysis_event,
            timeout=120  # 2 minutes timeout
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Agent execution completed in {execution_time:.2f}s")
        print(f"📊 Response type: {type(result)}")
        
        # Process the results
        if hasattr(result, 'data'):
            analysis_results = result.data
        else:
            analysis_results = result
        
        print(f"🔍 Analysis Results Overview:")
        print(f"   - Result keys: {list(analysis_results.keys()) if isinstance(analysis_results, dict) else 'Not a dict'}")
        
        # Save results to output directory
        output_dir = Path(__file__).parent.parent / "src" / "outputs" / "code_analyzer"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save findings
        findings_file = output_dir / "findings" / f"auth_service_analysis_{timestamp}.json"
        findings_file.parent.mkdir(exist_ok=True)
        
        # Save metrics
        metrics_file = output_dir / "metrics" / f"auth_service_metrics_{timestamp}.json"
        metrics_file.parent.mkdir(exist_ok=True)
        
        # Save report
        report_file = output_dir / "reports" / f"auth_service_report_{timestamp}.md"
        report_file.parent.mkdir(exist_ok=True)
        
        # Process and save results
        if isinstance(analysis_results, dict):
            # Save findings
            findings = analysis_results.get('findings', [])
            findings_data = {
                "timestamp": timestamp,
                "agent": "code_analyzer",
                "file_analyzed": str(target_file),
                "findings_count": len(findings),
                "findings": findings
            }
            
            with open(findings_file, 'w') as f:
                json.dump(findings_data, f, indent=2)
            
            # Save metrics
            metrics = analysis_results.get('metrics', {})
            metrics_data = {
                "timestamp": timestamp,
                "execution_time": execution_time,
                "file_analyzed": str(target_file),
                "metrics": metrics,
                "agent_response": {
                    "success": analysis_results.get('success', True),
                    "agent_name": analysis_results.get('agent_name', 'code_analyzer')
                }
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Generate markdown report
            report_content = f"""# Code Analysis Report - AuthenticationAppService.ts
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Agent: Google ADK Code Analyzer

## File Information
- **File**: {target_file}
- **Size**: {target_file.stat().st_size} bytes
- **Lines**: {lines_count}
- **Analysis Time**: {execution_time:.2f}s

## Summary
- **Total Findings**: {len(findings)}
- **Agent Success**: {analysis_results.get('success', True)}

"""
            
            # Add findings details
            if findings:
                # Group findings by category
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
                        line_num = finding.get('line_number', finding.get('line', 'N/A'))
                        severity = finding.get('severity', 'unknown')
                        title = finding.get('title', finding.get('message', 'Issue detected'))
                        description = finding.get('description', finding.get('details', ''))
                        
                        report_content += f"**{title}** ({severity})\n"
                        report_content += f"- Line: {line_num}\n"
                        if description:
                            report_content += f"- Description: {description}\n"
                        report_content += "\n"
            else:
                report_content += "## No Issues Found\n\nThe code analyzer found no issues with this file.\n\n"
            
            # Add metrics section
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
            
            # Add raw agent response
            report_content += f"\n## Agent Response Details\n\n```json\n{json.dumps(analysis_results, indent=2)}\n```\n"
            
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            print(f"\n💾 Results saved:")
            print(f"   - Findings: {findings_file}")
            print(f"   - Metrics: {metrics_file}")
            print(f"   - Report: {report_file}")
            
            print(f"\n📊 Analysis Summary:")
            print(f"   - Findings: {len(findings)}")
            print(f"   - Categories: {len(set(f.get('category', 'general') for f in findings))}")
            print(f"   - Execution time: {execution_time:.2f}s")
            
            # Show top findings
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
            # Handle non-dict responses
            print(f"⚠️  Unexpected response format: {type(analysis_results)}")
            with open(output_dir / f"raw_response_{timestamp}.json", 'w') as f:
                json.dump(str(analysis_results), f, indent=2)
        
    except Exception as e:
        print(f"❌ Agent invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function"""
    print("🏗️  Google ADK Code Analyzer Integration Test")
    print("📋 Testing with real AuthenticationAppService.ts file")
    print("")
    
    success = await test_code_analyzer_agent()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📁 Check src/outputs/code_analyzer/ for detailed results")
        print("🌐 You can also view results via:")
        print("   - File Manager: http://localhost:8082")
        print("   - ADK Portal: http://localhost:8200")
    else:
        print("\n❌ Test failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())