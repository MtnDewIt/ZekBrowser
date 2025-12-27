#!/bin/sh

set -e

# Ensure storage directories exist with correct permissions
mkdir -p /var/www/storage/framework/sessions
mkdir -p /var/www/storage/framework/views
mkdir -p /var/www/storage/framework/cache
mkdir -p /var/www/storage/logs
mkdir -p /var/www/database

# Create SQLite database if it doesn't exist
if [ ! -f /var/www/database/database.sqlite ]; then
    touch /var/www/database/database.sqlite
    chown www-data:www-data /var/www/database/database.sqlite
fi

# Copy env file if it doesn't exist
if [ ! -f /var/www/.env ]; then
    cp /var/www/.env.example /var/www/.env
fi

# Generate application key if not set
if ! grep -q "^APP_KEY=base64:" /var/www/.env 2>/dev/null; then
    php /var/www/artisan key:generate --force
fi

# Set permissions
chown -R www-data:www-data /var/www/storage
chown -R www-data:www-data /var/www/bootstrap/cache
chown -R www-data:www-data /var/www/database
chmod -R 775 /var/www/storage
chmod -R 775 /var/www/bootstrap/cache

# Run migrations
php /var/www/artisan migrate --force

# Clear and cache configuration
php /var/www/artisan config:clear
php /var/www/artisan config:cache
php /var/www/artisan route:cache
php /var/www/artisan view:cache

# Create supervisor log directory
mkdir -p /var/log/supervisor

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf