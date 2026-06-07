# Demo Flow

This demo recreates a production-style autonomous health gate. In production, the
workflow would be triggered when an asset closes a telemetry window. In the demo,
the button or curl command manually starts the exact same workflow for the cycle
31 telemetry event.

Scenario:

- asset: NASA C-MAPSS FD001 turbofan unit 1,
- trigger: cycle 31 telemetry window closed,
- condition: known high-pressure-compressor degradation context,
- decision: keep monitoring or open a maintenance review,
- action: retrieve domain docs from Qdrant, run diagnosis, validate RUL 112, and
  create a ticket.

## 1. Start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:5173`.

## 2. Primary System

The public demo shows `NASA C-MAPSS FD001 Unit 1`.

Known benchmark values:

- observed cycles: `31`
- ground-truth RUL: `112`
- expected failure cycle: `143`

## 3. Run SignalTrace

```bash
curl -X POST http://localhost:8122/workflows/diagnose \
  -H "Content-Type: application/json" \
  -d "{\"domain_id\":\"nasa_cmapss_turbofan\",\"system_id\":\"FD001-UNIT-001\",\"question\":\"What is the engine health status and what should maintenance do?\",\"create_ticket\":true}"
```

Expected behavior:

- returns `run_id`,
- loads current signals,
- retrieves NASA C-MAPSS reference chunks,
- computes baseline diagnosis,
- optionally calls `gpt-5.4-nano`,
- validates expected label `112` and `143`,
- creates one ticket,
- returns a complete trace.

## 4. Run Eval Directly

```bash
curl -X POST http://localhost:8122/evals/nasa-cmapss/fd001-unit-001
```

Expected behavior:

- `passed = true`,
- expected RUL is `112`,
- expected failure cycle is `143`,
- evidence includes `cmapss_reference.md`.

## 5. Secondary Domain Pack

The drone pack remains as a second example of domain-pack reuse:

```bash
curl -X POST http://localhost:8122/agent/diagnose \
  -H "Content-Type: application/json" \
  -d "{\"domain_id\":\"drone_inspection\",\"system_id\":\"DRN-INSPECT-01\",\"question\":\"Battery sag and ESC temperature warning during bridge inspection. What should I do?\"}"
```
