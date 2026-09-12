@echo off
setlocal
title Dat lai mat khau - Cong thong tin Lu doan 21
chcp 65001 >nul

cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo [LOI] Khong tim thay moi truong Python venv tai backend\venv.
    echo.
    pause
    exit /b 1
)

echo ============================================================
echo   CONG CU DAT LAI MAT KHAU - LU DOAN THONG TIN 21
echo ============================================================
echo.
echo Danh sach tai khoan hien co trong he thong:
echo.

venv\Scripts\python.exe scripts\check_login.py

echo.
echo ============================================================
echo   NHAP THONG TIN TAI KHOAN CAN DAT LAI MAT KHAU
echo ============================================================
echo.

set /p USERNAME="-> Nhap Ten dang nhap (username): "
if "%USERNAME%"=="" (
    echo [!] Ban chua nhap ten dang nhap. Thoat.
    pause
    exit /b 0
)

set /p NEWPASS="-> Nhap Mat khau moi: "
if "%NEWPASS%"=="" (
    echo [!] Ban chua nhap mat khau moi. Thoat.
    pause
    exit /b 0
)

echo.
echo Dang cap nhat mat khau...
venv\Scripts\python.exe scripts\check_login.py --user "%USERNAME%" --set-password "%NEWPASS%"

echo.
echo ============================================================
echo   HOAN TAT!
echo   Ban co the dang nhap ngay bang tai khoan va mat khau vua dat.
echo ============================================================
echo.
pause
