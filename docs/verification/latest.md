# Verification Snapshot

Date: 2026-06-07

## Local Backend

```powershell
cd backend
python -m pytest tests -q
python -m ruff check app tests
```

Result:

```text
29 passed, 5 skipped, 1 warning
All checks passed!
```

## Local Frontend

```powershell
cd frontend
npm run build
npm run test:e2e
```

Result:

```text
vite build succeeded
1 passed, 1 skipped
```

Note:

```text
The default frontend e2e run keeps Docker-backed browser coverage gated behind LIVE_E2E=1.
```

## Docker Stack Rebuild

```powershell
docker compose up --build -d
docker compose ps
```

Result:

```text
backend, frontend, postgres, and qdrant containers rebuilt or restarted successfully
backend healthy on 127.0.0.1:8122
frontend available on 127.0.0.1:5173
```

## Docker Live Without OpenAI

Backend API:

```powershell
cd backend
$env:LIVE_E2E='1'
python -m pytest tests/test_live_e2e_api.py -q
```

Result:

```text
2 passed
```

Frontend browser:

```powershell
cd frontend
$env:LIVE_E2E='1'
npx playwright test e2e/signaltrace-live.spec.ts
```

Result:

```text
1 passed
```

Manual workflow proof:

```powershell
@'
import json, httpx
base='http://127.0.0.1:8122'
with httpx.Client(base_url=base, timeout=30.0) as client:
    ingest = client.post('/documents/ingest', json={'domain_id':'nasa_cmapss_turbofan'})
    workflow = client.post('/workflows/diagnose', json={
        'domain_id':'nasa_cmapss_turbofan',
        'system_id':'FD001-UNIT-001',
        'question':'Explain the cycle 31 health gate with evidence provenance.',
        'create_ticket': True,
    })
    print(json.dumps({
        'documents_indexed': ingest.json().get('documents_indexed'),
        'chunks_indexed': ingest.json().get('chunks_indexed'),
        'validation_passed': workflow.json().get('validation', {}).get('passed'),
        'source_types': sorted({item.get('source_type') for item in workflow.json().get('evidence', []) if item.get('source_type')}),
        'source_paths': [item.get('source_path') for item in workflow.json().get('evidence', [])[:3]],
        'source_authorities': sorted({item.get('source_authority') for item in workflow.json().get('evidence', []) if item.get('source_authority')}),
        'has_http_source_url': any(str(item.get('source_url', '')).startswith('http') for item in workflow.json().get('evidence', [])),
        'ticket_id': workflow.json().get('ticket', {}).get('id') if workflow.json().get('ticket') else None,
    }, indent=2))
'@ | python -
```

Result:

```text
{
  "documents_indexed": 3,
  "chunks_indexed": 29,
  "validation_passed": true,
  "source_types": [
    "nasa"
  ],
  "source_paths": [
    "documents/health_gate_policy.md",
    "documents/health_gate_policy.md",
    "documents/health_gate_policy.md"
  ],
  "source_authorities": [
    "nasa_official"
  ],
  "has_http_source_url": true,
  "ticket_id": 56
}
```

## GitHub Pages Build

```powershell
cd frontend
$env:GITHUB_PAGES='true'
npm run build
Select-String -Path dist\index.html -Pattern '/physical-systems-intelligence/'
```

Result:

```text
vite build succeeded
dist/index.html contains /physical-systems-intelligence/ asset paths
```

## Private Reference Scan

```powershell
rg -n --ignore-case -f private-banned-terms.txt README.md docs backend frontend docker-compose.yml .github
```

Result:

```text
no matches
```
