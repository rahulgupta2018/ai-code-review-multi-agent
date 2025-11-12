"""
Utility functions for ADK Code Review System
Helper functions for session management and user interaction
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

def extract_code_from_input(user_input: str) -> Dict[str, Any]:
    """
    Extract code and language from user input.
    
    Args:
        user_input: Raw user input containing code and instructions
        
    Returns:
        Dictionary with extracted code, language, and analysis type
    """
    result = {
        'code': '',
        'language': 'python',  # default
        'analysis_type': 'general',
        'original_input': user_input
    }
    
    # Look for code blocks with language specification
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    code_blocks = re.findall(code_block_pattern, user_input, re.DOTALL)
    
    if code_blocks:
        # Use the first code block found
        language, code = code_blocks[0]
        result['code'] = code.strip()
        if language:
            result['language'] = language.lower()
    else:
        # Look for common code patterns
        # This is a simple heuristic - could be improved
        lines = user_input.split('\n')
        code_lines = []
        
        for line in lines:
            # Skip obviously non-code lines
            if (line.strip().startswith(('Review', 'Analyze', 'Check', 'Please', 'Can you')) and 
                not any(keyword in line for keyword in ['def ', 'class ', 'import ', '=', '(', ')', '{', '}'])):
                continue
            
            # Look for code-like patterns
            if any(pattern in line for pattern in ['def ', 'class ', 'import ', 'from ', 'if __name__', '    ']):
                code_lines.append(line)
        
        if code_lines:
            result['code'] = '\n'.join(code_lines)
    
    # Determine analysis type from user input
    input_lower = user_input.lower()
    if any(keyword in input_lower for keyword in ['quality', 'maintainability', 'readability']):
        result['analysis_type'] = 'quality'
    elif any(keyword in input_lower for keyword in ['security', 'vulnerability', 'secure']):
        result['analysis_type'] = 'security'
    elif any(keyword in input_lower for keyword in ['complexity', 'cyclomatic', 'maintainability']):
        result['analysis_type'] = 'complexity'
    elif any(keyword in input_lower for keyword in ['static', 'lint', 'issues']):
        result['analysis_type'] = 'static'
    elif any(keyword in input_lower for keyword in ['ast', 'parse', 'syntax']):
        result['analysis_type'] = 'ast'
    
    return result

def format_analysis_result(result: Any) -> str:
    """
    Format analysis result for user-friendly display.
    
    Args:
        result: Analysis result from agent
        
    Returns:
        Formatted string for display
    """
    if isinstance(result, str):
        return result
    
    if not isinstance(result, dict):
        return str(result)
    
    formatted_output = []
    
    # Handle different result structures
    if 'status' in result:
        if result['status'] == 'error':
            return f"❌ Analysis Error: {result.get('error_message', 'Unknown error')}"
        
        if result['status'] == 'success':
            formatted_output.append("✅ Analysis completed successfully\n")
    
    # Format tool-specific results
    if 'results' in result:
        results = result['results']
        
        # Security findings
        if 'security_findings' in results and results['security_findings']:
            formatted_output.append("🔒 Security Analysis:")
            for finding in results['security_findings']:
                severity_emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '⚡', 'low': '💡'}.get(finding.get('severity', 'low'), '💡')
                formatted_output.append(f"  {severity_emoji} {finding.get('message', 'Security issue found')}")
                if 'line' in finding:
                    formatted_output.append(f"     Line {finding['line']}: {finding.get('evidence', '')}")
            formatted_output.append("")
        
        # Code quality issues
        if 'code_quality_issues' in results and results['code_quality_issues']:
            formatted_output.append("📊 Code Quality Analysis:")
            for issue in results['code_quality_issues']:
                severity_emoji = {'high': '⚠️', 'medium': '⚡', 'low': '💡'}.get(issue.get('severity', 'low'), '💡')
                formatted_output.append(f"  {severity_emoji} {issue.get('message', 'Quality issue found')}")
                if 'line' in issue:
                    formatted_output.append(f"     Line {issue['line']}: {issue.get('evidence', '')}")
            formatted_output.append("")
        
        # Complexity metrics
        if 'complexity_metrics' in results:
            metrics = results['complexity_metrics']
            formatted_output.append("🧮 Complexity Analysis:")
            if 'cyclomatic_complexity' in metrics:
                cc = metrics['cyclomatic_complexity']
                cc_emoji = "🟢" if cc <= 10 else "🟡" if cc <= 15 else "🔴"
                formatted_output.append(f"  {cc_emoji} Cyclomatic Complexity: {cc}")
            
            if 'maintainability_index' in metrics:
                mi = metrics['maintainability_index']
                mi_emoji = "🟢" if mi >= 20 else "🟡" if mi >= 10 else "🔴"
                formatted_output.append(f"  {mi_emoji} Maintainability Index: {mi:.1f}")
            
            formatted_output.append("")
        
        # Recommendations
        if 'recommendations' in results and results['recommendations']:
            formatted_output.append("💡 Recommendations:")
            for rec in results['recommendations']:
                formatted_output.append(f"  • {rec}")
            formatted_output.append("")
    
    # Summary information
    if 'summary' in result:
        summary = result['summary']
        if 'total_issues' in summary and summary['total_issues'] > 0:
            formatted_output.append("📈 Summary:")
            formatted_output.append(f"  Total Issues: {summary['total_issues']}")
            if summary.get('critical_issues', 0) > 0:
                formatted_output.append(f"  🚨 Critical: {summary['critical_issues']}")
            if summary.get('high_issues', 0) > 0:
                formatted_output.append(f"  ⚠️ High: {summary['high_issues']}")
            if summary.get('medium_issues', 0) > 0:
                formatted_output.append(f"  ⚡ Medium: {summary['medium_issues']}")
            if summary.get('low_issues', 0) > 0:
                formatted_output.append(f"  💡 Low: {summary['low_issues']}")
            formatted_output.append("")
    
    # Execution time
    if 'execution_time_seconds' in result:
        formatted_output.append(f"⏱️ Analysis completed in {result['execution_time_seconds']:.2f} seconds")
    
    return '\n'.join(formatted_output) if formatted_output else "Analysis completed - no specific issues found."

def validate_code_input(code: str) -> Dict[str, Any]:
    """
    Validate that the provided code is suitable for analysis.
    
    Args:
        code: Code string to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': False,
        'issues': [],
        'warnings': [],
        'suggestions': []
    }
    
    if not code or not code.strip():
        result['issues'].append("No code provided for analysis")
        return result
    
    # Check minimum length
    if len(code.strip()) < 10:
        result['warnings'].append("Code snippet is very short - analysis may be limited")
    
    # Check for common code patterns
    code_indicators = ['def ', 'class ', 'import ', 'from ', '=', '(', ')', '{', '}']
    if not any(indicator in code for indicator in code_indicators):
        result['warnings'].append("Input doesn't appear to contain code - analysis may not be meaningful")
    
    # Check for extremely long code
    if len(code) > 10000:
        result['warnings'].append("Code is very long - consider analyzing smaller chunks for better results")
    
    # Basic syntax check for Python (simple heuristic)
    if 'def ' in code or 'class ' in code:
        # Check for basic Python indentation
        lines = code.split('\n')
        has_indented_lines = any(line.startswith('    ') or line.startswith('\t') for line in lines)
        if not has_indented_lines and any('def ' in line or 'class ' in line for line in lines):
            result['warnings'].append("Python code may have indentation issues")
    
    # If we get here without critical issues, mark as valid
    if not result['issues']:
        result['valid'] = True
        if not result['warnings']:
            result['suggestions'].append("Code appears ready for analysis")
    
    return result

def add_user_query_to_history(session_service, app_name: str, user_id: str, session_id: str, user_input: str):
    """
    Add user query to session history.
    
    Args:
        session_service: ADK session service
        app_name: Application name
        user_id: User identifier
        session_id: Session identifier
        user_input: User's input query
    """
    try:
        session = session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Add to review requests history
        if 'review_requests' not in session.state:
            session.state['review_requests'] = []
        
        session.state['review_requests'].append({
            'timestamp': datetime.now().isoformat(),
            'query': user_input[:200] + '...' if len(user_input) > 200 else user_input,  # Truncate long queries
            'processed': False
        })
        
        # Keep only last 20 requests
        if len(session.state['review_requests']) > 20:
            session.state['review_requests'] = session.state['review_requests'][-20:]
            
    except Exception as e:
        print(f"Warning: Could not update query history: {e}")

async def call_agent_async(runner, user_id: str, session_id: str, user_input: str):
    """
    Call agent asynchronously with user input.
    
    Args:
        runner: ADK runner instance
        user_id: User identifier
        session_id: Session identifier
        user_input: User's input
        
    Returns:
        Agent response
    """
    try:
        result = await runner.run_async(
            user_id=user_id,
            session_id=session_id,
            user_message=user_input
        )
        return result
    except Exception as e:
        print(f"Error calling agent: {e}")
        return None

def create_code_analysis_prompt(code: str, language: str, analysis_type: str) -> str:
    """
    Create a structured prompt for code analysis.
    
    Args:
        code: Code to analyze
        language: Programming language
        analysis_type: Type of analysis requested
        
    Returns:
        Formatted prompt string
    """
    analysis_instructions = {
        'quality': "Focus on code quality, maintainability, readability, and best practices",
        'security': "Focus on security vulnerabilities, potential exploits, and secure coding practices", 
        'complexity': "Focus on cyclomatic complexity, code complexity metrics, and maintainability",
        'static': "Focus on static analysis, potential bugs, code issues, and lint-like problems",
        'ast': "Focus on syntax validation, code structure, and AST-level analysis",
        'general': "Provide a comprehensive code review covering quality, security, and best practices"
    }
    
    instruction = analysis_instructions.get(analysis_type, analysis_instructions['general'])
    
    prompt = f"""
Please analyze the following {language} code. {instruction}.

Code to analyze:
```{language}
{code}
```

Please provide:
1. Detailed analysis results
2. Specific issues found (with line numbers if applicable)
3. Severity levels for any issues
4. Actionable recommendations for improvement
5. Best practices suggestions

Use your available tools for comprehensive analysis.
"""
    
    return prompt