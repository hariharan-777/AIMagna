# Build & Compilation Guide

This document explains how to build and validate the workspace.

## 🚀 Quick Start

### Windows
```bash
build.bat
```

### Linux/Mac
```bash
chmod +x build.sh
./build.sh
```

### Cross-Platform (Python)
```bash
python build.py
```

## 📋 Build Scripts Overview

### 1. `build.py` - Full Build Script
**Purpose:** Complete workspace build with all validations

**What it does:**
- ✅ Installs all Python dependencies from `requirements.txt`
- ✅ Compiles Python files to bytecode
- ✅ Validates syntax and imports
- ✅ Creates necessary directories
- ✅ Checks environment configuration

**Usage:**
```bash
python build.py
```

### 2. `validate_workspace.py` - Validation Script
**Purpose:** Comprehensive workspace validation

**What it checks:**
- ✅ Python syntax in all `.py` files
- ✅ Module imports and dependencies
- ✅ Python version compatibility (3.8+)
- ✅ Required packages installation
- ✅ Environment configuration

**Usage:**
```bash
python validate_workspace.py
```

### 3. `quick_check.py` - Fast Check
**Purpose:** Quick syntax and import validation (< 5 seconds)

**What it checks:**
- ✅ Syntax errors in Python files
- ✅ Basic import functionality

**Usage:**
```bash
python quick_check.py
```

## 📦 Build Process

The build process follows these steps:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Installs:
- `google-cloud-storage` - GCS operations
- `google-cloud-bigquery` - BigQuery operations  
- `google-cloud-aiplatform` - Vertex AI integration
- `pandas` - Data processing
- `openpyxl` - Excel file support
- `python-dotenv` - Environment variables

### Step 2: Compile Python Files
```bash
python -m compileall .
```

Generates `.pyc` bytecode files for:
- Faster module loading
- Syntax validation
- Distribution preparation

### Step 3: Validate Workspace
```bash
python validate_workspace.py
```

Runs comprehensive checks on:
- All Python source files
- Module dependencies
- Environment setup

### Step 4: Setup Directories
Creates required directories:
- `downloads/` - Downloaded source data
- `normalized/` - Processed CSV files
- `__pycache__/` - Python bytecode cache

### Step 5: Environment Check
Verifies:
- `.env` file exists (optional)
- GCP credentials configured
- Required environment variables set

## 🔧 Manual Build Steps

If automated scripts fail, follow these manual steps:

### 1. Check Python Version
```bash
python --version
# Should be 3.8 or higher
```

### 2. Install Dependencies
```bash
pip install google-cloud-storage google-cloud-bigquery google-cloud-aiplatform pandas openpyxl python-dotenv
```

### 3. Syntax Validation
```bash
# Validate individual files
python -m py_compile main.py
python -m py_compile fetch_data.py
python -m py_compile LocalNormalizerAgent.py
python -m py_compile BigQueryAgent.py
python -m py_compile VertexAIQueryAgent.py
```

### 4. Import Testing
```bash
python -c "import fetch_data; import LocalNormalizerAgent; import BigQueryAgent; print('✅ Imports OK')"
```

### 5. Create Directories
```bash
mkdir downloads
mkdir normalized
```

## 🐛 Troubleshooting

### Build Fails: "Module not found"
**Solution:** Install missing dependencies
```bash
pip install -r requirements.txt
```

### Build Fails: "Syntax Error"
**Solution:** Check Python file for errors
```bash
python -m py_compile <filename>.py
```

### Build Fails: "Permission Denied"
**Solution:** 
- Windows: Run as Administrator
- Linux/Mac: Use `chmod +x build.sh`

### Import Errors
**Solution:** Ensure all files are in the same directory
```bash
python -c "import sys; print(sys.path)"
```

## ✅ Verification

After successful build, verify with:

```bash
# Quick check
python quick_check.py

# Full validation
python validate_workspace.py

# Run application
python main.py
```

## 📊 Expected Output

### Successful Build:
```
======================================================================
  🎉 BUILD SUCCESSFUL
======================================================================

Next steps:

1️⃣  Configure your environment:
     • Set up .env file with GCP credentials
     • Authenticate: gcloud auth application-default login

2️⃣  Run the application:
     python main.py
```

### Failed Build:
```
❌ BUILD FAILED

Dependencies: ✅ PASSED
Compilation: ✅ PASSED  
Validation: ❌ FAILED

Please fix the issues above before running the application
```

## 🔄 CI/CD Integration

For automated builds in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Build Workspace
  run: |
    python build.py
    if [ $? -ne 0 ]; then exit 1; fi
```

## 📝 Notes

- Build scripts create bytecode (`.pyc`) files - these are safe to commit to `.gitignore`
- Validation runs automatically during build
- Environment setup is optional but recommended
- All scripts support both Windows and Unix systems

## 🆘 Support

If build issues persist:
1. Check Python version: `python --version`
2. Verify pip installation: `pip --version`
3. Update pip: `python -m pip install --upgrade pip`
4. Clear cache: Delete `__pycache__/` directories
5. Reinstall dependencies: `pip install --force-reinstall -r requirements.txt`
