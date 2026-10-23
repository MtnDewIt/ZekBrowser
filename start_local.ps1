$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies and building..."

composer install --ignore-platform-reqs --no-autoloader
npm install
pip install -r requirements.txt

# Keep an existing .env (and its APP_KEY); only bootstrap one on first run.
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    php artisan key:generate
}

# Never recreate the database file: New-Item -Force would truncate it.
if (-not (Test-Path database/database.sqlite)) {
    New-Item -Path database -Name database.sqlite -ItemType File | Out-Null
}
php artisan migrate

npm run build

Write-Host "Starting servers..."

$laravel = Start-Process cmd `
    -ArgumentList '/k "php artisan serve --host=127.0.0.1 --port=8000"' `
    -PassThru

$python = Start-Process cmd `
    -ArgumentList '/k "python -m uvicorn server:app --host 127.0.0.1 --port 8001"' `
    -PassThru

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

foreach ($proc in @($laravel, $python, $vite)) {
    taskkill /PID $proc.Id /T /F | Out-Null
}

Write-Host "All servers stopped."
