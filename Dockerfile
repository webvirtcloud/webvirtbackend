FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN set -eux; \
	apk add --no-cache gcc g++ pango musl-dev mariadb-dev libffi-dev openssl-dev; \
    rm -rf /var/cache/apk/*

COPY ./requirements/develop.txt ./requirements/production.txt /app/

RUN python3 -m pip install -U pip wheel setuptools; \
    python3 -m pip install -r develop.txt
