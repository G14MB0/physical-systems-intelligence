import { BookOpen, Link2, Info } from "lucide-react";
import type { WorkflowUiResult } from "../services/api";

function hostnameLabel(url: string): string {
  if (!url) {
    return "";
  }
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function EvidencePanel({ result }: { result: WorkflowUiResult | null }) {
  if (!result) {
    return (
      <article className="card diagnosis-card">
        <div className="card-heading">
          <BookOpen size={20} />
          <span>Knowledge Grounding</span>
        </div>
        <p className="empty-state">Ingested documents and RAG evidence will appear here after the diagnostics run.</p>
      </article>
    );
  }

  return (
    <article className="card diagnosis-card">
      <div className="card-heading">
        <BookOpen size={20} />
        <span>Knowledge Grounding</span>
      </div>

      <div className="diagnosis-summary">
        <strong>Structured Diagnosis:</strong>
        <p className="diagnosis-text">{result.diagnosis}</p>
      </div>

      <div className="retrieval-summary-box">
        <div className="retrieval-stat">
          <span className="retrieval-stat-label">RAG Vector DB</span>
          <strong className="retrieval-stat-val">Qdrant Active</strong>
        </div>
        <div className="retrieval-stat">
          <span className="retrieval-stat-label">Retrieved Excerpts</span>
          <strong className="retrieval-stat-val">{result.sources.length} sources</strong>
        </div>
        <div className="retrieval-stat">
          <span className="retrieval-stat-label">Avg Search Score</span>
          <strong className="retrieval-stat-val">
            {(result.sources.reduce((acc, s) => acc + s.score, 0) / result.sources.length).toFixed(2)}
          </strong>
        </div>
      </div>

      <div className="qdrant-role-badge-section" style={{ marginBottom: "1.25rem" }}>
        <p className="qdrant-role-badge">
          <Info size={12} style={{ marginRight: "0.25rem" }} />
          <strong>Role:</strong> {result.situation.qdrantRole}
        </p>
      </div>

      <div className="sources-list animate-fade-in" style={{ maxHeight: "450px", overflowY: "auto" }}>
        {result.sources.map((source) => (
          <div className="source-item" key={source.chunkId || `${source.path}-${source.rank}`} style={{ marginBottom: "1rem" }}>
            <div className="source-item-header">
              <span className="source-rank-badge">rank {source.rank}</span>
              <strong>{source.sourceLabel || source.path}</strong>
            </div>
            
            <h5 className="source-item-title">
              {source.title} {source.sectionTitle && ` - ${source.sectionTitle}`}
            </h5>

            {/* Collapse only the raw text excerpt to save space and look cleaner */}
            <details className="source-excerpt-details" style={{ margin: "0.5rem 0" }}>
              <summary style={{ fontSize: "0.78rem", color: "#0041d0", cursor: "pointer", fontWeight: 600 }}>
                View document excerpt
              </summary>
              <p className="source-excerpt" style={{ margin: "0.5rem 0 0", fontSize: "0.82rem", lineHeight: "1.5", color: "#cbd5e1", fontStyle: "italic" }}>
                "{source.excerpt}"
              </p>
            </details>

            <div className="source-item-footer" style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "0.5rem" }}>
              <span>score {source.score.toFixed(2)}</span>
              <span>provider: <strong>{source.provider}</strong></span>
              {source.sourceAuthority && <span>{source.sourceAuthority}</span>}
              {source.sourceUrls && source.sourceUrls.length > 1 && (
                <span>
                  +{source.sourceUrls.length - 1} related source{source.sourceUrls.length > 2 ? "s" : ""}
                </span>
              )}
              {source.sourceUrl && (
                <a href={source.sourceUrl} target="_blank" rel="noreferrer" className="source-link" style={{ marginLeft: "auto" }}>
                  <Link2 size={12} />
                  {hostnameLabel(source.sourceUrl)}
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Model & token usage sub-panel */}
      <div className="token-usage-footer">
        <div className="usage-row">
          <span>Model: <strong className="ai-model-name">{result.usage.model ?? "deterministic"}</strong></span>
          <span>
            Tokens: <strong>{result.usage.inputTokens}</strong> in / <strong>{result.usage.outputTokens}</strong> out (Total: {result.usage.totalTokens})
          </span>
        </div>
      </div>
    </article>
  );
}
export default EvidencePanel;
