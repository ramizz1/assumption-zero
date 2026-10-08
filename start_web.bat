@echo off
setlocal enabledelayedexpansion

title Assumption Zero - Web Launcher
color 0B

echo.
echo  ==============================================================
echo  =      ASSUMPTION ZERO - Web App Launcher                   =
echo  =      Stress-test your MVP before you build it             =
echo  ==============================================================
echo.

:: -- Locate project root (directory of this script) --------------------------
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV=%BACKEND%\.venv"

:: -- Check Python -------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.12+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: -- Check Node.js ------------------------------------------------------------
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo         Install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: -- Setup backend venv if missing --------------------------------------------
if not exist "%VENV%\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Installing backend dependencies...
    "%VENV%\Scripts\pip.exe" install -e "%BACKEND%[dev]" --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
    echo [INFO] Backend dependencies installed successfully.
) else (
    echo [INFO] Backend virtual environment found.
)

:: -- Install frontend dependencies if missing ---------------------------------
if not exist "%FRONTEND%\node_modules" (
    echo [INFO] Installing frontend dependencies - npm install...
    pushd "%FRONTEND%"
    npm install
    if errorlevel 1 (
        popd
        echo [ERROR] npm install failed. Make sure Node.js is installed.
        pause
        exit /b 1
    )
    popd
    echo [INFO] Frontend dependencies installed.
) else (
    echo [INFO] Frontend node_modules found.
)

:: -- Create data directory ----------------------------------------------------
if not exist "%ROOT%azero_data" mkdir "%ROOT%azero_data"
if not exist "%ROOT%azero_data\analyses" mkdir "%ROOT%azero_data\analyses"

:: -- Determine free ports -----------------------------------------------------
if "%AZERO_BACKEND_PORT%"=="" (
    for /f "tokens=*" %%p in ('"%VENV%\Scripts\python.exe" -c "import socket; print(next(p for p in range(8010, 8040) if socket.socket().connect_ex(('127.0.0.1', p)) != 0))" 2^>nul') do set "AZERO_BACKEND_PORT=%%p"
)
if "%AZERO_BACKEND_PORT%"=="" set "AZERO_BACKEND_PORT=8010"

set "FRONTEND_PORT="
for /f "tokens=*" %%p in ('"%VENV%\Scripts\python.exe" -c "import socket; print(next(p for p in range(5173, 5200) if socket.socket().connect_ex(('127.0.0.1', p)) != 0))" 2^>nul') do set "FRONTEND_PORT=%%p"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5173"

:: -- Write helper scripts for new cmd windows ---------------------------------
set "BACKEND_SCRIPT=%TEMP%\azero_backend_start.bat"
set "FRONTEND_SCRIPT=%TEMP%\azero_frontend_start.bat"

(
echo @echo off
echo title Assumption Zero - Backend API
echo cd /d %BACKEND%
echo %VENV%\Scripts\uvicorn.exe assumption_zero.main:app --host 0.0.0.0 --port %AZERO_BACKEND_PORT% --reload
echo pause
) > "%BACKEND_SCRIPT%"

(
echo @echo off
echo title Assumption Zero - Frontend
echo cd /d %FRONTEND%
echo set "VITE_API_PROXY_TARGET=http://127.0.0.1:%AZERO_BACKEND_PORT%"
echo npm run dev -- --port %FRONTEND_PORT% --strictPort
echo pause
) > "%FRONTEND_SCRIPT%"

:: -- Start Backend in new window ----------------------------------------------
echo.
echo [INFO] Starting backend API on http://localhost:%AZERO_BACKEND_PORT% ...
start "Assumption Zero - Backend" cmd /k "%BACKEND_SCRIPT%"

:: -- Give backend a moment to boot --------------------------------------------
timeout /t 2 /nobreak >nul

:: -- Start Frontend in new window ---------------------------------------------
echo [INFO] Starting frontend on http://localhost:%FRONTEND_PORT% ...
start "Assumption Zero - Frontend" cmd /k "%FRONTEND_SCRIPT%"

:: -- Give Vite a moment to compile --------------------------------------------
timeout /t 4 /nobreak >nul

:: -- Open browser -------------------------------------------------------------
echo [INFO] Opening browser at http://localhost:%FRONTEND_PORT% ...
start "" "http://localhost:%FRONTEND_PORT%"

echo.
echo  ==============================================================
echo  =  DONE - Assumption Zero is running!                       =
echo  =                                                           =
echo  =  Frontend:  http://localhost:%FRONTEND_PORT%                         =
echo  =  Backend:   http://localhost:%AZERO_BACKEND_PORT%                         =
echo  =  API Docs:  http://localhost:%AZERO_BACKEND_PORT%/docs                    =
echo  =                                                           =
echo  =  Close the Backend/Frontend windows to stop the app.     =
echo  ==============================================================
echo.
pause
