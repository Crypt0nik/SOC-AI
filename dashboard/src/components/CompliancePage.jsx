import { useEffect, useState } from 'react';
import { fetchComplianceStats } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';
import ProGate from './ProGate.jsx';

const WINDOWS = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
  { label: '1 year', value: 365 },
];

const SEV_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];

function KpiCard({ label, value, sub, color }) {
  const { T } = useTheme();
  return (
    <div style={{
      backgroundColor: T.surface,
      border: `1px solid ${T.border}`,
      borderRadius: '10px',
      padding: '16px 18px',
      flex: 1,
    }}>
      <div style={{ fontSize: '11px', color: T.textMuted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ fontSize: '26px', fontWeight: 700, color: color ?? T.text, lineHeight: 1, marginBottom: '4px' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: '11px', color: T.textDimmer }}>{sub}</div>}
    </div>
  );
}

function SectionCard({ title, icon, children }) {
  const { T } = useTheme();
  return (
    <div style={{
      backgroundColor: T.surface,
      border: `1px solid ${T.border}`,
      borderRadius: '10px',
      padding: '16px 18px',
    }}>
      <div style={{
        fontSize: '12px', fontWeight: 600, color: T.text,
        marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px',
      }}>
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

function ComplianceInner() {
  const { T } = useTheme();
  const [windowDays, setWindowDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    fetchComplianceStats(windowDays)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [windowDays]);

  const handleExport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance_${windowDays}d.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '2px',
          backgroundColor: T.surface, border: `1px solid ${T.border}`,
          borderRadius: '7px', padding: '2px',
        }}>
          {WINDOWS.map((w) => (
            <button
              key={w.value}
              onClick={() => setWindowDays(w.value)}
              style={{
                padding: '4px 12px', borderRadius: '5px', fontSize: '12px',
                fontWeight: 500, border: 'none', cursor: 'pointer',
                transition: 'all 0.1s',
                backgroundColor: windowDays === w.value ? T.bg : 'transparent',
                color: windowDays === w.value ? T.text : T.textMuted,
                boxShadow: windowDays === w.value ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              {w.label}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <button
          onClick={handleExport}
          disabled={!data}
          style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            padding: '5px 12px', fontSize: '12px', fontWeight: 500,
            backgroundColor: 'transparent',
            border: `1px solid ${T.borderSubtle}`,
            borderRadius: '6px', cursor: data ? 'pointer' : 'default',
            color: data ? T.text : T.textDimmer,
            transition: 'all 0.1s',
          }}
          onMouseEnter={(e) => { if (data) { e.currentTarget.style.borderColor = T.border; } }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.borderSubtle; }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export JSON
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '20px', textAlign: 'center', fontSize: '13px',
          color: T.errorText, backgroundColor: T.surface,
          border: `1px solid ${T.border}`, borderRadius: '10px',
        }}>
          Failed to load compliance data: {error}
        </div>
      )}

      {/* Loading skeleton */}
      {!data && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[1, 2, 3].map((i) => (
            <div key={i} style={{
              height: '80px', backgroundColor: T.surface,
              border: `1px solid ${T.border}`, borderRadius: '10px',
              animation: 'pulse 1.5s ease-in-out infinite',
              opacity: 0.6,
            }} />
          ))}
        </div>
      )}

      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* KPI row */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <KpiCard
              label="Total Alerts"
              value={data.total_alerts.toLocaleString()}
              sub={`Last ${windowDays} days`}
            />
            <KpiCard
              label="Triaged"
              value={`${data.triaged_pct}%`}
              sub={`${(100 - data.triaged_pct).toFixed(1)}% pending or error`}
              color={data.triaged_pct >= 90 ? '#4ade80' : data.triaged_pct >= 70 ? '#FFB300' : '#FF0000'}
            />
            <KpiCard
              label="Mean Triage Time"
              value={data.mean_triage_seconds < 60
                ? `${Math.round(data.mean_triage_seconds)}s`
                : `${(data.mean_triage_seconds / 60).toFixed(1)}m`}
              sub="LLM response latency"
            />
            <KpiCard
              label="High FP Risk"
              value={data.false_positive_count}
              sub="Alerts with HIGH false-positive risk"
              color={data.false_positive_count > 0 ? '#FFB300' : undefined}
            />
          </div>

          {/* Severity + Attack types row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            {/* Severity breakdown */}
            <SectionCard
              title="Severity Breakdown"
              icon={<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={T.textMuted} strokeWidth="2" strokeLinecap="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>}
            >
              {SEV_ORDER.map((sev) => {
                const count = data.by_severity[sev] ?? 0;
                const total = data.total_alerts || 1;
                const pct = Math.round((count / total) * 100);
                const color = SEVERITY_COLOR[sev] ?? '#666666';
                return (
                  <div key={sev} style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 600, color, letterSpacing: '0.04em' }}>{sev}</span>
                      <span style={{ fontSize: '11px', color: T.textMuted }}>{count} ({pct}%)</span>
                    </div>
                    <div style={{ height: '4px', backgroundColor: T.border, borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', width: `${pct}%`, backgroundColor: color,
                        borderRadius: '2px', transition: 'width 0.4s ease',
                      }} />
                    </div>
                  </div>
                );
              })}
            </SectionCard>

            {/* Top attack types */}
            <SectionCard
              title="Top Attack Types"
              icon={<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={T.textMuted} strokeWidth="2" strokeLinecap="round"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/><path d="M13 13l6 6"/></svg>}
            >
              {data.top_attack_types.length === 0 ? (
                <div style={{ fontSize: '12px', color: T.textDimmer, textAlign: 'center', padding: '20px 0' }}>
                  No triage data yet
                </div>
              ) : (() => {
                const max = Math.max(1, ...data.top_attack_types.map((a) => a.count));
                return data.top_attack_types.map((item, i) => {
                  const pct = Math.round((item.count / max) * 100);
                  return (
                    <div key={item.type} style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '11px', color: T.text, display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span style={{ fontSize: '10px', color: T.textDimmer, width: '14px' }}>#{i + 1}</span>
                          {item.type}
                        </span>
                        <span style={{ fontSize: '11px', color: T.textMuted }}>{item.count}</span>
                      </div>
                      <div style={{ height: '4px', backgroundColor: T.border, borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', width: `${pct}%`, backgroundColor: '#FF6600',
                          borderRadius: '2px', transition: 'width 0.4s ease',
                        }} />
                      </div>
                    </div>
                  );
                });
              })()}
            </SectionCard>
          </div>

          {/* MITRE coverage */}
          <SectionCard
            title={`MITRE ATT&CK Coverage — ${data.mitre_coverage.length} technique${data.mitre_coverage.length !== 1 ? 's' : ''} detected`}
            icon={<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={T.textMuted} strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>}
          >
            {data.mitre_coverage.length === 0 ? (
              <div style={{ fontSize: '12px', color: T.textDimmer, textAlign: 'center', padding: '12px 0' }}>
                No MITRE techniques identified yet
              </div>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {data.mitre_coverage.map((tid) => (
                  <span key={tid} style={{
                    fontSize: '11px', fontFamily: 'monospace',
                    color: T.mitreText, backgroundColor: `${T.mitreText}18`,
                    border: `1px solid ${T.mitreText}40`,
                    borderRadius: '4px', padding: '2px 7px',
                  }}>
                    {tid}
                  </span>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Compliance note */}
          <div style={{
            padding: '12px 16px',
            backgroundColor: T.surface,
            border: `1px solid ${T.border}`,
            borderRadius: '8px',
            display: 'flex', alignItems: 'flex-start', gap: '10px',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={T.textMuted} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: '1px' }}>
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span style={{ fontSize: '12px', color: T.textMuted, lineHeight: 1.5 }}>
              This report covers alert activity from the last <strong>{windowDays} days</strong> and is intended to support NIS2 / ISO 27001 internal audits.
              Data reflects LLM-qualified triage outcomes. Export to JSON for archival.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CompliancePage() {
  return (
    <ProGate feature="compliance" description="Security compliance metrics for NIS2 / ISO 27001 audits">
      <ComplianceInner />
    </ProGate>
  );
}
