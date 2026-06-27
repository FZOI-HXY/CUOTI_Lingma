@echo off
chcp 65001 >nul 2>&1
setlocal

set "VENV_PYTHON=F:\CUOTI_Lingma\venv312\Scripts\python.exe"

echo ============================================================
echo   Installing PyMuPDF into venv312
echo ============================================================
echo.

echo [1/2] Installing PyMuPDF...
"%VENV_PYTHON%" -m pip install "PyMuPDF>=1.24.0"
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
echo.

echo [2/2] Verifying import...
"%VENV_PYTHON%" -c "import fitz; print('PyMuPDF version:', fitz.__version__)"
if %errorlevel% neq 0 (
    echo [ERROR] import fitz failed
    pause
    exit /b 1
)

echo.
echo [OK] PyMuPDF installed and verified
echo ============================================================
pause
