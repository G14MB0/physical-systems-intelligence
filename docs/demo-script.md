# Demo Script

## Browser Demo

1. Open the frontend.
2. Confirm the first viewport shows `Physical Systems Intelligence`, `SignalTrace Runtime`, and `NASA C-MAPSS FD001 Unit 1`.
3. Click `Run SignalTrace`.
4. Watch the workflow trace complete:
   `load_signals`, `retrieve_docs`, `compute_baseline`, `ai_diagnose`, `validate_expected`, `create_ticket`.
5. Point out the real benchmark values:
   `31` observed cycles, `112` ground-truth RUL, `143` expected failure cycle.
6. Show evidence, AI token usage when enabled, and the created ticket.

## API Demo

```bash
curl -X POST http://localhost:8122/workflows/diagnose \
  -H "Content-Type: application/json" \
  -d "{\"domain_id\":\"nasa_cmapss_turbofan\",\"system_id\":\"FD001-UNIT-001\",\"question\":\"What is the engine health status and what should maintenance do?\",\"create_ticket\":true}"
```
