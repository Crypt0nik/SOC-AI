import { useEffect, useState } from 'react';
import { fetchAlert } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';

function timeAgo(ts) {
  if (!ts) return '—';
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function CopyableIP({ ip }) {
  const { T } = useTheme();
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(ip).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button onClick={copy} title="Copy IP" style={{
      backgroundColor: 'transparent', border: 'none', cursor: 'pointer',
      color: copied ? '#4ade80' : T.text,
      fontFamily: 'monospace', fontSize: '13px', padding: 0,
      display: 'flex', alignItems: 'center', gap: '5px',
      transition: 'color 0.15s',
    }}>
      {ip}
      {copied ? (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      ) : (
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={T.textDim} strokeWidth="1.5" strokeLinecap="round">
          <rect x="9" y="9" width="13" height="13" rx="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
      )}
    </button>
  );
}

function ConfidenceBar({ value }) {
  const { T } = useTheme();
  const pct = Math.max(0, Math.min(100, value ?? 0));
  const color = pct >= 80 ? '#FF0000' : pct >= 60 ? '#FF6600' : pct >= 40 ? '#FFB300' : '#0066CC';
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
        <span style={{ fontSize: '11px', color: T.textDim, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence</span>
        <span style={{ fontSize: '12px', fontWeight: 700, color }}>{pct}%</span>
      </div>
      <div style={{ height: '3px', backgroundColor: T.border, borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, backgroundColor: color, borderRadius: '2px', transition: 'width 0.3s ease' }} />
      </div>
    </div>
  );
}

function Section({ title, children }) {
  const { T } = useTheme();
  return (
    <div style={{ borderTop: `1px solid ${T.borderSubtle}`, paddingTop: '14px', marginTop: '14px' }}>
      <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', color: T.textDim, marginBottom: '12px', fontWeight: 600 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function KV({ label, children, mono = false }) {
  const { T } = useTheme();
  if (children == null || children === '') return null;
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ fontSize: '11px', color: T.textDim, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '3px' }}>{label}</div>
      <div style={{ fontSize: '13px', color: T.text, fontFamily: mono ? 'monospace' : 'inherit' }}>{children}</div>
    </div>
  );
}

function SentenceList({ text }) {
  const { T } = useTheme();
  if (!text) return null;
  const sentences = text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 4);
  if (sentences.length <= 1) {
    return <p style={{ margin: 0, fontSize: '13px', lineHeight: 1.65, color: T.text }}>{text}</p>;
  }
  return (
    <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
      {sentences.map((s, i) => (
        <li key={i} style={{ fontSize: '13px', lineHeight: 1.55, color: T.text }}>{s}</li>
      ))}
    </ul>
  );
}

export default function AlertDetail({ alertId, onClose, onNavigate, canPrev, canNext }) {
  const { T } = useTheme();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setDetail(null);
    setError(null);
    fetchAlert(alertId)
      .then(setDetail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [alertId]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key === 'ArrowLeft' && canPrev) onNavigate(-1);
      if (e.key === 'ArrowRight' && canNext) onNavigate(1);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose, onNavigate, canPrev, canNext]);

  const effectiveSev = detail?.triage?.severity ?? detail?.severity;
  const sevColor = effectiveSev ? (SEVERITY_COLOR[effectiveSev] ?? '#666666') : '#666666';

  const navBtnStyle = (enabled) => ({
    backgroundColor: 'transparent',
    border: `1px solid ${T.borderSubtle}`,
    borderRadius: '5px',
    width: '26px', height: '26px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: enabled ? 'pointer' : 'default',
    color: enabled ? T.textMuted : T.borderSubtle,
    flexShrink: 0,
    transition: 'color 0.1s, border-color 0.1s',
  });

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 50,
        display: 'flex', alignItems: 'stretch', justifyContent: 'flex-end',
        backgroundColor: T.overlay,
        backdropFilter: 'blur(2px)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="panel-enter"
        style={{
          width: '480px', maxWidth: '100vw',
          backgroundColor: T.surface,
          borderLeft: `1px solid ${T.border}`,
          display: 'flex', flexDirection: 'column',
          overflowY: 'auto',
        }}
      >
        {/* Panel header */}
        <div style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${T.borderSubtle}`,
          display: 'flex', alignItems: 'center', gap: '8px',
          position: 'sticky', top: 0,
          backgroundColor: T.surface,
          zIndex: 1,
        }}>
          <button
            onClick={() => canPrev && onNavigate(-1)}
            disabled={!canPrev}
            title="Previous (←)"
            style={navBtnStyle(canPrev)}
            onMouseEnter={(e) => { if (canPrev) { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; } }}
            onMouseLeave={(e) => { if (canPrev) { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; } }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <button
            onClick={() => canNext && onNavigate(1)}
            disabled={!canNext}
            title="Next (→)"
            style={navBtnStyle(canNext)}
            onMouseEnter={(e) => { if (canNext) { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; } }}
            onMouseLeave={(e) => { if (canNext) { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; } }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>

          <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: sevColor, display: 'inline-block', flexShrink: 0 }} />

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: T.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {detail?.rule_name ?? (loading ? 'Loading…' : '—')}
            </div>
            <div style={{ fontSize: '10px', color: T.textDimmer, fontFamily: 'monospace' }}>#{alertId}</div>
          </div>

          <button
            onClick={onClose}
            title="Close (Esc)"
            style={navBtnStyle(true)}
            onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Panel body */}
        <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: T.textDimmer, fontSize: '13px' }}>Loading…</div>
          )}
          {error && (
            <div style={{ textAlign: 'center', padding: '48px 0' }}>
              <p style={{ color: T.errorText, fontSize: '13px', marginBottom: '4px' }}>Failed to load alert</p>
              <p style={{ color: T.textDimmer, fontSize: '12px' }}>{error}</p>
            </div>
          )}
          {detail && (
            <>
              {/* Severity + meta */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{
                  backgroundColor: sevColor, color: 'white',
                  fontSize: '11px', fontWeight: 700, padding: '2px 8px',
                  borderRadius: '4px', letterSpacing: '0.04em',
                }}>
                  {effectiveSev}
                </span>
                <span style={{ fontSize: '11px', color: T.textMuted }}>{timeAgo(detail.timestamp)}</span>
                {detail.status === 'triaged' && (
                  <span style={{
                    fontSize: '10px', color: T.triagedText, backgroundColor: T.triagedBg,
                    border: `1px solid ${T.triagedBorder}`, borderRadius: '3px', padding: '1px 6px',
                  }}>triaged ✓</span>
                )}
              </div>

              {/* Detection info grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
                <KV label="Rule ID"><span style={{ fontFamily: 'monospace' }}>{detail.rule_id}</span></KV>
                <KV label="Source IP">
                  {detail.source_ip ? <CopyableIP ip={detail.source_ip} /> : <span style={{ color: T.textDimmer }}>—</span>}
                </KV>
                <KV label="Matched">{detail.matched_count}×</KV>
                <KV label="Status">{detail.status}</KV>
              </div>

              {/* Raw log */}
              <Section title="Raw Log">
                <pre style={{
                  backgroundColor: T.terminalBg,
                  border: `1px solid ${T.borderSubtle}`,
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '11px', fontFamily: 'monospace',
                  color: T.terminalText,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                  maxHeight: '180px', overflowY: 'auto',
                  margin: 0, lineHeight: 1.5,
                }}>
                  {detail.raw_log}
                </pre>
              </Section>

              {/* LLM Triage */}
              <Section title="LLM Triage Analysis">
                {detail.triage ? (
                  <>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px', marginBottom: '4px' }}>
                      <KV label="Attack Type">{detail.triage.attack_type}</KV>
                      <KV label="MITRE ATT&CK">
                        {detail.triage.mitre_id
                          ? <span style={{ fontFamily: 'monospace', color: T.mitreText }}>{detail.triage.mitre_id}</span>
                          : <span style={{ color: T.textDimmer }}>—</span>}
                      </KV>
                      <KV label="FP Risk">{detail.triage.false_positive_risk}</KV>
                      <KV label="Backend">{detail.triage.backend}</KV>
                    </div>
                    <ConfidenceBar value={detail.triage.confidence} />

                    {/* Summary */}
                    {detail.triage.summary && (
                      <div style={{ marginBottom: '14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '8px' }}>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{ color: T.textDim, flexShrink: 0 }}>
                            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                          </svg>
                          <span style={{ fontSize: '11px', color: T.textDim, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Analysis</span>
                        </div>
                        <SentenceList text={detail.triage.summary} />
                      </div>
                    )}

                    {/* Recommendation */}
                    {detail.triage.recommendation && (
                      <div style={{
                        backgroundColor: T.surfaceHover,
                        border: `1px solid ${T.borderSubtle}`,
                        borderRadius: '7px',
                        padding: '12px 14px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '8px' }}>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FF6600" strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0 }}>
                            <polyline points="9 18 15 12 9 6"/>
                          </svg>
                          <span style={{ fontSize: '11px', color: '#FF6600', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>Recommended Action</span>
                        </div>
                        <SentenceList text={detail.triage.recommendation} />
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{
                    padding: '16px', textAlign: 'center', fontSize: '13px',
                    color: T.textDimmer, backgroundColor: T.terminalBg,
                    border: `1px solid ${T.borderSubtle}`, borderRadius: '6px',
                  }}>
                    Awaiting LLM triage…
                  </div>
                )}
              </Section>

              {/* Keyboard hints */}
              <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: `1px solid ${T.borderSubtle}`, display: 'flex', gap: '14px' }}>
                {[['Esc', 'close'], ['← →', 'navigate']].map(([key, label]) => (
                  <span key={key} style={{ fontSize: '11px', color: T.textDimmer, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <kbd style={{
                      fontFamily: 'monospace', border: `1px solid ${T.border}`,
                      borderRadius: '3px', padding: '1px 5px', color: T.textDim, fontSize: '10px',
                    }}>{key}</kbd>
                    {label}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
