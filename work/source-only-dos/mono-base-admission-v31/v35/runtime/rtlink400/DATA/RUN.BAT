@echo off
D:\RTLINK.EXE @LOCAL.LNK < NUL > LINK.LOG
if not exist LOCAL.EXE goto noexe
LOCAL.EXE > OBS.BIN
echo EXECUTED > RUN.LOG
goto done
:noexe
echo NOEXE > RUN.LOG
:done
