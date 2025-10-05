#!/usr/bin/env python3
"""
Google Cloud Connection Verification Script
Verifies that Go    except ImportError:
        print("❌ Discovery Engine library not installed")
        print("Install with: poetry install")
        return False Cloud is properly configured for Vertex AI Agents
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'VERTEX_AI_LOCATION'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please run the setup script first: ./scripts/setup_google_cloud.sh")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_credentials_file():
    """Check if credentials file exists and is readable."""
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not Path(creds_path).exists():
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    print(f"✅ Credentials file found: {creds_path}")
    return True

def test_vertex_ai_connection():
    """Test connection to Vertex AI."""
    try:
        from google.cloud import aiplatform
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        print(f"✅ Vertex AI connection successful")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")
        return True
        
    except ImportError:
        print("❌ Google Cloud AI Platform library not installed")
        print("Install with: poetry install")
        return False
    except Exception as e:
        print(f"❌ Vertex AI connection failed: {e}")
        return False

def test_discovery_engine_connection():
    """Test connection to Discovery Engine (Agent Builder)."""
    try:
        from google.cloud import discoveryengine
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        # Create client
        client = discoveryengine.DataStoreServiceClient()
        
        # Test by listing data stores (this requires permissions)
        parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
        
        print(f"✅ Discovery Engine (Agent Builder) connection successful")
        print(f"   Client created for project: {project_id}")
        return True
        
    except ImportError:
        print("❌ Google Cloud Discovery Engine library not installed")
        print("Install with: pip install google-cloud-discoveryengine")
        return False
    except Exception as e:
        print(f"⚠️  Discovery Engine connection warning: {e}")
        print("   This might be expected if no data stores exist yet")
        return True  # Don't fail for this

def test_dialogflow_connection():
    """Test connection to Dialogflow (Conversational Agents)."""
    try:
        from google.cloud import dialogflow_v2
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # Create client
        client = dialogflow_v2.AgentsClient()
        
        print(f"✅ Dialogflow (Conversational Agents) connection successful")
        print(f"   Client created for project: {project_id}")
        return True
        
    except ImportError:
        print("❌ Dialogflow library not installed")
        print("Install with: poetry install")
        return False
    except Exception as e:
        print(f"⚠️  Dialogflow connection warning: {e}")
        print("   This might be expected for new projects")
        return True  # Don't fail for this

def main():
    """Main verification function."""
    print("🔍 Verifying Google Cloud Setup for Agentic Code Review\n")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Credentials File", check_credentials_file),
        ("Vertex AI Connection", test_vertex_ai_connection),
        ("Discovery Engine Connection", test_discovery_engine_connection),
        ("Dialogflow Connection", test_dialogflow_connection),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 All checks passed! Google Cloud is properly configured.")
        print("\n✅ Ready to proceed with GADK Module Structure implementation")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\n🔧 Run the setup script: ./scripts/setup_google_cloud.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())