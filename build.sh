#!/bin/bash
# Unix/Linux/Mac Build Script for Workspace

set -e

echo ""
echo "======================================================================"
echo "  BUILDING PYTHON WORKSPACE"
echo "======================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Run the Python build script
python3 build.py

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "  BUILD COMPLETED SUCCESSFULLY"
    echo "======================================================================"
    echo ""
    echo "You can now run: python3 main.py"
    echo ""
else
    echo ""
    echo "======================================================================"
    echo "  BUILD FAILED"
    echo "======================================================================"
    echo ""
    echo "Please review the errors above and try again."
    echo ""
    exit 1
fi
