FROM dockerhub/library/php:8.3.4-cli-alpine3.19

RUN apk update && apk upgrade
COPY app /var/www/html
WORKDIR /var/www/html
EXPOSE 80
CMD ["php", "-S", "0.0.0.0:80"]
