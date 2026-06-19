# start.ps1
# This script starts the Nota backend and frontend servers in separate windows.

Write-Host "Starting Nota Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn app.main:app --reload --port 8000"

Write-Host "Starting Nota Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Both servers are starting. You can access Nota at http://localhost:3000" -ForegroundColor Green
