@echo off
REM CurioCut Windows Local Standby Task Scheduler
REM Dispatches the Kaggle GPU video pipeline at peak IST hours:
REM - 12:25 PM IST (triggers for 1:00 PM Lunch window)
REM - 06:25 PM IST (triggers for 7:00 PM Evening surge)

set PYTHON_EXE=python
set DISPATCHER_SCRIPT=%~dp0trigger_kaggle.py

echo ========================================================
echo   Setting up CurioCut Local Standby Scheduler
echo ========================================================

REM Create Lunch Task (12:25 PM)
schtasks /create /tn "CurioCut_Lunch_Short" /tr "%PYTHON_EXE% \"%DISPATCHER_SCRIPT%\"" /sc daily /st 12:25 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Scheduled Lunch Short at 12:25 PM IST
) else (
    echo [Notice] Please run this batch script as Administrator to register scheduled tasks.
)

REM Create Evening Task (06:25 PM)
schtasks /create /tn "CurioCut_Evening_Short" /tr "%PYTHON_EXE% \"%DISPATCHER_SCRIPT%\"" /sc daily /st 18:25 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Scheduled Evening Short at 06:25 PM IST
) else (
    echo [Notice] Please run this batch script as Administrator to register scheduled tasks.
)

echo.
echo Standby scheduler setup complete!
pause

