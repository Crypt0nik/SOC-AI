import { useEffect, useState } from 'react';
import { fetchMitreStats } from '../api.js';
import { useTheme } from '../theme.js';
import ProGate from './ProGate.jsx';

// Techniques present in the 10 SOC-AI Sigma rules
const TECHNIQUES = [
  { id: 'T1110',     name: 'Brute Force',                tactic: 'Credential Access' },
  { id: 'T1110.001', name: 'Password Guessing',          tactic: 'Credential Access' },
  { id: 'T1110.004', name: 'Credential Stuffing',        tactic: 'Credential Access' },
  { id: 'T1190',     name: 'Exploit Public-Facing App',  tactic: 'Initial Access' },
  { id: 'T1078',     name: 'Valid Accounts',             tactic: 'Defense Evasion' },
  { id: 'T1059',     name: 'Command & Scripting',        tactic: 'Execution' },
  { id: 'T1547',     name: 'Boot/Logon Autostart',       tactic: 'Persistence' },
  { id: 'T1548',     name: 'Abuse Elevation Control',    tactic: 'Privilege Escalation' },
  { id: 'T1046',     name: 'Network Service Discovery',  tactic: 'Discovery' },
  { id: 'T1041',     name: 'Exfil Over C2 Channel',      tactic: 'Exfiltration' },
  { id: 'T1071',     name: 'App Layer Protocol',         tactic: 'Command & Control' },
  { id: 'T1566',     name: 'Phishing',                   tactic: 'Initial Access' },
];

const TACTIC_ORDER = [
  'Initial Access', 'Execution', 'Persistence', 'Privilege Escalation',
  'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement',
  'Collection', 'Command & Control', 'Exfiltration', 'Impact',
];

function heatColor(count, max) {
  if (!count || max === 0) return null;
  const t = Math.min(count / max, 1);
  if (t < 0.33) return `rgba(255, 179, 0, ${0.3 + t * 0.4})`;
  if (t < 0.66) return `rgba(255, 102, 0, ${0.5 + t * 0.3})`;
  return `rgba(255, 0, 0, ${0.6 + t * 0.4})`;
}

function HeatmapInner() {
  const { T } = useTheme();
  const [data, setData] = useState(null);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    fetchMitreStats().then(setData).catch(() => setData({ techniques: [] }));
  }, []);

  const countMap = {};
  (data?.techniques ?? []).forEach((t) => { countMap[t.id] = t.count; });
  const maxCount = Math.max(1, ...Object.values(countMap));

  const byTactic = {};
  TECHNIQUES.forEach((t) => {
    if (!byTactic[t.tactic]) byTactic[t.tactic] = [];
    byTactic[t.tactic].push(t);
  });

  const tactics = TACTIC_ORDER.filter((tac) => byTactic[tac]);

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: T.textDimmer, fontSize: '13px' }}>
        Loading MITRE data…
      </div>
    );
  }

  if (Object.keys(countMap).length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: T.textDimmer }}>
        <div style={{ fontSize: '24px', marginBottom: '8px' }}>🛡️</div>
        <div style={{ fontSize: '13px' }}>No MITRE data yet — run attack simulations</div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', gap: '6px', minWidth: 'max-content' }}>
          {tactics.map((tactic) => (
            <div key={tactic}>
              <div style={{
                fontSize: '9px', fontWeight: 600, textTransform: 'uppercase',
                letterSpacing: '0.05em', color: T.textDim,
                marginBottom: '5px', textAlign: 'center',
                maxWidth: '80px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {tactic}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                {(byTactic[tactic] ?? []).map((tech) => {
                  const count = countMap[tech.id] ?? 0;
                  const bg = heatColor(count, maxCount);
                  return (
                    <div
                      key={tech.id}
                      onMouseEnter={(e) => setTooltip({ tech, count, x: e.clientX, y: e.clientY })}
                      onMouseLeave={() => setTooltip(null)}
                      style={{
                        width: '72px', height: '32px',
                        borderRadius: '4px',
                        backgroundColor: bg ?? T.surface,
                        border: `1px solid ${bg ? 'transparent' : T.borderSubtle}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: count ? 'pointer' : 'default',
                        transition: 'opacity 0.1s',
                      }}
                      onMouseOver={(e) => { if (count) e.currentTarget.style.opacity = '0.8'; }}
                      onMouseOut={(e) => { e.currentTarget.style.opacity = '1'; }}
                    >
                      <span style={{ fontSize: '10px', fontFamily: 'monospace', color: count ? '#fff' : T.textDimmer, fontWeight: count ? 700 : 400 }}>
                        {tech.id.split('.')[0]}
                        {tech.id.includes('.') ? <span style={{ opacity: 0.7 }}>.{tech.id.split('.')[1]}</span> : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed',
          left: tooltip.x + 12, top: tooltip.y - 10,
          backgroundColor: T.dropdownBg,
          border: `1px solid ${T.border}`,
          borderRadius: '7px',
          padding: '8px 12px',
          zIndex: 200,
          boxShadow: T.dropdownShadow,
          pointerEvents: 'none',
        }}>
          <div style={{ fontWeight: 700, fontSize: '12px', color: T.text, marginBottom: '2px' }}>
            {tooltip.tech.id}
          </div>
          <div style={{ fontSize: '11px', color: T.textMuted, marginBottom: '4px' }}>
            {tooltip.tech.name}
          </div>
          <div style={{ fontSize: '11px', color: tooltip.count ? '#FF6600' : T.textDimmer, fontWeight: 600 }}>
            {tooltip.count ? `${tooltip.count} detection${tooltip.count > 1 ? 's' : ''}` : 'No detections'}
          </div>
        </div>
      )}
    </div>
  );
}

export default function MitreHeatmap() {
  return (
    <ProGate feature="mitre_heatmap" description="Visualise detected MITRE ATT&CK techniques across your environment">
      <HeatmapInner />
    </ProGate>
  );
}
