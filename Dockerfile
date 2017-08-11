FROM python:3.6

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get -y install zip && rm -rf /var/lib/apt/lists/*
RUN pip install virtualenv
RUN make zip
