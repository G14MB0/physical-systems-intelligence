import { expect, test } from "@playwright/test";

test("renders NASA SignalTrace workflow replay", async ({ page }) => {
  let releaseApi!: () => void;
  const apiGate = new Promise<void>((resolve) => {
    releaseApi = resolve;
  });
  await page.route("**/workflows/diagnose", async (route) => {
    await apiGate;
    await route.fulfill({
      json: {
        run_id: "run-test",
        domain_id: "nasa_cmapss_turbofan",
        system_id: "FD001-UNIT-001",
        question: "What is the engine health status and what should maintenance do?",
        diagnosis:
          "Risk is low. FD001 unit 1 has 31 observed cycles and NASA ground-truth RUL is 112 cycles.",
        risk_level: "low",
        evidence: [
          {
            source_path: "documents/cmapss_reference.md",
            title: "NASA C-MAPSS and FD001 Reference",
            section_title: "Remaining useful life meaning",
            source_label: "NASA DASHlink and NASA NTRS",
            source_url: "https://c3.ndc.nasa.gov/dashlink/resources/139/",
            source_urls: [
              "https://c3.ndc.nasa.gov/dashlink/resources/139/",
              "https://c3.ndc.nasa.gov/dashlink/resources/14/",
              "https://ntrs.nasa.gov/api/citations/20120007104/downloads/20120007104.pdf",
              "https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf",
            ],
            source_authority: "nasa_official",
            source_type: "nasa",
            text: "Remaining useful life is remaining cycles from last observed point until simulated failure, and FD001 labels keep that meaning for each test trajectory.",
            score: 1.4,
            chunk_id: "cmapss-reference-rul-1",
            retrieval_rank: 1,
            embedding_provider: "hash",
          },
          {
            source_path: "documents/health_gate_policy.md",
            title: "FD001 Health Gate Framing",
            section_title: "Evidence fields worth carrying with gate result",
            source_label: "NASA DASHlink, NASA NTRS, and repo-pinned FD001 micro-sample",
            source_url: "https://c3.ndc.nasa.gov/dashlink/resources/14/",
            source_urls: [
              "https://c3.ndc.nasa.gov/dashlink/resources/14/",
              "https://c3.ndc.nasa.gov/dashlink/resources/139/",
              "https://ntrs.nasa.gov/api/citations/20205001125/downloads/Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf",
            ],
            source_authority: "nasa_official",
            source_type: "nasa",
            text: "Health-gate replay should carry source label, canonical URL, and section context so operational decisions stay auditable instead of benchmark-only.",
            score: 1.1,
            chunk_id: "health-gate-policy-1",
            retrieval_rank: 2,
            embedding_provider: "hash",
          },
        ],
        recommended_actions: ["Use NASA ground truth RUL of 112 cycles as the verification target."],
        situation: {
          scenario_name: "Autonomous turbofan health gate replay",
          trigger: "Cycle 31 telemetry window closed",
          physical_condition: "FD001 unit 1 has completed its latest observed cycle under known HPC degradation conditions.",
          decision_required: "Decide whether to keep monitoring or open a maintenance review.",
          qdrant_role: "Retrieve operating context, RUL semantics, and maintenance policy from domain documents with source-backed provenance.",
          signal_window: [
            { cycle: 27, sensor_2: 642.08, sensor_3: 1586.65, sensor_4: 1400.31, sensor_11: 47.34, sensor_15: 8.4494 },
            { cycle: 28, sensor_2: 641.93, sensor_3: 1594.25, sensor_4: 1401.29, sensor_11: 47.05, sensor_15: 8.4470 },
            { cycle: 29, sensor_2: 641.95, sensor_3: 1587.15, sensor_4: 1398.11, sensor_11: 47.42, sensor_15: 8.4212 },
            { cycle: 30, sensor_2: 642.79, sensor_3: 1585.72, sensor_4: 1400.97, sensor_11: 47.40, sensor_15: 8.4110 },
            { cycle: 31, sensor_2: 642.58, sensor_3: 1581.22, sensor_4: 1398.91, sensor_11: 47.23, sensor_15: 8.4024 },
          ],
        },
        trace: [
          { step: "load_signals", status: "completed", summary: "Loaded signals.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
          { step: "retrieve_docs", status: "completed", summary: "Retrieved evidence.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
          { step: "compute_baseline", status: "completed", summary: "Computed baseline.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
          { step: "ai_diagnose", status: "completed", summary: "AI disabled in test.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
          { step: "validate_expected", status: "completed", summary: "Validated expected label.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
          { step: "create_ticket", status: "completed", summary: "Created ticket.", started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:00Z", payload: {} },
        ],
        validation: {
          passed: true,
          expected: { ground_truth_rul_cycles: 112, expected_failure_cycle: 143 },
          observed: { ground_truth_rul_cycles: 112, expected_failure_cycle: 143 },
          checks: [],
        },
        expected_label: { ground_truth_rul_cycles: 112, expected_failure_cycle: 143 },
        ticket: {
          id: 1007,
          title: "Review FD001-UNIT-001 diagnostic run",
          status: "open",
        },
        ai_model: "gpt-5.4-nano",
        ai_usage: { input_tokens: 609, output_tokens: 503, total_tokens: 1112 },
      },
    });
  });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Physical Systems Intelligence" })).toBeVisible();
  await expect(page.getByText("Autonomous trigger replay", { exact: true })).toBeVisible();
  await expect(page.getByText("NASA C-MAPSS FD001 Unit 1").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Autonomous health gate replay" })).toBeVisible();
  await expect(page.getByText("Cycle 31 telemetry window closed")).toBeVisible();
  await expect(page.getByText("ground-truth RUL", { exact: true })).toBeVisible();
  await expect(page.getByText("validate_expected")).toHaveCount(0);

  await page.getByRole("button", { name: /Run SignalTrace/i }).click();

  await expect(page.getByText("load_signals")).toBeVisible();
  await expect(page.getByText("Loading FD001 unit 1 telemetry snapshot.")).toBeVisible();
  await expect(page.getByText("validate_expected")).toHaveCount(0);
  await expect(page.getByText("Risk is low")).toHaveCount(0);
  releaseApi();

  await expect(page.getByText("Risk is low")).toBeVisible();
  await expect(page.getByText(/source-backed provenance/)).toBeVisible();
  await expect(page.getByText(/RUL semantics/)).toBeVisible();
  await expect(page.getByText("NASA DASHlink and NASA NTRS")).toBeVisible();
  await expect(page.getByText("NASA C-MAPSS and FD001 Reference")).toBeVisible();
  await expect(page.getByText("Remaining useful life meaning")).toBeVisible();
  await expect(page.getByRole("link", { name: "c3.ndc.nasa.gov" }).first()).toBeVisible();
  await expect(page.getByText("rank 1")).toBeVisible();
  await expect(page.getByText("hash").first()).toBeVisible();
  await expect(page.getByText("score 1.40")).toBeVisible();
  await expect(page.getByText("nasa_official").first()).toBeVisible();
  await expect(page.getByText("+3 related sources")).toBeVisible();
  await expect(page.getByText("NASA DASHlink, NASA NTRS, and repo-pinned FD001 micro-sample")).toBeVisible();
  await expect(page.getByText("FD001 Health Gate Framing")).toBeVisible();
  await expect(page.getByText("Evidence fields worth carrying with gate result")).toBeVisible();
  await expect(page.getByRole("link", { name: "c3.ndc.nasa.gov" }).nth(1)).toBeVisible();
  await expect(page.getByText("rank 2")).toBeVisible();
  await expect(page.getByText("score 1.10")).toBeVisible();
  await expect(page.getByText("+2 related sources")).toBeVisible();
  await expect(page.getByText("sensor 15").first()).toBeVisible();
  await expect(page.getByText("validate_expected")).toBeVisible();
  await expect(page.getByText("gpt-5.4-nano")).toBeVisible();
  await expect(page.getByText("Ticket PSI-1007")).toBeVisible();
});
