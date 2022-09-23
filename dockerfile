# syntax=docker/dockerfile:1
FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get update
RUN apt-get -y install apt-utils
RUN apt-get -y install cron
RUN apt-get -y install rsyslog
COPY hh_cron /etc/cron.d/
RUN chmod 0644 /etc/cron.d/hh_cron
RUN crontab /etc/cron.d/hh_cron
RUN pip install -r requirements.txt
COPY . /code/
