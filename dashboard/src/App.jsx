import { useState } from 'react';
import AlertDetail from './components/AlertDetail.jsx';
import AlertList from './components/AlertList.jsx';
import ExportButton from './components/ExportButton.jsx';
import SeverityFilter from './components/SeverityFilter.jsx';
import StatsBar from './components/StatsBar.jsx';

export default function App() {
  const [severity, setSeverity] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0' }}>
      {/* ── Sidebar ── */}
      <aside
        className="w-60 flex-shrink-0 flex flex-col overflow-y-auto"
        style={{ backgroundColor: '#0f1524', borderRight: '1px solid #1e2a3a' }}
      >
        {/* Logo */}
        <div className="px-5 py-5" style={{ borderBottom: '1px solid #1e2a3a' }}>
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: '#FF0000' }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div>
              <div className="text-white font-bold text-sm leading-none tracking-wide">SOC-AI</div>
              <div className="text-xs mt-0.5" style={{ color: '#4a5568' }}>Community Edition</div>
            </div>
          </div>
        </div>

        {/* Severity filter */}
        <div className="px-4 py-4" style={{ borderBottom: '1px solid #1e2a3a' }}>
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#4a5568' }}>
            Severity
          </div>
          <SeverityFilter selected={severity} onChange={setSeverity} />
        </div>

        {/* Stats 24h */}
        <div className="px-4 py-4" style={{ borderBottom: '1px solid #1e2a3a' }}>
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#4a5568' }}>
            Last 24 hours
          </div>
          <StatsBar />
        </div>

        <div className="flex-1" />

        {/* Export */}
        <div className="px-4 py-4" style={{ borderTop: '1px solid #1e2a3a' }}>
          <ExportButton severity={severity} />
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 overflow-y-auto">
        <div className="px-6 py-6">
          <div className="mb-5">
            <h1 className="text-xl font-bold text-white tracking-tight">Alert Dashboard</h1>
            <p className="text-sm mt-0.5" style={{ color: '#4a5568' }}>
              {severity ? `Showing ${severity} alerts` : 'All alerts — real-time LLM triage'}
            </p>
          </div>
          <AlertList
            key={severity ?? 'all'}
            severity={severity}
            onSelect={setSelectedId}
          />
        </div>
      </main>

      {/* ── Detail panel ── */}
      {selectedId !== null && (
        <AlertDetail alertId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
