import { useState, useCallback, useRef, useEffect } from 'react';
import AlertDetail from './components/AlertDetail.jsx';
import AlertList from './components/AlertList.jsx';
import ExportButton from './components/ExportButton.jsx';
import SeverityFilter from './components/SeverityFilter.jsx';
import StatsBar from './components/StatsBar.jsx';
import { ThemeContext, DARK, LIGHT } from './theme.js';

const SORT_OPTIONS = [
  { label: 'Newest first', value: 'date_desc' },
  { label: 'Oldest first', value: 'date_asc' },
  { label: 'Severity ↓', value: 'sev_desc' },
  { label: 'Severity ↑', value: 'sev_asc' },
];

const STATUS_OPTIONS = [
  { label: 'All', value: null },
  { label: 'Triaged', value: 'triaged' },
  { label: 'Pending', value: 'untriaged' },
  { label: 'Error', value: 'error' },
];

function timeAgo(date) {
  if (!date) return '';
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  return `${Math.floor(diff / 60)}m ago`;
}

export default function App() {
  const [isDark, setIsDark] = useState(true);
  const T = isDark ? DARK : LIGHT;

  const [severity, setSeverity] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [statusFilter, setStatusFilter] = useState(null);
  const [showSort, setShowSort] = useState(false);
  const [showStatus, setShowStatus] = useState(false);
  const [alertIds, setAlertIds] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedText, setLastUpdatedText] = useState('');
  const sortRef = useRef(null);
  const statusRef = useRef(null);

  // Sync body class for scrollbar CSS
  useEffect(() => {
    document.body.className = isDark ? 'dark' : 'light';
  }, [isDark]);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (sortRef.current && !sortRef.current.contains(e.target)) setShowSort(false);
      if (statusRef.current && !statusRef.current.contains(e.target)) setShowStatus(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => setRefreshKey((k) => k + 1), 5000);
    return () => clearInterval(id);
  }, [autoRefresh]);

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

  const btnStyle = (active) => ({
    backgroundColor: 'transparent',
    border: `1px solid ${active ? T.border : T.borderSubtle}`,
    borderRadius: '6px',
    padding: '5px 8px',
    color: active ? T.text : T.textMuted,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
    transition: 'all 0.1s',
  });

  return (
    <ThemeContext.Provider value={{ T, isDark, toggle: () => setIsDark((d) => !d) }}>
      <div style={{
        backgroundColor: T.bg,
        color: T.text,
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
        transition: 'background-color 0.2s, color 0.2s',
      }}>

        {/* ── Header ── */}
        <header style={{
          backgroundColor: T.bg,
          borderBottom: `1px solid ${T.border}`,
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          gap: '10px',
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
            <span style={{ fontWeight: 700, fontSize: '14px', letterSpacing: '-0.02em', color: T.text }}>SOC-AI</span>
            <span style={{ fontSize: '11px', color: T.textMuted, borderLeft: `1px solid ${T.border}`, paddingLeft: '8px' }}>Community</span>
          </div>

          <div style={{ width: '1px', height: '18px', backgroundColor: T.border, flexShrink: 0 }} />

          {/* Search */}
          <div style={{ position: 'relative', width: '260px' }}>
            <svg style={{ position: 'absolute', left: '9px', top: '50%', transform: 'translateY(-50%)', color: T.textMuted, pointerEvents: 'none' }}
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
                backgroundColor: T.surface,
                border: `1px solid ${T.borderSubtle}`,
                borderRadius: '6px',
                padding: '5px 28px 5px 28px',
                fontSize: '13px',
                color: T.text,
                outline: 'none',
                transition: 'border-color 0.1s',
              }}
              onFocus={(e) => { e.target.style.borderColor = T.border; }}
              onBlur={(e) => { e.target.style.borderColor = T.borderSubtle; }}
            />
            {search && (
              <button onClick={() => setSearch('')} style={{
                position: 'absolute', right: '7px', top: '50%', transform: 'translateY(-50%)',
                backgroundColor: 'transparent', border: 'none', color: T.textMuted, cursor: 'pointer', padding: '2px', lineHeight: 1,
              }}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            )}
          </div>

          <div style={{ flex: 1 }} />

          {/* Stats chips */}
          <StatsBar />

          <div style={{ width: '1px', height: '18px', backgroundColor: T.border, flexShrink: 0 }} />

          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh((a) => !a)}
            title={autoRefresh ? 'Auto-refresh ON — click to pause' : 'Auto-refresh OFF — click to enable'}
            style={btnStyle(autoRefresh)}
            onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = autoRefresh ? T.text : T.textMuted; e.currentTarget.style.borderColor = autoRefresh ? T.border : T.borderSubtle; }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {autoRefresh
                ? <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>
                : <><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></>
              }
            </svg>
            <span style={{ fontSize: '11px' }}>{autoRefresh ? 'Live' : 'Paused'}</span>
          </button>

          {/* Manual refresh */}
          <button
            onClick={() => { setRefreshKey((k) => k + 1); setLastUpdated(new Date()); }}
            title="Refresh now"
            style={btnStyle(false)}
            onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>

          {/* Theme toggle */}
          <button
            onClick={() => setIsDark((d) => !d)}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={btnStyle(false)}
            onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.border; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.borderSubtle; }}
          >
            {isDark ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>

          {/* Export */}
          <ExportButton severity={severity} />
        </header>

        {/* ── Toolbar ── */}
        <div style={{
          backgroundColor: T.bg,
          borderBottom: `1px solid ${T.borderSubtle}`,
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

          <div style={{ width: '1px', height: '16px', backgroundColor: T.borderSubtle, margin: '0 4px' }} />

          {/* Status filter dropdown */}
          <div style={{ position: 'relative' }} ref={statusRef}>
            <button
              onClick={() => setShowStatus((s) => !s)}
              style={{
                backgroundColor: statusFilter ? `${T.borderSubtle}` : 'transparent',
                border: `1px solid ${statusFilter ? T.border : T.borderSubtle}`,
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '12px',
                color: statusFilter ? T.text : T.textDim,
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '5px',
                whiteSpace: 'nowrap',
                transition: 'all 0.1s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.text; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = statusFilter ? T.border : T.borderSubtle; e.currentTarget.style.color = statusFilter ? T.text : T.textDim; }}
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
              </svg>
              {STATUS_OPTIONS.find((o) => o.value === statusFilter)?.label ?? 'Status'}
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>

            {showStatus && (
              <div style={{
                position: 'absolute', left: 0, top: 'calc(100% + 4px)',
                backgroundColor: T.dropdownBg, border: `1px solid ${T.border}`,
                borderRadius: '8px', padding: '4px', zIndex: 100,
                minWidth: '140px', boxShadow: T.dropdownShadow,
              }}>
                {STATUS_OPTIONS.map((opt) => (
                  <button key={opt.label} onClick={() => { setStatusFilter(opt.value); setShowStatus(false); }}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '6px 10px', fontSize: '12px',
                      color: statusFilter === opt.value ? T.text : T.textMuted,
                      backgroundColor: statusFilter === opt.value ? T.borderSubtle : 'transparent',
                      border: 'none', borderRadius: '5px', cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => { if (statusFilter !== opt.value) e.currentTarget.style.backgroundColor = T.surfaceHover; }}
                    onMouseLeave={(e) => { if (statusFilter !== opt.value) e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div style={{ flex: 1 }} />

          {lastUpdatedText && (
            <span style={{ fontSize: '11px', color: T.textDimmer }}>Updated {lastUpdatedText}</span>
          )}

          {/* Sort dropdown */}
          <div style={{ position: 'relative' }} ref={sortRef}>
            <button
              onClick={() => setShowSort((s) => !s)}
              style={{
                backgroundColor: 'transparent',
                border: `1px solid ${T.borderSubtle}`,
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '12px',
                color: T.textDim,
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '5px',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = T.border; e.currentTarget.style.color = T.text; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.borderSubtle; e.currentTarget.style.color = T.textDim; }}
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
                position: 'absolute', right: 0, top: 'calc(100% + 4px)',
                backgroundColor: T.dropdownBg, border: `1px solid ${T.border}`,
                borderRadius: '8px', padding: '4px', zIndex: 100,
                minWidth: '160px', boxShadow: T.dropdownShadow,
              }}>
                {SORT_OPTIONS.map((opt) => (
                  <button key={opt.value} onClick={() => { setSortBy(opt.value); setShowSort(false); }}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '6px 10px', fontSize: '12px',
                      color: sortBy === opt.value ? T.text : T.textMuted,
                      backgroundColor: sortBy === opt.value ? T.borderSubtle : 'transparent',
                      border: 'none', borderRadius: '5px', cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => { if (sortBy !== opt.value) e.currentTarget.style.backgroundColor = T.surfaceHover; }}
                    onMouseLeave={(e) => { if (sortBy !== opt.value) e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Main ── */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
          <AlertList
            key={severity ?? 'all'}
            severity={severity}
            refreshKey={refreshKey}
            search={search}
            sortBy={sortBy}
            statusFilter={statusFilter}
            onSelect={setSelectedId}
            selectedId={selectedId}
            onAlertsLoaded={handleAlertsLoaded}
          />
        </main>

        {/* ── Detail panel ── */}
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
    </ThemeContext.Provider>
  );
}
