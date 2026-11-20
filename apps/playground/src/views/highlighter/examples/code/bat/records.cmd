@echo off
rem Read CSV fields without executing the input file.
for /f "tokens=1,2 delims=," %%A in (records.csv) do (
  echo Name: %%A Score: %%B
)

node report.js --format text > report.txt 2>&1
if errorlevel 1 echo Report failed
