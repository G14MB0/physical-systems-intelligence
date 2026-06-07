import { expect, test } from "@playwright/test";

test("docker frontend runs SignalTrace workflow through live backend", async ({ page }) => {
  test.skip(!process.env.LIVE_E2E, "Set LIVE_E2E=1 for Docker-backed e2e");

  await page.goto(process.env.LIVE_FRONTEND_URL ?? "http://127.0.0.1:5173");
  const workflowResponse = page.waitForResponse((response) =>
    response.url().includes("/workflows/diagnose") && response.status() === 200,
  );

  await page.getByRole("button", { name: /Run SignalTrace/i }).click();
  const workflow = await workflowResponse;

  const workflowPayload = await workflow.json();
  expect(workflowPayload.validation.passed).toBe(true);
  expect(workflowPayload.expected_label.ground_truth_rul_cycles).toBe(112);
  const firstEvidence = workflowPayload.evidence[0] as {
    source_label?: string;
    title?: string;
    source_url?: string;
    retrieval_rank?: number;
  };
  if (workflowPayload.ai_model) {
    expect(workflowPayload.ai_model).toBe("gpt-5.4-nano");
    expect(workflowPayload.ai_usage.total_tokens).toBeGreaterThan(0);
    await expect(page.getByText("gpt-5.4-nano")).toBeVisible();
    await expect(page.getByText(/total tokens/)).toBeVisible();
  }
  expect(workflowPayload.evidence.length).toBeGreaterThan(0);
  expect(
    workflowPayload.evidence.some(
      (item: {
        source_path?: string;
        source_label?: string;
        source_url?: string;
        source_authority?: string;
      }) =>
      typeof item.source_path === "string" &&
        item.source_path.startsWith("documents/") &&
        typeof item.source_label === "string" &&
        item.source_label.length > 0 &&
        typeof item.source_url === "string" &&
        item.source_url.startsWith("http") &&
        item.source_authority === "nasa_official",
    ),
  ).toBe(true);
  await expect(page.getByText("validate_expected")).toBeVisible();
  if (firstEvidence.source_label) {
    await expect(page.getByText(firstEvidence.source_label).first()).toBeVisible();
  }
  if (firstEvidence.title) {
    await expect(page.getByText(firstEvidence.title).first()).toBeVisible();
  }
  if (firstEvidence.source_url) {
    const sourceHost = new URL(firstEvidence.source_url).hostname.replace(/^www\./, "");
    await expect(page.getByRole("link", { name: sourceHost }).first()).toBeVisible();
  }
  if (firstEvidence.retrieval_rank) {
    await expect(page.getByText(`rank ${firstEvidence.retrieval_rank}`)).toBeVisible();
  }
  await expect(page.getByText("nasa_official").first()).toBeVisible();
  await expect(page.getByText("Ticket PSI-")).toBeVisible();
  await expect(page.getByText("Backend unavailable")).toHaveCount(0);
});
