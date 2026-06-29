import { exportUrl } from '../api.js';
import { useTheme } from '../theme.js';

export default function ExportButton({ severity }) {
  const { T } = useTheme();

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
        border: `1px solid ${T.border}`,
        borderRadius: '6px',
        padding: '5px 12px',
        fontSize: '12px',
        color: T.textMuted,
        cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: '6px',
        transition: 'all 0.1s',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.color = T.text; e.currentTarget.style.borderColor = T.textDim; }}
      onMouseLeave={(e) => { e.currentTarget.style.color = T.textMuted; e.currentTarget.style.borderColor = T.border; }}
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
