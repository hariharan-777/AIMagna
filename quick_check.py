#!/usr/bin/env python3
"""
Quick Workspace Check
Fast syntax and import validation
"""
import sys
import py_compile
from pathlib import Path


def quick_check():
    """Quick syntax and import check"""
    print("🔍 Quick Workspace Check\n")
    
    # Get Python files
    py_files = [f for f in Path('.').glob('*.py') if f.name not in ['quick_check.py', 'build.py', 'validate_workspace.py']]
    
    errors = []
    
    # Syntax check
    print("Checking syntax...", end=" ")
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Syntax error in {py_file.name}")
    
    if not errors:
        print("✅")
    else:
        print("❌")
        for error in errors:
            print(f"  {error}")
        return False
    
    # Import check
    print("Checking imports...", end=" ")
    modules = ['fetch_data', 'LocalNormalizerAgent', 'BigQueryAgent', 'VertexAIQueryAgent', 'SchemaAnalyzerAgent', 'adk']
    
    for module in modules:
        try:
            __import__(module)
        except Exception as e:
            errors.append(f"Import error: {module} - {e}")
    
    if not errors:
        print("✅")
    else:
        print("❌")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("\n✅ All checks passed! Workspace is ready.\n")
    return True


if __name__ == "__main__":
    try:
        success = quick_check()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Check failed: {e}")
        sys.exit(1)
