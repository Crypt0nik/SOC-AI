import { useEffect, useState } from 'react';
import { fetchStats } from '../api.js';
import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';

export default function StatsBar() {
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

  if (error) return <div className="text-xs italic" style={{ color: '#4a5568' }}>Stats unavailable</div>;
  if (!stats) return <div className="text-xs italic" style={{ color: '#374151' }}>Loading…</div>;

  return (
    <div className="space-y-2.5">
      {ALL_SEVERITIES.map((sev) => {
        const count = stats.counts?.[sev] ?? 0;
        const color = SEVERITY_COLOR[sev];
        const isCritical = sev === 'CRITICAL';
        return (
          <div key={sev} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2 h-2 rounded-full flex-shrink-0${isCritical && count > 0 ? ' dot-pulse' : ''}`}
                style={{ backgroundColor: color }}
              />
              <span className="text-xs" style={{ color: '#9ca3af' }}>{sev}</span>
            </div>
            <span className="text-sm font-bold tabular-nums" style={{ color }}>{count}</span>
          </div>
        );
      })}
    </div>
  );
}
