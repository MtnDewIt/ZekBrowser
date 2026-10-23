#!/bin/sh
# Container entrypoint: prepare writable dirs, the SQLite database and .env,
# run migrations and cache Laravel config, then hand over to supervisord.
set -eu

APP_DIR="/var/www"
ENV_FILE="$APP_DIR/.env"
DB_FILE="$APP_DIR/database/database.sqlite"
LEGACY_DB="/legacy_database_import/database.sqlite"

for dir in storage/framework/sessions storage/framework/views storage/framework/cache storage/logs database; do
    mkdir -p "$APP_DIR/$dir"
done

if [ ! -f "$DB_FILE" ]; then
    if [ -f "$LEGACY_DB" ]; then
        echo "Importing legacy database from $LEGACY_DB..."
        cp "$LEGACY_DB" "$DB_FILE"
    else
        echo "Creating new database..."
        touch "$DB_FILE"
    fi
fi

if [ ! -f "$ENV_FILE" ]; then
    cp "$APP_DIR/.env.example" "$ENV_FILE"
fi

if ! grep -q "^APP_KEY=base64:" "$ENV_FILE"; then
    php "$APP_DIR/artisan" key:generate --force
fi

# Pin the values the container relies on, whatever the shipped .env says.
set_env() {
    if grep -q "^$1=" "$ENV_FILE"; then
        sed -i "s|^$1=.*|$1=$2|" "$ENV_FILE"
    else
        echo "$1=$2" >> "$ENV_FILE"
    fi
}

set_env APP_ENV production
set_env APP_DEBUG false
set_env APP_URL ""
set_env PYTHON_API_URL http://127.0.0.1:8001

chown -R www-data:www-data "$APP_DIR/storage" "$APP_DIR/bootstrap/cache" "$APP_DIR/database"
chmod -R 775 "$APP_DIR/storage" "$APP_DIR/bootstrap/cache"

php "$APP_DIR/artisan" migrate --force

php "$APP_DIR/artisan" config:clear
php "$APP_DIR/artisan" config:cache
php "$APP_DIR/artisan" route:cache
php "$APP_DIR/artisan" view:cache

mkdir -p /var/log/supervisor

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
