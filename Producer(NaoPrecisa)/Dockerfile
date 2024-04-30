FROM python:3.8-alpine

WORKDIR /app

COPY Producer.py .
COPY Sample.json .

RUN pip install --upgrade pip
RUN pip install pika

ENTRYPOINT ["tail", "-f", "/dev/null"]