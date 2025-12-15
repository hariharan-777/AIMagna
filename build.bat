@echo off
REM Windows Batch Script for Building Workspace

echo.
echo ======================================================================
echo   BUILDING PYTHON WORKSPACE
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Run the Python build script
python build.py

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo   BUILD COMPLETED SUCCESSFULLY
    echo ======================================================================
    echo.
    echo You can now run: python main.py
    echo.
) else (
    echo.
    echo ======================================================================
    echo   BUILD FAILED
    echo ======================================================================
    echo.
    echo Please review the errors above and try again.
    echo.
)

exit /b %errorlevel%
