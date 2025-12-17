FROM python:3.10-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1️⃣ Install CPU-only PyTorch separately
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch==2.9.1+cpu torchvision==0.24.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# 2️⃣ Install the rest of requirements (remove torch/torchvision from requirements.txt!)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "1", "-k", "gthread", "-b", "0.0.0.0:8080", "app:app"]
