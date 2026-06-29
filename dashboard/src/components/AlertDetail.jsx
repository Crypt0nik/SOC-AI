import { useEffect, useState } from 'react';
import { fetchAlert } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';

function Field({ label, value, mono = false }) {
  if (value == null || value === '') return null;
  return (
    <div className="mb-3">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-gray-200 text-sm ${mono ? 'font-mono' : ''}`}>{value}</div>
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
        <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
        <span className="text-sm font-bold text-gray-300">{pct}%</span>
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
    /* Overlay */
    <div
      className="fixed inset-0 z-50 flex items-start justify-end"
      style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Side panel */}
      <div className="w-full max-w-2xl h-full overflow-y-auto bg-gray-900 border-l border-gray-700 flex flex-col">
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b border-gray-800"
          style={{ borderLeftColor: sevColor, borderLeftWidth: '4px' }}
        >
          <div>
            <h2 className="text-lg font-bold text-white">
              Alert #{alertId}
            </h2>
            {detail && (
              <p className="text-sm text-gray-400">{detail.rule_name}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-200 text-xl font-light transition-colors px-2"
            aria-label="Close"
          >
            x
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 px-6 py-4">
          {loading && (
            <div className="text-center py-16 text-gray-500">Loading…</div>
          )}

          {error && (
            <div className="text-center py-16 text-red-400">
              <p>Failed to load alert</p>
              <p className="text-sm text-gray-500 mt-1">{error}</p>
            </div>
          )}

          {detail && (
            <>
              {/* Alert metadata */}
              <section className="mb-6">
                <h3 className="text-xs uppercase tracking-widest text-gray-500 mb-3 font-semibold">
                  Detection
                </h3>
                <div className="grid grid-cols-2 gap-x-6">
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                      Severity
                    </div>
                    <span
                      className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
                      style={{ backgroundColor: sevColor }}
                    >
                      {effectiveSev}
                    </span>
                  </div>
                  <Field label="Rule ID" value={detail.rule_id} mono />
                  <Field label="Source IP" value={detail.source_ip} mono />
                  <Field label="Matched Count" value={detail.matched_count} />
                  <Field label="Timestamp" value={detail.timestamp} />
                  <Field label="Status" value={detail.status} />
                </div>
              </section>

              {/* Raw log */}
              <section className="mb-6">
                <h3 className="text-xs uppercase tracking-widest text-gray-500 mb-3 font-semibold">
                  Raw Log
                </h3>
                <pre className="bg-gray-950 rounded p-3 text-xs font-mono text-green-400 whitespace-pre-wrap break-all overflow-x-auto">
                  {detail.raw_log}
                </pre>
              </section>

              {/* Triage */}
              {detail.triage ? (
                <section>
                  <h3 className="text-xs uppercase tracking-widest text-gray-500 mb-3 font-semibold">
                    LLM Triage Analysis
                  </h3>
                  <div className="bg-gray-950 rounded p-4 border border-gray-800">
                    <div className="grid grid-cols-2 gap-x-6 mb-2">
                      <Field label="Attack Type" value={detail.triage.attack_type} />
                      <Field label="MITRE ATT&CK" value={detail.triage.mitre_id} mono />
                      <div className="mb-3">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                          False Positive Risk
                        </div>
                        <span className="text-sm text-gray-200">
                          {detail.triage.false_positive_risk}
                        </span>
                      </div>
                      <Field label="Backend" value={detail.triage.backend} />
                    </div>
                    <ConfidenceBar value={detail.triage.confidence} />
                    <Field label="Summary" value={detail.triage.summary} />
                    <Field label="Recommendation" value={detail.triage.recommendation} />
                  </div>
                </section>
              ) : (
                <section>
                  <div className="bg-gray-950 rounded p-4 border border-gray-800 text-center text-gray-500 text-sm">
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
