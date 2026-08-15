# RAG

A **native RAG (Retrieval-Augmented Generation)** application that lets you chat with your own PDF documents. Instead of relying on the LLM's training data, it retrieves relevant passages from your files, feeds them as context, and generates answers grounded in that content — with page-level citations.

Built with **LangChain**, **Groq**, **Ollama**, and **FastAPI**.

### How native RAG works here

```
Your PDFs  →  Chunk & Embed  →  Vector Store (Chroma)
                                        ↓
Your Question  →  Retrieve top-k chunks  →  Groq LLM  →  Grounded Answer + Sources
```

1. **Retrieve** — embed the question and find the most similar document chunks  
2. **Augment** — inject those chunks into the LLM prompt as context  
3. **Generate** — the LLM answers strictly from the retrieved content  

This keeps responses accurate, traceable, and scoped to *your* data — not the open web.

## Features

- **PDF ingestion** — async upload with background task tracking
- **Vector search** — Chroma + Ollama embeddings (`snowflake-arctic-embed:137m`)
- **LLM answers** — Groq (`openai/gpt-oss-120b`) with LCEL chain
- **Guardrails** — input validation and output grounding checks
- **RAG evaluation** — faithfulness, answer relevancy, context precision
- **REST API** — FastAPI with API-key auth and SSE streaming
- **CLI** — ingest, query, and eval from the terminal
- **Docker** — production image with Gunicorn and auto-restart
- **Postman** — ready-made collection for local and Docker

## Stack

| Component | Technology |
|-----------|------------|
| LLM | Groq — `openai/gpt-oss-120b` |
| Embeddings | Ollama — `snowflake-arctic-embed:137m` |
| Vector store | Chroma |
| Framework | LangChain (LCEL) |
| API | FastAPI |
| Production server | Gunicorn + Uvicorn workers |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (dependency locking and export for Docker)
- [Ollama](https://ollama.com/) running locally
- [Groq API key](https://console.groq.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

```bash
ollama pull snowflake-arctic-embed:137m
```

## Project structure

```
4_RAG/
├── src/
│   ├── api/                # FastAPI app and routes
│   │   ├── main.py
│   │   ├── middleware/
│   │   └── routes/
│   ├── utils/              # Config, LLM, guardrails, tasks
│   ├── rag/                # Ingest, retriever, chain, prompts
│   ├── schemas/            # Pydantic request/response models
│   └── services/           # Eval and other services
├── data/                   # PDF documents
├── storage/                # Chroma index + task state (gitignored)
├── eval/                   # Golden Q&A set for /eval
├── postman/                # Postman collection + environments
├── tests/
├── main.py                 # CLI entry point
├── gunicorn.conf.py        # Production server config
├── Dockerfile
├── docker-compose.yml
├── uv.lock                 # Locked dependencies (uv)
├── requirements.txt        # Exported for Docker (pip install -r)
└── .env.example
```

## Setup

### 1. Clone and install

```bash
cd 4_RAG
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see [API keys](#api-keys) below):

```env
groq_api_key=gsk-your-key-here
llm_model=openai/gpt-oss-120b
embedding_model=snowflake-arctic-embed:137m
ollama_base_url=http://localhost:11434
API_KEY=your-secret-api-key-here
```

### API keys

This project uses **two different keys**. Do not confuse them.

| Variable | Where it comes from | Purpose |
|----------|---------------------|---------|
| `groq_api_key` | [Groq Console](https://console.groq.com/) → API Keys | Calls the Groq LLM for generating answers |
| `API_KEY` | **You create it yourself** | Protects *your* FastAPI endpoints |

#### `groq_api_key` (Groq — external)

1. Sign up at [console.groq.com](https://console.groq.com/)
2. Go to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_`)
4. Paste into `.env`:
   ```env
   groq_api_key=gsk_xxxxxxxxxxxxxxxx
   ```

#### `API_KEY` (yours — not from any website)

There is **no signup or download** for `API_KEY`. You invent any strong secret string and put it in `.env`. The server checks that clients send the same value in the `X-API-Key` header.

**Generate one (pick any method):**

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

Then set it in `.env`:

```env
API_KEY=my-super-secret-key-abc123xyz
```

**Use it in requests:**

```bash
curl -H "X-API-Key: my-super-secret-key-abc123xyz" ...
```

In Postman, set the same value in the environment variable `apiKey` (must match `.env` exactly).

> **Important:** If you change `API_KEY` in `.env`, restart the server and update Postman/curl to use the new value.

### 3. Ingest a document

```bash
python main.py ingest --recreate
```

### 4. Ask a question

```bash
python main.py query "What were Apple's total net sales in FY2025?"
```

## Logging

Logs go to **stdout** so you can see what the app is doing in both local dev and Docker. Configure via `.env`:

```env
LOG_LEVEL=INFO
LOG_FORMAT=text
# LOG_FORMAT=json          # structured JSON (better for Docker/log tools)
# LOG_FILE=./storage/app.log
```

### Log levels

| Level | What you see |
|-------|--------------|
| `DEBUG` | Detailed retrieval and internal steps |
| `INFO` | Startup, requests, ingest progress, queries (default) |
| `WARNING` | Guardrail blocks, missing index |
| `ERROR` | Task failures, exceptions |

Set `LOG_LEVEL=DEBUG` in `.env` when troubleshooting.

### Local — view logs

Start the server and watch the terminal:

```powershell
.\scripts\run-dev.ps1
```

Example output:

```
2026-08-13 11:45:00 | INFO     | 4rag.api | Application startup | host=0.0.0.0 port=8000 ...
2026-08-13 11:45:10 | INFO     | 4rag.api.middleware | Request started | method=POST path=/query
2026-08-13 11:45:12 | INFO     | 4rag.api.query | Query completed | answer_length=142
2026-08-13 11:45:12 | INFO     | 4rag.api.middleware | Request completed | method=POST path=/query status=200 duration_ms=1842.5
```

CLI commands also log to the same terminal:

```bash
python main.py ingest --recreate
python main.py query "Your question"
```

### Docker — view logs

```bash
# Follow live logs
docker compose logs -f rag-api

# Last 100 lines
docker compose logs --tail=100 rag-api
```

Use `LOG_FORMAT=json` in `.env` for structured logs in Docker:

```json
{"timestamp": "2026-08-13T06:15:00Z", "level": "INFO", "logger": "4rag.rag.ingest", "message": "Ingest completed | file=report.pdf chunks=364 ..."}
```

### What gets logged

| Event | Logger | Example |
|-------|--------|---------|
| App startup/shutdown | `4rag.api` | index loaded, model names |
| HTTP requests | `4rag.api.middleware` | method, path, status, duration |
| PDF upload | `4rag.api.ingest` | filename, size |
| Ingest pipeline | `4rag.rag.ingest` | split chunks, embed complete |
| Background tasks | `4rag.utils.tasks` | task created/completed/failed |
| Queries | `4rag.api.query` | sources count, answer length |
| Guardrail blocks | `4rag.api.query` | reason (no secrets logged) |

> API keys and Groq tokens are **never** written to logs.

## Running the API

### Local development (Windows / macOS / Linux)

Uses **Uvicorn** with hot reload:

```powershell
# Windows
.\scripts\run-dev.ps1
```

```bash
# Or directly
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### Production (Linux / Docker)

Uses **Gunicorn** (not supported natively on Windows):

```bash
bash scripts/run-prod.sh
```

> Gunicorn settings are in `gunicorn.conf.py` and driven by env vars (`GUNICORN_TIMEOUT`, `GUNICORN_WORKERS`, etc.).

## Docker

Ollama must run on the **host machine**. The container reaches it via `host.docker.internal`.

Dependencies are installed from a locked `requirements.txt` (exported from `uv.lock`) — not via `pip install .`, so the image does not need `README.md` at build time.

### 1. Lock dependencies and export requirements

Run these **before your first Docker build**, and again whenever you change `pyproject.toml`:

```bash
uv lock
uv export --format requirements-txt --no-emit-project --no-dev -o requirements.txt
docker compose build --no-cache
```

| Command | What it does |
|---------|--------------|
| `uv lock` | Resolves and locks all dependencies into `uv.lock` |
| `uv export ... -o requirements.txt` | Exports pinned deps for Docker (`pip install -r`) |
| `docker compose build --no-cache` | Rebuilds the image with fresh dependencies |

### 2. Start the container

```bash
# Build and start (auto-restart enabled)
docker compose up -d --build

# View logs
docker compose logs -f rag-api

# Stop
docker compose down
```

Docker Compose mounts `./data` and `./storage` as volumes and sets:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Liveness + dependency checks |
| `POST` | `/ingest` | Yes | Upload PDF → returns `task_id` |
| `GET` | `/tasks/{task_id}` | Yes | Poll ingest/rebuild status |
| `POST` | `/index/rebuild` | Yes | Re-embed all PDFs in `data/` |
| `POST` | `/query` | Yes | Question → answer + sources |
| `POST` | `/query/stream` | Yes | SSE token streaming |
| `POST` | `/eval` | Yes | RAG quality metrics |

All protected routes require the header (value must match `API_KEY` in your `.env` — see [API keys](#api-keys)):

```
X-API-Key: <your API_KEY from .env>
```

### Example: upload and query

```bash
# Upload PDF
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@data/Apple's FY2025 10-K Annual Report.pdf"

# Poll task (replace TASK_ID)
curl http://localhost:8000/tasks/TASK_ID \
  -H "X-API-Key: your-secret-api-key-here"

# Query
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What are Apple'\''s main risk factors?\"}"
```

## Postman

Import into Postman:

1. `postman/rag.postman_collection.json`
2. `postman/local.postman_environment.json` — for local dev
3. `postman/docker.postman_environment.json` — for Docker

Set `apiKey` in the environment to the **same value as `API_KEY` in `.env`** (you define this yourself — not from Groq). See [API keys](#api-keys).

## CLI

```bash
# Ingest a single PDF or all PDFs in data/
python main.py ingest --file "data/report.pdf"
python main.py ingest --all --recreate

# Query
python main.py query "Your question here"

# Run evaluation
python main.py eval
```

## Configuration reference

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind host |
| `API_PORT` | `8000` | Server port |
| `GUNICORN_WORKERS` | `2` | Gunicorn worker processes |
| `GUNICORN_TIMEOUT` | `120` | Worker timeout (seconds) |
| `GUNICORN_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout |
| `GUNICORN_KEEPALIVE` | `5` | HTTP keep-alive (seconds) |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap |
| `RETRIEVER_TOP_K` | `4` | Retrieved chunks per query |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max PDF upload size |
| `LOG_LEVEL` | `INFO` | App log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | `text` | `text` or `json` |
| `LOG_FILE` | — | Optional file path (also logs to stdout) |

Full list: `.env.example`

## Tests

```bash
python -m pytest tests/ -q
```

## Architecture

```
PDF Upload → Load & Split → Ollama Embed → Chroma Store
                                              ↓
User Question → Guardrails → Retrieve → Groq LLM → Answer + Sources
```

## License

Private / internal use.
