FROM python:slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY modelAgency.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP modelAgency.py

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
