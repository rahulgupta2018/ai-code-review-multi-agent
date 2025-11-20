"""
Quick test to verify FileArtifactService basic functionality
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from util.artifact_service import FileArtifactService
from google.genai import types


async def test_artifact_service():
    print("🧪 Testing FileArtifactService...")
    
    # Create service with test directory
    service = FileArtifactService(base_dir="./test_artifacts")
    print(f"✅ Created service with base_dir: {service.base_dir}")
    
    # Test data
    app_name = "Test_App"
    user_id = "test_user_123"
    
    # Test 1: Save code input
    print("\n📝 Test 1: Save code input artifact...")
    code_content = """def hello_world():
    print("Hello, World!")
    return True
"""
    filename = "code_input_test_001.py"
    version = await service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        filename=filename,
        artifact=types.Part(text=code_content),
        session_id="session_123",
        custom_metadata={"language": "python", "lines": 3}
    )
    print(f"✅ Saved code artifact, version: {version}")
    
    # Test 2: Load code input
    print("\n📖 Test 2: Load code input artifact...")
    loaded = await service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        filename=filename
    )
    if loaded and loaded.text:
        print(f"✅ Loaded artifact ({len(loaded.text)} chars)")
        print(f"   Content preview: {loaded.text[:50]}...")
    else:
        print("❌ Failed to load artifact")
    
    # Test 3: Save report
    print("\n📊 Test 3: Save report artifact...")
    report_content = """# Code Review Report

**Analysis ID:** test_001
**Date:** 2025-11-18

## Summary
- Code quality: Good
- Issues found: 0
"""
    report_filename = "report_test_001.md"
    await service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        filename=report_filename,
        artifact=types.Part(text=report_content),
        custom_metadata={"analysis_id": "test_001", "issues_count": 0}
    )
    print(f"✅ Saved report artifact")
    
    # Test 4: List all artifacts
    print("\n📋 Test 4: List all artifacts...")
    artifacts = await service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id
    )
    print(f"✅ Found {len(artifacts)} artifacts:")
    for artifact in artifacts:
        print(f"   - {artifact}")
    
    # Test 5: Get metadata
    print("\n🔍 Test 5: Get artifact metadata...")
    metadata = service.get_artifact_metadata(app_name, user_id, filename)
    if metadata:
        print(f"✅ Retrieved metadata:")
        print(f"   - Created: {metadata.get('created_at', 'unknown')}")
        print(f"   - Size: {metadata.get('size_bytes', 0)} bytes")
        print(f"   - Language: {metadata.get('custom', {}).get('language', 'unknown')}")
    else:
        print("❌ No metadata found")
    
    # Test 6: List versions
    print("\n📦 Test 6: List artifact versions...")
    versions = await service.list_artifact_versions(
        app_name=app_name,
        user_id=user_id,
        filename=filename
    )
    print(f"✅ Found {len(versions)} versions:")
    for v in versions:
        print(f"   - Version {v.version}: {v.canonical_uri}")
    
    # Test 7: Directory structure
    print("\n📁 Test 7: Verify directory structure...")
    user_dir = service.base_dir / app_name / user_id
    subdirs = ["inputs", "reports", "sub_agent_outputs"]
    for subdir in subdirs:
        path = user_dir / subdir
        if path.exists():
            file_count = len(list(path.glob("*")))
            print(f"✅ {subdir}/ exists ({file_count} files)")
        else:
            print(f"⚠️  {subdir}/ not created (no files yet)")
    
    print("\n✅ All tests passed!")
    print(f"\n🗑️  Test artifacts stored in: {service.base_dir}")
    print("   You can manually inspect the directory structure.")


if __name__ == "__main__":
    asyncio.run(test_artifact_service())
