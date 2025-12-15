#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Workspace Build Script
Installs dependencies, validates code, and prepares workspace
"""
import os
import sys
import io
import subprocess
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


def run_command(cmd, description, check=True):
    """Run a command and report results"""
    print(f"\n{description}...")
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr and result.returncode != 0:
        print(f"⚠️  Errors/Warnings:\n{result.stderr}")
    
    success = result.returncode == 0
    
    if success:
        print(f"✅ {description} completed successfully")
    else:
        print(f"❌ {description} failed")
        if check:
            return False
    
    return success


def check_requirements_file():
    """Check if requirements.txt exists"""
    print_header("CHECKING REQUIREMENTS FILE")
    
    if Path('requirements.txt').exists():
        print("✅ requirements.txt found")
        print("\nContents:")
        with open('requirements.txt', 'r') as f:
            for line in f:
                if line.strip():
                    print(f"  - {line.strip()}")
        return True
    else:
        print("⚠️  requirements.txt not found")
        print("\nCreating default requirements.txt...")
        
        default_requirements = [
            "google-cloud-storage>=2.10.0",
            "google-cloud-bigquery>=3.11.0",
            "google-cloud-aiplatform>=1.35.0",
            "pandas>=2.0.0",
            "openpyxl>=3.1.0",
            "python-dotenv>=1.0.0",
        ]
        
        with open('requirements.txt', 'w') as f:
            f.write('\n'.join(default_requirements))
        
        print("✅ Created requirements.txt with default packages")
        return True


def install_dependencies():
    """Install Python dependencies"""
    print_header("STEP 1: INSTALLING DEPENDENCIES")
    
    if not check_requirements_file():
        return False
    
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python packages"
    )


def compile_workspace():
    """Compile all Python files"""
    print_header("STEP 2: COMPILING PYTHON FILES")
    
    return run_command(
        "python -m compileall .",
        "Compiling Python bytecode",
        check=False  # Non-critical
    )


def validate_workspace():
    """Run workspace validation"""
    print_header("STEP 3: VALIDATING WORKSPACE")
    
    if not Path('validate_workspace.py').exists():
        print("⚠️  validate_workspace.py not found, skipping validation")
        return True
    
    return run_command(
        "python validate_workspace.py",
        "Running workspace validation"
    )


def setup_directories():
    """Create necessary directories"""
    print_header("STEP 4: SETTING UP DIRECTORIES")
    
    directories = [
        'downloads',
        'normalized',
        '__pycache__',
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_name}/")
        else:
            print(f"ℹ️  Directory exists: {dir_name}/")
    
    return True


def check_env_file():
    """Check and guide .env file setup"""
    print_header("STEP 5: ENVIRONMENT CONFIGURATION")
    
    if Path('.env').exists():
        print("✅ .env file exists")
        print("\nCurrent configuration:")
        
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Mask sensitive values
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if any(secret in key.upper() for secret in ['KEY', 'SECRET', 'PASSWORD']):
                                print(f"  {key}=***")
                            else:
                                print(f"  {line}")
        except Exception as e:
            print(f"⚠️  Could not read .env file: {e}")
        
        return True
    else:
        print("[!] .env file not found")
        print("\nCreate .env file with the following variables:")
        print("  BQ_PROJECT_ID=your-project-id")
        print("  BQ_DATASET_ID=your-dataset-id")
        print("  GOOGLE_CLOUD_PROJECT=your-project-id")
        print("  GOOGLE_CLOUD_LOCATION=us-central1")
        print("  GOOGLE_API_KEY=your-api-key")
        print("\n[INFO] This is optional but recommended for production use")
        return True  # Not critical for build


def print_summary():
    """Print build summary and next steps"""
    print_header("BUILD SUCCESSFUL")
    
    print("Next steps:\n")
    print("[1] Configure your environment:")
    print("     • Set up .env file with GCP credentials")
    print("     • Authenticate: gcloud auth application-default login\n")
    
    print("[2] Run the application:")
    print("     python main.py\n")
    
    print("[3] Or run individual scripts:")
    print("     - Fetch data:     python fetch_data.py")
    print("     - Query BigQuery: python VertexAIQueryAgent.py \"your query\"\n")
    
    print("Documentation:")
    print("     • README.md")
    print("     • WORKFLOW_GUIDE.md")
    print("     • QUICKSTART.md\n")


def main():
    """Main build function"""
    print_header("BUILDING WORKSPACE")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}\n")
    
    steps = [
        (install_dependencies, "Dependencies"),
        (compile_workspace, "Compilation"),
        (validate_workspace, "Validation"),
        (setup_directories, "Directory Setup"),
        (check_env_file, "Environment"),
    ]
    
    results = {}
    
    for step_func, step_name in steps:
        try:
            results[step_name] = step_func()
            if not results[step_name] and step_name in ["Dependencies", "Validation"]:
                print(f"\n❌ Critical step failed: {step_name}")
                print("Build cannot continue. Please fix the errors above.")
                return False
        except Exception as e:
            print(f"\n❌ Error in {step_name}: {e}")
            import traceback
            traceback.print_exc()
            results[step_name] = False
            if step_name in ["Dependencies", "Validation"]:
                return False
    
    # Print results summary
    print_header("BUILD RESULTS")
    
    for step_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {step_name}: {status}")
    
    print()
    
    # Check if build was successful
    critical_steps = ["Dependencies", "Validation"]
    if all(results.get(step, False) for step in critical_steps):
        print_summary()
        return True
    else:
        print("[WARNING] Build completed with warnings")
        print("Some non-critical steps failed. Review the output above.")
        return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Build interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] Build failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
