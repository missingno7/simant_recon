@echo off
PROBE.EXE > NUL
if errorlevel 112 goto bad
if not errorlevel 111 goto bad
echo PASS > FULLRUN.LOG
goto done
:bad
echo FAIL > FULLRUN.LOG
:done
