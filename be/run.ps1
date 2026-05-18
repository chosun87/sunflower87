Write-Host "=========================================" -ForegroundColor Yellow
Write-Host " 🌻 sunflower87 Backend Server Starting..." -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow

# PowerShell 가상 환경 활성화 및 실행
& .\venv\Scripts\Activate.ps1
python migrate.py
python main.py

Read-Host "Press Enter to exit..."
