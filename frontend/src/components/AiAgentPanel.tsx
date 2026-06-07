import { Bot, ArrowRight, ShieldAlert, CheckCircle2, Ticket, Cpu } from "lucide-react";
import type { WorkflowUiResult } from "../services/api";

interface AiAgentPanelProps {
  result: WorkflowUiResult | null;
  status: "idle" | "running" | "fallback";
  onRun: () => void;
}

export function AiAgentPanel({ result, status, onRun }: AiAgentPanelProps) {
  const isRunning = status === "running";

  const getRiskBadge = (level: "low" | "medium" | "high") => {
    const colors = {
      low: { bg: "#e6f4ea", text: "#137333", label: "Low Risk" },
      medium: { bg: "#fef7e0", text: "#b06000", label: "Moderate Risk" },
      high: { bg: "#fce8e6", text: "#c5221f", label: "High Risk" },
    };
    const current = colors[level] || colors.low;
    return (
      <span
        style={{
          backgroundColor: current.bg,
          color: current.text,
          padding: "0.25rem 0.6rem",
          borderRadius: "999px",
          fontWeight: 700,
          fontSize: "0.75rem",
          display: "inline-flex",
          alignItems: "center",
          gap: "0.25rem",
        }}
      >
        <ShieldAlert size={12} />
        {current.label}
      </span>
    );
  };

  return (
    <article className="card agent-panel">
      <div className="card-heading agent-header">
        <div className="agent-avatar">
          <Bot size={22} />
          <span className="pulse-dot"></span>
        </div>
        <div>
          <h3>PSI Agent Assistant</h3>
          <span className="agent-status">
            {isRunning ? "Analyzing system state..." : result ? "Analysis complete" : "System Standby"}
          </span>
        </div>
      </div>

      {!result && !isRunning && (
        <div className="agent-standby">
          <p className="standby-text">
            Telemetry stream is active. Trigger an autonomous analysis cycle to diagnose asset conditions and generate recommendation tickets.
          </p>
          <button className="primary-link run-button-full" onClick={onRun}>
            Run SignalTrace
            <ArrowRight size={18} />
          </button>
        </div>
      )}

      {isRunning && (
        <div className="agent-thinking">
          <div className="loader-ring"></div>
          <p>Analyzing turbofan signals and scanning Qdrant documentation...</p>
        </div>
      )}

      {result && !isRunning && (
        <div className="agent-findings">
          <div className="findings-meta">
            {getRiskBadge(result.riskLevel)}
            <span className="model-badge">
              <Cpu size={12} />
              AI Agent Active
            </span>
          </div>

          <div className="proposal-box">
            <h4 className="proposal-title">Proposed Decision</h4>
            <p className="proposal-desc">{result.situation.decisionRequired}</p>

            {result.ticket && (
              <div className="ticket-action-box">
                <div className="ticket-info">
                  <Ticket size={16} />
                  <div>
                    <strong>Ticket PSI-{result.ticket.id}</strong>
                    <span>{result.ticket.title}</span>
                  </div>
                </div>
                <div className="ticket-status-tag">
                  {result.ticket.status.toUpperCase()}
                </div>
              </div>
            )}

            <div className="proposed-actions">
              <strong>Recommended Actions:</strong>
              <ul>
                {result.actions.map((action, idx) => (
                  <li key={idx} className="action-li">
                    <CheckCircle2 size={14} className="action-check-icon" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="agent-actions">
            <button className="agent-btn approve-btn" onClick={() => alert("Maintenance ticket approved and sent to maintenance management system (MES).")}>
              Approve Recommendation
            </button>
            <button className="agent-btn re-run-btn" onClick={onRun}>
              Run SignalTrace
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
