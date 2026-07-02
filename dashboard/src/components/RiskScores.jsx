import { useEffect, useState } from 'react';
import { fetchRiskScores } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';
import ProGate from './ProGate.jsx';

function RiskScoresInner({ onIpClick }) {
  const { T } = useTheme();
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchRiskScores(10).then(setData).catch(() => setData({ scores: [] }));
    const id = setInterval(() => fetchRiskScores(10).then(setData).catch(() => {}), 15000);
    return () => clearInterval(id);
  }, []);

  if (!data) {
    return <div style={{ padding: '24px', textAlign: 'center', color: T.textDimmer, fontSize: '13px' }}>Loading…</div>;
  }

  if (data.scores.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: T.textDimmer }}>
        <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49"/><path d="M7.76 7.76a6 6 0 0 0 0 8.49"/><path d="M20.07 4.93a10 10 0 0 1 0 14.14"/><path d="M3.93 4.93a10 10 0 0 0 0 14.14"/>
          </svg>
        </div>
        <div style={{ fontSize: '13px' }}>No risk data yet</div>
      </div>
    );
  }

  const maxScore = Math.max(1, ...data.scores.map((s) => s.score));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {data.scores.map((item, i) => {
        const color = SEVERITY_COLOR[item.top_severity] ?? '#666666';
        const pct = Math.round((item.score / maxScore) * 100);
        return (
          <div
            key={item.source_ip}
            onClick={() => onIpClick?.(item.source_ip)}
            style={{
              backgroundColor: T.surface,
              border: `1px solid ${T.borderSubtle}`,
              borderRadius: '7px',
              padding: '10px 12px',
              cursor: 'pointer',
              transition: 'border-color 0.1s, background-color 0.1s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.backgroundColor = T.surfaceHover; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.borderSubtle; e.currentTarget.style.backgroundColor = T.surface; }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '11px', color: T.textDim, fontWeight: 600, flexShrink: 0, width: '16px' }}>
                #{i + 1}
              </span>
              <span style={{ fontFamily: 'monospace', fontSize: '12px', color: T.text, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.source_ip}
              </span>
              <span style={{
                fontSize: '10px', fontWeight: 700, color, backgroundColor: `${color}18`,
                border: `1px solid ${color}40`, borderRadius: '4px', padding: '1px 6px', flexShrink: 0,
              }}>
                {item.top_severity}
              </span>
              <span style={{ fontSize: '12px', fontWeight: 700, color, flexShrink: 0 }}>
                {item.score}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ flex: 1, height: '3px', backgroundColor: T.border, borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${pct}%`, backgroundColor: color, borderRadius: '2px', transition: 'width 0.4s ease' }} />
              </div>
              <span style={{ fontSize: '10px', color: T.textDim, flexShrink: 0 }}>
                {item.alert_count} alert{item.alert_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function RiskScores({ onIpClick }) {
  return (
    <ProGate feature="risk_scores" description="Rank source IPs by cumulative attack risk score">
      <RiskScoresInner onIpClick={onIpClick} />
    </ProGate>
  );
}
