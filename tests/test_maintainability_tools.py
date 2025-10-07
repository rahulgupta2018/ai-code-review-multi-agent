#!/usr/bin/env python3
"""
Test script to verify both maintainability tools work with new function names
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_function_imports():
    """Test that both tools can import their new function names"""
    print("🧪 Testing Function Imports")
    print("=" * 40)
    
    try:
        # Test scorer imports
        from agents.code_analyzer.tools.maintainability_scorer import (
            maintainability_scoring, 
            maintainability_scorer_tool,
            enhanced_maintainability_analysis  # backward compatibility
        )
        print("✅ Scorer functions imported successfully:")
        print("  - maintainability_scoring() ✓")
        print("  - maintainability_scorer_tool() ✓")
        print("  - enhanced_maintainability_analysis() ✓ (backward compatibility)")
        
    except ImportError as e:
        print(f"❌ Scorer import failed: {e}")
        return False
    
    try:
        # Test assessor imports
        from agents.code_analyzer.tools.maintainability_assessor import (
            maintainability_assessment,
            maintainability_assessor_tool,
            enhanced_maintainability_analysis as assessor_legacy  # backward compatibility
        )
        print("✅ Assessor functions imported successfully:")
        print("  - maintainability_assessment() ✓")
        print("  - maintainability_assessor_tool() ✓")
        print("  - enhanced_maintainability_analysis() ✓ (backward compatibility)")
        
    except ImportError as e:
        print(f"❌ Assessor import failed: {e}")
        return False
    
    print("\n🎉 All function imports successful!")
    return True

def test_function_signatures():
    """Test that functions have correct signatures"""
    print("\n🔍 Testing Function Signatures")
    print("=" * 40)
    
    from agents.code_analyzer.tools.maintainability_scorer import maintainability_scoring
    from agents.code_analyzer.tools.maintainability_assessor import maintainability_assessment
    
    import inspect
    
    # Check scorer signature
    scorer_sig = inspect.signature(maintainability_scoring)
    print(f"maintainability_scoring{scorer_sig}")
    
    # Check assessor signature  
    assessor_sig = inspect.signature(maintainability_assessment)
    print(f"maintainability_assessment{assessor_sig}")
    
    # Verify they're different (one takes files list, other takes file_path)
    scorer_params = list(scorer_sig.parameters.keys())
    assessor_params = list(assessor_sig.parameters.keys())
    
    if 'files' in scorer_params and 'file_path' in assessor_params:
        print("✅ Function signatures are correctly differentiated")
        print("  - Scorer takes 'files' (multi-file)")
        print("  - Assessor takes 'file_path' (single-file)")
        return True
    else:
        print("❌ Function signatures are not properly differentiated")
        return False

async def test_routing_logic():
    """Test that agent routing logic works"""
    print("\n🔀 Testing Routing Logic")
    print("=" * 40)
    
    try:
        from agents.code_analyzer.agent import CodeAnalyzerAgent
        
        agent = CodeAnalyzerAgent()
        
        # Test single file (should use assessor)
        single_file = [{"file_path": "test.py", "content": "print('hello')"}]
        should_assess = agent._should_use_detailed_assessment(single_file)
        
        # Test multiple files (should use scorer)
        multi_files = [
            {"file_path": "test1.py", "content": "print('hello')"},
            {"file_path": "test2.py", "content": "print('world')"}
        ]
        should_score = agent._should_use_detailed_assessment(multi_files)
        
        if should_assess and not should_score:
            print("✅ Routing logic works correctly:")
            print("  - Single file → Detailed Assessment ✓")
            print("  - Multiple files → Quantitative Scoring ✓")
            return True
        else:
            print(f"❌ Routing logic failed: single={should_assess}, multi={should_score}")
            return False
            
    except Exception as e:
        print(f"❌ Routing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Maintainability Tools Function Names Test")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_function_imports()
    
    # Test signatures
    success &= test_function_signatures()
    
    # Test routing
    success &= asyncio.run(test_routing_logic())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Summary:")
        print("  - Function names updated successfully")
        print("  - No naming conflicts between tools")
        print("  - Intelligent routing logic implemented")
        print("  - Backward compatibility maintained")
    else:
        print("❌ SOME TESTS FAILED!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)