#!/bin/sh

set -e

mkdir -p /var/www/storage/framework/sessions
mkdir -p /var/www/storage/framework/views
mkdir -p /var/www/storage/framework/cache
mkdir -p /var/www/storage/logs
mkdir -p /var/www/database

if [ ! -f /var/www/database/database.sqlite ]; then
    touch /var/www/database/database.sqlite
    chown www-data:www-data /var/www/database/database.sqlite
fi

if [ ! -f /var/www/.env ]; then
    cp /var/www/.env.example /var/www/.env
fi

if ! grep -q "^APP_KEY=base64:" /var/www/.env 2>/dev/null; then
    php /var/www/artisan key:generate --force
fi

sed -i 's/^APP_ENV=.*/APP_ENV=production/' /var/www/.env
sed -i 's/^APP_DEBUG=.*/APP_DEBUG=false/' /var/www/.env

sed -i 's/^APP_URL=.*/APP_URL=/' /var/www/.env

if ! grep -q "^PYTHON_API_URL=" /var/www/.env 2>/dev/null; then
    echo "PYTHON_API_URL=http://127.0.0.1:8001" >> /var/www/.env
else
    sed -i 's|^PYTHON_API_URL=.*|PYTHON_API_URL=http://127.0.0.1:8001|' /var/www/.env
fi

chown -R www-data:www-data /var/www/storage
chown -R www-data:www-data /var/www/bootstrap/cache
chown -R www-data:www-data /var/www/database
chmod -R 775 /var/www/storage
chmod -R 775 /var/www/bootstrap/cache

php /var/www/artisan migrate --force

php /var/www/artisan config:clear
php /var/www/artisan config:cache
php /var/www/artisan route:cache
php /var/www/artisan view:cache

mkdir -p /var/log/supervisor

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf