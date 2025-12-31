$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies and building..."

composer install --ignore-platform-reqs --no-autoloader
npm install
pip install -r requirements.txt

Copy-Item .env.example .env -Force
php artisan key:generate

New-Item -Path database -Name database.sqlite -ItemType File -Force | Out-Null
php artisan migrate

npm run build

Write-Host "Starting servers..."

# Laravel on port 8000 (handles both web and API proxying)
$laravel = Start-Process cmd `
    -ArgumentList '/k "php artisan serve --host=127.0.0.1 --port=8000"' `
    -PassThru

# Python on port 8001 (internal only)
$python = Start-Process cmd `
    -ArgumentList '/k "python -m uvicorn server:app --host 127.0.0.1 --port 8001"' `
    -PassThru

# Vite for hot module replacement
$vite = Start-Process cmd `
    -ArgumentList '/k "npm run dev"' `
    -PassThru

Write-Host "All servers started."
Write-Host "Application: http://localhost:8000"
Write-Host "Python API (internal): http://localhost:8001"
Write-Host ""
Write-Host "Press any key to stop all servers..."
[Console]::ReadKey($true) | Out-Null

Write-Host "Stopping servers..."

taskkill /PID $laravel.Id /T /F | Out-Null
taskkill /PID $python.Id  /T /F | Out-Null
taskkill /PID $vite.Id    /T /F | Out-Null

Write-Host "All servers stopped."