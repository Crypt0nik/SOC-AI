import { useEffect, useState } from 'react';
import { fetchAlerts } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';

const PAGE_SIZE = 20;

function SeverityBadge({ severity }) {
  const color = SEVERITY_COLOR[severity] ?? '#666666';
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
      style={{ backgroundColor: color }}
    >
      {severity}
    </span>
  );
}

function StatusBadge({ status }) {
  const styles = {
    triaged:   { backgroundColor: '#0d2211', color: '#4ade80', border: '1px solid #166534' },
    error:     { backgroundColor: '#2a0f0f', color: '#f87171', border: '1px solid #991b1b' },
    untriaged: { backgroundColor: '#1f1a0a', color: '#facc15', border: '1px solid #713f12' },
  };
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-medium"
      style={styles[status] ?? styles.untriaged}
    >
      {status}
    </span>
  );
}

function formatTs(ts) {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return ts;
  }
}

function AlertCard({ alert, onSelect }) {
  const effectiveSev = alert.triage?.severity ?? alert.severity;
  const color = SEVERITY_COLOR[effectiveSev] ?? '#666666';
  const isCritical = effectiveSev === 'CRITICAL';

  return (
    <div
      onClick={() => onSelect(alert.id)}
      className={`relative rounded-lg cursor-pointer transition-all duration-150 ${isCritical ? 'critical-glow' : ''}`}
      style={{
        backgroundColor: '#0f1524',
        border: `1px solid ${isCritical ? '#3a0a0a' : '#1e2a3a'}`,
        borderLeft: `4px solid ${color}`,
      }}
      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#141c30'; }}
      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#0f1524'; }}
    >
      <div className="px-4 py-3.5">
        {/* Top row: severity badge + rule name + status */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <SeverityBadge severity={effectiveSev} />
            <span className="text-sm font-semibold text-white truncate">{alert.rule_name}</span>
          </div>
          <StatusBadge status={alert.status} />
        </div>

        {/* Rule ID */}
        <div className="text-xs mb-2.5" style={{ color: '#4a5568' }}>
          {alert.rule_id}
        </div>

        {/* Metadata row */}
        <div className="flex items-center gap-4 flex-wrap">
          {alert.source_ip && (
            <span className="flex items-center gap-1 text-xs font-mono" style={{ color: '#9ca3af' }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              {alert.source_ip}
            </span>
          )}
          <span className="text-xs" style={{ color: '#4a5568' }}>
            ×{alert.matched_count}
          </span>
          <span className="text-xs" style={{ color: '#4a5568' }}>
            {formatTs(alert.timestamp)}
          </span>
          {alert.triage?.mitre_id && (
            <span
              className="text-xs px-1.5 py-0.5 rounded font-mono"
              style={{ backgroundColor: '#0d1b2a', color: '#60a5fa', border: '1px solid #1e3a5f' }}
            >
              {alert.triage.mitre_id}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AlertList({ severity, onSelect }) {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPage(1);
  }, [severity]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fetchAlerts({ severity, page, pageSize: PAGE_SIZE })
      .then((d) => { if (alive) setData(d); })
      .catch((e) => { if (alive) setError(e.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [severity, page]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center py-20" style={{ color: '#4a5568' }}>
        <div className="text-sm">Loading alerts…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16" style={{ color: '#f87171' }}>
        <p className="font-semibold">Failed to load alerts</p>
        <p className="text-sm mt-1" style={{ color: '#4a5568' }}>{error}</p>
        <p className="text-xs mt-2" style={{ color: '#374151' }}>
          API:{' '}
          <code style={{ color: '#6b7280' }}>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
        </p>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-20" style={{ color: '#4a5568' }}>
        <p className="text-base font-medium mb-1" style={{ color: '#6b7280' }}>No alerts found</p>
        {severity && <p className="text-sm">Try clearing the severity filter.</p>}
      </div>
    );
  }

  return (
    <div>
      {/* Cards */}
      <div className="space-y-2 fade-in">
        {data.items.map((alert) => (
          <AlertCard key={alert.id} alert={alert} onSelect={onSelect} />
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-5 text-xs" style={{ color: '#4a5568' }}>
        <span>{data.total} alert{data.total !== 1 ? 's' : ''}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 rounded transition-colors disabled:opacity-30"
            style={{ border: '1px solid #1e2a3a', color: '#6b7280' }}
            onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.borderColor = '#374151'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#1e2a3a'; }}
          >
            ← Prev
          </button>
          <span style={{ color: '#374151' }}>
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1.5 rounded transition-colors disabled:opacity-30"
            style={{ border: '1px solid #1e2a3a', color: '#6b7280' }}
            onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.borderColor = '#374151'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#1e2a3a'; }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
