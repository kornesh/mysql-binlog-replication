FROM python:3.5

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade --no-cache-dir -r /app/requirements.txt

ENTRYPOINT python /app/main.py
