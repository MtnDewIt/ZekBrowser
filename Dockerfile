FROM php:8.5-fpm-alpine AS builder

WORKDIR /var/www

RUN apk add --no-cache \
    git \
    curl \
    unzip \
    nodejs \
    npm

COPY composer.json composer.lock* ./
COPY package.json package-lock.json* ./

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

COPY . .

RUN composer install --no-dev --optimize-autoloader --no-interaction

RUN npm ci && npm run build
RUN rm -rf node_modules

FROM php:8.5-fpm-alpine

WORKDIR /var/www

RUN apk add --no-cache \
    nginx \
    supervisor \
    python3 \
    py3-pip \
    libpng \
    oniguruma \
    libxml2 \
    shadow

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

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages --upgrade pip>=25.3

COPY --from=builder /var/www /var/www

COPY server.py /var/www/server.py
COPY dewrito.json /var/www/dewrito.json
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/http.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chown -R www-data:www-data /var/www \
    && chmod -R 755 /var/www/storage \
    && chmod -R 755 /var/www/bootstrap/cache

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]