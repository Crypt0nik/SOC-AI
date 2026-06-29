import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';
import { useTheme } from '../theme.js';

export default function SeverityFilter({ selected, onChange }) {
  const { T } = useTheme();
  const buttons = [{ label: 'All', value: null }, ...ALL_SEVERITIES.map((s) => ({ label: s, value: s }))];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      {buttons.map(({ label, value }) => {
        const active = selected === value;
        const color = value ? SEVERITY_COLOR[value] : null;
        return (
          <button
            key={label}
            onClick={() => onChange(value)}
            style={{
              padding: '3px 10px',
              borderRadius: '5px',
              fontSize: '12px',
              fontWeight: active ? 600 : 400,
              cursor: 'pointer',
              border: `1px solid ${active
                ? (color ? color : T.borderSelected)
                : T.borderSubtle}`,
              backgroundColor: active
                ? (color ? `${color}18` : T.surfaceHover)
                : 'transparent',
              color: active
                ? (color ? color : T.text)
                : T.textDim,
              transition: 'all 0.1s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.borderColor = T.border;
                e.currentTarget.style.color = T.textMuted;
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.borderColor = T.borderSubtle;
                e.currentTarget.style.color = T.textDim;
              }
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
