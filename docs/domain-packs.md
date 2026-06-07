# Domain Packs

Domain packs make the system reusable without rewriting the backend.

## Structure

```text
backend/app/domains/<domain_id>/
  manifest.yaml
  documents/
  signals/
  prompts/
```

## Required Files

`manifest.yaml` defines:

- domain id,
- human name,
- description,
- primary system id,
- systems.

`signals/<system_id>.json` defines:

- current signal values,
- active events,
- severity.

`documents/*.md` defines:

- manuals,
- limits,
- troubleshooting guides,
- safety procedures.

`prompts/*.md` defines:

- domain-specific diagnostic policy.

## Add Another System Type

1. Copy `drone_inspection`.
2. Rename the domain id.
3. Replace documents.
4. Replace signal JSON.
5. Update prompts.
6. Run `POST /documents/ingest`.

No API changes are required.

## Included Packs

### `drone_inspection`

Pseudoreal operational demo with bridge-inspection drone telemetry, maintenance manual, operating limits, and ticket action.

### `nasa_cmapss_turbofan`

Real reference benchmark based on NASA C-MAPSS FD001. The included micro-sample uses FD001 test unit 1 final observed cycle and the published `RUL_FD001.txt` first label:

- observed cycles: `31`
- ground-truth RUL: `112`
- expected failure cycle: `143`

Use this pack for functional verification against real documentation, real data rows, and a real expected value.
