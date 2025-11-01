FROM python:3.11-slim

ENV TZ=Europe/Brussels \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
      tzdata libpq-dev gcc libssl-dev libffi-dev netcat-openbsd curl \
  && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/wait-for-it.sh /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
