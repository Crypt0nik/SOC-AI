import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';

export default function SeverityFilter({ selected, onChange }) {
  const buttons = [{ label: 'All', value: null }, ...ALL_SEVERITIES.map((s) => ({ label: s, value: s }))];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      {buttons.map(({ label, value }) => {
        const active = selected === value;
        const color = value ? SEVERITY_COLOR[value] : '#fafafa';
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
              border: `1px solid ${active ? (value ? color : '#3f3f46') : '#1c1c1f'}`,
              backgroundColor: active ? (value ? `${color}20` : '#1c1c1f') : 'transparent',
              color: active ? (value ? color : '#fafafa') : '#52525b',
              transition: 'all 0.1s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.borderColor = '#27272a';
                e.currentTarget.style.color = '#a1a1aa';
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.borderColor = '#1c1c1f';
                e.currentTarget.style.color = '#52525b';
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
