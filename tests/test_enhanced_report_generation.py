#!/usr/bin/env python3
"""
Enhanced Report Generation Test
Tests the enhanced report generator with LLM-powered insights, structured metrics,
and actionable recommendations using the real analysis tools.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the enhanced report generator
from agents.base.tools.report_generator import create_enhanced_report_generator

# Import the agent classes
from agents.code_analyzer.agent import CodeAnalysisConfig, CodeAnalyzerAgent


def create_test_code_files():
    """Create sample code files with various quality issues for testing"""
    
    test_files_dir = Path(__file__).parent / "test_files" 
    test_files_dir.mkdir(exist_ok=True)
    
    # Test file 1: Poor quality Python code with multiple issues
    poor_code = '''
def process_user_data(data):
    # Poor quality: deep nesting, no documentation, complex logic
    if data:
        if data.get("name"):
            if len(data["name"]) > 0:
                if data.get("email"):
                    if "@" in data["email"]:
                        if data.get("age"):
                            if data["age"] > 0:
                                if data.get("preferences"):
                                    if isinstance(data["preferences"], dict):
                                        if "theme" in data["preferences"]:
                                            return True
    return False

def calculate_metrics(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t):
    # Poor quality: too many parameters, no documentation, complex calculation
    result = a + b + c + d + e + f + g + h + i + j
    result = result * k + l - m + n / o
    for x in range(100):
        if x % 2 == 0:
            result += x
        else:
            result -= x
            for y in range(50):
                result += y * 2
                if y > 25:
                    for z in range(10):
                        result += z
    return result

def duplicate_logic_1(x):
    # Duplicate code pattern
    result = x * 2
    result = result + 10
    result = result / 3
    return result

def duplicate_logic_2(y):
    # Duplicate code pattern (same as above)
    result = y * 2
    result = result + 10
    result = result / 3
    return result

class DataProcessor:
    def __init__(self):
        # Poor quality: no documentation, unclear variable names
        self.x = 1
        self.y = 2
        self.data = {}
        
    def process(self,data):
        # Poor quality: no documentation, minimal logic
        return data+1
    
    def validate(self,input):
        # Poor quality: always returns True
        return True
'''
    
    # Test file 2: Good quality Python code
    good_code = '''"""
High-quality user authentication service with proper documentation,
error handling, and clean architecture following best practices.
"""

from typing import Optional, Dict, Any
import logging
import hashlib

logger = logging.getLogger(__name__)


class UserAuthenticationService:
    """
    Service for handling user authentication with comprehensive validation
    and security measures.
    
    This service provides secure user authentication with features like:
    - Password validation and hashing
    - Session management
    - Security logging
    - Rate limiting protection
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication service with configuration.
        
        Args:
            config: Configuration dictionary containing auth settings
                   - max_login_attempts: Maximum failed login attempts (default: 3)
                   - session_timeout: Session timeout in seconds (default: 3600)
                   - password_min_length: Minimum password length (default: 8)
        """
        self.config = config
        self.max_attempts = config.get('max_login_attempts', 3)
        self.session_timeout = config.get('session_timeout', 3600)
        self.password_min_length = config.get('password_min_length', 8)
        self.failed_attempts = {}
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password.
        
        Args:
            username: User's username (must be at least 3 characters)
            password: User's password (must meet security requirements)
            
        Returns:
            Dict containing user session data if authentication successful,
            None if authentication fails
            
        Raises:
            ValueError: If username or password format is invalid
            SecurityError: If account is locked due to too many failed attempts
        """
        if not self._validate_credentials(username, password):
            logger.warning(f"Invalid credential format for user: {username}")
            return None
        
        if self._is_account_locked(username):
            logger.warning(f"Account locked for user: {username}")
            return None
        
        try:
            user_data = self._fetch_user_data(username)
            if self._verify_password(password, user_data.get('password_hash')):
                self._reset_failed_attempts(username)
                session = self._create_session(user_data)
                logger.info(f"Successful authentication for user: {username}")
                return session
            else:
                self._record_failed_attempt(username)
                logger.warning(f"Password verification failed for user: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return None
    
    def _validate_credentials(self, username: str, password: str) -> bool:
        """
        Validate credential format and basic requirements.
        
        Returns:
            True if credentials meet minimum format requirements
        """
        if not username or len(username) < 3:
            return False
        if not password or len(password) < self.password_min_length:
            return False
        return True
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts."""
        return self.failed_attempts.get(username, 0) >= self.max_attempts
    
    def _fetch_user_data(self, username: str) -> Dict[str, Any]:
        """
        Fetch user data from secure storage.
        
        Note: In production, this would connect to a secure database
        """
        # Placeholder implementation
        return {
            "user_id": f"user_{username}",
            "username": username, 
            "password_hash": self._hash_password("secure_password")
        }
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against stored hash using secure comparison."""
        return self._hash_password(password) == password_hash
    
    def _hash_password(self, password: str) -> str:
        """Create secure hash of password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _create_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create authenticated user session with security metadata."""
        return {
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "session_id": f"session_{int(time.time())}_{user_data.get('user_id')}",
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + self.session_timeout,
            "permissions": ["read", "write"]
        }
    
    def _record_failed_attempt(self, username: str) -> None:
        """Record failed login attempt for security monitoring."""
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
    
    def _reset_failed_attempts(self, username: str) -> None:
        """Reset failed login attempts after successful authentication."""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
'''
    
    # Test file 3: Mixed quality JavaScript code
    js_code = '''/**
 * User profile management system with mixed quality patterns
 * Demonstrates both good and poor coding practices
 */

class UserProfileManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.cache = new Map();
        this.requestQueue = [];
    }

    /**
     * Retrieves user profile with caching support and error handling
     * @param {string} userId - The user identifier (required)
     * @returns {Promise<Object>} User profile data
     * @throws {Error} If userId is invalid or request fails
     */
    async getUserProfile(userId) {
        if (!userId || typeof userId !== 'string') {
            throw new Error('Valid user ID string is required');
        }

        // Check cache first for performance
        if (this.cache.has(userId)) {
            return this.cache.get(userId);
        }

        try {
            const profile = await this.apiClient.get(`/users/${userId}`);
            
            // Cache the result with TTL
            this.cache.set(userId, profile);
            setTimeout(() => {
                this.cache.delete(userId);
            }, 300000); // 5 minutes TTL
            
            return profile;
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            throw new Error(`Profile fetch failed: ${error.message}`);
        }
    }

    // POOR QUALITY: Deep nesting, no documentation, unclear logic
    updateUserPreferences(userId, preferences) {
        if (userId) {
            if (preferences) {
                if (typeof preferences === 'object') {
                    if (preferences.theme) {
                        if (preferences.theme === 'dark' || preferences.theme === 'light') {
                            if (preferences.language) {
                                if (preferences.language.length === 2) {
                                    if (preferences.notifications) {
                                        if (preferences.notifications.email !== undefined) {
                                            if (preferences.notifications.push !== undefined) {
                                                if (preferences.privacy) {
                                                    if (preferences.privacy.shareData !== undefined) {
                                                        return this.apiClient.patch(`/users/${userId}/preferences`, preferences);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    // POOR QUALITY: No error handling, unclear nested loops, no documentation
    processUserData(data) {
        let result = [];
        for (let i = 0; i < data.length; i++) {
            for (let j = 0; j < data[i].items.length; j++) {
                for (let k = 0; k < data[i].items[j].properties.length; k++) {
                    for (let l = 0; l < data[i].items[j].properties[k].values.length; l++) {
                        result.push(data[i].items[j].properties[k].values[l]);
                    }
                }
            }
        }
        return result;
    }

    // DUPLICATE CODE: Similar to getUserProfile but with slight differences
    async getUser(userId) {
        if (!userId) {
            throw new Error('User ID is required');
        }

        if (this.cache.has(userId)) {
            return this.cache.get(userId);
        }

        try {
            const user = await this.apiClient.get(`/users/${userId}`);
            this.cache.set(userId, user);
            return user;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            throw error;
        }
    }

    // DUPLICATE CODE: Another similar method
    async fetchUserData(id) {
        if (!id) {
            throw new Error('ID is required');
        }

        if (this.cache.has(id)) {
            return this.cache.get(id);
        }

        try {
            const userData = await this.apiClient.get(`/users/${id}`);
            this.cache.set(id, userData);
            return userData;
        } catch (error) {
            console.error('Failed to fetch user data:', error);
            throw error;
        }
    }
}

// POOR QUALITY: No class, global functions, no error handling
function validateEmail(email) {
    if (email) {
        if (email.includes('@')) {
            if (email.includes('.')) {
                if (email.length > 5) {
                    if (email.indexOf('@') > 0) {
                        if (email.lastIndexOf('.') > email.indexOf('@')) {
                            return true;
                        }
                    }
                }
            }
        }
    }
    return false;
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


async def run_enhanced_analysis(file_paths):
    """Run analysis using real tools via the agent"""
    print("🔍 Running comprehensive analysis with real tools...")
    
    all_findings = []
    all_metrics = {}
    start_time = time.time()
    
    # Initialize agent like the working test
    print("🤖 Initializing Code Analyzer Agent...")
    config = CodeAnalysisConfig(
        enable_enhanced_analysis=True,
        parallel_analysis=True,
        output_format='json'
    )
    agent = CodeAnalyzerAgent(config=config)
    print(f"✅ Agent initialized with {len(agent.tools)} tools")
    
    for file_path in file_paths:
        print(f"  📄 Analyzing: {Path(file_path).name}")
        
        try:
            # Use the agent's _analyze_single_file method like the working test
            findings, metrics = await agent._analyze_single_file(file_path, "enhanced")
            
            # Convert findings to consistent format
            processed_findings = []
            for finding in findings:
                finding_dict = {
                    'file': file_path,
                    'line': getattr(finding, 'line_number', getattr(finding, 'line', 1)),
                    'severity': str(getattr(finding, 'severity', 'MEDIUM')),
                    'category': getattr(finding, 'category', 'general'),
                    'description': getattr(finding, 'description', getattr(finding, 'message', 'Issue detected')),
                    'recommendation': getattr(finding, 'recommendation', '')
                }
                processed_findings.append(finding_dict)
            
            all_findings.extend(processed_findings)
            all_metrics[file_path] = metrics
            
            print(f"    ✅ Found {len(processed_findings)} issues")
            print(f"    📊 Metrics: {len(metrics)} categories")
            
        except Exception as e:
            print(f"    ❌ Error analyzing {file_path}: {e}")
            all_findings.append({
                'file': file_path,
                'line': 1,
                'severity': 'HIGH',
                'category': 'analysis_error',
                'description': f'Analysis failed: {str(e)}',
                'recommendation': 'Check file syntax and format'
            })
    
    execution_time = time.time() - start_time
    
    return {
        'findings': all_findings,
        'metrics': all_metrics,
        'execution_time': execution_time,
        'success': True
    }

def load_test_files_content(file_paths):
    """Load test file contents for code examples in report"""
    content_map = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content_map[file_path] = f.read()
        except Exception as e:
            print(f"⚠️ Failed to load {file_path}: {e}")
            content_map[file_path] = "# File content could not be loaded"
    return content_map

async def main():
    """Main test function"""
    print("🚀 Enhanced Report Generation Test")
    print("=" * 60)
    
    # Create test files
    print("\n📝 Creating test code files...")
    test_files = create_test_code_files()
    print(f"✅ Created {len(test_files)} test files:")
    for file_path in test_files:
        print(f"  - {Path(file_path).name}")
    
    # Run analysis
    print("\n🔍 Running comprehensive analysis...")
    analysis_result = await run_enhanced_analysis(test_files)
    
    print(f"✅ Analysis completed in {analysis_result['execution_time']:.2f}s")
    print(f"📊 Total findings: {len(analysis_result['findings'])}")
    
    # Setup output directory  
    output_dir = Path(__file__).parent.parent / "src" / "outputs" / "code_analyzer" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate enhanced report
    print("\n📊 Generating enhanced comprehensive report...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"enhanced_analysis_report_{timestamp}.md"
    
    try:
        # Load test files content for code examples
        test_files_content = load_test_files_content(test_files)
        
        # Create enhanced report generator
        report_generator = create_enhanced_report_generator()
        
        # Generate comprehensive report with LLM insights
        await report_generator.generate_enhanced_report(
            analysis_result,
            str(report_path),
            test_files_content
        )
        
        print(f"✅ Enhanced report generated: {report_path}")
        print(f"📄 Report size: {report_path.stat().st_size / 1024:.1f} KB")
        
        # Display summary
        print("\n📋 Analysis Summary:")
        print(f"  - Files analyzed: {len(analysis_result['metrics'])}")
        print(f"  - Total findings: {len(analysis_result['findings'])}")
        print(f"  - Execution time: {analysis_result['execution_time']:.2f}s")
        
        # Show findings breakdown by severity
        severity_counts = {}
        for finding in analysis_result['findings']:
            severity = finding.get('severity', 'UNKNOWN').replace('FindingSeverity.', '')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("\n📊 Findings by Severity:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                print(f"  - {severity}: {count}")
        
        # Show findings by category
        category_counts = {}
        for finding in analysis_result['findings']:
            category = finding.get('category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\n📊 Findings by Category:")
        for category, count in sorted(category_counts.items()):
            print(f"  - {category}: {count}")
        
        # Save raw analysis data for debugging
        raw_data_path = output_dir / f"raw_analysis_data_{timestamp}.json"
        with open(raw_data_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        print(f"📄 Raw data saved: {raw_data_path}")
        
        print("\n🎉 Enhanced report generation test completed successfully!")
        print(f"👀 View the enhanced report at: {report_path}")
        
        # Output key information for verification
        print(f"\n🔍 Report Preview:")
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20]):  # Show first 20 lines
                print(f"  {i+1:2d}: {line.rstrip()}")
            if len(lines) > 20:
                print(f"  ... and {len(lines) - 20} more lines")
        
        return 0
        
    except Exception as e:
        print(f"❌ Enhanced report generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Generate fallback basic report
        print("📄 Generating fallback basic report...")
        basic_content = f"""# Basic Code Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Files Analyzed: {len(analysis_result['metrics'])}
- Total Findings: {len(analysis_result['findings'])}
- Execution Time: {analysis_result['execution_time']:.2f}s

## Findings
"""
        
        for i, finding in enumerate(analysis_result['findings'], 1):
            basic_content += f"{i}. **{finding.get('description', 'Issue detected')}**\n"
            basic_content += f"   - File: {finding.get('file', 'unknown')}\n"
            basic_content += f"   - Line: {finding.get('line', 'N/A')}\n"
            basic_content += f"   - Severity: {finding.get('severity', 'UNKNOWN')}\n\n"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(basic_content)
        
        print(f"📄 Basic report saved: {report_path}")
        return 1

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