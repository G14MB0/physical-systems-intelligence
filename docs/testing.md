# Testing

## Backend

```bash
cd backend
python -m pytest tests -q
python -m ruff check app tests
```

Coverage focus:

- domain pack loading,
- document ingestion and retrieval,
- structured diagnosis,
- NASA C-MAPSS expected RUL verification,
- workflow trace and eval endpoints,
- FastAPI endpoints,
- ticket creation.

## Frontend

```bash
cd frontend
npm run build
npm run test:e2e
```

Coverage focus:

- page render,
- signal panel,
- diagnosis replay,
- source visibility,
- ticket result visibility.

## Docker

```bash
docker compose config
docker compose up --build
```

Use the curl commands in `docs/demo-flow.md` for API smoke checks.

## Live OpenAI

Live OpenAI tests are gated:

```powershell
$env:OPENAI_LIVE_E2E='1'
$env:LIVE_API_URL='http://127.0.0.1:8122'
python -m pytest tests/test_live_workflow_openai_api.py -q
```

The live test requires:

- `ai_model == "gpt-5.4-nano"`
- `ai_usage.total_tokens > 0`
- trace includes `ai_diagnose`
- NASA validation passes
