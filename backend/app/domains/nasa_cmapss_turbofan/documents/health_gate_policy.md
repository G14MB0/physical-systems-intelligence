---
title: FD001 Health Gate Framing
source_label: NASA DASHlink, NASA NTRS, and repo-pinned FD001 micro-sample
source_url: https://c3.ndc.nasa.gov/dashlink/resources/14/
source_urls:
  - https://c3.ndc.nasa.gov/dashlink/resources/14/
  - https://c3.ndc.nasa.gov/dashlink/resources/139/
  - https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf
source_authority: nasa_official
source_type: curated_reference
accessed_on: 2026-06-07
transformation_notes: Curated policy-style adaptation grounded in official NASA explanations of C-MAPSS degradation, prognostics data needs, and run-to-failure semantics, then narrowed to this repository's FD001 unit-1 replay at cycle 31. Repo-local decision language is interpretive framing for demo use, not verbatim NASA operating policy.
---

# FD001 Health Gate Framing

This document explains why local demo stops at cycle 31 and why that moment is treated as a health gate instead of arbitrary benchmark question prompt. NASA sources define run-to-failure and remaining-life semantics; repository then pins one last-observed-cycle snapshot to create deterministic operational replay.

## Why a health gate fits C-MAPSS

NASA's prognostics material is built around progression of damage over time, not around isolated alarm code lookup. The source publications discuss estimating degradation, tracking health indicators, and reasoning about remaining life from sensor histories. That makes a gate at end of observed telemetry window a faithful framing for demo: system has accumulated evidence up to one cycle boundary and now must decide what that evidence means before next cycle arrives.

## Why cycle 31 is chosen here

Cycle 31 is not a universal NASA threshold. It is repository's pinned last observed cycle for FD001 test unit 1. Local signal payload includes final five observed rows ending at cycle 31, and local expected-label file preserves NASA ground-truth RUL value for that same unit. Using cycle 31 lets the demo start from fully fixed evidence package: known telemetry window, known benchmark identity, and known post-hoc RUL label for validation.

## What happens after cycle 31 in benchmark terms

At cycle 31, benchmark observer has not yet seen failure. NASA benchmark semantics say the test trajectory is truncated before end of life. The published label says how many additional cycles remain beyond that last row. In this repo's pinned example, that remaining-life label is preserved separately in local validation artifacts. Health gate therefore sits at point where evidence is incomplete in time but complete enough to require interpretation.

## Why this is still operationally meaningful

NASA's real-flight run-to-failure paper argues that prognostics datasets are useful when they connect multivariate observations to future end-of-life outcomes. A decision point before actual failure is exactly where operator value lives. In real operations, teams do not wait for full failure trajectory to complete. They evaluate latest available telemetry, compare it with degradation knowledge, and decide whether continued monitoring is enough or whether maintenance planning must start.

## Connection to gradual compressor degradation

The repo domain frames this FD001 pack around gradual compressor-related deterioration. NASA sources support the broader mechanics behind that framing by describing degradation through component efficiency and flow-capacity changes, and by noting that the high-pressure compressor can be among the more rapidly degrading components in realistic fleet simulations. The narrower statement that this local replay is specifically compressor-centered is repo framing for this benchmark pack.

## Difference between NASA source facts and repo policy text

NASA sources provide benchmark structure, degradation modeling concepts, and RUL semantics. They do not prescribe exact local action text such as "open maintenance review now." That wording is repo-level framing added so the autonomous replay can produce traceable decisions. The factual core remains source-backed: observed cycle count, remaining-life semantics, and projected-failure semantics, while the exact maintenance-review posture is local interpretation.

## What decision this demo is actually making

The demo decision is modest. It is not claiming certified maintenance prognosis from five rows alone. It is deciding whether current evidence package should stay in monitoring mode or be escalated into review with attached provenance. That matches the product story captured elsewhere in repo: telemetry window closed, physical condition summarized, documentation retrieved, decision required, and ticket-ready explanation produced.

## Evidence fields worth carrying with gate result

A useful gate result should preserve at least these benchmark facts:

- dataset and unit identity
- last observed cycle
- ground-truth remaining cycles when available for validation
- projected failure cycle derived from observed plus remaining
- operating-condition summary
- fault-mode summary
- source provenance for retrieved NASA documentation

These fields let user distinguish model interpretation from benchmark ground truth and make later audits easier.
