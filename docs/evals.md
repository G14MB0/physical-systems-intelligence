# Evals

The MVP includes one real expected-label eval based on NASA C-MAPSS FD001 unit 1.

## Case

```text
domain_id: nasa_cmapss_turbofan
system_id: FD001-UNIT-001
observed_cycles: 31
ground_truth_rul_cycles: 112
expected_failure_cycle: 143
```

Expected label file:

```text
backend/app/domains/nasa_cmapss_turbofan/evals/FD001-UNIT-001.expected.json
```

## API

```bash
curl -X POST http://localhost:8122/evals/nasa-cmapss/fd001-unit-001
```

The eval passes only when:

- the expected RUL label is present,
- the expected failure cycle matches,
- retrieved evidence includes the C-MAPSS reference document.
