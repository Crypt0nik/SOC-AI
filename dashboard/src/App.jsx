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
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-gray-900 border-b border-gray-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold tracking-tight text-white">
              SOC-AI
            </span>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded font-medium">
              Community Edition
            </span>
          </div>
          <StatsBar />
        </div>
      </header>

      {/* Toolbar */}
      <div className="sticky top-[57px] z-30 flex items-center justify-between gap-4 px-6 py-2.5 bg-gray-900 border-b border-gray-800">
        <SeverityFilter selected={severity} onChange={setSeverity} />
        <ExportButton severity={severity} />
      </div>

      {/* Main content */}
      <main className="px-6 py-5">
        {/* key resets pagination when severity filter changes */}
        <AlertList
          key={severity ?? 'all'}
          severity={severity}
          onSelect={setSelectedId}
        />
      </main>

      {/* Alert detail side panel */}
      {selectedId !== null && (
        <AlertDetail alertId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}
