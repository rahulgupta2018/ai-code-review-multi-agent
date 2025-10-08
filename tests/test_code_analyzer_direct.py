#!/usr/bin/env python3
"""
Direct Code Analysis Tools Test
Tests individual analysis tools and generates outputs to src/outputs/code_analyzer
"""

import json
import time
from pathlib import Path
from datetime import datetime

def create_test_code_files():
    """Create sample code files with various quality issues for testing"""
    
    test_files_dir = Path(__file__).parent / "test_files" 
    test_files_dir.mkdir(exist_ok=True)
    
    # Test file 1: Poor quality Python code
    poor_code = '''
def calculate_complex_stuff(a, b, c, d, e, f, g, h, i, j):
    """This function has too many parameters and nested conditions"""
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
    """Duplicate function #1"""
    result = x * 2
    result = result + 10
    result = result / 3
    return result

def duplicate_logic_2(y):
    """Duplicate function #2 - same logic as #1"""
    result = y * 2
    result = result + 10
    result = result / 3
    return result

class badlyNamedClass:
    """Class with poor naming and structure"""
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

def analyze_code_complexity(file_path, content):
    """Analyze code complexity metrics"""
    lines = content.split('\n')
    
    # Basic complexity metrics
    metrics = {
        "lines_of_code": len([line for line in lines if line.strip()]),
        "total_lines": len(lines),
        "functions": content.count("def ") + content.count("function "),
        "classes": content.count("class "),
        "cyclomatic_complexity": calculate_cyclomatic_complexity(content),
        "nesting_depth": calculate_max_nesting_depth(content)
    }
    
    findings = []
    
    # Check for complexity issues
    if metrics["cyclomatic_complexity"] > 10:
        findings.append({
            "file": file_path,
            "line": 0,
            "severity": "high",
            "category": "complexity",
            "title": "High Cyclomatic Complexity",
            "description": f"Cyclomatic complexity is {metrics['cyclomatic_complexity']}, which exceeds the recommended threshold of 10"
        })
    
    if metrics["nesting_depth"] > 4:
        findings.append({
            "file": file_path,
            "line": 0, 
            "severity": "medium",
            "category": "complexity",
            "title": "Deep Nesting",
            "description": f"Maximum nesting depth is {metrics['nesting_depth']}, consider refactoring"
        })
    
    return metrics, findings

def detect_code_duplication(file_path, content):
    """Detect code duplication"""
    lines = content.split('\n')
    findings = []
    
    # Simple duplication detection - look for similar function patterns
    function_lines = [i for i, line in enumerate(lines) if 'def ' in line or 'function ' in line]
    
    for i, func_line in enumerate(function_lines):
        for j, other_func_line in enumerate(function_lines[i+1:], i+1):
            # Get function bodies (simplified)
            func1_end = function_lines[i+1] if i+1 < len(function_lines) else len(lines)
            func2_end = function_lines[j+1] if j+1 < len(function_lines) else len(lines)
            
            func1_body = '\n'.join(lines[func_line:func1_end])
            func2_body = '\n'.join(lines[other_func_line:func2_end])
            
            # Simple similarity check
            similarity = calculate_similarity(func1_body, func2_body)
            if similarity > 0.8:
                findings.append({
                    "file": file_path,
                    "line": func_line + 1,
                    "severity": "medium",
                    "category": "duplication",
                    "title": "Potential Code Duplication",
                    "description": f"Function at line {func_line + 1} appears similar to function at line {other_func_line + 1}"
                })
    
    return {"duplicated_blocks": len(findings)}, findings

def assess_maintainability(file_path, content):
    """Assess maintainability of code"""
    lines = content.split('\n')
    
    # Basic maintainability metrics
    metrics = {
        "documentation_ratio": calculate_documentation_ratio(content),
        "average_function_length": calculate_avg_function_length(content),
        "naming_consistency": assess_naming_consistency(content),
        "modularity_score": assess_modularity(content)
    }
    
    findings = []
    
    # Check maintainability issues
    if metrics["documentation_ratio"] < 0.2:
        findings.append({
            "file": file_path,
            "line": 0,
            "severity": "medium",
            "category": "maintainability",
            "title": "Poor Documentation",
            "description": f"Documentation ratio is {metrics['documentation_ratio']:.2f}, consider adding more comments"
        })
    
    if metrics["average_function_length"] > 50:
        findings.append({
            "file": file_path,
            "line": 0,
            "severity": "medium", 
            "category": "maintainability",
            "title": "Long Functions",
            "description": f"Average function length is {metrics['average_function_length']:.1f} lines, consider breaking down large functions"
        })
    
    return metrics, findings

# Helper functions for analysis
def calculate_cyclomatic_complexity(content):
    """Calculate cyclomatic complexity"""
    # Count decision points
    decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or']
    complexity = 1  # Base complexity
    
    for keyword in decision_keywords:
        complexity += content.count(keyword)
    
    return min(complexity, 50)  # Cap at reasonable maximum

def calculate_max_nesting_depth(content):
    """Calculate maximum nesting depth"""
    lines = content.split('\n')
    max_depth = 0
    current_depth = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('if ', 'for ', 'while ', 'try:', 'def ', 'class ')):
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif stripped in ['else:', 'elif', 'except:', 'finally:']:
            continue
        elif not stripped or stripped.startswith('#'):
            continue
        else:
            # Check for end of block (simplified)
            if line and not line[0].isspace() and current_depth > 0:
                current_depth = max(0, current_depth - 1)
    
    return max_depth

def calculate_similarity(text1, text2):
    """Calculate simple text similarity"""
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
        
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)

def calculate_documentation_ratio(content):
    """Calculate ratio of documentation to code"""
    lines = content.split('\n')
    doc_lines = 0
    code_lines = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        elif stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            doc_lines += 1
        elif stripped.startswith('//') or stripped.startswith('/*'):
            doc_lines += 1
        else:
            code_lines += 1
    
    if code_lines == 0:
        return 0
    return doc_lines / (doc_lines + code_lines)

def calculate_avg_function_length(content):
    """Calculate average function length"""
    lines = content.split('\n')
    function_starts = []
    
    for i, line in enumerate(lines):
        if 'def ' in line or 'function ' in line:
            function_starts.append(i)
    
    if not function_starts:
        return 0
    
    total_length = 0
    for i, start in enumerate(function_starts):
        end = function_starts[i + 1] if i + 1 < len(function_starts) else len(lines)
        total_length += end - start
    
    return total_length / len(function_starts)

def assess_naming_consistency(content):
    """Assess naming consistency score"""
    # Simplified - just check for consistent casing
    snake_case_count = content.count('_')
    camel_case_patterns = sum(1 for char in content if char.isupper())
    
    total_patterns = snake_case_count + camel_case_patterns
    if total_patterns == 0:
        return 1.0
    
    # Higher score if one pattern dominates
    dominant_pattern = max(snake_case_count, camel_case_patterns)
    return dominant_pattern / total_patterns

def assess_modularity(content):
    """Assess modularity score"""
    lines = content.split('\n')
    
    # Count imports, classes, functions
    imports = sum(1 for line in lines if line.strip().startswith(('import ', 'from ')))
    classes = content.count('class ')
    functions = content.count('def ') + content.count('function ')
    
    # Simple modularity score
    total_structures = classes + functions
    if total_structures == 0:
        return 0.5
    
    # Higher score for more modular code
    return min(1.0, (imports + total_structures) / 10)

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
        "agent": "code_analyzer",
        "findings": results.get("findings", [])
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
        category = finding.get('category', 'general')
        if category not in findings_by_category:
            findings_by_category[category] = []
        findings_by_category[category].append(finding)
    
    for category, category_findings in findings_by_category.items():
        report_content += f"\n### {category.title()} ({len(category_findings)} issues)\n\n"
        for finding in category_findings:
            file_path = finding.get('file', 'unknown')
            line_num = finding.get('line', 0)
            title = finding.get('title', 'Issue detected')
            description = finding.get('description', '')
            severity = finding.get('severity', 'unknown')
            
            report_content += f"**{title}** ({severity})\n"
            report_content += f"- File: `{file_path}:{line_num}`\n"
            report_content += f"- Description: {description}\n\n"
    
    # Add metrics details
    report_content += "\n## Detailed Metrics\n\n"
    for file_path, file_metrics in results.get("metrics", {}).items():
        report_content += f"### {file_path}\n\n"
        if isinstance(file_metrics, dict):
            for metric_name, metric_value in file_metrics.items():
                if isinstance(metric_value, float):
                    report_content += f"- **{metric_name}**: {metric_value:.2f}\n"
                else:
                    report_content += f"- **{metric_name}**: {metric_value}\n"
        report_content += "\n"
    
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    return {
        "findings_file": str(findings_file),
        "metrics_file": str(metrics_file),
        "report_file": str(report_file)
    }

def run_comprehensive_test():
    """Run comprehensive test of the code analyzer tools"""
    print("🚀 Starting Comprehensive Code Analysis Test")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create test files
    print("📝 Creating test code files...")
    test_files = create_test_code_files()
    print(f"✅ Created {len(test_files)} test files")
    
    # Setup output directory
    output_dir = Path(__file__).parent.parent / "src" / "outputs" / "code_analyzer"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analysis results
    all_findings = []
    all_metrics = {}
    
    # Test each file
    for i, file_path in enumerate(test_files, 1):
        print(f"\n📊 Analyzing file {i}/{len(test_files)}: {Path(file_path).name}")
        print("-" * 40)
        
        try:
            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Run all analysis tools
            complexity_metrics, complexity_findings = analyze_code_complexity(file_path, content)
            duplication_metrics, duplication_findings = detect_code_duplication(file_path, content)
            maintainability_metrics, maintainability_findings = assess_maintainability(file_path, content)
            
            # Combine results
            file_metrics = {
                "complexity": complexity_metrics,
                "duplication": duplication_metrics,
                "maintainability": maintainability_metrics
            }
            
            file_findings = complexity_findings + duplication_findings + maintainability_findings
            
            all_metrics[file_path] = file_metrics
            all_findings.extend(file_findings)
            
            print(f"✅ Analysis complete:")
            print(f"   - Complexity findings: {len(complexity_findings)}")
            print(f"   - Duplication findings: {len(duplication_findings)}")
            print(f"   - Maintainability findings: {len(maintainability_findings)}")
            print(f"   - Total findings: {len(file_findings)}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    
    # Prepare combined results
    execution_time = time.time() - start_time
    combined_result = {
        "findings": all_findings,
        "metrics": all_metrics,
        "execution_time": execution_time,
        "success": True,
        "errors": []
    }
    
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
    
    # Show findings breakdown
    findings_by_category = {}
    for finding in all_findings:
        category = finding.get('category', 'general')
        findings_by_category[category] = findings_by_category.get(category, 0) + 1
    
    print(f"\n📋 Findings by Category:")
    for category, count in findings_by_category.items():
        print(f"   - {category.title()}: {count}")
    
    return output_files

if __name__ == "__main__":
    run_comprehensive_test()