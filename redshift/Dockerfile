FROM python:3.5

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY . /app/

ENTRYPOINT python /app/main.py
