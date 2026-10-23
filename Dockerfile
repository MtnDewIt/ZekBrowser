FROM php:8.5.12-fpm-alpine AS builder

WORKDIR /var/www

RUN apk add --no-cache \
    git \
    curl \
    unzip \
    nodejs \
    npm

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

COPY . .

RUN composer install --no-dev --optimize-autoloader --no-interaction

RUN npm ci && npm run build && rm -rf node_modules

FROM php:8.5.12-fpm-alpine

WORKDIR /var/www

RUN apk add --no-cache \
    nginx \
    supervisor \
    python3 \
    py3-pip \
    libpng \
    oniguruma \
    libxml2 \
    shadow \
    sqlite

RUN apk add --no-cache --virtual .build-deps \
    libpng-dev \
    oniguruma-dev \
    libxml2-dev \
    gcc \
    musl-dev \
    make \
    && docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd \
    && apk del .build-deps

COPY requirements.txt .

RUN pip3 install --no-cache-dir --break-system-packages --upgrade "pip>=25.3" \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY --from=builder /var/www /var/www

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/http.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh docker/backup.sh docker/restore.sh /usr/local/bin/

RUN echo "0 */6 * * * /usr/local/bin/backup.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/backup.sh /usr/local/bin/restore.sh \
    && chown -R www-data:www-data /var/www \
    && chmod -R 755 /var/www/storage /var/www/bootstrap/cache

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
