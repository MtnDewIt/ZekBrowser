#!/bin/sh
# Bare-metal update: pull, install, migrate, rebuild. The site comes back up
# even when a step fails, so a broken deploy does not leave it in maintenance mode.

set -eu

cd "$(dirname "$0")"

php artisan down
trap 'php artisan up' EXIT

git pull

composer install --no-dev --optimize-autoloader --no-interaction
npm ci
pip install -r requirements.txt

php artisan migrate --force
npm run build

php artisan config:cache
php artisan route:cache
php artisan view:cache
