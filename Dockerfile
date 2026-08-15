FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from lockfile export (no editable project install)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application code
COPY src/ ./src/
COPY eval/ ./eval/
COPY gunicorn.conf.py ./

RUN mkdir -p /app/data /app/storage/chroma /app/storage/tasks

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('API_PORT','8000')+'/health', timeout=5)" || exit 1

CMD ["gunicorn", "src.api.main:app", "-c", "gunicorn.conf.py"]
