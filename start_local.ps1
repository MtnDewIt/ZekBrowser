$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies and building..."

composer install --ignore-platform-reqs
npm install
pip install -r requirements.txt

Copy-Item .env.example .env -Force
php artisan key:generate

New-Item -Path database -Name database.sqlite -ItemType File -Force | Out-Null
php artisan migrate

npm run build

Write-Host "Starting servers..."

$laravel = Start-Process cmd `
    -ArgumentList '/k "php artisan serve"' `
    -PassThru

$python = Start-Process cmd `
    -ArgumentList '/k "python server.py"' `
    -PassThru

$vite = Start-Process cmd `
    -ArgumentList '/k "npm run dev"' `
    -PassThru

Write-Host "All servers started."
Write-Host "Press any key to stop all servers..."
[Console]::ReadKey($true) | Out-Null

Write-Host "Stopping servers..."

taskkill /PID $laravel.Id /T /F | Out-Null
taskkill /PID $python.Id  /T /F | Out-Null
taskkill /PID $vite.Id    /T /F | Out-Null

Write-Host "All servers stopped."
