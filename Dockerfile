FROM python:3.6

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get -y install zip && rm -rf /var/lib/apt/lists/*
RUN pip install virtualenv

RUN make virtualenv
RUN .venv/bin/pip install jobs/

ENTRYPOINT ["/bin/bash", "/app/bin/run.sh"]

CMD ["help"]
