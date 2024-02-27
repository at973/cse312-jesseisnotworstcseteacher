# syntax=docker/dockerfile:1
FROM python:3.10-alpine
WORKDIR /code
ENV WEB_APP=server.py
ENV WEB_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 8080
COPY . .
CMD python -u server.py