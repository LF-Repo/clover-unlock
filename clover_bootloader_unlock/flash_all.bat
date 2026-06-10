@echo off
rem Fastboot flash script
fastboot %* getvar product 2>&1 | findstr /r /c:"^product: *clover" || echo Missmatching image and device
fastboot %* getvar product 2>&1 | findstr /r /c:"^product: *clover" || exit /B 1
if not %ERRORLEVEL% == 0 exit /B 1

fastboot %* stage unlock.bin
fastboot %* oem unlock