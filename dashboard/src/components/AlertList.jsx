import { useEffect, useRef, useState } from 'react';
import { deleteAlert, fetchAlerts } from '../api.js';
import { SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';

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
  const { T } = useTheme();
  const [copied, setCopied] = useState(false);
  const copy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(ip).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button onClick={copy} title="Copy IP" style={{
      backgroundColor: 'transparent', border: 'none', cursor: 'pointer', padding: 0,
      color: copied ? '#4ade80' : T.textMuted,
      fontSize: '11px', fontFamily: 'monospace',
      display: 'flex', alignItems: 'center', gap: '3px',
      transition: 'color 0.15s',
    }}>
      {copied ? (
        <>
          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
          Copied
        </>
      ) : (
        <>
          <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          {ip}
        </>
      )}
    </button>
  );
}

function AlertCard({ alert, onSelect, isSelected, onDelete }) {
  const { T } = useTheme();
  const [hovering, setHovering] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const effectiveSev = alert.triage?.severity ?? alert.severity;
  const color = SEVERITY_COLOR[effectiveSev] ?? '#666666';
  const isCritical = effectiveSev === 'CRITICAL';

  const baseBg = isCritical ? T.surfaceCritical : T.surface;
  const hoverBg = isCritical ? T.surfaceCriticalHover : T.surfaceHover;
  const baseBorder = isSelected ? T.borderSelected : isCritical ? T.borderCritical : T.borderSubtle;

  const handleDelete = (e) => {
    e.stopPropagation();
    setDeleting(true);
    deleteAlert(alert.id)
      .then(() => onDelete(alert.id))
      .catch(() => setDeleting(false));
  };

  return (
    <div
      onClick={() => onSelect(alert.id)}
      className={isCritical ? 'critical-glow' : ''}
      style={{
        backgroundColor: baseBg,
        border: `1px solid ${baseBorder}`,
        borderRadius: '8px',
        cursor: 'pointer',
        padding: '10px 14px',
        transition: 'background-color 0.1s, border-color 0.1s',
        position: 'relative',
        opacity: deleting ? 0.4 : 1,
      }}
      onMouseEnter={(e) => {
        setHovering(true);
        e.currentTarget.style.backgroundColor = hoverBg;
        if (!isSelected) e.currentTarget.style.borderColor = isCritical ? T.borderCritical : T.border;
      }}
      onMouseLeave={(e) => {
        setHovering(false);
        e.currentTarget.style.backgroundColor = baseBg;
        e.currentTarget.style.borderColor = baseBorder;
      }}
    >
      {/* Delete button — shown on hover */}
      {hovering && !deleting && (
        <button
          onClick={handleDelete}
          title="Delete alert"
          style={{
            position: 'absolute', top: '8px', right: '8px',
            backgroundColor: 'transparent',
            border: `1px solid ${T.borderSubtle}`,
            borderRadius: '4px',
            width: '22px', height: '22px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', color: T.textDim,
            transition: 'all 0.1s', zIndex: 1,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = T.errorText; e.currentTarget.style.borderColor = T.errorBorder; e.currentTarget.style.backgroundColor = T.errorBg; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = T.textDim; e.currentTarget.style.borderColor = T.borderSubtle; e.currentTarget.style.backgroundColor = 'transparent'; }}
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6"/><path d="M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
      )}
      {/* Row 1: severity indicator + rule name + time + chevron */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '5px' }}>
        {/* Severity dot */}
        <span
          className={isCritical ? 'dot-pulse' : ''}
          style={{
            display: 'inline-block', width: '7px', height: '7px',
            borderRadius: '50%', backgroundColor: color, flexShrink: 0,
          }}
        />
        {/* Severity label */}
        <span style={{
          fontSize: '10px', fontWeight: 700, letterSpacing: '0.06em',
          color, textTransform: 'uppercase', flexShrink: 0,
        }}>
          {effectiveSev}
        </span>
        {/* Rule name */}
        <span style={{
          fontWeight: 600, fontSize: '13px', color: T.text,
          flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {alert.rule_name}
        </span>
        <span style={{ fontSize: '11px', color: T.textDimmer, flexShrink: 0 }}>{timeAgo(alert.timestamp)}</span>
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={T.textDimmer} strokeWidth="2" strokeLinecap="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </div>

      {/* Row 2: rule_id · IP · count · MITRE · status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', paddingLeft: '14px' }}>
        <span style={{ fontSize: '11px', color: T.textDimmer, fontFamily: 'monospace' }}>{alert.rule_id}</span>

        {alert.source_ip && (
          <>
            <span style={{ color: T.borderSubtle }}>·</span>
            <CopyIP ip={alert.source_ip} />
          </>
        )}

        {alert.matched_count > 1 && (
          <>
            <span style={{ color: T.borderSubtle }}>·</span>
            <span style={{ fontSize: '11px', color: T.textDim }}>×{alert.matched_count}</span>
          </>
        )}

        {alert.triage?.mitre_id && (
          <>
            <span style={{ color: T.borderSubtle }}>·</span>
            <span style={{
              fontSize: '10px', fontFamily: 'monospace', color: T.mitreText,
              backgroundColor: T.mitreBg, padding: '1px 5px',
              borderRadius: '3px', border: `1px solid ${T.mitreBorder}`,
            }}>
              {alert.triage.mitre_id}
            </span>
          </>
        )}

        <div style={{ flex: 1 }} />

        {alert.status === 'triaged' && (
          <span style={{
            fontSize: '10px', color: T.triagedText, backgroundColor: T.triagedBg,
            border: `1px solid ${T.triagedBorder}`, borderRadius: '4px', padding: '1px 6px',
          }}>triaged ✓</span>
        )}
        {alert.status === 'error' && (
          <span style={{
            fontSize: '10px', color: T.errorText, backgroundColor: T.errorBg,
            border: `1px solid ${T.errorBorder}`, borderRadius: '4px', padding: '1px 6px',
          }}>error</span>
        )}
        {alert.status === 'untriaged' && (
          <span style={{
            fontSize: '10px', color: T.textDimmer, backgroundColor: 'transparent',
            border: `1px solid ${T.borderSubtle}`, borderRadius: '4px', padding: '1px 6px',
          }}>pending</span>
        )}
      </div>
    </div>
  );
}

export default function AlertList({ severity, refreshKey, search, sortBy, statusFilter, onSelect, selectedId, onAlertsLoaded, onDeleted }) {
  const { T } = useTheme();
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animate, setAnimate] = useState(true);
  const prevPage = useRef(page);
  const isFirst = useRef(true);

  useEffect(() => { setPage(1); }, [severity]);

  useEffect(() => {
    const pageChanged = prevPage.current !== page;
    prevPage.current = page;
    const shouldAnimate = isFirst.current || pageChanged;
    isFirst.current = false;
    setAnimate(shouldAnimate);

    let alive = true;
    setLoading(true);
    setError(null);
    fetchAlerts({ severity, page, pageSize: PAGE_SIZE })
      .then((d) => { if (alive) setData(d); })
      .catch((e) => { if (alive) setError(e.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [severity, page, refreshKey]);

  // Client-side filters + sort
  let filtered = data?.items ?? [];
  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter((a) =>
      (a.rule_name ?? '').toLowerCase().includes(q) ||
      (a.source_ip ?? '').toLowerCase().includes(q),
    );
  }
  if (statusFilter) {
    filtered = filtered.filter((a) => a.status === statusFilter);
  }
  filtered = sortAlerts(filtered, sortBy);

  useEffect(() => {
    if (!data) return;
    let items = data.items;
    const q = search?.toLowerCase();
    if (q) items = items.filter((a) =>
      (a.rule_name ?? '').toLowerCase().includes(q) ||
      (a.source_ip ?? '').toLowerCase().includes(q),
    );
    if (statusFilter) items = items.filter((a) => a.status === statusFilter);
    items = sortAlerts(items, sortBy);
    onAlertsLoaded?.(items.map((a) => a.id), new Date());
  }, [data, search, sortBy, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  const paginationBtnStyle = (disabled) => ({
    padding: '4px 10px', borderRadius: '5px',
    border: `1px solid ${T.border}`,
    backgroundColor: 'transparent',
    color: disabled ? T.borderSubtle : T.textMuted,
    cursor: disabled ? 'default' : 'pointer',
    fontSize: '12px',
    transition: 'color 0.1s, border-color 0.1s',
  });

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: T.textDimmer, fontSize: '13px' }}>
        Loading alerts…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0' }}>
        <p style={{ color: T.errorText, fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Failed to load alerts</p>
        <p style={{ color: T.textDimmer, fontSize: '12px' }}>{error}</p>
        <p style={{ color: T.textDimmer, fontSize: '11px', marginTop: '4px' }}>
          API: <code style={{ fontFamily: 'monospace' }}>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
        </p>
      </div>
    );
  }

  if (!data || filtered.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: T.textDimmer }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px', display: 'block' }}>
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <p style={{ fontSize: '14px', color: T.textDim, marginBottom: '4px' }}>No alerts found</p>
        {(severity || search || statusFilter) && (
          <p style={{ fontSize: '12px' }}>Try clearing the filters.</p>
        )}
      </div>
    );
  }

  return (
    <div className={animate ? 'fade-in' : ''}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {filtered.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onSelect={onSelect}
            isSelected={alert.id === selectedId}
            onDelete={(id) => {
              setData((prev) => prev ? { ...prev, items: prev.items.filter((a) => a.id !== id), total: prev.total - 1 } : prev);
              onDeleted?.(id);
            }}
          />
        ))}
      </div>

      {/* Pagination */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginTop: '20px', fontSize: '12px', color: T.textDimmer,
      }}>
        <span>
          {(search || statusFilter)
            ? `${filtered.length} match${filtered.length !== 1 ? 'es' : ''} · ${data.total} total`
            : `${data.total} alert${data.total !== 1 ? 's' : ''}`}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            style={paginationBtnStyle(page <= 1)}
            onMouseEnter={(e) => { if (page > 1) { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; } }}
            onMouseLeave={(e) => { e.currentTarget.style.color = page <= 1 ? T.borderSubtle : T.textMuted; e.currentTarget.style.borderColor = T.border; }}
          >
            ← Prev
          </button>
          <span style={{ color: T.textDim }}>{page} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            style={paginationBtnStyle(page >= totalPages)}
            onMouseEnter={(e) => { if (page < totalPages) { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; } }}
            onMouseLeave={(e) => { e.currentTarget.style.color = page >= totalPages ? T.borderSubtle : T.textMuted; e.currentTarget.style.borderColor = T.border; }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
