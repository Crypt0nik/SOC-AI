import { useState, useCallback, useRef, useEffect } from 'react';
import AlertDetail from './components/AlertDetail.jsx';
import AlertList from './components/AlertList.jsx';
import ExportButton from './components/ExportButton.jsx';
import SeverityFilter from './components/SeverityFilter.jsx';
import StatsBar from './components/StatsBar.jsx';

const SORT_OPTIONS = [
  { label: 'Newest first', value: 'date_desc' },
  { label: 'Oldest first', value: 'date_asc' },
  { label: 'Severity ↓', value: 'sev_desc' },
  { label: 'Severity ↑', value: 'sev_asc' },
];

function timeAgo(date) {
  if (!date) return '';
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  return `${Math.floor(diff / 60)}m ago`;
}

const S = {
  bg: '#09090b',
  surface: '#111113',
  border: '#27272a',
  borderSubtle: '#1c1c1f',
  text: '#fafafa',
  muted: '#71717a',
  dim: '#52525b',
};

export default function App() {
  const [severity, setSeverity] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [showSort, setShowSort] = useState(false);
  const [alertIds, setAlertIds] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedText, setLastUpdatedText] = useState('');
  const sortRef = useRef(null);

  // Close sort dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (sortRef.current && !sortRef.current.contains(e.target)) setShowSort(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Tick "Updated X ago"
  useEffect(() => {
    if (!lastUpdated) return;
    setLastUpdatedText(timeAgo(lastUpdated));
    const id = setInterval(() => setLastUpdatedText(timeAgo(lastUpdated)), 5000);
    return () => clearInterval(id);
  }, [lastUpdated]);

  const handleAlertsLoaded = useCallback((ids, updatedAt) => {
    setAlertIds(ids);
    setLastUpdated(updatedAt);
    setLastUpdatedText(timeAgo(updatedAt));
  }, []);

  const navigate = useCallback((dir) => {
    if (selectedId === null || alertIds.length === 0) return;
    const idx = alertIds.indexOf(selectedId);
    if (idx === -1) return;
    const next = alertIds[idx + dir];
    if (next !== undefined) setSelectedId(next);
  }, [selectedId, alertIds]);

  const currentIdx = selectedId !== null ? alertIds.indexOf(selectedId) : -1;

  return (
    <div style={{
      backgroundColor: S.bg,
      color: S.text,
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
    }}>

      {/* ── Header ────────────────────────────────────────────── */}
      <header style={{
        backgroundColor: S.bg,
        borderBottom: `1px solid ${S.border}`,
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: '12px',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <div style={{
            width: '26px', height: '26px',
            backgroundColor: '#FF0000',
            borderRadius: '6px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <span style={{ fontWeight: 700, fontSize: '14px', letterSpacing: '-0.02em' }}>SOC-AI</span>
          <span style={{ fontSize: '11px', color: S.muted, borderLeft: `1px solid ${S.border}`, paddingLeft: '8px' }}>Community</span>
        </div>

        <div style={{ width: '1px', height: '18px', backgroundColor: S.border }} />

        {/* Search */}
        <div style={{ position: 'relative', width: '280px' }}>
          <svg style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: S.muted, pointerEvents: 'none' }}
            width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="Search rule or IP…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: S.surface,
              border: `1px solid ${S.borderSubtle}`,
              borderRadius: '6px',
              padding: '5px 28px 5px 30px',
              fontSize: '13px',
              color: S.text,
              outline: 'none',
              transition: 'border-color 0.1s',
            }}
            onFocus={(e) => { e.target.style.borderColor = S.border; }}
            onBlur={(e) => { e.target.style.borderColor = S.borderSubtle; }}
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              style={{
                position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)',
                backgroundColor: 'transparent', border: 'none', color: S.muted,
                cursor: 'pointer', padding: '2px', lineHeight: 1,
              }}
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
        </div>

        <div style={{ flex: 1 }} />

        {/* Stats chips */}
        <StatsBar />

        <div style={{ width: '1px', height: '18px', backgroundColor: S.border }} />

        {/* Refresh */}
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          title="Refresh alerts"
          style={{
            backgroundColor: 'transparent',
            border: `1px solid ${S.borderSubtle}`,
            borderRadius: '6px',
            padding: '5px 8px',
            color: S.muted,
            cursor: 'pointer',
            display: 'flex', alignItems: 'center',
            transition: 'all 0.1s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = S.text; e.currentTarget.style.borderColor = S.border; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = S.muted; e.currentTarget.style.borderColor = S.borderSubtle; }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>

        {/* Export */}
        <ExportButton severity={severity} />
      </header>

      {/* ── Toolbar ───────────────────────────────────────────── */}
      <div style={{
        backgroundColor: S.bg,
        borderBottom: `1px solid ${S.borderSubtle}`,
        height: '44px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: '6px',
        position: 'sticky',
        top: '56px',
        zIndex: 39,
      }}>
        <SeverityFilter selected={severity} onChange={setSeverity} />

        <div style={{ flex: 1 }} />

        {lastUpdatedText && (
          <span style={{ fontSize: '11px', color: '#27272a' }}>Updated {lastUpdatedText}</span>
        )}

        {/* Sort dropdown */}
        <div style={{ position: 'relative' }} ref={sortRef}>
          <button
            onClick={() => setShowSort((s) => !s)}
            style={{
              backgroundColor: 'transparent',
              border: `1px solid ${S.borderSubtle}`,
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px',
              color: S.muted,
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '5px',
              whiteSpace: 'nowrap',
            }}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="21" y1="10" x2="7" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/>
              <line x1="21" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="7" y2="18"/>
            </svg>
            {SORT_OPTIONS.find((o) => o.value === sortBy)?.label}
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>

          {showSort && (
            <div style={{
              position: 'absolute',
              right: 0,
              top: 'calc(100% + 4px)',
              backgroundColor: S.surface,
              border: `1px solid ${S.border}`,
              borderRadius: '8px',
              padding: '4px',
              zIndex: 100,
              minWidth: '160px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}>
              {SORT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setSortBy(opt.value); setShowSort(false); }}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '6px 10px',
                    fontSize: '12px',
                    color: sortBy === opt.value ? S.text : S.muted,
                    backgroundColor: sortBy === opt.value ? '#1c1c1f' : 'transparent',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => { if (sortBy !== opt.value) e.currentTarget.style.backgroundColor = '#18181b'; }}
                  onMouseLeave={(e) => { if (sortBy !== opt.value) e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Main ──────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
        <AlertList
          key={`${severity ?? 'all'}-${refreshKey}`}
          severity={severity}
          search={search}
          sortBy={sortBy}
          onSelect={setSelectedId}
          selectedId={selectedId}
          onAlertsLoaded={handleAlertsLoaded}
        />
      </main>

      {/* ── Detail panel ──────────────────────────────────────── */}
      {selectedId !== null && (
        <AlertDetail
          alertId={selectedId}
          onClose={() => setSelectedId(null)}
          onNavigate={navigate}
          canPrev={currentIdx > 0}
          canNext={currentIdx !== -1 && currentIdx < alertIds.length - 1}
        />
      )}
    </div>
  );
}
