@echo off
set "EEVEE_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if defined PROCESSOR_ARCHITEW6432 set "EEVEE_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%EEVEE_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Installer_capteur_CPU.ps1"
if errorlevel 1 echo Installation failed. Run Installer_capteur_CPU.ps1 in an elevated PowerShell window for details.
pause
