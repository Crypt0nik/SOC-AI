import { ALL_SEVERITIES, SEVERITY_COLOR } from '../severity.js';

export default function SeverityFilter({ selected, onChange }) {
  const buttons = [{ label: 'All', value: null }, ...ALL_SEVERITIES.map((s) => ({ label: s, value: s }))];

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {buttons.map(({ label, value }) => {
        const active = selected === value;
        const color = value ? SEVERITY_COLOR[value] : null;
        return (
          <button
            key={label}
            onClick={() => onChange(value)}
            className="px-3 py-1 rounded text-xs font-semibold border transition-all"
            style={
              active
                ? {
                    backgroundColor: color ?? '#374151',
                    borderColor: color ?? '#374151',
                    color: '#ffffff',
                  }
                : {
                    backgroundColor: 'transparent',
                    borderColor: color ?? '#4B5563',
                    color: color ?? '#9CA3AF',
                  }
            }
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
