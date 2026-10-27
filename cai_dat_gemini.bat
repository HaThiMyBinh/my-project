@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" (
    if not exist ".env.example" (
        echo Khong tim thay .env.example. Hay dat tep nay trong thu muc PetCare.
        pause
        exit /b 1
    )
    copy /y ".env.example" ".env" >nul
    if errorlevel 1 (
        echo Khong the tao tep .env.
        pause
        exit /b 1
    )
)
echo Notepad se mo tep .env.
echo Dan API key sau GEMINI_API_KEY=, bam Ctrl+S roi dong Notepad.
echo Khong gui API key cho nguoi khac.
notepad.exe ".env"
echo Sau khi luu, dong cua so PetCare dang chay va mo lai run.bat.
pause
