const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8122";

type Evidence = {
  source_path: string;
  title: string;
  section_title?: string;
  source_label?: string;
  source_url?: string;
  source_urls?: string[];
  source_authority?: string;
  source_type?: string;
  text: string;
  score: number;
  chunk_id?: string;
  retrieval_rank?: number;
  embedding_provider?: string;
};

type WorkflowApiResponse = {
  diagnosis: string;
  risk_level: "low" | "medium" | "high";
  situation: {
    scenario_name: string;
    trigger: string;
    physical_condition: string;
    decision_required: string;
    qdrant_role: string;
    signal_window: Array<Record<string, number>>;
    asset_type?: string;
    fault_mode?: string;
    operating_condition?: string;
  };
  evidence: Evidence[];
  recommended_actions: string[];
  trace: Array<{ step: string; summary: string }>;
  validation: {
    passed: boolean;
    expected?: { ground_truth_rul_cycles?: number; expected_failure_cycle?: number } | null;
  };
  expected_label?: { ground_truth_rul_cycles?: number; expected_failure_cycle?: number } | null;
  ticket?: { id: number; title: string; status: string } | null;
  ai_model: string | null;
  ai_usage: { input_tokens: number; output_tokens: number; total_tokens: number };
};

export type WorkflowUiResult = {
  diagnosis: string;
  riskLevel: "low" | "medium" | "high";
  situation: {
    scenarioName: string;
    trigger: string;
    physicalCondition: string;
    decisionRequired: string;
    qdrantRole: string;
    signalWindow: Array<Record<string, number>>;
    assetType?: string;
    faultMode?: string;
    operatingCondition?: string;
  };
  validation: {
    passed: boolean;
    expected: { groundTruthRul: number | null };
    expectedFailureCycle: number | null;
  };
  trace: Array<{ step: string; summary: string }>;
  sources: Array<{
    chunkId: string;
    path: string;
    title: string;
    sectionTitle: string;
    sourceLabel: string;
    sourceUrl: string;
    sourceUrls: string[];
    sourceAuthority: string;
    sourceType: string;
    excerpt: string;
    rank: number;
    provider: string;
    score: number;
  }>;
  actions: string[];
  ticket: { id: number; title: string; status: string } | null;
  usage: { model: string | null; inputTokens: number; outputTokens: number; totalTokens: number };
};

export async function runWorkflowDiagnosis(): Promise<WorkflowUiResult> {
  const workflow = await postJson<WorkflowApiResponse>("/workflows/diagnose", {
    domain_id: "nasa_cmapss_turbofan",
    system_id: "FD001-UNIT-001",
    question: "What is the engine health status and what should maintenance do?",
    create_ticket: true,
  });

  const expectedLabel = workflow.expected_label ?? workflow.validation.expected ?? null;

  return {
    diagnosis: workflow.diagnosis,
    riskLevel: workflow.risk_level,
    situation: {
      scenarioName: workflow.situation.scenario_name,
      trigger: workflow.situation.trigger,
      physicalCondition: workflow.situation.physical_condition,
      decisionRequired: workflow.situation.decision_required,
      qdrantRole: workflow.situation.qdrant_role,
      signalWindow: workflow.situation.signal_window,
      assetType: workflow.situation.asset_type,
      faultMode: workflow.situation.fault_mode,
      operatingCondition: workflow.situation.operating_condition,
    },
    validation: {
      passed: workflow.validation.passed,
      expected: {
        groundTruthRul: expectedLabel?.ground_truth_rul_cycles ?? null,
      },
      expectedFailureCycle: expectedLabel?.expected_failure_cycle ?? null,
    },
    trace: workflow.trace.map((event) => ({ step: event.step, summary: event.summary })),
    sources: workflow.evidence.map((item) => ({
      chunkId: item.chunk_id ?? "",
      path: item.source_path,
      title: item.title,
      sectionTitle: item.section_title ?? "",
      sourceLabel: item.source_label ?? "",
      sourceUrl: item.source_url ?? "",
      sourceUrls: item.source_urls ?? [],
      sourceAuthority: item.source_authority ?? "",
      sourceType: item.source_type ?? "",
      excerpt: item.text,
      rank: item.retrieval_rank ?? 0,
      provider: item.embedding_provider ?? "unknown",
      score: item.score,
    })),
    actions: workflow.recommended_actions,
    ticket: workflow.ticket ?? null,
    usage: {
      model: workflow.ai_model,
      inputTokens: workflow.ai_usage.input_tokens,
      outputTokens: workflow.ai_usage.output_tokens,
      totalTokens: workflow.ai_usage.total_tokens,
    },
  };
}

async function postJson<T = unknown>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`);
  }
  return (await response.json()) as T;
}
