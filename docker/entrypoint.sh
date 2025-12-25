#!/bin/sh

set -e

# Create SQLite database if it doesn't exist
if [ ! -f /var/www/database/database.sqlite ]; then
    touch /var/www/database/database.sqlite
    chown www-data:www-data /var/www/database/database.sqlite
fi

# Generate application key if not set
if [ ! -f /var/www/.env ]; then
    cp /var/www/.env.example /var/www/.env
    php /var/www/artisan key:generate
fi

# Run migrations
php /var/www/artisan migrate --force

# Cache configuration
php /var/www/artisan config:cache
php /var/www/artisan route:cache
php /var/www/artisan view:cache

# Create supervisor log directory
mkdir -p /var/log/supervisor

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf