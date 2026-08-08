@echo off
title Build Assumption Zero Installer
color 0B

echo.
echo  Building Assumption Zero Windows Installer...
echo  Requires: Inno Setup 6+  (https://jrsoftware.org/isinfo.php)
echo.

:: Try default Inno Setup installation paths
set "ISCC="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

:: Try Chocolatey path
if exist "C:\ProgramData\chocolatey\bin\iscc.exe" (
    set "ISCC=C:\ProgramData\chocolatey\bin\iscc.exe"
)

if "%ISCC%"=="" (
    echo [ERROR] Inno Setup 6 not found. Please install it from:
    echo         https://jrsoftware.org/isdl.php
    echo.
    echo You can also install via Chocolatey:
    echo   choco install innosetup
    echo.
    pause
    exit /b 1
)

echo [INFO] Using Inno Setup compiler: %ISCC%
echo.

:: Create output directory
if not exist "%~dp0dist" mkdir "%~dp0dist"

:: Compile the installer
"%ISCC%" "%~dp0setup_assumption_zero.iss"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  SUCCESS! Installer built in:
echo  %~dp0dist\
echo ====================================================
echo.
explorer "%~dp0dist"
pause
