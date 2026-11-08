@echo off
call :greet Virgo
call :greet Galaxy
goto :eof

:greet
echo Hello, %~1!
exit /b 0
