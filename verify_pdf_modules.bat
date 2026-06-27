@echo off
chcp 65001 >nul 2>&1
setlocal

set "VENV_PYTHON=F:\CUOTI_Lingma\venv312\Scripts\python.exe"
set "BACKEND_DIR=F:\CUOTI_Lingma\backend"

echo ============================================================
echo   Verifying PDF module imports (fixed)
echo ============================================================
echo.

echo [1/3] Testing pdf_service import...
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, r'%BACKEND_DIR%'); from app.services.pdf_service import pdf_service; print('  OK: pdf_service singleton'); print('  has render_pages_to_images:', hasattr(pdf_service, 'render_pages_to_images'))"
if %errorlevel% neq 0 (
    echo [ERROR] pdf_service import failed
    pause
    exit /b 1
)

echo [2/3] Testing pdf router import...
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, r'%BACKEND_DIR%'); from app.routers.pdf import router; print('  OK: pdf router, routes:', len(router.routes))"
if %errorlevel% neq 0 (
    echo [ERROR] pdf router import failed
    pause
    exit /b 1
)

echo [3/3] Testing validators (PDF functions)...
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, r'%BACKEND_DIR%'); from app.utils.validators import validate_pdf_type, validate_pdf_magic_bytes, is_pdf_file; print('  OK: validators'); print('  test.pdf:', validate_pdf_type('test.pdf')); print('  test.jpg:', validate_pdf_type('test.jpg'))"
if %errorlevel% neq 0 (
    echo [ERROR] validators import failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   All PDF module imports verified successfully!
echo ============================================================
pause
