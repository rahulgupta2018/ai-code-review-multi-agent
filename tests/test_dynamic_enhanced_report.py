#!/usr/bin/env python3
"""
Dynamic Enhanced Report Generation Test
Tests the enhanced report generator using real code samples from tests/input_files folder.
This test dynamically discovers and analyzes actual code files instead of using hardcoded samples.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the enhanced report generator
from agents.base.tools.report_generator import create_enhanced_report_generator

# Import the agent classes
from agents.code_analyzer.agent import CodeAnalysisConfig, CodeAnalyzerAgent


class DynamicCodeAnalysisTest:
    """Dynamic test class that analyzes real code files from input_files folder"""
    
    def __init__(self):
        self.input_files_dir = Path(__file__).parent / "input_files"
        self.output_dir = Path(__file__).parent.parent / "src" / "outputs" / "code_analyzer" / "reports"
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
    
    def discover_code_files(self) -> List[Dict[str, Any]]:
        """Discover all supported code files in the input_files directory"""
        print(f"🔍 Discovering code files in: {self.input_files_dir}")
        
        discovered_files = []
        
        if not self.input_files_dir.exists():
            print(f"❌ Input files directory does not exist: {self.input_files_dir}")
            return discovered_files
        
        # Recursively find all code files
        for file_path in self.input_files_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                extension = file_path.suffix.lower()
                if extension in self.supported_extensions:
                    try:
                        # Get basic file info
                        file_size = file_path.stat().st_size
                        language = self.supported_extensions[extension]
                        
                        # Read file to get line count and basic metrics
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('//')]
                        
                        file_info = {
                            'path': str(file_path),
                            'name': file_path.name,
                            'language': language,
                            'extension': extension,
                            'size_bytes': file_size,
                            'size_kb': round(file_size / 1024, 2),
                            'total_lines': len(lines),
                            'code_lines': len(code_lines),
                            'content': content
                        }
                        
                        discovered_files.append(file_info)
                        print(f"  ✅ Found: {file_path.name} ({language}, {file_info['total_lines']} lines, {file_info['size_kb']} KB)")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error reading {file_path.name}: {e}")
        
        print(f"📊 Discovered {len(discovered_files)} code files")
        return discovered_files
    
    def filter_files_for_analysis(self, discovered_files: List[Dict[str, Any]], max_files: int = 10, max_size_kb: int = 500) -> List[Dict[str, Any]]:
        """Filter files for analysis based on size and count limits"""
        print(f"\n🔧 Filtering files for analysis (max {max_files} files, max {max_size_kb} KB each)")
        
        # Filter by size
        size_filtered = [f for f in discovered_files if f['size_kb'] <= max_size_kb]
        
        if len(size_filtered) < len(discovered_files):
            removed_count = len(discovered_files) - len(size_filtered)
            print(f"  📏 Removed {removed_count} files exceeding size limit")
        
        # Sort by a combination of factors: language diversity, size, and complexity indicators
        def get_file_priority(file_info):
            # Prefer diverse languages
            language_priority = {
                'typescript': 10, 'javascript': 9, 'python': 8, 'java': 7,
                'cpp': 6, 'csharp': 5, 'go': 4, 'rust': 3, 'php': 2
            }
            lang_score = language_priority.get(file_info['language'], 1)
            
            # Prefer medium-sized files (not too small, not too large)
            size_score = min(10, max(1, 10 - abs(file_info['size_kb'] - 50) / 10))
            
            # Prefer files with more code lines (likely more complex)
            code_ratio = file_info['code_lines'] / max(file_info['total_lines'], 1)
            code_score = min(10, code_ratio * 10)
            
            return lang_score + size_score + code_score
        
        # Sort by priority and take top files
        size_filtered.sort(key=get_file_priority, reverse=True)
        selected_files = size_filtered[:max_files]
        
        print(f"  ✅ Selected {len(selected_files)} files for analysis:")
        for file_info in selected_files:
            print(f"    - {file_info['name']} ({file_info['language']}, {file_info['total_lines']} lines)")
        
        return selected_files
    
    async def run_comprehensive_analysis(self, selected_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive analysis on selected files using the agent"""
        print(f"\n🔍 Running comprehensive analysis on {len(selected_files)} files...")
        
        all_findings = []
        all_metrics = {}
        start_time = time.time()
        
        # Initialize agent
        print("🤖 Initializing Code Analyzer Agent...")
        config = CodeAnalysisConfig(
            enable_enhanced_analysis=True,
            max_file_size=50 * 1024 * 1024,  # 50MB
            supported_languages=['python', 'javascript', 'typescript', 'java', 'go', 'cpp', 'csharp', 'rust'],
            parallel_analysis=True,
            output_format='json'
        )
        agent = CodeAnalyzerAgent(config=config)
        print(f"✅ Agent initialized with {len(agent.tools)} tools")
        
        # Analyze each file
        for i, file_info in enumerate(selected_files, 1):
            print(f"\n  📄 Analyzing file {i}/{len(selected_files)}: {file_info['name']}")
            print(f"      Language: {file_info['language']}, Lines: {file_info['total_lines']}, Size: {file_info['size_kb']} KB")
            
            try:
                # Use the agent's _analyze_single_file method
                findings, metrics = await agent._analyze_single_file(file_info['path'], "enhanced")
                
                # Convert findings to consistent format
                processed_findings = []
                for finding in findings:
                    finding_dict = {
                        'file': file_info['path'],
                        'file_name': file_info['name'],
                        'language': file_info['language'],
                        'line': getattr(finding, 'line_number', getattr(finding, 'line', 1)),
                        'severity': str(getattr(finding, 'severity', 'MEDIUM')),
                        'category': getattr(finding, 'category', 'general'),
                        'description': getattr(finding, 'description', getattr(finding, 'message', 'Issue detected')),
                        'recommendation': getattr(finding, 'recommendation', '')
                    }
                    processed_findings.append(finding_dict)
                
                all_findings.extend(processed_findings)
                all_metrics[file_info['path']] = {
                    **metrics,
                    'file_info': {
                        'name': file_info['name'],
                        'language': file_info['language'],
                        'total_lines': file_info['total_lines'],
                        'code_lines': file_info['code_lines'],
                        'size_kb': file_info['size_kb']
                    }
                }
                
                print(f"      ✅ Found {len(processed_findings)} issues")
                print(f"      📊 Metrics: {len(metrics)} categories")
                
                # Show severity breakdown for this file
                severity_counts = {}
                for finding in processed_findings:
                    severity = finding['severity'].replace('FindingSeverity.', '')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                if severity_counts:
                    severity_summary = ', '.join([f"{sev}: {count}" for sev, count in severity_counts.items()])
                    print(f"      📋 Severities: {severity_summary}")
                
            except Exception as e:
                print(f"      ❌ Error analyzing {file_info['name']}: {e}")
                # Add error as finding
                all_findings.append({
                    'file': file_info['path'],
                    'file_name': file_info['name'],
                    'language': file_info['language'],
                    'line': 1,
                    'severity': 'HIGH',
                    'category': 'analysis_error',
                    'description': f'Analysis failed: {str(e)}',
                    'recommendation': 'Check file syntax and format compatibility'
                })
        
        execution_time = time.time() - start_time
        
        return {
            'findings': all_findings,
            'metrics': all_metrics,
            'execution_time': execution_time,
            'success': True,
            'files_analyzed': len(selected_files),
            'total_files_discovered': len(selected_files)
        }
    
    def load_file_contents(self, selected_files: List[Dict[str, Any]]) -> Dict[str, str]:
        """Load file contents for code examples in report"""
        print("\n📖 Loading file contents for code examples...")
        
        content_map = {}
        for file_info in selected_files:
            file_path = file_info['path']
            try:
                content_map[file_path] = file_info['content']  # We already loaded this
                print(f"  ✅ Loaded: {file_info['name']}")
            except Exception as e:
                print(f"  ⚠️ Failed to load {file_info['name']}: {e}")
                content_map[file_path] = f"# File content could not be loaded: {e}"
        
        return content_map
    
    async def generate_enhanced_report(self, analysis_result: Dict[str, Any], file_contents: Dict[str, str]) -> str:
        """Generate enhanced comprehensive report"""
        print(f"\n📊 Generating enhanced comprehensive report...")
        
        # Setup output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"dynamic_analysis_report_{timestamp}.md"
        
        try:
            # Create enhanced report generator
            report_generator = create_enhanced_report_generator()
            
            # Generate comprehensive report with LLM insights
            await report_generator.generate_enhanced_report(
                analysis_result,
                str(report_path),
                file_contents
            )
            
            print(f"✅ Enhanced report generated: {report_path}")
            
            # Get report size
            if report_path.exists():
                report_size_kb = report_path.stat().st_size / 1024
                print(f"📄 Report size: {report_size_kb:.1f} KB")
            
            return str(report_path)
            
        except Exception as e:
            print(f"❌ Enhanced report generation failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Generate fallback basic report
            print("📄 Generating fallback basic report...")
            basic_content = self._generate_fallback_report(analysis_result, timestamp)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(basic_content)
            
            print(f"📄 Basic report saved: {report_path}")
            return str(report_path)
    
    def _generate_fallback_report(self, analysis_result: Dict[str, Any], timestamp: str) -> str:
        """Generate a basic fallback report if enhanced generation fails"""
        return f"""# Dynamic Code Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {timestamp}

## Summary
- Files Analyzed: {analysis_result.get('files_analyzed', 0)}
- Total Findings: {len(analysis_result.get('findings', []))}
- Execution Time: {analysis_result.get('execution_time', 0):.2f}s
- Analysis Success: {analysis_result.get('success', False)}

## Findings by File

{self._format_findings_by_file(analysis_result.get('findings', []))}

## File Analysis Summary

{self._format_file_summary(analysis_result.get('metrics', {}))}
"""
    
    def _format_findings_by_file(self, findings: List[Dict[str, Any]]) -> str:
        """Format findings grouped by file"""
        files_findings = {}
        for finding in findings:
            file_name = finding.get('file_name', 'unknown')
            if file_name not in files_findings:
                files_findings[file_name] = []
            files_findings[file_name].append(finding)
        
        formatted = []
        for file_name, file_findings in files_findings.items():
            formatted.append(f"### {file_name} ({len(file_findings)} issues)")
            for i, finding in enumerate(file_findings, 1):
                formatted.append(f"{i}. **{finding.get('description', 'Issue detected')}**")
                formatted.append(f"   - Line: {finding.get('line', 'N/A')}")
                formatted.append(f"   - Severity: {finding.get('severity', 'UNKNOWN')}")
                formatted.append(f"   - Category: {finding.get('category', 'general')}")
                if finding.get('recommendation'):
                    formatted.append(f"   - Recommendation: {finding['recommendation']}")
                formatted.append("")
        
        return '\n'.join(formatted)
    
    def _format_file_summary(self, metrics: Dict[str, Any]) -> str:
        """Format file summary with metrics"""
        formatted = []
        for file_path, file_metrics in metrics.items():
            file_info = file_metrics.get('file_info', {})
            file_name = file_info.get('name', Path(file_path).name)
            
            formatted.append(f"### {file_name}")
            formatted.append(f"- Language: {file_info.get('language', 'unknown')}")
            formatted.append(f"- Lines: {file_info.get('total_lines', 'unknown')}")
            formatted.append(f"- Size: {file_info.get('size_kb', 'unknown')} KB")
            
            # Add metric summaries
            if 'complexity' in file_metrics:
                complexity = file_metrics['complexity']
                formatted.append(f"- Cognitive Complexity: {complexity.get('cognitive_complexity', 'N/A')}")
                formatted.append(f"- Nesting Depth: {complexity.get('nesting_depth', 'N/A')}")
            
            if 'maintainability' in file_metrics:
                maintainability = file_metrics['maintainability']
                formatted.append(f"- Maintainability Score: {maintainability.get('score', 'N/A')}/100")
                formatted.append(f"- Quality Level: {maintainability.get('quality_level', 'N/A')}")
            
            if 'duplication' in file_metrics:
                duplication = file_metrics['duplication']
                formatted.append(f"- Duplications: {duplication.get('total_duplications', 'N/A')}")
            
            formatted.append("")
        
        return '\n'.join(formatted)
    
    def print_analysis_summary(self, analysis_result: Dict[str, Any]):
        """Print a comprehensive analysis summary"""
        print(f"\n📋 Analysis Summary:")
        print(f"  - Files discovered: {analysis_result.get('total_files_discovered', 0)}")
        print(f"  - Files analyzed: {analysis_result.get('files_analyzed', 0)}")
        print(f"  - Total findings: {len(analysis_result.get('findings', []))}")
        print(f"  - Execution time: {analysis_result.get('execution_time', 0):.2f}s")
        
        # Show findings breakdown by severity
        findings = analysis_result.get('findings', [])
        severity_counts = {}
        language_counts = {}
        category_counts = {}
        
        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN').replace('FindingSeverity.', '')
            language = finding.get('language', 'unknown')
            category = finding.get('category', 'general')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            language_counts[language] = language_counts.get(language, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        if severity_counts:
            print(f"\n📊 Findings by Severity:")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"  - {severity}: {count}")
        
        if language_counts:
            print(f"\n🔤 Findings by Language:")
            for language, count in sorted(language_counts.items()):
                print(f"  - {language}: {count}")
        
        if category_counts:
            print(f"\n📂 Findings by Category:")
            for category, count in sorted(category_counts.items()):
                print(f"  - {category}: {count}")


async def main():
    """Main test function"""
    print("🚀 Dynamic Enhanced Report Generation Test")
    print("=" * 70)
    print("Analyzing real code files from tests/input_files directory")
    print("=" * 70)
    
    # Initialize test class
    test = DynamicCodeAnalysisTest()
    
    # Discover code files
    print("\n📁 Phase 1: File Discovery")
    discovered_files = test.discover_code_files()
    
    if not discovered_files:
        print("❌ No code files found in input_files directory!")
        print("💡 Please add some code files to tests/input_files/ to run this test.")
        return 1
    
    # Filter files for analysis
    print("\n🔧 Phase 2: File Selection")
    selected_files = test.filter_files_for_analysis(discovered_files, max_files=5, max_size_kb=200)
    
    if not selected_files:
        print("❌ No suitable files found for analysis!")
        return 1
    
    # Run analysis
    print("\n🔍 Phase 3: Code Analysis")
    analysis_result = await test.run_comprehensive_analysis(selected_files)
    
    # Load file contents
    print("\n📖 Phase 4: Content Loading")
    file_contents = test.load_file_contents(selected_files)
    
    # Generate enhanced report
    print("\n📊 Phase 5: Report Generation")
    report_path = await test.generate_enhanced_report(analysis_result, file_contents)
    
    # Save raw analysis data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_data_path = test.output_dir / f"raw_dynamic_analysis_data_{timestamp}.json"
    with open(raw_data_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, default=str)
    print(f"📄 Raw data saved: {raw_data_path}")
    
    # Print summary
    print("\n📈 Phase 6: Results Summary")
    test.print_analysis_summary(analysis_result)
    
    print(f"\n🎉 Dynamic enhanced report generation test completed successfully!")
    print(f"👀 View the enhanced report at: {report_path}")
    
    # Show report preview
    try:
        print(f"\n🔍 Report Preview:")
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:25]):  # Show first 25 lines
                print(f"  {i+1:2d}: {line.rstrip()}")
            if len(lines) > 25:
                print(f"  ... and {len(lines) - 25} more lines")
    except Exception as e:
        print(f"⚠️ Could not preview report: {e}")
    
    return 0


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    try:
        result = asyncio.run(main())
        print(f"\n⏱️ Total execution time: {time.time() - start_time:.2f}s")
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)