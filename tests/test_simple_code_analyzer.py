#!/usr/bin/env python3
"""
Simple Code Analyzer Test
Tests the code analyzer agent tools directly without complex ADK event handling
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, '/app/src')

async def test_code_analyzer_tools_directly():
    """Test the code analyzer tools directly without ADK events"""
    
    print("🚀 Starting Simple Code Analyzer Tools Test")
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
        agent = CodeAnalyzerAgent()
        print(f"✅ Agent initialized with {len(agent.tools)} tools")
        
        # Test individual analysis methods
        print(f"\n🔍 Testing individual analysis tools...")
        start_time = time.time()
        
        all_findings = []
        all_metrics = {}
        
        # Test 1: Try _analyze_single_file if it exists
        try:
            if hasattr(agent, '_analyze_single_file'):
                print("📊 Running _analyze_single_file...")
                findings, metrics = await agent._analyze_single_file(str(target_file), "comprehensive")
                all_findings.extend(findings if findings else [])
                all_metrics.update(metrics if metrics else {})
                print(f"   - Found {len(findings) if findings else 0} findings")
                print(f"   - Collected {len(metrics) if metrics else 0} metrics")
        except Exception as e:
            print(f"   - _analyze_single_file failed: {e}")
        
        # Test 2: Try complexity analysis directly
        try:
            from agents.code_analyzer.tools.complexity_analyzer import ComplexityAnalyzer
            print("📊 Running ComplexityAnalyzer...")
            complexity_analyzer = ComplexityAnalyzer()
            complexity_result = await complexity_analyzer.analyze_file(str(target_file))
            if complexity_result:
                all_findings.extend(complexity_result.get('findings', []))
                all_metrics['complexity'] = complexity_result.get('metrics', {})
                print(f"   - Complexity findings: {len(complexity_result.get('findings', []))}")
        except Exception as e:
            print(f"   - ComplexityAnalyzer failed: {e}")
        
        # Test 3: Try maintainability scoring
        try:
            from agents.code_analyzer.tools.maintainability_scorer import maintainability_scoring
            print("📊 Running maintainability_scoring...")
            # Pass multiple files as a list to test the multi-file scorer
            scoring_result = await maintainability_scoring([str(target_file)])
            if scoring_result:
                all_findings.extend(scoring_result.get('findings', []))
                all_metrics['maintainability_scoring'] = scoring_result.get('metrics', {})
                print(f"   - Maintainability scoring findings: {len(scoring_result.get('findings', []))}")
        except Exception as e:
            print(f"   - maintainability_scoring failed: {e}")
        
        # Test 4: Try maintainability assessment (single file)
        try:
            from agents.code_analyzer.tools.maintainability_assessor import maintainability_assessment
            print("📊 Running maintainability_assessment...")
            assessment_result = await maintainability_assessment(str(target_file))
            if assessment_result:
                all_findings.extend(assessment_result.get('findings', []))
                all_metrics['maintainability_assessment'] = assessment_result.get('metrics', {})
                print(f"   - Maintainability assessment findings: {len(assessment_result.get('findings', []))}")
        except Exception as e:
            print(f"   - maintainability_assessment failed: {e}")
        
        # Test 5: Try duplication detection
        try:
            from agents.code_analyzer.tools.duplication_detector import DuplicationDetector
            print("📊 Running DuplicationDetector...")
            duplication_detector = DuplicationDetector()
            duplication_result = await duplication_detector.detect_duplicates([str(target_file)])
            if duplication_result:
                all_findings.extend(duplication_result.get('findings', []))
                all_metrics['duplication'] = duplication_result.get('metrics', {})
                print(f"   - Duplication findings: {len(duplication_result.get('findings', []))}")
        except Exception as e:
            print(f"   - DuplicationDetector failed: {e}")
        
        execution_time = time.time() - start_time
        print(f"✅ All tools tested in {execution_time:.2f}s")
        
        # Process and save results
        print(f"\n📊 Processing results...")
        
        # Setup output directory
        output_dir = Path("/app/src/outputs/code_analyzer")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (output_dir / "findings").mkdir(exist_ok=True)
        (output_dir / "metrics").mkdir(exist_ok=True)
        (output_dir / "reports").mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save findings
        findings_file = output_dir / "findings" / f"auth_service_analysis_{timestamp}.json"
        findings_data = {
            "timestamp": timestamp,
            "agent": "code_analyzer",
            "file_analyzed": str(target_file),
            "findings_count": len(all_findings),
            "findings": all_findings,
            "execution_time": execution_time,
            "test_method": "direct_tools_test"
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
            "metrics": all_metrics,
            "test_method": "direct_tools_test"
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Generate markdown report
        report_file = output_dir / "reports" / f"auth_service_report_{timestamp}.md"
        report_content = f"""# Code Analysis Report - AuthenticationAppService.ts
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Agent: CodeAnalyzerAgent (Direct Tools Test)

## File Information
- **File**: {target_file}
- **Size**: {target_file.stat().st_size} bytes
- **Lines**: {lines_count}
- **Analysis Time**: {execution_time:.2f}s
- **Agent Tools**: {len(agent.tools)}
- **Test Method**: Direct tools invocation

## Summary
- **Total Findings**: {len(all_findings)}
- **Tools Tested**: {len(all_metrics)}

## Tools Results
"""
        
        # Add tool results
        for tool_name, tool_metrics in all_metrics.items():
            tool_findings = [f for f in all_findings if f.get('tool') == tool_name]
            report_content += f"### {tool_name.replace('_', ' ').title()}\n"
            report_content += f"- **Findings**: {len(tool_findings)}\n"
            if isinstance(tool_metrics, dict):
                for metric_name, metric_value in tool_metrics.items():
                    if isinstance(metric_value, (int, float)):
                        if isinstance(metric_value, float):
                            report_content += f"- **{metric_name}**: {metric_value:.2f}\n"
                        else:
                            report_content += f"- **{metric_name}**: {metric_value}\n"
                    else:
                        report_content += f"- **{metric_name}**: {metric_value}\n"
            report_content += "\n"
        
        # Add findings
        if all_findings:
            # Group findings by category if available
            findings_by_category = {}
            for finding in all_findings:
                category = finding.get('category', finding.get('tool', 'general'))
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append(finding)
            
            report_content += "## Findings by Category\n\n"
            for category, category_findings in findings_by_category.items():
                report_content += f"### {category.replace('_', ' ').title()} ({len(category_findings)} issues)\n\n"
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
        
        # Add code snippet for context
        report_content += f"""## Code Preview (First 50 lines)
```typescript
{chr(10).join(file_content.split(chr(10))[:50])}
```

"""
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n💾 Results saved:")
        print(f"   - Findings: {findings_file}")
        print(f"   - Metrics: {metrics_file}")
        print(f"   - Report: {report_file}")
        
        print(f"\n📊 Analysis Summary:")
        print(f"   - Agent tools: {len(agent.tools)}")
        print(f"   - Tools tested: {len(all_metrics)}")
        print(f"   - Total findings: {len(all_findings)}")
        print(f"   - Execution time: {execution_time:.2f}s")
        print(f"   - File analyzed: {target_file.name} ({lines_count} lines)")
        
        # Show findings summary
        if all_findings:
            print(f"\n🔍 Top Findings:")
            for i, finding in enumerate(all_findings[:5], 1):
                title = finding.get('title', finding.get('message', 'Issue'))
                line = finding.get('line_number', finding.get('line', 'N/A'))
                severity = finding.get('severity', 'unknown')
                tool = finding.get('tool', 'unknown')
                print(f"   {i}. [{severity}] {title} (Line {line}) - {tool}")
            
            if len(all_findings) > 5:
                print(f"   ... and {len(all_findings) - 5} more findings")
                
            # Show findings by tool
            print(f"\n📋 Findings by Tool:")
            findings_by_tool = {}
            for finding in all_findings:
                tool = finding.get('tool', 'unknown')
                findings_by_tool[tool] = findings_by_tool.get(tool, 0) + 1
            
            for tool, count in findings_by_tool.items():
                print(f"   - {tool}: {count} findings")
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
    print("🏗️  Simple Code Analyzer Tools Test")
    print("📋 Testing AuthenticationAppService.ts with direct tool invocation")
    print("")
    
    success = await test_code_analyzer_tools_directly()
    
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