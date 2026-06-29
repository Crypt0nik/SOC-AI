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

  if (error) {
    return (
      <div className="text-xs text-gray-500 italic">Stats unavailable</div>
    );
  }

  if (!stats) {
    return <div className="text-xs text-gray-600 italic">Loading stats…</div>;
  }

  return (
    <div className="flex items-center gap-3 text-xs font-semibold">
      {ALL_SEVERITIES.map((sev) => (
        <span key={sev} className="flex items-center gap-1">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: SEVERITY_COLOR[sev] }}
          />
          <span className="text-gray-400">{sev}</span>
          <span
            className="font-bold"
            style={{ color: SEVERITY_COLOR[sev] }}
          >
            {stats.counts?.[sev] ?? 0}
          </span>
        </span>
      ))}
      <span className="text-gray-600 ml-1">/ 24h</span>
    </div>
  );
}
