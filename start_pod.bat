@echo off
setlocal enabledelayedexpansion

set "BASE=%~dp0"
set "SONG_OUT=C:\Users\agoll\Desktop\VPSRTfr\Content\Assets+Media\Song.wav"
set "FFMPEG=C:\Users\agoll\Desktop\TOOLS\ffmpeg-2025-05-19-git-c55d65ac0a-full_build\bin\ffmpeg.exe"
set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"

echo ====================================================
echo [1/9] %DATE%  %TIME%   Launching Flask server...
echo ====================================================
start "" py "%BASE%server.py"

echo.
echo [2/9] Waiting for tunnel.txt...
set "TUNNELFILE=%BASE%tunnel.txt"
:waitTunnel
if not exist "%TUNNELFILE%" (
    timeout /t 1 >nul
    goto waitTunnel
)
findstr "PUBLIC_URL=" "%TUNNELFILE%" >nul || goto waitTunnel

echo.
echo [3/9] Launching Chrome to QR page...
start "" "%CHROME%" --kiosk http://localhost:5000

echo.
echo [4/9] Cleaning old files...
del /q "%BASE%trimmed.mp3" 2>nul
del /q "%BASE%latest.mp3" 2>nul
del /q "%SONG_OUT%" 2>nul

echo.
echo [5/9] Waiting for trimmed.mp3 in %BASE% ...
:waitTrimmed
if not exist "%BASE%trimmed.mp3" (
    echo . waiting...
    timeout /t 1 >nul
    goto waitTrimmed
)
for %%I in ("%BASE%trimmed.mp3") do set "SIZE=%%~zI"
if "%SIZE%"=="0" (
    echo . waiting for write completion...
    timeout /t 1 >nul
    goto waitTrimmed
)

echo.
echo [6/9] Converting trimmed.mp3 → Song.wav...
"%FFMPEG%" -y -i "%BASE%trimmed.mp3" -acodec pcm_s16le -ar 48000 -ac 2 "%SONG_OUT%"

if exist "%SONG_OUT%" (
    echo.
    echo [7/9] ✅ Song.wav created successfully.
) else (
    echo.
    echo [7/9] ❌ Conversion failed.
    pause
    exit /b
)

echo.
echo [8/9] Launching Unreal shortcut...
start "" "%USERPROFILE%\Desktop\launcher.bat - Shortcut.lnk"

echo.
echo [9/9] Done. QR ready on desktop, upload from mobile, Unreal will open after song conversion.
exit
