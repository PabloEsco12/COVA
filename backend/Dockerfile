FROM python:3.10-slim

ENV TZ=Europe/Brussels \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      tzdata libpq-dev gcc libssl-dev libffi-dev netcat-openbsd curl \
  && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
