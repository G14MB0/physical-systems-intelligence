import { useState } from "react";
import {
  ArrowRight,
  ClipboardCheck,
  Database,
  Gauge,
  Monitor,
  Presentation,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { SignalTraceConsole } from "./components/SignalTraceConsole";
import { ProcessDiagram } from "./components/ProcessDiagram";
import { nasaReplay } from "./domain/nasaDemo";
import { runWorkflowDiagnosis, type WorkflowUiResult } from "./services/api";

const stagedTrace: WorkflowUiResult["trace"] = [
  { step: "load_signals", summary: "Loading FD001 unit 1 telemetry snapshot." },
  { step: "retrieve_docs", summary: "Retrieving NASA C-MAPSS evidence chunks." },
  { step: "compute_baseline", summary: "Computing deterministic health baseline." },
  { step: "ai_diagnose", summary: "Preparing structured diagnosis path." },
  { step: "validate_expected", summary: "Checking expected benchmark label." },
  { step: "create_ticket", summary: "Preparing operational action ticket." },
];

export default function App() {
  const [view, setView] = useState<"presentation" | "dashboard">("presentation");
  const [result, setResult] = useState<WorkflowUiResult | null>(null);
  const [pendingTrace, setPendingTrace] = useState<WorkflowUiResult["trace"]>([]);
  const [status, setStatus] = useState<"idle" | "running" | "fallback">("idle");
  const visible = result;

  async function runSignalTrace() {
    setStatus("running");
    setResult(null);
    setPendingTrace([stagedTrace[0]]);
    let stageIndex = 1;
    const traceTimer = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stagedTrace.length);
      setPendingTrace(stagedTrace.slice(0, stageIndex));
      if (stageIndex >= stagedTrace.length) {
        window.clearInterval(traceTimer);
      }
    }, 260);
    try {
      const apiResult = await runWorkflowDiagnosis();
      setResult(apiResult);
      window.clearInterval(traceTimer);
      setPendingTrace([]);
      setStatus("idle");
    } catch {
      window.clearInterval(traceTimer);
      setPendingTrace([]);
      setResult(nasaReplay);
      setStatus("fallback");
    }
  }

  return (
    <div className={`app-shell theme-${view}`}>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Physical Systems Intelligence home">
          <span className="brand-mark">PS</span>
          <span>Physical Systems Intelligence</span>
        </a>
        <nav className="nav">
          <button
            className={`nav-tab-btn ${view === "presentation" ? "active" : ""}`}
            onClick={() => setView("presentation")}
          >
            <Presentation size={16} />
            <span>Product Presentation</span>
          </button>
          <button
            className={`nav-tab-btn ${view === "dashboard" ? "active" : ""}`}
            onClick={() => setView("dashboard")}
          >
            <Monitor size={16} />
            <span>Operations Dashboard</span>
          </button>
        </nav>
      </header>

      {view === "presentation" ? (
        <main className="presentation-view animate-fade-in">
          {/* Hero Area */}
          <section className="hero-landing">
            <div className="landing-accent-line"></div>
            <p className="eyebrow">Autonomous trigger replay</p>
            <h1>Physical Systems Intelligence</h1>
            <p className="lede">
              Reliable AI Diagnostics for Physical Assets using telemetry, technical documentation, and validated actions.
            </p>
            <div className="hero-actions">
              <button className="primary-link" onClick={() => setView("dashboard")}>
                Open Interactive Dashboard
                <ArrowRight size={18} />
              </button>
              <a className="secondary-link" href="#process-architecture">
                Learn how it works
              </a>
            </div>
          </section>

          {/* Demo Scope & Simulation Details */}
          <section className="demo-scope-band">
            <div className="section-title-centered">
              <span className="eyebrow">Demo Scope</span>
              <h2>What the Simulation Replays</h2>
            </div>
            <div className="scope-grid">
              <div className="scope-card">
                <span className="scope-num">01</span>
                <h3>Asset & Ingest</h3>
                <p>NASA C-MAPSS turbofan test unit 1 finishes cycle 31. Telemetry ingest triggers an autonomous health gate analysis.</p>
              </div>
              <div className="scope-card">
                <span className="scope-num">02</span>
                <h3>Fault Mode Scope</h3>
                <p>Simulating High Pressure Compressor (HPC) degradation under sea-level operating conditions.</p>
              </div>
              <div className="scope-card">
                <span className="scope-num">03</span>
                <h3>Target Validation</h3>
                <p>Validates remaining useful life (RUL) against the benchmark ground-truth label of 112 cycles.</p>
              </div>
            </div>
          </section>

          {/* Interactive Process Diagram */}
          <section id="process-architecture" className="process-band">
            <div className="section-title-centered">
              <span className="eyebrow">Diagnostic Flow</span>
              <h2>End-to-End Workflow Pipeline</h2>
              <p className="section-subtitle">Click on each stage to understand the diagnostic sequence</p>
            </div>
            <ProcessDiagram />
          </section>

          {/* Embedded Dashboard Simulation */}
          <section className="embedded-console-band">
            <div className="section-title-centered">
              <span className="eyebrow">Embedded Operations Console</span>
              <h2>System Dashboard Preview</h2>
              <p className="section-subtitle">Interactive demo embedding fixture data from a cycle 31 diagnostic run</p>
            </div>
            <div className="device-mockup">
              <div className="device-header">
                <div className="dots">
                  <span className="dot dot-red"></span>
                  <span className="dot dot-yellow"></span>
                  <span className="dot dot-green"></span>
                </div>
                <div className="device-title">Operations Console (Unit 1 Replay)</div>
              </div>
              <div className="device-body">
                <SignalTraceConsole
                  result={null}
                  pendingTrace={[]}
                  status="idle"
                  onRun={() => {
                    setView("dashboard");
                    runSignalTrace();
                  }}
                />
              </div>
            </div>
          </section>

          {/* How to Run Locally */}
          <section className="get-started-band">
            <div className="section-title-centered">
              <span className="eyebrow">Ingestion & Evaluation</span>
              <h2>Run Live Diagnostics Locally</h2>
            </div>
            <div className="terminal-card">
              <div className="terminal-header">
                <Terminal size={16} />
                <span>Quick Start CLI</span>
              </div>
              <pre>{`# Start Qdrant, PostgreSQL, FastAPI & Vite frontend
docker compose up --build

# Ingest NASA C-MAPSS document packs into Qdrant vector database
curl -X POST http://localhost:8122/documents/ingest

# Trigger a diagnostic run on the FastAPI backend
curl -X POST http://localhost:8122/workflows/diagnose \\
  -H "Content-Type: application/json" \\
  -d '{"domain_id": "nasa_cmapss_turbofan", "system_id": "FD001-UNIT-001"}'`}</pre>
            </div>
          </section>
        </main>
      ) : (
        <main className="dashboard-view animate-fade-in">
          <div className="dashboard-header-bar">
            <div>
              <span className="eyebrow">Live Console</span>
              <h1>Physical Fleet Operations</h1>
            </div>
            <div className="dashboard-status-indicator">
              <ShieldCheck size={18} color="#10b981" />
              <span>Pipeline Online</span>
              {status === "fallback" && (
                <span className="fallback-tag">Offline Replay</span>
              )}
            </div>
          </div>
          <SignalTraceConsole
            result={visible}
            pendingTrace={pendingTrace}
            status={status}
            onRun={runSignalTrace}
          />
        </main>
      )}
    </div>
  );
}
