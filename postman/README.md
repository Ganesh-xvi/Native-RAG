# Postman — 4-RAG API

## Import

1. Open Postman → **Import**
2. Add these files:
   - `rag.postman_collection.json`
   - `local.postman_environment.json` **or** `docker.postman_environment.json`
3. Select the environment from the top-right dropdown

## Environments

| Environment | `baseUrl` | When to use |
|-------------|-----------|-------------|
| **4-RAG Local** | `http://localhost:8000` | `uvicorn` or `scripts/run-dev.ps1` |
| **4-RAG Docker** | `http://localhost:8000` | `docker compose up` (port mapped from host) |

Update `apiKey` in the environment to match `API_KEY` in your `.env`.

## Suggested flow

1. **GET /health** — confirm server is up
2. **POST /ingest** — select a PDF file in the `file` form field
3. **GET /tasks/{task_id}** — poll until `status` is `completed` (taskId auto-saved)
4. **POST /query** — ask a question
5. **POST /eval** — run RAG metrics

## Docker notes

- Ollama must run on the **host** (`ollama pull snowflake-arctic-embed:137m`)
- Container reaches Ollama via `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- Groq API key is read from `.env` mounted via `docker-compose.yml`
