@echo off
PROBE.EXE > NUL
if errorlevel 137 goto bad
if not errorlevel 136 goto bad
echo PASS > FULLRUN.LOG
goto done
:bad
echo FAIL > FULLRUN.LOG
:done
