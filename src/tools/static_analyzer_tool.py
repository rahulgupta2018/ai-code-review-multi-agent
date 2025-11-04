"""
Static Analyzer Tool Implementation for ADK Code Review System.

This tool provides static code analysis and security vulnerability detection.
"""

import time
import re
from typing import Dict, Any, Optional, List


class StaticAnalyzerTool:
    """Static code analysis and security scanning tool."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **parameters):
        """Initialize the static analyzer tool with configuration."""
        self.config = config or {}
        self.parameters = parameters
        self.name = "StaticAnalyzerTool"
        self.description = "Static code analysis and security vulnerability detection"
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute static analysis on the provided code context."""
        execution_start = time.time()
        
        try:
            # Extract code and language from context
            code = context.get('code', context.get('test_code', ''))
            language = context.get('language', 'python')
            
            if not code:
                return {
                    'status': 'error',
                    'error_message': 'No code provided for analysis',
                    'tool_name': self.name
                }
            
            # Perform static analysis
            analysis_result = {
                'status': 'success',
                'tool_name': self.name,
                'language': language,
                'analysis_type': 'static_analysis',
                'results': {
                    'security_findings': self._analyze_security_issues(code, language),
                    'code_quality_issues': self._analyze_code_quality(code, language),
                    'potential_bugs': self._detect_potential_bugs(code, language),
                    'risk_assessment': self._assess_risk_level(code),
                    'recommendations': self._generate_recommendations(code, language)
                },
                'summary': {
                    'total_issues': 0,
                    'critical_issues': 0,
                    'high_issues': 0,
                    'medium_issues': 0,
                    'low_issues': 0
                },
                'metadata': {
                    'tool_version': '1.0.0',
                    'analysis_timestamp': time.time(),
                    'configuration': self.config,
                    'parameters': self.parameters
                }
            }
            
            # Count issues by severity
            all_findings = (analysis_result['results']['security_findings'] + 
                          analysis_result['results']['code_quality_issues'] + 
                          analysis_result['results']['potential_bugs'])
            
            for finding in all_findings:
                analysis_result['summary']['total_issues'] += 1
                severity = finding.get('severity', 'low')
                analysis_result['summary'][f'{severity}_issues'] += 1
            
            execution_time = time.time() - execution_start
            analysis_result['execution_time_seconds'] = execution_time
            
            return analysis_result
            
        except Exception as e:
            execution_time = time.time() - execution_start
            return {
                'status': 'error',
                'tool_name': self.name,
                'error_message': str(e),
                'error_type': type(e).__name__,
                'execution_time_seconds': execution_time
            }
    
    def _analyze_security_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code for security vulnerabilities."""
        security_findings = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected', 'high'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected', 'high'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected', 'high'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token detected', 'medium'),
        ]
        
        for pattern, message, severity in secret_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                security_findings.append({
                    'type': 'security_vulnerability',
                    'category': 'hardcoded_secrets',
                    'message': message,
                    'severity': severity,
                    'line': code[:match.start()].count('\n') + 1,
                    'evidence': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                })
        
        # Check for SQL injection patterns
        sql_patterns = [
            (r'execute\s*\([^)]*%s[^)]*\)', 'Potential SQL injection via string formatting', 'critical'),
            (r'query\s*\+\s*["\'][^"\']*["\']', 'Potential SQL injection via string concatenation', 'high'),
        ]
        
        for pattern, message, severity in sql_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                security_findings.append({
                    'type': 'security_vulnerability',
                    'category': 'sql_injection',
                    'message': message,
                    'severity': severity,
                    'line': code[:match.start()].count('\n') + 1,
                    'evidence': match.group()
                })
        
        return security_findings
    
    def _analyze_code_quality(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code quality issues."""
        quality_issues = []
        
        lines = code.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines):
            if len(line) > 120:
                quality_issues.append({
                    'type': 'code_quality',
                    'category': 'line_length',
                    'message': f'Line too long ({len(line)} characters)',
                    'severity': 'low',
                    'line': i + 1,
                    'evidence': line[:80] + '...' if len(line) > 80 else line
                })
        
        # Check for TODO/FIXME comments
        todo_patterns = [
            (r'#\s*TODO', 'TODO comment found', 'low'),
            (r'#\s*FIXME', 'FIXME comment found', 'medium'),
            (r'#\s*HACK', 'HACK comment found', 'medium'),
        ]
        
        for pattern, message, severity in todo_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                quality_issues.append({
                    'type': 'code_quality',
                    'category': 'technical_debt',
                    'message': message,
                    'severity': severity,
                    'line': code[:match.start()].count('\n') + 1,
                    'evidence': match.group()
                })
        
        return quality_issues
    
    def _detect_potential_bugs(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect potential bugs in the code."""
        potential_bugs = []
        
        # Check for empty except blocks
        if language.lower() == 'python':
            empty_except_pattern = r'except[^:]*:\s*pass'
            matches = re.finditer(empty_except_pattern, code)
            for match in matches:
                potential_bugs.append({
                    'type': 'potential_bug',
                    'category': 'error_handling',
                    'message': 'Empty except block - errors may be silently ignored',
                    'severity': 'medium',
                    'line': code[:match.start()].count('\n') + 1,
                    'evidence': match.group()
                })
        
        # Check for print statements (potential debug code)
        print_patterns = [
            (r'print\s*\(', 'Print statement found - potential debug code', 'low'),
            (r'console\.log\s*\(', 'Console.log found - potential debug code', 'low'),
        ]
        
        for pattern, message, severity in print_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                potential_bugs.append({
                    'type': 'potential_bug',
                    'category': 'debug_code',
                    'message': message,
                    'severity': severity,
                    'line': code[:match.start()].count('\n') + 1,
                    'evidence': match.group()
                })
        
        return potential_bugs
    
    def _assess_risk_level(self, code: str) -> Dict[str, Any]:
        """Assess overall risk level of the code."""
        risk_factors = {
            'hardcoded_credentials': len(re.findall(r'password|api_key|secret|token', code, re.IGNORECASE)),
            'external_calls': len(re.findall(r'requests\.|urllib\.|http', code, re.IGNORECASE)),
            'file_operations': len(re.findall(r'open\(|file\(|read\(|write\(', code, re.IGNORECASE)),
            'eval_usage': len(re.findall(r'eval\(|exec\(', code, re.IGNORECASE)),
        }
        
        total_risk_score = sum(risk_factors.values())
        
        if total_risk_score >= 10:
            risk_level = 'high'
        elif total_risk_score >= 5:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'overall_risk_level': risk_level,
            'risk_score': total_risk_score,
            'risk_factors': risk_factors
        }
    
    def _generate_recommendations(self, code: str, language: str) -> List[str]:
        """Generate security and quality recommendations."""
        recommendations = []
        
        if 'password' in code.lower() or 'api_key' in code.lower():
            recommendations.append("Use environment variables or secure configuration for sensitive data")
        
        if 'eval(' in code or 'exec(' in code:
            recommendations.append("Avoid using eval() or exec() - consider safer alternatives")
        
        if len(code.split('\n')) > 100:
            recommendations.append("Consider breaking down large files into smaller, more manageable modules")
        
        if 'TODO' in code or 'FIXME' in code:
            recommendations.append("Address TODO and FIXME comments before production deployment")
        
        return recommendations