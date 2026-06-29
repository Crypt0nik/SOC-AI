import { useEffect, useState } from 'react';
import { fetchStats } from '../api.js';
import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';

export default function StatsBar() {
  const { T } = useTheme();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      fetchStats()
        .then((s) => { if (alive) { setStats(s); setError(false); } })
        .catch(() => { if (alive) setError(true); });
    load();
    const id = setInterval(load, 5000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (error || !stats) return null;

  const hasAny = ALL_SEVERITIES.some((s) => (stats.counts?.[s] ?? 0) > 0);
  if (!hasAny) return (
    <span style={{ fontSize: '12px', color: T.textDimmer }}>No alerts in 24h</span>
  );

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      {ALL_SEVERITIES.map((sev) => {
        const count = stats.counts?.[sev] ?? 0;
        if (count === 0) return null;
        const color = SEVERITY_COLOR[sev];
        const isCritical = sev === 'CRITICAL';
        return (
          <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span
              className={isCritical ? 'dot-pulse' : ''}
              style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: color, display: 'inline-block', flexShrink: 0 }}
            />
            <span style={{ fontSize: '12px', fontWeight: 600, color, fontVariantNumeric: 'tabular-nums' }}>{count}</span>
            <span style={{ fontSize: '11px', color: T.textMuted }}>{sev}</span>
          </div>
        );
      })}
    </div>
  );
}
