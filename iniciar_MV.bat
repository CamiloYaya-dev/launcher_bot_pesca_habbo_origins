@echo off
cd /d "%~dp0"
"C:\Program Files\qemu\qemu-system-x86_64.exe" ^
 -m 4096 ^
 -smp 2 ^
 -hda tiny10.img ^
 -net nic ^
 -net user ^
 -display sdl ^
 -accel whpx
pause
