@echo off
REM SPDX-License-Identifier: Apache-2.0
REM Copyright 2026 Fabio Campolim
REM ---------------------------------------------------------------------------
REM  Kwant installer launcher for cmd.exe users.
REM  Double-click this file, or run it from a command prompt.
REM  It just calls the PowerShell script next to it, bypassing the execution
REM  policy for this one invocation only (nothing is changed permanently).
REM ---------------------------------------------------------------------------

setlocal

echo.
echo  Installing Kwant 1.5 ... this will take several minutes.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_kwant_windows.ps1" %*

set RC=%ERRORLEVEL%

echo.
if %RC% NEQ 0 (
    echo  Installation reported errors ^(exit code %RC%^). Scroll up for details.
) else (
    echo  Finished. Open a NEW command prompt, then:  conda activate kwant
)
echo.

pause
endlocal
exit /b %RC%
