# FROM python:3-alpine3.16
FROM python:3-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install git gcc && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
COPY ./requirements.txt /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY ./leaf2mqtt.py /app

ENTRYPOINT ["python", "leaf2mqtt.py"]