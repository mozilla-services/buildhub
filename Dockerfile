FROM python:3.6-slim
MAINTAINER Product Delivery irc://irc.mozilla.org/#product-delivery

RUN \
    apt-get update && \
    apt-get -y install zip make gcc && \
    rm -rf /var/lib/apt/lists/* && \
    pip install virtualenv

COPY . /app
WORKDIR /app

RUN mkdir /app/cache
ENV CACHE_FOLDER /app/cache

RUN \
    make virtualenv && \
    .venv/bin/pip install jobs/ && \
    .venv/bin/pip freeze > dependencies.txt

RUN groupadd -g 10001 app && \
    useradd -M -u 10001 -g 10001 -G app -d /app -s /sbin/nologin app

ENTRYPOINT ["/bin/bash", "/app/bin/run.sh"]

USER app

CMD ["help"]
