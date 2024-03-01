# pull the official docker image
FROM python:3.12.2-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client-15

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
