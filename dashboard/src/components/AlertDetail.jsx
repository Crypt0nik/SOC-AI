import { useEffect, useState } from 'react';
import { fetchAlert } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';

function Field({ label, value, mono = false }) {
  if (value == null || value === '') return null;
  return (
    <div className="mb-3">
      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: '#4a5568' }}>{label}</div>
      <div className={`text-sm ${mono ? 'font-mono' : ''}`} style={{ color: '#d1d5db' }}>{value}</div>
    </div>
  );
}

function ConfidenceBar({ value }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 80 ? '#FF0000' : pct >= 60 ? '#FF6600' : pct >= 40 ? '#FFB300' : '#0066CC';
  return (
    <div className="mb-3">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
        Confidence
      </div>
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#1e2a3a' }}>
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
        <span className="text-sm font-bold" style={{ color: '#d1d5db' }}>{pct}%</span>
      </div>
    </div>
  );
}

export default function AlertDetail({ alertId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchAlert(alertId)
      .then(setDetail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [alertId]);

  const effectiveSev = detail?.triage?.severity ?? detail?.severity;
  const sevColor = effectiveSev ? (SEVERITY_COLOR[effectiveSev] ?? '#666666') : '#666666';

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-end"
      style={{ backgroundColor: 'rgba(0,0,0,0.65)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Side panel — slides in from right */}
      <div
        className="w-full max-w-2xl h-full overflow-y-auto flex flex-col slide-in-right"
        style={{ backgroundColor: '#0f1524', borderLeft: `1px solid ${sevColor}44` }}
      >
        {/* Colored header bar */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{
            borderBottom: `1px solid #1e2a3a`,
            borderLeft: `4px solid ${sevColor}`,
          }}
        >
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span
                className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
                style={{ backgroundColor: sevColor }}
              >
                {effectiveSev ?? '…'}
              </span>
              <span className="text-xs font-mono" style={{ color: '#4a5568' }}>#{alertId}</span>
            </div>
            <h2 className="text-base font-bold text-white leading-snug">
              {detail?.rule_name ?? 'Loading…'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 ml-4 w-7 h-7 flex items-center justify-center rounded transition-colors"
            style={{ color: '#4a5568', border: '1px solid #1e2a3a' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#e2e8f0'; e.currentTarget.style.borderColor = '#374151'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#4a5568'; e.currentTarget.style.borderColor = '#1e2a3a'; }}
            aria-label="Close"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 px-6 py-5">
          {loading && (
            <div className="text-center py-16" style={{ color: '#4a5568' }}>Loading…</div>
          )}

          {error && (
            <div className="text-center py-16" style={{ color: '#f87171' }}>
              <p>Failed to load alert</p>
              <p className="text-sm mt-1" style={{ color: '#4a5568' }}>{error}</p>
            </div>
          )}

          {detail && (
            <>
              {/* Detection metadata */}
              <section className="mb-6">
                <h3 className="text-xs uppercase tracking-widest font-semibold mb-3" style={{ color: '#4a5568' }}>
                  Detection
                </h3>
                <div className="grid grid-cols-2 gap-x-6">
                  <Field label="Rule ID" value={detail.rule_id} mono />
                  <Field label="Source IP" value={detail.source_ip} mono />
                  <Field label="Matched Count" value={detail.matched_count} />
                  <Field label="Status" value={detail.status} />
                  <Field label="Timestamp" value={detail.timestamp} />
                </div>
              </section>

              {/* Raw log */}
              <section className="mb-6">
                <h3 className="text-xs uppercase tracking-widest font-semibold mb-3" style={{ color: '#4a5568' }}>
                  Raw Log
                </h3>
                <pre
                  className="rounded p-3 text-xs font-mono whitespace-pre-wrap break-all overflow-x-auto"
                  style={{ backgroundColor: '#070b13', color: '#4ade80', border: '1px solid #1e2a3a' }}
                >
                  {detail.raw_log}
                </pre>
              </section>

              {/* Triage */}
              {detail.triage ? (
                <section>
                  <h3 className="text-xs uppercase tracking-widest font-semibold mb-3" style={{ color: '#4a5568' }}>
                    LLM Triage Analysis
                  </h3>
                  <div className="rounded p-4" style={{ backgroundColor: '#070b13', border: '1px solid #1e2a3a' }}>
                    <div className="grid grid-cols-2 gap-x-6 mb-2">
                      <Field label="Attack Type" value={detail.triage.attack_type} />
                      <Field label="MITRE ATT&CK" value={detail.triage.mitre_id} mono />
                      <Field label="False Positive Risk" value={detail.triage.false_positive_risk} />
                      <Field label="Backend" value={detail.triage.backend} />
                    </div>
                    <ConfidenceBar value={detail.triage.confidence} />
                    <Field label="Summary" value={detail.triage.summary} />
                    <Field label="Recommendation" value={detail.triage.recommendation} />
                  </div>
                </section>
              ) : (
                <section>
                  <div
                    className="rounded p-4 text-center text-sm"
                    style={{ backgroundColor: '#070b13', border: '1px solid #1e2a3a', color: '#4a5568' }}
                  >
                    Not yet triaged — waiting for LLM agent
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
