@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo =========================================================
echo  KHOI DONG PETCARE SPA MANAGEMENT SYSTEM - NHOM 6
echo =========================================================
echo Dang khoi chay may chu FastAPI va giao dien Web...
python run_app.py
pause
