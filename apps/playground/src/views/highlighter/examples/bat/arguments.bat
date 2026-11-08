@echo off
if "%~1"=="" goto usage

set "source=%~1"
if not exist "%source%" (
  echo File not found: %source%
  exit /b 1
)

echo Selected "%source%"
exit /b 0

:usage
echo Usage: %~nx0 input.txt
exit /b 2
