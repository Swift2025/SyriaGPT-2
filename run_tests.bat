@echo off
echo Starting SyriaGPT API Endpoint Testing...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Install requirements if needed
echo Installing test requirements...
pip install -r test_requirements.txt

REM Run the simple test suite
echo.
echo Running API endpoint tests...
echo.
python run_tests_simple.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ❌ Some tests failed. Check the output above for details.
) else (
    echo.
    echo ✅ All tests passed successfully!
)

echo.
echo Press any key to exit...
pause >nul
