@echo off
setlocal enabledelayedexpansion
title AugmentCode Unlimited - Main Menu

:menu
cls
echo.
echo ========================================
echo   AugmentCode Unlimited - Main Menu
echo ========================================
echo.
echo   [1] Launch GUI
echo   [2] Quick Rotation
echo   [3] Check Status
echo   [4] Service Management
echo   [5] View Rotation History
echo   [6] API Dashboard
echo   [7] Configuration
echo   [0] Exit
echo.
echo ========================================
set /p choice="Enter your choice: "

if "%choice%"=="1" goto launch_gui
if "%choice%"=="2" goto quick_rotation
if "%choice%"=="3" goto check_status
if "%choice%"=="4" goto service_menu
if "%choice%"=="5" goto view_history
if "%choice%"=="6" goto api_dashboard
if "%choice%"=="7" goto configuration
if "%choice%"=="0" goto exit
goto invalid_choice

:launch_gui
cls
echo.
echo ========================================
echo   Launching GUI...
echo ========================================
echo.
call start.bat
goto menu

:quick_rotation
cls
echo.
echo ========================================
echo   Quick Rotation
echo ========================================
echo.
echo INFO: Starting quick rotation...
python -c "from core.rotation_engine import RotationEngine; from utils.paths import PathManager; from utils.backup import BackupManager; from core.vscode_handler import VSCodeHandler; from utils.rotation_validator import RotationValidator; engine = RotationEngine(VSCodeHandler(PathManager(), BackupManager()), BackupManager(), PathManager(), RotationValidator(PathManager(), VSCodeHandler(PathManager(), BackupManager())), None); result = engine.perform_rotation('manual'); print('SUCCESS' if result['success'] else 'FAILED:', result.get('message', 'Unknown error'))"
echo.
pause
goto menu

:check_status
cls
echo.
echo ========================================
echo   Check Status
echo ========================================
echo.
echo INFO: Checking system status...
python -c "from core.token_monitor import TokenExpirationMonitor; from core.api_monitor import OpusAPIMonitor; from utils.paths import PathManager; tm = TokenExpirationMonitor(PathManager()); api = OpusAPIMonitor(); token_status = tm.check_token_status(); api_status = api.check_api_status(); print('Token Status:', 'EXPIRED' if token_status['expired'] else 'ACTIVE'); print('API Status:', 'HEALTHY' if api_status.get('healthy', False) else 'UNHEALTHY'); print('Rate Limited:', 'YES' if api_status.get('rate_limited', False) else 'NO')"
echo.
pause
goto menu

:service_menu
cls
echo.
echo ========================================
echo   Service Management
echo ========================================
echo.
echo   [a] Start Service
echo   [b] Stop Service
echo   [c] Service Status
echo   [d] Install Service
echo   [e] Uninstall Service
echo   [m] Back to Main Menu
echo.
set /p service_choice="Enter your choice: "

if "%service_choice%"=="a" goto start_service
if "%service_choice%"=="b" goto stop_service
if "%service_choice%"=="c" goto service_status
if "%service_choice%"=="d" goto install_service
if "%service_choice%"=="e" goto uninstall_service
if "%service_choice%"=="m" goto menu
goto invalid_choice

:start_service
cls
echo.
echo ========================================
echo   Starting Service...
echo ========================================
echo.
python -c "from service.service_manager import ServiceManager; sm = ServiceManager(); result = sm.start_service(); print(result.get('message', result.get('error', 'Unknown error')))"
echo.
pause
goto service_menu

:stop_service
cls
echo.
echo ========================================
echo   Stopping Service...
echo ========================================
echo.
python -c "from service.service_manager import ServiceManager; sm = ServiceManager(); result = sm.stop_service(); print(result.get('message', result.get('error', 'Unknown error')))"
echo.
pause
goto service_menu

:service_status
cls
echo.
echo ========================================
echo   Service Status
echo ========================================
echo.
python -c "from service.service_manager import ServiceManager; sm = ServiceManager(); result = sm.get_service_status(); print('Status:', result.get('status', 'UNKNOWN')); print('Message:', result.get('message', 'No message'))"
echo.
pause
goto service_menu

:install_service
cls
echo.
echo ========================================
echo   Installing Service...
echo ========================================
echo.
echo WARNING: This requires administrator privileges!
python -c "from service.service_manager import ServiceManager; sm = ServiceManager(); result = sm.install_service(); print(result.get('message', result.get('error', 'Unknown error')))"
echo.
pause
goto service_menu

:uninstall_service
cls
echo.
echo ========================================
echo   Uninstalling Service...
echo ========================================
echo.
echo WARNING: This requires administrator privileges!
python -c "from service.service_manager import ServiceManager; sm = ServiceManager(); result = sm.uninstall_service(); print(result.get('message', result.get('error', 'Unknown error')))"
echo.
pause
goto service_menu

:view_history
cls
echo.
echo ========================================
echo   Rotation History
echo ========================================
echo.
python -c "from utils.rotation_history import RotationHistory; rh = RotationHistory(); stats = rh.get_statistics(days=30); print('Total Rotations:', stats.get('total_rotations', 0)); print('Successful:', stats.get('successful_rotations', 0)); print('Failed:', stats.get('failed_rotations', 0)); recent = rh.get_recent_rotations(days=7); print('\\nRecent Rotations (last 7 days):'); [print(f\"  {r.get('timestamp', 'N/A')}: {r.get('trigger', 'N/A')} - {'SUCCESS' if r.get('success') else 'FAILED'}\") for r in recent[-10:]]"
echo.
pause
goto menu

:api_dashboard
cls
echo.
echo ========================================
echo   API Dashboard
echo ========================================
echo.
python -c "from core.api_monitor import OpusAPIMonitor; api = OpusAPIMonitor(); status = api.check_api_status(); print('API Health:', 'HEALTHY' if status.get('healthy', False) else 'UNHEALTHY'); print('Rate Limited:', 'YES' if status.get('rate_limited', False) else 'NO'); print('Last Check:', status.get('last_check_time', 'N/A')); print('Recent Rate Limits:', len(status.get('recent_rate_limits', [])))"
echo.
pause
goto menu

:configuration
cls
echo.
echo ========================================
echo   Configuration
echo ========================================
echo.
echo INFO: Opening configuration directory...
start "" "%USERPROFILE%\.cursor_rotation"
echo.
pause
goto menu

:invalid_choice
cls
echo.
echo ERROR: Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:exit
cls
echo.
echo ========================================
echo   Thank you for using AugmentCode Unlimited!
echo ========================================
echo.
timeout /t 2 >nul
exit /b 0

