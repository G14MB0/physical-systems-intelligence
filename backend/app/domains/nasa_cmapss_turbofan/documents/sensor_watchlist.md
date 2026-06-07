---
title: FD001 Signal Window and Watchlist Context
source_label: NASA run-to-failure and C-MAPSS source adaptations
source_url: https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf
source_urls:
  - https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf
  - https://c3.ndc.nasa.gov/dashlink/resources/14/
  - https://ntrs.nasa.gov/api/citations/20120007104/downloads/20120007104.pdf
source_authority: nasa_official
source_type: curated_reference
accessed_on: 2026-06-07
transformation_notes: Plain-text adaptation from NASA material describing C-MAPSS variables, flight-conditioned run-to-failure trajectories, and health modeling. The specific five-channel watchlist and cycle-27-to-31 window are repo-local curation of included FD001 micro-sample for deterministic replay, not full NASA variable set.
---

# FD001 Signal Window and Watchlist Context

NASA sources make clear that prognostics work depends on multivariate operating traces, not only final labels. This file explains how local replay narrows that larger signal space into small auditable watchlist while staying anchored to benchmark semantics.

## C-MAPSS has more than one kind of variable

NASA's real-flight run-to-failure document separates scenario descriptors from measurements and virtual sensors. Examples include altitude, Mach number, throttle-resolver angle, temperatures, pressures, and rotating-speed related measurements. The benchmark is therefore rich enough to support both operating-context questions and degradation questions.

## Why local demo shows only last observed window

DASHlink's degradation-data writeup says one measurement snapshot per flight was sufficient in that simulation framing because degradation from wear and tear is gradual rather than sudden within a single flight. The local replay borrows only the high-level motivation from that idea: because degradation is gradual, the UI can present a compact recent window for operator context instead of full history. That compaction choice is repo design, not NASA guidance about exact window size.

## Why five rows are enough for demo framing

The repository keeps a short recent slice for unit 1 so user can see immediate lead-in to the local gate cycle. This does not replace full trajectory for modeling work. It gives compact operational context around last observed state while benchmark documents and expected-label metadata provide longer-horizon interpretation.

## Why these five channels were selected

The local watchlist uses sensor 2, sensor 3, sensor 4, sensor 11, and sensor 15 from included micro-sample. NASA source material supports using simulated sensor outputs to characterize fault evolution, but it does not declare this exact five-channel subset as canonical FD001 watchlist. This subset is a repo compaction choice inspired by gradual-degradation framing and by the need to keep replay readable while still exposing several changing measurements near the decision point.

## How sensor view relates to health parameters

NASA's technical memorandum says gradual degradation in C-MAPSS is represented through efficiency and flow-capacity modifiers for each module. The watchlist values are therefore indirect evidence, not direct health modifiers. Operators or downstream models infer likely health state by comparing observed measurement behavior with known degradation context, especially compressor-related deterioration in this FD001 framing.

## What remaining useful life is not

Remaining useful life is not sensor 15, not single pressure value, and not one threshold crossing in displayed rows. It is future-cycle label defined relative to last observed cycle. NASA benchmark separates measurement history from end-of-life target. The watchlist helps explain present condition; the RUL label explains how much simulated life remained after that present condition.

## Why real-flight paper still helps this benchmark corpus

The 2020 NASA run-to-failure paper uses C-MAPSS under realistic flight conditions and describes altitude, Mach, throttle, and many measured variables across run-to-failure trajectories. Although repo demo uses classic FD001 subset rather than that newer dataset, the paper reinforces same retrieval themes: trajectories are multivariate, degradation unfolds over use history, and end-of-life semantics belong to future portion of trajectory not yet observed.

## What user should infer from cycle-31 window

User should infer that engine has reached latest available observed condition under known benchmark scenario, and system now needs source-backed context before deciding next action. User should not infer that five displayed rows alone prove certified maintenance action. They are compact evidence slice paired with NASA benchmark semantics, retrieved documents, and repo-pinned validation labels.
