FROM python:3.8-alpine

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD . /app
RUN python manage.py migrate

EXPOSE 8000
CMD python manage.py runserver 0.0.0.0:8000
