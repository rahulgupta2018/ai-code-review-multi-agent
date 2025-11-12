"""
ADK Code Review System - Main Entry Point
Multi-agent code review system with session management and state tracking
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import the main code review orchestrator agent
from code_review_orchestrator.agent import code_review_orchestrator_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import utility functions
from utils import (
    extract_code_from_input, 
    format_analysis_result, 
    validate_code_input, 
    add_user_query_to_history,
    create_code_analysis_prompt
)

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# ===== PART 1: Initialize In-Memory Session Service =====
# Using in-memory storage for this example (non-persistent)
session_service = InMemorySessionService()

# ===== PART 2: Define Initial State =====
# This will be used when creating a new session
initial_state = {
    "user_name": "Code Reviewer",
    "review_requests": [],
    "analysis_history": [],
    "session_metadata": {
        "created_at": None,
        "total_reviews": 0,
        "active_agents": []
    },
    "quality_metrics": {
        "total_issues_found": 0,
        "critical_issues": 0,
        "high_issues": 0,
        "medium_issues": 0,
        "low_issues": 0
    }
}

def display_welcome():
    """Display welcome message and usage instructions."""
    print("=" * 60)
    print("🤖 ADK Multi-Agent Code Review System")
    print("=" * 60)
    print("\nWelcome to the AI-powered code review system!")
    print("\nSupported review types:")
    print("• Code quality analysis")
    print("• Static code analysis")
    print("• Complexity assessment")
    print("• Security vulnerability detection")
    print("• Best practices evaluation")
    print("\n📝 Usage Examples:")
    print("• 'Review this Python code for quality issues: [paste code]'")
    print("• 'Analyze the complexity of this function: [paste code]'")
    print("• 'Check for security vulnerabilities: [paste code]'")
    print("• 'Review code quality and suggest improvements: [paste code]'")
    print("\n💡 Commands:")
    print("• Type 'help' for detailed usage instructions")
    print("• Type 'status' to see session information")
    print("• Type 'clear' to reset session state")
    print("• Type 'exit' or 'quit' to end the session")
    print("=" * 60)

def display_help():
    """Display detailed help information."""
    print("\n📚 ADK Code Review System - Help")
    print("-" * 40)
    print("\n🎯 How to use:")
    print("1. Paste your code directly into the chat")
    print("2. Specify the type of analysis you want")
    print("3. The system will route your request to specialized agents")
    print("4. Review the comprehensive analysis results")
    print("\n🔧 Available Analysis Types:")
    print("• Quality Analysis: Code maintainability, readability, best practices")
    print("• Static Analysis: Security vulnerabilities, potential bugs")
    print("• Complexity Analysis: Cyclomatic complexity, maintainability metrics")
    print("• AST Analysis: Code structure and syntax validation")
    print("\n💻 Code Input Methods:")
    print("• Direct paste: Just paste your code and describe what you want")
    print("• With context: 'Review this Python class for quality issues: [code]'")
    print("• Specific focus: 'Check for security issues in this function: [code]'")
    print("\n📊 Session Features:")
    print("• State tracking across multiple reviews")
    print("• Analysis history preservation")
    print("• Cumulative metrics tracking")
    print("• Cross-review insights")

def display_session_status(session_service, app_name, user_id, session_id):
    """Display current session status and metrics."""
    try:
        session = session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        print("\n📊 Session Status")
        print("-" * 30)
        print(f"Session ID: {session_id}")
        print(f"User: {session.state.get('user_name', 'Unknown')}")
        print(f"Total Reviews: {session.state['session_metadata']['total_reviews']}")
        print(f"Review Requests: {len(session.state['review_requests'])}")
        
        metrics = session.state['quality_metrics']
        print(f"\n🔍 Quality Metrics Summary:")
        print(f"• Total Issues Found: {metrics['total_issues_found']}")
        print(f"• Critical Issues: {metrics['critical_issues']}")
        print(f"• High Priority: {metrics['high_issues']}")
        print(f"• Medium Priority: {metrics['medium_issues']}")
        print(f"• Low Priority: {metrics['low_issues']}")
        
        if session.state.get('analysis_history'):
            print(f"\n📈 Recent Analysis:")
            for i, analysis in enumerate(session.state['analysis_history'][-3:], 1):
                print(f"  {i}. {analysis.get('timestamp', 'Unknown time')}: {analysis.get('type', 'General')}")
    
    except Exception as e:
        print(f"❌ Error retrieving session status: {e}")

def update_session_metrics(session_service, app_name, user_id, session_id, analysis_result):
    """Update session metrics based on analysis results."""
    try:
        session = session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        # Update review count
        session.state['session_metadata']['total_reviews'] += 1
        
        # Update quality metrics if available
        if isinstance(analysis_result, dict) and 'results' in analysis_result:
            results = analysis_result['results']
            
            # Count issues from various analysis types
            total_new_issues = 0
            critical_new = high_new = medium_new = low_new = 0
            
            # Process different types of findings
            for finding_type in ['security_findings', 'code_quality_issues', 'potential_bugs']:
                if finding_type in results:
                    findings = results[finding_type]
                    if isinstance(findings, list):
                        for finding in findings:
                            severity = finding.get('severity', 'low')
                            total_new_issues += 1
                            
                            if severity == 'critical':
                                critical_new += 1
                            elif severity == 'high':
                                high_new += 1
                            elif severity == 'medium':
                                medium_new += 1
                            else:
                                low_new += 1
            
            # Update cumulative metrics
            metrics = session.state['quality_metrics']
            metrics['total_issues_found'] += total_new_issues
            metrics['critical_issues'] += critical_new
            metrics['high_issues'] += high_new
            metrics['medium_issues'] += medium_new
            metrics['low_issues'] += low_new
        
        # Add to analysis history
        session.state['analysis_history'].append({
            'timestamp': f"Review #{session.state['session_metadata']['total_reviews']}",
            'type': analysis_result.get('analysis_type', 'General Review'),
            'status': analysis_result.get('status', 'completed')
        })
        
        # Keep only last 10 analysis records
        if len(session.state['analysis_history']) > 10:
            session.state['analysis_history'] = session.state['analysis_history'][-10:]
            
    except Exception as e:
        print(f"⚠️ Warning: Could not update session metrics: {e}")

async def process_user_input(runner, user_id, session_id, user_input, session_service, app_name):
    """Process user input through the agent runner."""
    try:
        print("\n🔄 Processing your request...")
        
        # Extract and validate code from user input
        extracted = extract_code_from_input(user_input)
        
        if extracted['code']:
            print(f"📝 Detected {extracted['language']} code ({len(extracted['code'])} characters)")
            print(f"🎯 Analysis type: {extracted['analysis_type']}")
            
            # Validate the code
            validation = validate_code_input(extracted['code'])
            
            if not validation['valid']:
                print("❌ Code validation issues:")
                for issue in validation['issues']:
                    print(f"  • {issue}")
                return None
            
            if validation['warnings']:
                print("⚠️ Validation warnings:")
                for warning in validation['warnings']:
                    print(f"  • {warning}")
            
            # Create structured prompt for better analysis
            structured_prompt = create_code_analysis_prompt(
                extracted['code'], 
                extracted['language'], 
                extracted['analysis_type']
            )
            
            # Add query to history
            add_user_query_to_history(session_service, app_name, user_id, session_id, user_input)
            
            # Use structured prompt for analysis
            analysis_input = structured_prompt
        else:
            # Use original input if no code detected
            analysis_input = user_input
            print("💬 Processing general query...")
        
        # Run the agent with the processed input
        result = await runner.run_async(
            user_id=user_id,
            session_id=session_id,
            user_message=analysis_input
        )
        
        print("\n✅ Analysis Complete!")
        print("-" * 40)
        
        # Format and display the result
        if hasattr(result, 'content') and result.content:
            formatted_result = format_analysis_result(result.content)
            print(f"🤖 AI Analysis:\n{formatted_result}")
        elif isinstance(result, dict):
            if 'content' in result:
                formatted_result = format_analysis_result(result['content'])
                print(f"🤖 AI Analysis:\n{formatted_result}")
            else:
                formatted_result = format_analysis_result(result)
                print(f"🤖 Analysis Result:\n{formatted_result}")
        else:
            formatted_result = format_analysis_result(result)
            print(f"🤖 Response:\n{formatted_result}")
        
        # Update session metrics if we have analysis results
        if isinstance(result, dict):
            update_session_metrics(session_service, app_name, user_id, session_id, result)
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        import traceback
        print(f"Debug trace: {traceback.format_exc()}")
        return None

async def main_async():
    """Main async function for the code review system."""
    
    # Setup constants
    APP_NAME = "ADK_Code_Review_System"
    USER_ID = "code_reviewer_user"
    
    print("🚀 Initializing ADK Code Review System...")
    
    # ===== PART 3: Session Creation =====
    # Create a new session with initial state
    try:
        new_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state=initial_state.copy(),
        )
        SESSION_ID = new_session.id
        new_session.state['session_metadata']['created_at'] = f"Session {SESSION_ID}"
        print(f"✅ Created new session: {SESSION_ID}")
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return
    
    # ===== PART 4: Agent Runner Setup =====
    # Create a runner with the main code review orchestrator agent
    try:
        runner = Runner(
            agent=code_review_orchestrator_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        print("✅ Agent runner initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing runner: {e}")
        return
    
    # ===== PART 5: Interactive Code Review Loop =====
    display_welcome()
    
    while True:
        try:
            # Get user input
            print(f"\n{'='*60}")
            user_input = input("👤 Enter your code review request (or 'help'): ").strip()
            
            # Check for special commands
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Ending code review session. Goodbye!")
                break
            elif user_input.lower() == "help":
                display_help()
                continue
            elif user_input.lower() == "status":
                display_session_status(session_service, APP_NAME, USER_ID, SESSION_ID)
                continue
            elif user_input.lower() == "clear":
                # Reset session state
                new_session.state = initial_state.copy()
                new_session.state['session_metadata']['created_at'] = f"Session {SESSION_ID} (Reset)"
                print("🔄 Session state cleared successfully!")
                continue
            elif not user_input:
                print("⚠️ Please enter a code review request or command.")
                continue
            
            # Process the code review request
            await process_user_input(runner, USER_ID, SESSION_ID, user_input, session_service, APP_NAME)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Session interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("🔄 Continuing with session...")
    
    # ===== PART 6: Final State Examination =====
    print("\n" + "="*60)
    print("📊 Final Session Summary")
    print("="*60)
    
    try:
        final_session = session_service.get_session(
            app_name=APP_NAME, 
            user_id=USER_ID, 
            session_id=SESSION_ID
        )
        
        metadata = final_session.state['session_metadata']
        metrics = final_session.state['quality_metrics']
        
        print(f"Session ID: {SESSION_ID}")
        print(f"Total Reviews Completed: {metadata['total_reviews']}")
        print(f"Total Issues Found: {metrics['total_issues_found']}")
        print(f"Critical Issues: {metrics['critical_issues']}")
        print(f"High Priority Issues: {metrics['high_issues']}")
        
        if final_session.state['analysis_history']:
            print(f"\nAnalysis History ({len(final_session.state['analysis_history'])} entries):")
            for entry in final_session.state['analysis_history']:
                print(f"  • {entry['timestamp']}: {entry['type']} ({entry['status']})")
        
        print(f"\n🎉 Thank you for using the ADK Code Review System!")
        
    except Exception as e:
        print(f"❌ Error retrieving final session state: {e}")

def test_mode():
    """Run in test mode without ADK dependencies."""
    from utils import extract_code_from_input, validate_code_input, format_analysis_result
    
    print("🧪 Running in Test Mode (ADK components simulated)")
    print("="*60)
    
    # Test code extraction
    test_input = """
    Please review this Python code for quality issues:
    ```python
    def calculate_sum(a, b):
        return a + b
    
    class Calculator:
        def __init__(self):
            self.result = 0
        
        def add(self, x, y):
            self.result = x + y
            return self.result
    ```
    """
    
    print("Testing code extraction...")
    extracted = extract_code_from_input(test_input)
    print(f"✅ Extracted {extracted['language']} code:")
    print(f"   Length: {len(extracted['code'])} characters")
    print(f"   Analysis type: {extracted['analysis_type']}")
    
    # Test validation
    print("\nTesting code validation...")
    validation = validate_code_input(extracted['code'])
    print(f"✅ Validation result: {'Valid' if validation['valid'] else 'Invalid'}")
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"   ⚠️ {warning}")
    
    # Test result formatting
    print("\nTesting result formatting...")
    mock_result = {
        'status': 'success',
        'results': {
            'code_quality_issues': [
                {'message': 'Line too long', 'severity': 'low', 'line': 5},
                {'message': 'Missing docstring', 'severity': 'medium', 'line': 1}
            ],
            'complexity_metrics': {
                'cyclomatic_complexity': 3,
                'maintainability_index': 85.2
            }
        },
        'summary': {'total_issues': 2, 'medium_issues': 1, 'low_issues': 1},
        'execution_time_seconds': 0.15
    }
    
    formatted = format_analysis_result(mock_result)
    print("✅ Formatted result:")
    print(formatted)
    
    print("\n🎉 Test mode completed successfully!")

def main():
    """Entry point for the application."""
    # Check for different run modes
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'test':
            test_mode()
            return
        elif mode == 'api':
            # Start API server mode
            print("🌐 Starting ADK Code Review API Server...")
            import subprocess
            subprocess.run([
                sys.executable, "api_server.py"
            ])
            return
        elif mode == 'adk-web':
            # Start ADK Web UI mode
            print("🌐 Starting ADK Built-in Web UI...")
            import subprocess
            subprocess.run([
                sys.executable, "start_adk_web.py"
            ])
            return
        elif mode == 'hybrid':
            # Start both API server and background CLI
            print("🔄 Starting hybrid mode (API + Background CLI)...")
            import subprocess
            import threading
            
            def start_api():
                subprocess.run([sys.executable, "api_server.py"])
            
            # Start API server in background thread
            api_thread = threading.Thread(target=start_api, daemon=True)
            api_thread.start()
            
            print("✅ API server started in background")
            print("🖥️ Starting interactive CLI...")
            
            # Continue with CLI mode
            try:
                asyncio.run(main_async())
            except KeyboardInterrupt:
                print("\n\n👋 Hybrid mode terminated by user.")
            return
    
    # Default: Interactive CLI mode
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated by user.")
    except Exception as e:
        print(f"❌ Application error: {e}")
        print("\n💡 Available modes:")
        print("  • python main.py          - Interactive CLI (default)")
        print("  • python main.py api      - Web API server only") 
        print("  • python main.py adk-web  - ADK built-in Web UI")
        print("  • python main.py hybrid   - Both API + CLI")
        print("  • python main.py test     - Test utility functions")
        sys.exit(1)

if __name__ == "__main__":
    main()
