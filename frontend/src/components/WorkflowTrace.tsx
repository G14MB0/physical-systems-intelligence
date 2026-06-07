import { Activity, CheckCircle2 } from "lucide-react";
import type { WorkflowUiResult } from "../services/api";

export function WorkflowTrace({
  result,
  pendingTrace,
  status,
}: {
  result: WorkflowUiResult | null;
  pendingTrace: WorkflowUiResult["trace"];
  status: "idle" | "running" | "fallback";
}) {
  const trace = result?.trace ?? pendingTrace;
  const isRunning = status === "running";

  return (
    <article className="card trace-card">
      <div className="card-heading">
        <Activity size={20} />
        <span>Workflow execution trace</span>
      </div>
      {trace.length === 0 ? (
        <p className="empty-state">
          {isRunning ? "Workflow running..." : "Run SignalTrace to generate the live trace."}
        </p>
      ) : (
        <div className="trace-list animate-fade-in">
          {trace.map((event, idx) => {
            const isActive = idx === trace.length - 1 && isRunning;
            return (
              <div className={`trace-row ${isActive ? "active" : ""}`} key={event.step}>
                <CheckCircle2 size={18} />
                <div className="trace-row-content">
                  <strong>{event.step}</strong>
                  <span>{event.summary}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
