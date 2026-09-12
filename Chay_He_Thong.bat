@echo off
setlocal
title Cong thong tin noi bo Lu doan Thong tin 21 - May chu san xuat
chcp 65001 >nul

cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo [LOI] Khong tim thay moi truong ao Python tai backend\venv
    echo Hay cai dat lan dau truoc khi chay file nay:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [LOI] Khong tim thay backend\.env - can tao file cau hinh CSDL/mat khau truoc.
    echo Xem huong dan trong trang "Huong dan su dung" cua he thong.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

set "FE_DIST=..\fe-ludoan\dist\index.html"
if not exist "%FE_DIST%" set "FE_DIST=..\frontend\dist\index.html"
if not exist "%FE_DIST%" (
    echo [CANH BAO] Chua tim thay ban build giao dien tai fe-ludoan\dist
    echo He thong van chay duoc o che do API ^(/docs^) nhung se khong hien
    echo giao dien nguoi dung. De build giao dien, chay:
    echo   cd fe-ludoan ^&^& npm install ^&^& npm run build
    echo.
)

echo ============================================================
echo   CONG THONG TIN NOI BO LU DOAN THONG TIN 21 - BO DOI BIEN PHONG
echo   May chu san xuat dang khoi dong tren cong 8000...
echo.
echo   - Tai chinh may nay      : http://localhost:8000
echo   - Tai may khac trong LAN : http://^<IP may chu nay^>:8000
echo     ^(xem IP may chu bang lenh "ipconfig", muc IPv4 Address^)
echo.
echo   DONG cua so nay ^(hoac bam Ctrl+C^) de DUNG may chu.
echo ============================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo May chu da dung.
pause
