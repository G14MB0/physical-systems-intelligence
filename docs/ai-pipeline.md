# AI Pipeline

SignalTrace Runtime executes a traceable diagnostic workflow:

```text
load_signals -> retrieve_docs -> compute_baseline -> ai_diagnose -> validate_expected -> create_ticket
```

## Steps

- `load_signals`: reads the domain signal snapshot for the physical asset.
- `retrieve_docs`: indexes and searches technical documentation through the configured vector store.
- `compute_baseline`: creates deterministic risk, diagnosis, evidence, and actions.
- `ai_diagnose`: optionally calls OpenAI Responses API with `gpt-5.4-nano` and structured JSON output.
- `validate_expected`: compares the run against the domain expected label.
- `create_ticket`: persists an operational action ticket.

## Retrieval

The backend supports these embedding providers:

- `hash`: deterministic local test provider.
- `fastembed`: public Docker default for local semantic embeddings.
- `openai`: optional OpenAI embeddings provider.

Diagnosis generation uses `gpt-5.4-nano` when `OPENAI_DIAGNOSTICS_ENABLED=true`.

## Auditability

Workflow responses include:

- `run_id`
- `trace`
- `evidence`
- `validation`
- `ticket`
- `ai_model`
- `ai_usage`

Runs are persisted and can be reloaded through:

```text
GET /workflows/runs
GET /workflows/runs/{run_id}
```
