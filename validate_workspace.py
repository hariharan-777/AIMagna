#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace Validation Script
Validates all Python files for syntax errors and import issues
"""
import os
import sys
import io
import py_compile
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def validate_syntax():
    """Compile and validate all Python files for syntax errors"""
    print_header("STEP 1: SYNTAX VALIDATION")
    
    # Get all Python files (excluding __pycache__ and .venv)
    py_files = [
        f for f in Path('.').glob('*.py') 
        if f.name != 'validate_workspace.py' and f.name != 'build.py'
    ]
    
    if not py_files:
        print("⚠️  No Python files found in workspace")
        return False
    
    errors = []
    success = 0
    
    for py_file in sorted(py_files):
        try:
            print(f"  Compiling {py_file.name}...", end=" ")
            py_compile.compile(str(py_file), doraise=True)
            print("✅")
            success += 1
        except py_compile.PyCompileError as e:
            print("❌")
            errors.append((py_file.name, str(e)))
    
    print(f"\n  Results: {success}/{len(py_files)} files compiled successfully")
    
    if errors:
        print(f"\n  ⚠️  SYNTAX ERRORS FOUND:\n")
        for filename, error in errors:
            print(f"    {filename}:")
            print(f"      {error}\n")
        return False
    
    return True


def validate_imports():
    """Test that all module imports work"""
    print_header("STEP 2: IMPORT VALIDATION")
    
    modules = [
        ('fetch_data', 'GoogleCloudStorageAgent'),
        ('LocalNormalizerAgent', 'LocalNormalizerAgent'),
        ('BigQueryAgent', 'BigQueryAgent'),
        ('VertexAIQueryAgent', 'VertexAIQueryAgent'),
        ('SchemaAnalyzerAgent', 'SchemaAnalyzerAgent'),
        ('adk', 'AgentInput'),
    ]
    
    errors = []
    success = 0
    
    for module_name, class_name in modules:
        try:
            print(f"  Importing {module_name}.{class_name}...", end=" ")
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print("✅")
            success += 1
        except ImportError as e:
            print("❌")
            errors.append((module_name, f"Import error: {e}"))
        except AttributeError as e:
            print("⚠️")
            errors.append((module_name, f"Class not found: {e}"))
        except Exception as e:
            print("❌")
            errors.append((module_name, f"Unexpected error: {e}"))
    
    print(f"\n  Results: {success}/{len(modules)} imports successful")
    
    if errors:
        print(f"\n  ⚠️  IMPORT ERRORS FOUND:\n")
        for module, error in errors:
            print(f"    {module}:")
            print(f"      {error}\n")
        return False
    
    return True


def check_environment():
    """Check if environment is properly configured"""
    print_header("STEP 3: ENVIRONMENT CHECK")
    
    checks = []
    
    # Check .env file
    if os.path.exists('.env'):
        print("  ✅ .env file exists")
        checks.append(True)
    else:
        print("  ⚠️  .env file not found (optional but recommended)")
        checks.append(True)  # Not critical
    
    # Check required directories
    dirs_to_check = ['normalized']
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ directory exists")
        else:
            print(f"  ℹ️  {dir_name}/ directory will be created on first run")
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 8:
        print(f"  ✅ Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
        checks.append(True)
    else:
        print(f"  ⚠️  Python version: {py_version.major}.{py_version.minor}.{py_version.micro} (3.8+ recommended)")
        checks.append(False)
    
    return all(checks)


def check_dependencies():
    """Check if required packages are installed"""
    print_header("STEP 4: DEPENDENCY CHECK")
    
    required_packages = [
        'google.cloud.storage',
        'google.cloud.bigquery',
        'google.cloud.aiplatform',
        'pandas',
        'openpyxl',
        'dotenv',
    ]
    
    errors = []
    success = 0
    
    for package in required_packages:
        try:
            print(f"  Checking {package}...", end=" ")
            __import__(package)
            print("✅")
            success += 1
        except ImportError:
            print("❌")
            errors.append(package)
    
    print(f"\n  Results: {success}/{len(required_packages)} packages installed")
    
    if errors:
        print(f"\n  ⚠️  MISSING PACKAGES:\n")
        for package in errors:
            print(f"    - {package}")
        print(f"\n  Install missing packages with:")
        print(f"    pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main validation function"""
    print_header("WORKSPACE VALIDATION")
    print(f"Working Directory: {os.getcwd()}\n")
    
    results = {
        'syntax': validate_syntax(),
        'imports': validate_imports(),
        'environment': check_environment(),
        'dependencies': check_dependencies(),
    }
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    all_passed = all(results.values())
    
    for step, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {step.upper()}: {status}")
    
    print()
    
    if all_passed:
        print("  *** ALL VALIDATION CHECKS PASSED! ***")
        print("  [OK] Workspace is ready to run")
        print(f"\n  Run the application:")
        print(f"    python main.py")
        return True
    else:
        print("  [WARNING] SOME VALIDATION CHECKS FAILED")
        print("  Please fix the issues above before running the application")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
