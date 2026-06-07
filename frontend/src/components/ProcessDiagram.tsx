import { useState } from "react";
import { Cpu, Database, Gauge, Bot, ClipboardCheck } from "lucide-react";

interface Stage {
  id: string;
  label: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  tech: string;
}

const STAGES: Stage[] = [
  {
    id: "telemetry",
    label: "1. Telemetry Ingest",
    icon: <Gauge size={20} />,
    title: "Asset Telemetry Event",
    description: "FD001 unit 1 closes a telemetry window at Cycle 31 under known HPC degradation.",
    color: "#0041d0",
    tech: "FastAPI / telemetry stream",
  },
  {
    id: "retrieval",
    label: "2. Qdrant Retrieval",
    icon: <Database size={20} />,
    title: "Contextual RAG Retrieval",
    description: "Qdrant retrieves relevant NASA DASHlink and NTRS document chunks matching the operating situation.",
    color: "#ff0072",
    tech: "Qdrant / local embeddings",
  },
  {
    id: "baseline",
    label: "3. RUL Baseline",
    icon: <Cpu size={20} />,
    title: "Deterministic Baseline",
    description: "Calculates expected failure cycle and validates expected remaining useful life (RUL 112).",
    color: "#8b5cf6",
    tech: "Python math engine",
  },
  {
    id: "ai",
    label: "4. AI Diagnosis",
    icon: <Bot size={20} />,
    title: "Structured LLM Diagnosis",
    description: "Structured analysis of telemetry trends and retrieved references to produce grounded decision guidance.",
    color: "#10b981",
    tech: "GPT-5.4-nano / OpenAI SDK",
  },
  {
    id: "ticket",
    label: "5. Persistent Action",
    icon: <ClipboardCheck size={20} />,
    title: "Operational Action Ticket",
    description: "Persists workflow execution trace and opens a review ticket in PostgreSQL to trigger human verification.",
    color: "#f59e0b",
    tech: "PostgreSQL / DB agent",
  },
];

export function ProcessDiagram() {
  const [activeStage, setActiveStage] = useState<string>("telemetry");

  const currentStage = STAGES.find((s) => s.id === activeStage) || STAGES[0];

  return (
    <div className="process-diagram-container">
      <div className="svg-wrapper">
        <svg viewBox="0 0 800 120" className="process-svg" width="100%" height="100%">
          <defs>
            <linearGradient id="grad-telemetry-retrieval" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0041d0" />
              <stop offset="100%" stopColor="#ff0072" />
            </linearGradient>
            <linearGradient id="grad-retrieval-baseline" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff0072" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
            <linearGradient id="grad-baseline-ai" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
            <linearGradient id="grad-ai-ticket" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#f59e0b" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Connection Lines */}
          <line x1="120" y1="60" x2="240" y2="60" stroke="url(#grad-telemetry-retrieval)" strokeWidth="4" className="flow-line" />
          <line x1="280" y1="60" x2="400" y2="60" stroke="url(#grad-retrieval-baseline)" strokeWidth="4" className="flow-line" />
          <line x1="440" y1="60" x2="560" y2="60" stroke="url(#grad-baseline-ai)" strokeWidth="4" className="flow-line" />
          <line x1="600" y1="60" x2="720" y2="60" stroke="url(#grad-ai-ticket)" strokeWidth="4" className="flow-line" />

          {/* Nodes */}
          {STAGES.map((stage, idx) => {
            const cx = 80 + idx * 160;
            const cy = 60;
            const isActive = activeStage === stage.id;
            return (
              <g
                key={stage.id}
                className={`node-group ${isActive ? "active" : ""}`}
                onClick={() => setActiveStage(stage.id)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={cx}
                  cy={cy}
                  r="30"
                  fill="#ffffff"
                  stroke={stage.color}
                  strokeWidth={isActive ? "5" : "3"}
                  filter={isActive ? "url(#glow)" : ""}
                  className="node-circle"
                />
                <foreignObject x={cx - 15} y={cy - 15} width="30" height="30" style={{ pointerEvents: "none" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "100%",
                      height: "100%",
                      color: stage.color,
                    }}
                  >
                    {stage.icon}
                  </div>
                </foreignObject>
                <text
                  x={cx}
                  y={cy + 48}
                  textAnchor="middle"
                  className="node-label"
                  style={{
                    fill: isActive ? "#1a192b" : "#727272",
                    fontWeight: isActive ? 700 : 500,
                    fontSize: "0.8rem",
                  }}
                >
                  {stage.label.split(". ")[1]}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="stage-card" style={{ borderColor: currentStage.color }}>
        <div className="stage-card-header">
          <span className="stage-badge" style={{ backgroundColor: currentStage.color }}>
            {currentStage.tech}
          </span>
          <h4 style={{ color: currentStage.color }}>{currentStage.title}</h4>
        </div>
        <p className="stage-desc">{currentStage.description}</p>
      </div>
    </div>
  );
}
