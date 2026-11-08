@echo off
setlocal EnableDelayedExpansion
set "root=%~dp0"
set /a count=0

for %%F in ("%root%src\*.ts") do (
  set /a count+=1
  echo !count!: %%~nxF
)

echo Processed !count! files
endlocal
