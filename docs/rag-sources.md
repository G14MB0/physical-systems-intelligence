# RAG Sources

Current NASA demo corpus is repo-pinned in
`backend/app/domains/nasa_cmapss_turbofan/documents/` as long-form Markdown
adaptations for deterministic local ingestion. Each file keeps provenance
metadata in its front matter and is indexed with section-aware chunking plus
overlap windows for long sections.

## Corpus Inventory

### NASA C-MAPSS and FD001 Reference

- Local file:
  `backend/app/domains/nasa_cmapss_turbofan/documents/cmapss_reference.md`
- Source label: `NASA DASHlink and NASA NTRS`
- Purpose / role:
  baseline reference for C-MAPSS dataset purpose, FD001 structure, operating
  condition framing, degradation semantics, and remaining useful life meaning.
- Source authority: `nasa_official`
- Source type surfaced by runtime: `nasa`
- Source URLs:
  - `https://c3.ndc.nasa.gov/dashlink/resources/139/`
  - `https://c3.ndc.nasa.gov/dashlink/resources/14/`
  - `https://ntrs.nasa.gov/api/citations/20120007104/downloads/20120007104.pdf`
  - `https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf`

### FD001 Health Gate Framing

- Local file:
  `backend/app/domains/nasa_cmapss_turbofan/documents/health_gate_policy.md`
- Source label: `NASA DASHlink, NASA NTRS, and repo-pinned FD001 micro-sample`
- Purpose / role:
  explains why cycle 31 is replayed as autonomous health-gate trigger, how
  observed-cycle and failure-cycle semantics differ, and where repo policy text
  begins after NASA source facts.
- Source authority: `nasa_official`
- Source type surfaced by runtime: `nasa`
- Source URLs:
  - `https://c3.ndc.nasa.gov/dashlink/resources/14/`
  - `https://c3.ndc.nasa.gov/dashlink/resources/139/`
  - `https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf`

### FD001 Signal Window and Watchlist Context

- Local file:
  `backend/app/domains/nasa_cmapss_turbofan/documents/sensor_watchlist.md`
- Source label: `NASA run-to-failure and C-MAPSS source adaptations`
- Purpose / role:
  explains how repo narrows larger NASA signal space into cycle-27-to-31 replay
  window and five-channel watchlist while keeping remaining useful life
  semantics separate from displayed measurements.
- Source authority: `nasa_official`
- Source type surfaced by runtime: `nasa`
- Source URLs:
  - `https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf`
  - `https://c3.ndc.nasa.gov/dashlink/resources/14/`
  - `https://ntrs.nasa.gov/api/citations/20120007104/downloads/20120007104.pdf`

## What Retrieval Now Proves

- source text is pinned in repo, not fetched at runtime
- every evidence item can point back to source label, primary URL, related URLs,
  authority, type, and section title
- long sections are indexed as overlapping windows, so retrieval can return
  precise excerpts without dropping long-form NASA context
