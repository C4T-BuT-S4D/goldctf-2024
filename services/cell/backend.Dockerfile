FROM php:8.2-cli@sha256:e0941c06b8a4f6e48c7c57672dce608d1e314419b5c14b4f385cd9550cc7abb6 as backend

#RUN  --mount=type=bind,from=mlocati/php-extension-installer:1.5,source=/usr/bin/install-php-extensions,target=/usr/local/bin/install-php-extensions \
#      install-php-extensions opcache zip xsl dom exif intl pcntl bcmath sockets gd && \
#     apk del --no-cache  ${PHPIZE_DEPS} ${BUILD_DEPENDS}
RUN apt update && apt install -y git libpng-dev libzip-dev
RUN docker-php-ext-install gd zip opcache sockets

WORKDIR /app

ENV COMPOSER_ALLOW_SUPERUSER=1
COPY --from=composer:2.3 /usr/bin/composer /usr/bin/composer
COPY backend/composer.* .
RUN composer config --no-plugins allow-plugins.spiral/composer-publish-plugin false && \
    composer install --optimize-autoloader --no-dev

COPY --from=spiralscout/roadrunner:latest /usr/bin/rr /app

COPY backend/ .
COPY conf/rr.yml rr.yaml
COPY conf/backend.env .env

RUN mkdir -p /data/task/acls
RUN mkdir -p /data/task/user-files

CMD ./rr serve -c rr.yaml