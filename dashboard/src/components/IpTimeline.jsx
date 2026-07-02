import { useEffect, useState } from 'react';
import { fetchIpTimeline } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';
import ProGate from './ProGate.jsx';

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

function IpTimelineInner({ sourceIp, onSelectAlert, onClose }) {
  const { T } = useTheme();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    fetchIpTimeline(sourceIp)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [sourceIp]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 48,
        display: 'flex', alignItems: 'stretch', justifyContent: 'flex-end',
        backgroundColor: T.overlay,
        backdropFilter: 'blur(2px)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="panel-enter"
        style={{
          width: '420px', maxWidth: '100vw',
          backgroundColor: T.surface,
          borderLeft: `1px solid ${T.border}`,
          display: 'flex', flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${T.borderSubtle}`,
          display: 'flex', alignItems: 'center', gap: '8px',
          position: 'sticky', top: 0,
          backgroundColor: T.surface, zIndex: 1,
        }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={T.textMuted} strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: T.text }}>IP Timeline</div>
            <div style={{ fontSize: '11px', color: T.textDimmer, fontFamily: 'monospace' }}>{sourceIp}</div>
          </div>
          {data && (
            <span style={{ fontSize: '11px', color: T.textMuted }}>
              {data.total} alert{data.total !== 1 ? 's' : ''}
            </span>
          )}
          <button
            onClick={onClose}
            title="Close (Esc)"
            style={{
              backgroundColor: 'transparent',
              border: `1px solid ${T.borderSubtle}`,
              borderRadius: '5px',
              width: '26px', height: '26px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', color: T.textMuted,
              transition: 'color 0.1s, border-color 0.1s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
          {!data && !error && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: T.textDimmer, fontSize: '13px' }}>Loading…</div>
          )}
          {error && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: T.errorText, fontSize: '13px' }}>{error}</div>
          )}
          {data && data.alerts.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 0' }}>
              <div style={{ marginBottom: '8px', color: T.textDimmer }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
              </div>
              <div style={{ fontSize: '13px', color: T.textDimmer }}>No alerts found for this IP</div>
            </div>
          )}
          {data && data.alerts.length > 0 && (
            <div style={{ position: 'relative' }}>
              {/* Vertical timeline line */}
              <div style={{
                position: 'absolute', left: '7px', top: '8px',
                bottom: '8px', width: '1px',
                backgroundColor: T.borderSubtle,
              }} />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {data.alerts.map((alert) => {
                  const color = SEVERITY_COLOR[alert.eff_severity] ?? '#666666';
                  return (
                    <div
                      key={alert.id}
                      onClick={() => { onSelectAlert(alert.id); }}
                      style={{
                        display: 'flex', alignItems: 'flex-start', gap: '12px',
                        padding: '8px 8px 8px 24px',
                        borderRadius: '7px', cursor: 'pointer',
                        transition: 'background-color 0.1s',
                        position: 'relative',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = T.surfaceHover; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      {/* Dot on the timeline */}
                      <span style={{
                        position: 'absolute', left: '3px', top: '13px',
                        width: '9px', height: '9px', borderRadius: '50%',
                        backgroundColor: color,
                        border: `2px solid ${T.surface}`,
                        flexShrink: 0,
                        zIndex: 1,
                      }} />

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
                          <span style={{ fontSize: '10px', fontWeight: 700, color, letterSpacing: '0.04em' }}>
                            {alert.eff_severity}
                          </span>
                          <span style={{ fontSize: '10px', color: T.textDimmer }}>
                            {timeAgo(alert.timestamp)}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: T.text, fontWeight: 500, marginBottom: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {alert.rule_name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '10px', fontFamily: 'monospace', color: T.textMuted }}>{alert.rule_id}</span>
                          {alert.attack_type && (
                            <span style={{ fontSize: '10px', color: T.textDimmer }}>· {alert.attack_type}</span>
                          )}
                          {alert.mitre_id && (
                            <span style={{ fontSize: '10px', fontFamily: 'monospace', color: T.mitreText }}>{alert.mitre_id}</span>
                          )}
                        </div>
                      </div>

                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={T.textDimmer} strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0, marginTop: '4px' }}>
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function IpTimeline({ sourceIp, onSelectAlert, onClose }) {
  return (
    <ProGate feature="ip_timeline" description="Full alert history and activity timeline per source IP">
      <IpTimelineInner sourceIp={sourceIp} onSelectAlert={onSelectAlert} onClose={onClose} />
    </ProGate>
  );
}
