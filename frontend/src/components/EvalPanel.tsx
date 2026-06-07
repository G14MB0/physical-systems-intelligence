import type { WorkflowUiResult } from "../services/api";

export function EvalPanel({ result }: { result: WorkflowUiResult }) {
  return (
    <>
      <h3>Actions</h3>
      <ul>
        {result.actions.map((action) => (
          <li key={action}>{action}</li>
        ))}
      </ul>
      <div className="usage">
        <strong>{result.usage.model ?? "deterministic"}</strong>
        <span>
          {result.usage.inputTokens} in / {result.usage.outputTokens} out /{" "}
          {result.usage.totalTokens} total tokens
        </span>
      </div>
    </>
  );
}
