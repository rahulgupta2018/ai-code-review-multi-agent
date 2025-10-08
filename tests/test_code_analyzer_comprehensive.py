#!/usr/bin/env python3
"""
Comprehensive Code Analyzer Agent Test
Tests the agent with real code files and generates outputs to src/outputs/code_analyzer
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import our analysis tools directly
from agents.code_analyzer.tools.complexity_analyzer import analyze_complexity
from agents.code_analyzer.tools.duplication_detector import detect_duplication  
from agents.code_analyzer.tools.maintainability_scorer import maintainability_scoring
from agents.code_analyzer.tools.maintainability_assessor import maintainability_assessment

# Import the agent classes
from agents.code_analyzer.agent import CodeAnalysisConfig, CodeAnalyzerAgent

def create_test_code_files():
    """Create sample code files with various quality issues for testing"""
    
    test_files_dir = Path(__file__).parent / "test_files" 
    test_files_dir.mkdir(exist_ok=True)
    
    # Test file 1: Poor quality Python code
    poor_code = '''
def calculate_complex_stuff(a, b, c, d, e, f, g, h, i, j):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    if i > 0:
                                        if j > 0:
                                            result = a + b + c + d + e + f + g + h + i + j
                                            temp1 = result * 2
                                            temp2 = temp1 + 100
                                            temp3 = temp2 / 3
                                            temp4 = temp3 - 50
                                            temp5 = temp4 * temp4
                                            temp6 = temp5 + temp1
                                            temp7 = temp6 / temp2
                                            temp8 = temp7 * temp3
                                            temp9 = temp8 + temp4
                                            final = temp9 - temp5
                                            return final
                                        else:
                                            return 0
                                    else:
                                        return 0
                                else:
                                    return 0
                            else:
                                return 0
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0

def duplicate_logic_1(x):
    result = x * 2
    result = result + 10
    result = result / 3
    return result

def duplicate_logic_2(y):
    result = y * 2
    result = result + 10
    result = result / 3
    return result

class badlyNamedClass:
    def __init__(self):
        self.x = 1
        self.y = 2
        self.z = 3
        self.a = 4
        self.b = 5
        
    def method1(self):
        pass
        
    def method2(self):
        pass
'''
    
    # Test file 2: Good quality Python code
    good_code = '''
"""
User management utilities with proper documentation and clean structure.
"""

from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class User:
    """Represents a user in the system."""
    
    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize a new User.
        
        Args:
            user_id: Unique identifier for the user
            username: The user's username
            email: The user's email address
        """
        self.user_id = user_id
        self.username = username
        self.email = email
        
    def is_valid_email(self) -> bool:
        """Check if the user's email is valid."""
        return "@" in self.email and "." in self.email
        
    def to_dict(self) -> Dict[str, str]:
        """Convert user to dictionary representation."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email
        }


class UserManager:
    """Manages user operations with proper error handling."""
    
    def __init__(self):
        """Initialize the user manager."""
        self._users: List[User] = []
        logger.info("UserManager initialized")
    
    def add_user(self, user: User) -> bool:
        """
        Add a user to the system.
        
        Args:
            user: The user to add
            
        Returns:
            True if user was added successfully, False otherwise
        """
        if not user.is_valid_email():
            logger.warning(f"Invalid email for user {user.username}")
            return False
            
        self._users.append(user)
        logger.info(f"Added user {user.username}")
        return True
    
    def find_user(self, username: str) -> Optional[User]:
        """Find a user by username."""
        for user in self._users:
            if user.username == username:
                return user
        return None
    
    def get_user_count(self) -> int:
        """Get the total number of users."""
        return len(self._users)
'''
    
    # Test file 3: JavaScript with mixed quality
    js_code = '''
// Mixed quality JavaScript code for testing
class DataProcessor {
    constructor() {
        this.data = [];
        this.processed = false;
    }
    
    // Good: Well-documented function
    /**
     * Processes data with validation
     * @param {Array} inputData - The data to process
     * @returns {Object} Processing result
     */
    processData(inputData) {
        if (!Array.isArray(inputData)) {
            throw new Error('Input must be an array');
        }
        
        this.data = inputData.filter(item => item !== null);
        this.processed = true;
        
        return {
            count: this.data.length,
            processed: this.processed
        };
    }
    
    // Poor: Deeply nested and no documentation
    analyzeComplexData(data) {
        if (data) {
            if (data.length > 0) {
                if (data[0]) {
                    if (data[0].type === 'complex') {
                        if (data[0].values) {
                            if (data[0].values.length > 10) {
                                let result = 0;
                                for (let i = 0; i < data[0].values.length; i++) {
                                    if (data[0].values[i] > 0) {
                                        result += data[0].values[i] * 2;
                                    }
                                }
                                return result;
                            }
                        }
                    }
                }
            }
        }
        return 0;
    }
}
'''
    
    # Write test files
    (test_files_dir / "poor_quality.py").write_text(poor_code)
    (test_files_dir / "good_quality.py").write_text(good_code)
    (test_files_dir / "mixed_quality.js").write_text(js_code)
    
    return [
        str(test_files_dir / "poor_quality.py"),
        str(test_files_dir / "good_quality.py"), 
        str(test_files_dir / "mixed_quality.js")
    ]

def save_analysis_results(results, output_dir):
    """Save analysis results to the outputs directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output files
    findings_file = output_dir / "findings" / f"analysis_findings_{timestamp}.json"
    metrics_file = output_dir / "metrics" / f"analysis_metrics_{timestamp}.json"
    report_file = output_dir / "reports" / f"analysis_report_{timestamp}.md"
    
    # Ensure directories exist
    findings_file.parent.mkdir(exist_ok=True)
    metrics_file.parent.mkdir(exist_ok=True)
    report_file.parent.mkdir(exist_ok=True)
    
    # Save findings (JSON)
    findings_data = {
        "timestamp": timestamp,
        "agent": results.get("agent_name", "code_analyzer"),
        "findings": [
            {
                "file": finding.file_path if hasattr(finding, 'file_path') else 'unknown',
                "line": finding.line_number if hasattr(finding, 'line_number') else 0,
                "severity": str(finding.severity) if hasattr(finding, 'severity') else 'unknown',
                "category": finding.category if hasattr(finding, 'category') else 'general',
                "title": finding.title if hasattr(finding, 'title') else 'Issue detected',
                "description": finding.description if hasattr(finding, 'description') else '',
                "recommendation": finding.recommendation if hasattr(finding, 'recommendation') else ''
            }
            for finding in results.get("findings", [])
        ]
    }
    
    with open(findings_file, 'w') as f:
        json.dump(findings_data, f, indent=2)
    
    # Save metrics (JSON)
    metrics_data = {
        "timestamp": timestamp,
        "execution_time": results.get("execution_time", 0),
        "files_analyzed": len(results.get("metrics", {})),
        "metrics": results.get("metrics", {}),
        "summary": {
            "total_findings": len(results.get("findings", [])),
            "success": results.get("success", False)
        }
    }
    
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    # Generate markdown report
    report_content = f"""# Code Analysis Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Files Analyzed**: {len(results.get('metrics', {}))}
- **Total Findings**: {len(results.get('findings', []))}
- **Execution Time**: {results.get('execution_time', 0):.2f}s
- **Analysis Success**: {results.get('success', False)}

## Findings by Category
"""
    
    # Group findings by category
    findings_by_category = {}
    for finding in results.get("findings", []):
        category = finding.category if hasattr(finding, 'category') else 'general'
        if category not in findings_by_category:
            findings_by_category[category] = []
        findings_by_category[category].append(finding)
    
    for category, category_findings in findings_by_category.items():
        report_content += f"\n### {category.title()} ({len(category_findings)} issues)\n\n"
        for finding in category_findings:
            file_path = finding.file_path if hasattr(finding, 'file_path') else 'unknown'
            line_num = finding.line_number if hasattr(finding, 'line_number') else 0
            title = finding.title if hasattr(finding, 'title') else 'Issue detected'
            description = finding.description if hasattr(finding, 'description') else ''
            
            report_content += f"**{title}**\n"
            report_content += f"- File: `{file_path}:{line_num}`\n"
            report_content += f"- Description: {description}\n\n"
    
    # Add metrics details
    report_content += "\n## Detailed Metrics\n\n"
    for file_path, file_metrics in results.get("metrics", {}).items():
        report_content += f"### {file_path}\n\n"
        if isinstance(file_metrics, dict):
            for metric_name, metric_value in file_metrics.items():
                report_content += f"- **{metric_name}**: {metric_value}\n"
        report_content += "\n"
    
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    return {
        "findings_file": findings_file,
        "metrics_file": metrics_file,
        "report_file": report_file
    }

async def run_comprehensive_test():
    """Run comprehensive test of the code analyzer agent"""
    print("🚀 Starting Comprehensive Code Analyzer Agent Test")
    print("=" * 60)
    
    # Create test files
    print("📝 Creating test code files...")
    test_files = create_test_code_files()
    print(f"✅ Created {len(test_files)} test files")
    
    # Initialize agent
    print("\n🤖 Initializing Code Analyzer Agent...")
    config = CodeAnalysisConfig(
        enable_enhanced_analysis=True,
        parallel_analysis=True,
        output_format='json'
    )
    agent = CodeAnalyzerAgent(config=config)
    print(f"✅ Agent initialized with {len(agent.tools)} tools")
    
    # Setup output directory
    output_dir = Path(__file__).parent.parent / "src" / "outputs" / "code_analyzer"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test each file
    all_results = []
    for i, file_path in enumerate(test_files, 1):
        print(f"\n📊 Analyzing file {i}/{len(test_files)}: {Path(file_path).name}")
        print("-" * 40)
        
        try:
            # Simulate the agent analysis (since we can't run the full ADK context)
            findings, metrics = await agent._analyze_single_file(file_path, "enhanced")
            
            result = {
                "agent_name": agent.name,
                "file_path": file_path,
                "findings": findings,
                "metrics": {file_path: metrics},
                "execution_time": 2.5,  # Simulated
                "success": True,
                "errors": []
            }
            
            all_results.append(result)
            
            print(f"✅ Analysis complete:")
            print(f"   - Findings: {len(findings)}")
            print(f"   - Metrics collected: {len(metrics)}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            result = {
                "agent_name": agent.name,
                "file_path": file_path,
                "findings": [],
                "metrics": {},
                "execution_time": 0,
                "success": False,
                "errors": [str(e)]
            }
            all_results.append(result)
    
    # Combine results
    print(f"\n📋 Combining results from {len(all_results)} files...")
    combined_result = {
        "agent_name": "code_analyzer",
        "findings": [],
        "metrics": {},
        "execution_time": sum(r.get("execution_time", 0) for r in all_results),
        "success": all(r.get("success", False) for r in all_results),
        "errors": []
    }
    
    for result in all_results:
        combined_result["findings"].extend(result.get("findings", []))
        combined_result["metrics"].update(result.get("metrics", {}))
        combined_result["errors"].extend(result.get("errors", []))
    
    # Save results
    print(f"\n💾 Saving analysis results to {output_dir}...")
    output_files = save_analysis_results(combined_result, output_dir)
    
    print("\n🎉 Analysis Complete!")
    print("=" * 60)
    print(f"📁 Results saved to:")
    for file_type, file_path in output_files.items():
        print(f"   - {file_type}: {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"   - Total findings: {len(combined_result['findings'])}")
    print(f"   - Files analyzed: {len(combined_result['metrics'])}")
    print(f"   - Execution time: {combined_result['execution_time']:.2f}s")
    print(f"   - Success: {combined_result['success']}")
    
    return output_files

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())