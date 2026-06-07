import { EvidencePanel } from "./EvidencePanel";
import { TelemetryPanel } from "./TelemetryPanel";
import { WorkflowTrace } from "./WorkflowTrace";
import { AiAgentPanel } from "./AiAgentPanel";
import type { WorkflowUiResult } from "../services/api";

export function SignalTraceConsole({
  result,
  pendingTrace,
  status,
  onRun,
}: {
  result: WorkflowUiResult | null;
  pendingTrace: WorkflowUiResult["trace"];
  status: "idle" | "running" | "fallback";
  onRun: () => void;
}) {
  return (
    <section id="signaltrace" className="dashboard-grid">
      <div className="dashboard-col-left">
        <AiAgentPanel result={result} status={status} onRun={onRun} />
        <WorkflowTrace result={result} pendingTrace={pendingTrace} status={status} />
      </div>
      <div className="dashboard-col-right">
        <TelemetryPanel result={result} />
        <EvidencePanel result={result} />
      </div>
    </section>
  );
}
