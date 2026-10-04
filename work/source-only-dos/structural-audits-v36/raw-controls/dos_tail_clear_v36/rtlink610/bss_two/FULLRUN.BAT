@echo off
PROBE.EXE > NUL
if errorlevel 1 goto bad
echo PASS > FULLRUN.LOG
goto done
:bad
echo FAIL > FULLRUN.LOG
:done
