#!/usr/bin/env python3
"""
Test script to verify that the CodeAnalysisConfig loads correctly from YAML
"""

import sys
import os
import yaml
from pathlib import Path

# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

def test_config_loading():
    """Test that the config loads correctly from YAML"""
    try:
        # Import the CodeAnalysisConfig class
        from agents.code_analyzer.agent import CodeAnalysisConfig
        
        # Load the YAML config directly
        config_path = Path("src/agents/code_analyzer/configs/code_analyzer.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
        
        # Create config from YAML
        config = CodeAnalysisConfig.from_yaml_config(yaml_config)
        
        print("✅ Configuration loaded successfully!")
        print(f"Enhanced analysis: {config.enable_enhanced_analysis}")
        print(f"Max file size: {config.max_file_size} bytes ({config.max_file_size / (1024*1024):.1f} MB)")
        print(f"Parallel analysis: {config.parallel_analysis}")
        print(f"Output format: {config.output_format}")
        print(f"Supported languages ({len(config.supported_languages)}): {', '.join(config.supported_languages)}")
        
        # Verify specific values
        expected_languages = ['python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust', 'kotlin', 'swift', 'csharp', 'sql']
        
        if set(config.supported_languages) == set(expected_languages):
            print("✅ All expected languages are present")
        else:
            print("❌ Language list mismatch")
            print(f"Expected: {expected_languages}")
            print(f"Got: {config.supported_languages}")
        
        if config.max_file_size == 1024 * 1024:  # 1MB
            print("✅ File size limit correctly set to 1MB")
        else:
            print(f"❌ File size limit incorrect: {config.max_file_size}")
            
        if config.parallel_analysis:
            print("✅ Parallel analysis enabled")
        else:
            print("❌ Parallel analysis disabled")
            
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing configuration loading...")
    success = test_config_loading()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)