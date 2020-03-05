FROM python:3.8-alpine

RUN mkdir /app
WORKDIR /app

RUN apk add --update alpine-sdk openssl-dev libffi-dev openssl libffi

ADD requirements.txt /app
RUN pip install -r requirements.txt

RUN apk del alpine-sdk openssl-dev libffi-dev

ADD . /app
RUN python manage.py migrate

EXPOSE 8000
CMD daphne -b 0.0.0.0 -p 8000 auction_house.asgi:application
