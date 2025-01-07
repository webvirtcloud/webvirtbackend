FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN set -eux; \
	apk add --no-cache uv gcc g++ pango openssh-client fontconfig \
                       ttf-freefont font-noto terminus-font \
                       musl-dev mariadb-dev libffi-dev openssl-dev; \
    fc-cache -f; \
    rm -rf /var/cache/apk/*

COPY ./requirements/develop.txt ./requirements/production.txt /app/

RUN uv pip install --system -r develop.txt
