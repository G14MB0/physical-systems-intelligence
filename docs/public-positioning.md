# Public Positioning

## Name

Physical Systems Intelligence

## Demo Module

SignalTrace Runtime

## Position

Physical Systems Intelligence is a reusable AI runtime for physical assets. It connects telemetry snapshots, technical documentation, maintenance policy, AI reasoning, expected-label validation, and action tickets.

The target domains are machines, electrical systems, infrastructure, robotics, lab instruments, and test rigs. A domain pack swaps the asset documentation, signal schema, sample telemetry, and prompt policy while keeping the same runtime.

## Primary Proof Case

The public demo should lead with NASA C-MAPSS FD001, unit 1:

- observed cycles: 31
- published ground-truth RUL: 112
- expected failure cycle: 143
- source: NASA C-MAPSS `RUL_FD001` first row

This is stronger than a synthetic drone case because it gives the runtime a real labelled benchmark to validate against.

## What To Claim

- The project demonstrates a traceable AI diagnostic workflow.
- The runtime retrieves technical evidence before asking AI for structured diagnosis.
- The workflow can validate a known real benchmark label.
- The same core can be reused across physical domains by changing domain packs.

## What Not To Claim

- Do not claim a trained prognostic model.
- Do not claim production readiness.
- Do not claim live PLC, SCADA, MES, ERP, or fleet integration.
- Do not claim autonomous control.
- Do not mention or imitate private target companies or vendor product names.
