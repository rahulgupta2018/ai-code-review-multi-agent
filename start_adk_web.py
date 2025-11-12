#!/usr/bin/env python3
"""
ADK Web Interface Startup Script
Launches the built-in ADK web UI for interactive agent testing
"""

import os
import sys
import subprocess

def main():
    """Start the ADK web interface."""
    print("🌐 Starting ADK Web Interface...")
    print("📁 Agent Directory: /app")
    print("🔗 Web UI will be available at: http://localhost:8200")
    print("")
    
    # Change to the app directory
    os.chdir('/app')
    
    # Start ADK web interface
    # The current directory contains our code_review_orchestrator agent
    cmd = [
        'adk', 'web',
        '--host', '0.0.0.0',
        '--port', '8200',
        '--verbose',
        '--reload',
        '.'  # Current directory contains our agent
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("⏳ Starting ADK Web UI...")
    print("")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 ADK Web UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start ADK Web UI: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()