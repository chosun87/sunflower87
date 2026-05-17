@echo off
echo =========================================
echo  🌻 sunflower87 Backend Server Starting...
echo =========================================

:: 가상 환경 활성화 및 서버 실행
call venv\Scripts\activate.bat
python main.py

pause
