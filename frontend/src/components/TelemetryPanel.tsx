import { useState } from "react";
import { Cpu, ChevronDown, ChevronUp, Activity } from "lucide-react";
import { nasaReplay } from "../domain/nasaDemo";
import type { WorkflowUiResult } from "../services/api";

export function TelemetryPanel({ result }: { result: WorkflowUiResult | null }) {
  const situation = result?.situation ?? nasaReplay.situation;
  const validation = result?.validation ?? nasaReplay.validation;
  const [showTable, setShowTable] = useState(false);

  // Extract sensor data arrays for sparklines
  const signalWindow = situation.signalWindow;
  const getSensorData = (key: string): number[] => {
    return signalWindow.map((row) => (row[key] !== undefined ? row[key] : 0));
  };

  const sensorKeys = [
    { key: "sensor_2", label: "sensor 2 (T24 HPC Temp Outlet)", color: "#0041d0" },
    { key: "sensor_3", label: "sensor 3 (T50 LPT Temp Outlet)", color: "#ff0072" },
    { key: "sensor_4", label: "sensor 4 (P30 HPC Pres Outlet)", color: "#8b5cf6" },
    { key: "sensor_11", label: "sensor 11 (Ps30 Static Pres HPC)", color: "#10b981" },
    { key: "sensor_15", label: "sensor 15 (Nf Phys Fan Speed)", color: "#f59e0b" },
  ];

  return (
    <article className="card asset-card">
      <div className="card-heading">
        <Cpu size={20} />
        <h2>Autonomous health gate replay</h2>
      </div>

      <div className="asset-meta-header">
        <span className="asset-badge">NASA C-MAPSS FD001</span>
        <h2>NASA C-MAPSS FD001 Unit 1</h2>
        <p className="scenario-trigger" style={{ marginTop: "0.5rem", color: "#ff0072", fontWeight: 700, fontSize: "0.85rem" }}>
          {situation.trigger}
        </p>
      </div>

      <p className="scenario-copy">{situation.physicalCondition}</p>

      {/* KPI Stats Grid */}
      <div className="metric-grid">
        <Metric label="Current Cycle" value="31" subText="Latest Telemetry" />
        <Metric
          label="ground-truth RUL"
          value={validation.expected.groundTruthRul ? `${validation.expected.groundTruthRul}` : "N/A"}
          subText="Benchmark Target"
          highlight
        />
        <Metric
          label="Est. Failure Cycle"
          value={validation.expectedFailureCycle ? `${validation.expectedFailureCycle}` : "N/A"}
          subText="Projected Limit"
        />
        <Metric
          label="Validation Status"
          value={validation.passed ? "READY" : "FAILED"}
          subText="Assertion Check"
          status={validation.passed ? "pass" : "fail"}
        />
      </div>

      {/* Sensor Trends Grid */}
      <div className="sensor-trends-section">
        <h3>Sensor Trends (Last 5 Cycles)</h3>
        <div className="sensor-grid">
          {sensorKeys.map(({ key, label, color }) => {
            const data = getSensorData(key);
            const latestValue = data[data.length - 1];
            return (
              <div className="sensor-trend-card" key={key}>
                <div className="sensor-info">
                  <span className="sensor-label">{label}</span>
                  <strong className="sensor-val">{latestValue.toFixed(4)}</strong>
                </div>
                <div className="sensor-chart">
                  <Sparkline data={data} color={color} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Collapsible raw data table */}
      <div className="collapsible-table-section">
        <button
          className="collapse-toggle-btn"
          onClick={() => setShowTable(!showTable)}
          aria-expanded={showTable}
        >
          <span>Raw Signal Window Table</span>
          {showTable ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {showTable && (
          <div className="signal-window animate-fade-in">
            <table>
              <thead>
                <tr>
                  <th>cycle</th>
                  <th>sensor 2</th>
                  <th>sensor 3</th>
                  <th>sensor 4</th>
                  <th>sensor 11</th>
                  <th>sensor 15</th>
                </tr>
              </thead>
              <tbody>
                {signalWindow.map((row) => (
                  <tr key={row.cycle}>
                    <td>{row.cycle}</td>
                    <td>{row.sensor_2}</td>
                    <td>{row.sensor_3}</td>
                    <td>{row.sensor_4}</td>
                    <td>{row.sensor_11}</td>
                    <td>{row.sensor_15}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </article>
  );
}

function Metric({
  label,
  value,
  subText,
  highlight = false,
  status,
}: {
  label: string;
  value: string;
  subText: string;
  highlight?: boolean;
  status?: "pass" | "fail";
}) {
  let valueColor = "#1a192b";
  if (highlight) valueColor = "#0041d0";
  if (status === "pass") valueColor = "#10b981";
  if (status === "fail") valueColor = "#c5221f";

  return (
    <div className={`metric-tile ${highlight ? "highlighted-tile" : ""}`}>
      <span className="metric-tile-label">{label}</span>
      <strong className="metric-tile-val" style={{ color: valueColor }}>
        {value}
      </strong>
      <span className="metric-tile-sub">{subText}</span>
    </div>
  );
}

function Sparkline({ data, color = "#0041d0" }: { data: number[]; color?: string }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 120;
  const height = 30;
  const padding = 3;

  const pts = data.map((val, idx) => {
    const x = padding + (idx / (data.length - 1)) * (width - 2 * padding);
    const y = padding + (1 - (val - min) / range) * (height - 2 * padding);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const lastPt = pts[pts.length - 1].split(",");
  const cx = lastPt[0];
  const cy = lastPt[1];

  return (
    <svg width={width} height={height} className="sparkline-svg">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={pts.join(" ")}
      />
      <circle cx={cx} cy={cy} r="3.5" fill={color} className="sparkline-dot" />
    </svg>
  );
}
