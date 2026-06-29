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
      style={{
        backgroundColor: 'transparent',
        border: '1px solid #27272a',
        borderRadius: '6px',
        padding: '5px 12px',
        fontSize: '12px',
        color: '#71717a',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        transition: 'all 0.1s',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.color = '#fafafa'; e.currentTarget.style.borderColor = '#3f3f46'; }}
      onMouseLeave={(e) => { e.currentTarget.style.color = '#71717a'; e.currentTarget.style.borderColor = '#27272a'; }}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Export
    </button>
  );
}
