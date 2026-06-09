@echo off
rem Fastboot flash script
fastboot %* getvar product 2>&1 | findstr /r /c:"^product: *clover" || echo Missmatching image and device
fastboot %* getvar product 2>&1 | findstr /r /c:"^product: *clover" || exit /B 1
if not %ERRORLEVEL% == 0 exit /B 1

echo Flashing xbl
fastboot %* flash xbl %~dp0\images\xbl.elf
echo Flashing xblbak
fastboot %* flash xblbak %~dp0\images\xbl.elf

echo Flashing abl
fastboot %* flash abl %~dp0\images\abl.elf
echo Flashing ablbak
fastboot %* flash ablbak %~dp0\images\abl.elf

rem Miflash catch point
echo $fastboot %* reboot
