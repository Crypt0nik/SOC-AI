import { exportUrl } from '../api.js';

export default function ExportButton({ severity }) {
  const handleClick = () => {
    const url = exportUrl(severity);
    const a = document.createElement('a');
    a.href = url;
    a.download = `soc-ai-alerts${severity ? '-' + severity : ''}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <button
      onClick={handleClick}
      className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded text-xs font-semibold transition-all"
      style={{
        backgroundColor: '#111827',
        border: '1px solid #1e2a3a',
        color: '#6b7280',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#374151';
        e.currentTarget.style.color = '#e2e8f0';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = '#1e2a3a';
        e.currentTarget.style.color = '#6b7280';
      }}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Export JSON
    </button>
  );
}
