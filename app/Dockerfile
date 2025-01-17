FROM python:3.12.3-slim-bullseye

RUN groupadd -g 10001 -r pyapp && useradd --no-log-init -r -u 10001 -g pyapp pyapp

RUN apt-get update; apt-get install curl tzdata -y

COPY ./cmd/pyapp /cmd/pyapp
COPY /cmd/local.env.docker.example /cmd/local.env
COPY /cmd/logging_config.json /cmd/
COPY /cmd/requirements.txt.freeze /cmd/
WORKDIR /cmd

ENV PIP_ROOT_USER_ACTION=ignore
ENV MYAPP_ENV_PATH=/cmd/local.env
ENV MPLCONFIGDIR=/cmd/data/cache

RUN true \
    && pip install --upgrade pip \
    && pip install --no-cache-dir  -r requirements.txt.freeze

USER pyapp

ENTRYPOINT ["python3", "-m", "pyapp"]
