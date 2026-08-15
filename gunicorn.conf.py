"""Gunicorn configuration — values driven by environment variables."""

import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", f"{os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}")

# Workers
workers = int(os.getenv("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count() // 2 + 1)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
threads = int(os.getenv("GUNICORN_THREADS", "1"))

# Timeouts (seconds)
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Request limits
limit_request_line = int(os.getenv("GUNICORN_LIMIT_REQUEST_LINE", "8190"))
limit_request_fields = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELDS", "100"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", os.getenv("LOG_LEVEL", "info")).lower()
capture_output = True


def on_starting(server):
    server.log.info(
        "Gunicorn starting | bind=%s workers=%s timeout=%ss loglevel=%s",
        bind,
        workers,
        timeout,
        loglevel,
    )


def post_fork(server, worker):
    server.log.info("Worker spawned | pid=%s", worker.pid)

# Process naming
proc_name = os.getenv("GUNICORN_PROC_NAME", "rag-api")

# Reload (dev only — keep false in production/Docker)
reload = os.getenv("GUNICORN_RELOAD", "false").lower() in {"1", "true", "yes"}

# Preload app for faster worker spawn (disable if workers need isolated memory)
preload_app = os.getenv("GUNICORN_PRELOAD", "false").lower() in {"1", "true", "yes"}
