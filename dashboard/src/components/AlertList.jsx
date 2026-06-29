import { useEffect, useState } from 'react';
import { fetchAlerts } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';

const PAGE_SIZE = 20;
const SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };

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

function sortAlerts(items, sortBy) {
  const sorted = [...items];
  switch (sortBy) {
    case 'date_asc': return sorted.reverse();
    case 'sev_desc': return sorted.sort((a, b) => {
      const sa = SEV_ORDER[a.triage?.severity ?? a.severity] ?? 99;
      const sb = SEV_ORDER[b.triage?.severity ?? b.severity] ?? 99;
      return sa - sb;
    });
    case 'sev_asc': return sorted.sort((a, b) => {
      const sa = SEV_ORDER[a.triage?.severity ?? a.severity] ?? 99;
      const sb = SEV_ORDER[b.triage?.severity ?? b.severity] ?? 99;
      return sb - sa;
    });
    default: return sorted;
  }
}

function CopyIP({ ip }) {
  const [copied, setCopied] = useState(false);
  const copy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(ip).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button
      onClick={copy}
      title="Copy IP address"
      style={{
        backgroundColor: 'transparent',
        border: 'none',
        cursor: 'pointer',
        padding: 0,
        color: copied ? '#4ade80' : '#71717a',
        fontSize: '11px',
        fontFamily: 'monospace',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        transition: 'color 0.15s',
      }}
    >
      {copied ? (
        <>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
          Copied!
        </>
      ) : (
        <>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          {ip}
        </>
      )}
    </button>
  );
}

function AlertCard({ alert, onSelect, isSelected }) {
  const effectiveSev = alert.triage?.severity ?? alert.severity;
  const color = SEVERITY_COLOR[effectiveSev] ?? '#666666';
  const isCritical = effectiveSev === 'CRITICAL';

  return (
    <div
      onClick={() => onSelect(alert.id)}
      className={isCritical ? 'critical-glow' : ''}
      style={{
        backgroundColor: isCritical ? '#120404' : '#111113',
        border: `1px solid ${isSelected ? '#3f3f46' : isCritical ? '#3a0a0a' : '#1c1c1f'}`,
        borderLeft: `3px solid ${color}`,
        borderRadius: '8px',
        cursor: 'pointer',
        padding: '11px 14px',
        transition: 'background-color 0.1s, border-color 0.1s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = isCritical ? '#180808' : '#18181b';
        if (!isSelected) e.currentTarget.style.borderColor = isCritical ? '#4a1010' : '#27272a';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isCritical ? '#120404' : '#111113';
        e.currentTarget.style.borderColor = isSelected ? '#3f3f46' : isCritical ? '#3a0a0a' : '#1c1c1f';
      }}
    >
      {/* Row 1: severity dot + rule name + time + chevron */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
        <span
          className={isCritical ? 'dot-pulse' : ''}
          style={{
            display: 'inline-block',
            width: '7px', height: '7px',
            borderRadius: '50%',
            backgroundColor: color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontWeight: 600, fontSize: '13px', color: '#fafafa', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {alert.rule_name}
        </span>
        <span style={{ fontSize: '11px', color: '#3f3f46', flexShrink: 0 }}>{timeAgo(alert.timestamp)}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#3f3f46" strokeWidth="2" strokeLinecap="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </div>

      {/* Row 2: rule_id · IP · count · MITRE · status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '11px', color: '#3f3f46', fontFamily: 'monospace' }}>{alert.rule_id}</span>

        {alert.source_ip && (
          <>
            <span style={{ color: '#27272a' }}>·</span>
            <CopyIP ip={alert.source_ip} />
          </>
        )}

        {alert.matched_count > 1 && (
          <>
            <span style={{ color: '#27272a' }}>·</span>
            <span style={{ fontSize: '11px', color: '#52525b' }}>×{alert.matched_count}</span>
          </>
        )}

        {alert.triage?.mitre_id && (
          <>
            <span style={{ color: '#27272a' }}>·</span>
            <span style={{
              fontSize: '10px',
              fontFamily: 'monospace',
              color: '#60a5fa',
              backgroundColor: '#0c1b2e',
              padding: '1px 5px',
              borderRadius: '3px',
              border: '1px solid #1e3a5f',
            }}>
              {alert.triage.mitre_id}
            </span>
          </>
        )}

        <div style={{ flex: 1 }} />

        {alert.status === 'triaged' && (
          <span style={{ fontSize: '10px', color: '#4ade80', backgroundColor: '#0d2211', border: '1px solid #166534', borderRadius: '4px', padding: '1px 6px' }}>
            triaged ✓
          </span>
        )}
        {alert.status === 'error' && (
          <span style={{ fontSize: '10px', color: '#f87171', backgroundColor: '#2a0f0f', border: '1px solid #991b1b', borderRadius: '4px', padding: '1px 6px' }}>
            error
          </span>
        )}
        {alert.status === 'untriaged' && (
          <span style={{ fontSize: '10px', color: '#3f3f46', backgroundColor: 'transparent', border: '1px solid #27272a', borderRadius: '4px', padding: '1px 6px' }}>
            pending
          </span>
        )}
      </div>
    </div>
  );
}

export default function AlertList({ severity, search, sortBy, onSelect, selectedId, onAlertsLoaded }) {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { setPage(1); }, [severity]);

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

  // Compute filtered + sorted items
  let filtered = data?.items ?? [];
  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter(
      (a) =>
        (a.rule_name ?? '').toLowerCase().includes(q) ||
        (a.source_ip ?? '').toLowerCase().includes(q),
    );
  }
  filtered = sortAlerts(filtered, sortBy);

  // Notify parent of current visible IDs
  useEffect(() => {
    if (!data) return;
    let items = data.items;
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (a) =>
          (a.rule_name ?? '').toLowerCase().includes(q) ||
          (a.source_ip ?? '').toLowerCase().includes(q),
      );
    }
    items = sortAlerts(items, sortBy);
    onAlertsLoaded?.(items.map((a) => a.id), new Date());
  }, [data, search, sortBy]); // eslint-disable-line react-hooks/exhaustive-deps

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: '#3f3f46', fontSize: '13px' }}>
        Loading alerts…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0' }}>
        <p style={{ color: '#f87171', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Failed to load alerts</p>
        <p style={{ color: '#3f3f46', fontSize: '12px' }}>{error}</p>
        <p style={{ color: '#27272a', fontSize: '11px', marginTop: '4px' }}>
          API: <code style={{ fontFamily: 'monospace' }}>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
        </p>
      </div>
    );
  }

  if (!data || filtered.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: '#3f3f46' }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px', display: 'block' }}>
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <p style={{ fontSize: '14px', color: '#52525b', marginBottom: '4px' }}>No alerts found</p>
        {(severity || search) && (
          <p style={{ fontSize: '12px' }}>Try clearing the filters.</p>
        )}
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {filtered.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onSelect={onSelect}
            isSelected={alert.id === selectedId}
          />
        ))}
      </div>

      {/* Pagination */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '20px',
        fontSize: '12px',
        color: '#3f3f46',
      }}>
        <span>
          {search
            ? `${filtered.length} match${filtered.length !== 1 ? 'es' : ''} · ${data.total} total`
            : `${data.total} alert${data.total !== 1 ? 's' : ''}`}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            style={{
              padding: '4px 10px',
              borderRadius: '5px',
              border: '1px solid #27272a',
              backgroundColor: 'transparent',
              color: page <= 1 ? '#27272a' : '#71717a',
              cursor: page <= 1 ? 'default' : 'pointer',
              fontSize: '12px',
            }}
          >
            ← Prev
          </button>
          <span style={{ color: '#52525b' }}>{page} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            style={{
              padding: '4px 10px',
              borderRadius: '5px',
              border: '1px solid #27272a',
              backgroundColor: 'transparent',
              color: page >= totalPages ? '#27272a' : '#71717a',
              cursor: page >= totalPages ? 'default' : 'pointer',
              fontSize: '12px',
            }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
