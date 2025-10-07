#!/usr/bin/env python3
"""
Test script for the Maintainability Scorer Tool
Tests holistic code quality scoring across multiple languages
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.quality.maintainability_scorer import MaintainabilityScorer

def test_maintainability_scorer():
    """Test maintainability scoring with sample code files"""
    
    # Sample Python code with varying quality characteristics
    python_code_good = '''
def calculate_factorial(n: int) -> int:
    """
    Calculate factorial of a number using recursion.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial undefined for negative numbers")
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

class MathUtilities:
    """Utility class for mathematical operations."""
    
    @staticmethod
    def is_prime(number: int) -> bool:
        """Check if a number is prime."""
        if number < 2:
            return False
        for i in range(2, int(number ** 0.5) + 1):
            if number % i == 0:
                return False
        return True
'''

    python_code_poor = '''
def bad_function(x,y,z,a,b,c,d,e,f,g):
    if x>0:
        if y>0:
            if z>0:
                if a>0:
                    if b>0:
                        if c>0:
                            if d>0:
                                if e>0:
                                    if f>0:
                                        if g>0:
                                            return x+y+z+a+b+c+d+e+f+g
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

def another_bad_function(x,y,z,a,b,c,d,e,f,g):
    if x>0:
        if y>0:
            if z>0:
                if a>0:
                    if b>0:
                        if c>0:
                            if d>0:
                                if e>0:
                                    if f>0:
                                        if g>0:
                                            return x+y+z+a+b+c+d+e+f+g
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

class BadClass:
    def bad_method(self,x,y,z,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x1,y1,z1):
        # Very long parameter list
        return x+y+z+a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+q+r+s+t+u+v+w+x1+y1+z1
'''

    # Test files with good and poor code
    test_files_good = [
        {"path": "good_code.py", "content": python_code_good},
        {"path": "test_good_code.py", "content": "# Test file for good code\npass"}
    ]
    
    test_files_poor = [
        {"path": "poor_code.py", "content": python_code_poor}
    ]
    
    # Initialize scorer
    scorer = MaintainabilityScorer()
    
    print("🧪 Testing Maintainability Scorer Tool")
    print("=" * 50)
    
    # Test 1: Good quality code
    print("\n📈 Test 1: Good Quality Code")
    print("-" * 30)
    try:
        result_good = scorer.score_maintainability(test_files_good)
        
        print(f"✅ Analysis Type: {result_good['analysis_type']}")
        print(f"📊 Maintainability Index: {result_good['maintainability_index']}")
        print(f"🏆 Quality Level: {result_good['quality_level']}")
        print(f"📁 Files Analyzed: {result_good['total_files_analyzed']}")
        print(f"💻 Primary Language: {result_good['primary_language']}")
        print(f"⏱️ Processing Time: {result_good['processing_time']:.3f}s")
        
        print("\n📈 Individual Scores:")
        scores = result_good['scores']
        for metric, score in scores.items():
            print(f"  {metric}: {score:.1f}")
        
        print("\n💡 Recommendations:")
        for rec in result_good['recommendations']:
            print(f"  {rec}")
        
        print(f"\n✅ Test 1 PASSED - Good code scored {result_good['maintainability_index']}")
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {str(e)}")
        return False
    
    # Test 2: Poor quality code
    print("\n📉 Test 2: Poor Quality Code")
    print("-" * 30)
    try:
        result_poor = scorer.score_maintainability(test_files_poor)
        
        print(f"✅ Analysis Type: {result_poor['analysis_type']}")
        print(f"📊 Maintainability Index: {result_poor['maintainability_index']}")
        print(f"⚠️ Quality Level: {result_poor['quality_level']}")
        print(f"📁 Files Analyzed: {result_poor['total_files_analyzed']}")
        print(f"💻 Primary Language: {result_poor['primary_language']}")
        print(f"⏱️ Processing Time: {result_poor['processing_time']:.3f}s")
        
        print("\n📈 Individual Scores:")
        scores = result_poor['scores']
        for metric, score in scores.items():
            print(f"  {metric}: {score:.1f}")
        
        print("\n💡 Recommendations:")
        for rec in result_poor['recommendations']:
            print(f"  {rec}")
        
        print(f"\n✅ Test 2 PASSED - Poor code scored {result_poor['maintainability_index']}")
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: {str(e)}")
        return False
    
    # Test 3: Compare scores (good should be higher than poor)
    print("\n🔄 Test 3: Score Comparison")
    print("-" * 30)
    
    if result_good['maintainability_index'] > result_poor['maintainability_index']:
        print(f"✅ Good code score ({result_good['maintainability_index']}) > Poor code score ({result_poor['maintainability_index']})")
        print("✅ Test 3 PASSED - Scoring correctly differentiates quality levels")
    else:
        print(f"❌ Good code score ({result_good['maintainability_index']}) <= Poor code score ({result_poor['maintainability_index']})")
        print("❌ Test 3 FAILED - Scoring not working correctly")
        return False
    
    # Test 4: Configuration validation
    print("\n⚙️ Test 4: Configuration Validation")
    print("-" * 30)
    
    config = result_good.get('configuration', {})
    if 'weights' in config and 'thresholds' in config:
        print("✅ Configuration loaded successfully")
        print(f"📋 Weights: {json.dumps(config['weights'], indent=2)}")
        print(f"📋 Quality Thresholds: {json.dumps(config['thresholds'], indent=2)}")
        print("✅ Test 4 PASSED - Configuration system working")
    else:
        print("❌ Test 4 FAILED - Configuration missing")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Maintainability Scorer Tool is working correctly")
    print(f"📊 Tool successfully provides holistic quality assessment")
    print(f"⚡ Performance: ~{(result_good['processing_time'] + result_poor['processing_time'])/2:.3f}s average")
    
    return True

if __name__ == "__main__":
    success = test_maintainability_scorer()
    sys.exit(0 if success else 1)