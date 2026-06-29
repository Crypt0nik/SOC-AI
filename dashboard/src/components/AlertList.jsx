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
    triaged:   { backgroundColor: '#1a3a1a', color: '#4ade80', border: '1px solid #166534' },
    error:     { backgroundColor: '#3a1a1a', color: '#f87171', border: '1px solid #991b1b' },
    untriaged: { backgroundColor: '#2a2a1a', color: '#facc15', border: '1px solid #713f12' },
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

export default function AlertList({ severity, onSelect }) {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Reset page when severity filter changes
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
    return <div className="text-center py-16 text-gray-500">Loading alerts…</div>;
  }

  if (error) {
    return (
      <div className="text-center py-16 text-red-400">
        <p className="font-semibold">Failed to load alerts</p>
        <p className="text-sm text-gray-500 mt-1">{error}</p>
        <p className="text-xs text-gray-600 mt-2">
          Make sure the API is running at{' '}
          <code className="text-gray-400">{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
        </p>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="text-lg">No alerts found</p>
        {severity && (
          <p className="text-sm mt-1">Try clearing the severity filter.</p>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-900 text-gray-400 text-left text-xs uppercase tracking-wider">
              <th className="px-4 py-3 w-12">#</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Rule</th>
              <th className="px-4 py-3">Source IP</th>
              <th className="px-4 py-3 text-center">Count</th>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {data.items.map((alert) => {
              const effectiveSev = alert.triage?.severity ?? alert.severity;
              return (
                <tr
                  key={alert.id}
                  onClick={() => onSelect(alert.id)}
                  className="bg-gray-900 hover:bg-gray-800 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-gray-600 font-mono text-xs">
                    {alert.id}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={effectiveSev} />
                  </td>
                  <td className="px-4 py-3 text-gray-200">
                    <div className="font-medium">{alert.rule_name}</div>
                    <div className="text-xs text-gray-500">{alert.rule_id}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-300">
                    {alert.source_ip ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300">
                    {alert.matched_count}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {formatTs(alert.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={alert.status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 text-sm text-gray-400">
        <span>
          {data.total} alert{data.total !== 1 ? 's' : ''} total
        </span>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1 rounded border border-gray-700 disabled:opacity-30 hover:border-gray-500 transition-colors"
          >
            Prev
          </button>
          <span className="text-xs">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1 rounded border border-gray-700 disabled:opacity-30 hover:border-gray-500 transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
