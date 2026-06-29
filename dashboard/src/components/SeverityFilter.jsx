import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';

export default function SeverityFilter({ selected, onChange }) {
  const buttons = [{ label: 'All', value: null }, ...ALL_SEVERITIES.map((s) => ({ label: s, value: s }))];

  return (
    <div className="flex flex-col gap-1.5">
      {buttons.map(({ label, value }) => {
        const active = selected === value;
        const color = value ? SEVERITY_COLOR[value] : '#6b7280';
        return (
          <button
            key={label}
            onClick={() => onChange(value)}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-xs font-semibold transition-all text-left"
            style={
              active
                ? {
                    backgroundColor: value ? `${color}22` : '#1f2937',
                    borderLeft: `3px solid ${color}`,
                    color: value ? color : '#e2e8f0',
                    paddingLeft: '9px',
                  }
                : {
                    backgroundColor: 'transparent',
                    borderLeft: '3px solid transparent',
                    color: '#6b7280',
                    paddingLeft: '9px',
                  }
            }
          >
            {value && (
              <span
                className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: active ? color : '#374151' }}
              />
            )}
            {label}
          </button>
        );
      })}
    </div>
  );
}
