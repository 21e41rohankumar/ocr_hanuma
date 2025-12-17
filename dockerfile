FROM python:3.10-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install ONLY required system libs
RUN apt-get update && apt-get install -y \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 🚨 CRITICAL: no cache, single layer
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "1", "-k", "gthread", "-b", "0.0.0.0:8080", "app:app"]
