import { usePlan } from '../plan.jsx';
import { useTheme } from '../theme.js';

export default function ProGate({ feature, description, children }) {
  const { features } = usePlan();
  const { T } = useTheme();

  if (features.includes(feature)) return children;

  return (
    <div style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden', minHeight: '120px' }}>
      <div style={{ filter: 'blur(3px)', pointerEvents: 'none', userSelect: 'none', opacity: 0.5 }}>
        {children}
      </div>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        backgroundColor: T.overlay,
        backdropFilter: 'blur(4px)',
        gap: '6px',
      }}>
        <span style={{ fontSize: '24px', lineHeight: 1 }}>⚡</span>
        <span style={{ color: '#FF6600', fontWeight: 700, fontSize: '13px' }}>Pro Feature</span>
        {description && (
          <span style={{ color: T.textMuted, fontSize: '12px', textAlign: 'center', maxWidth: '220px', lineHeight: 1.4 }}>
            {description}
          </span>
        )}
        <a
          href="https://github.com/Crypt0nik/SOC-AI"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            marginTop: '4px',
            fontSize: '11px',
            color: '#FF6600',
            border: '1px solid #FF6600',
            borderRadius: '5px',
            padding: '3px 10px',
            textDecoration: 'none',
            opacity: 0.85,
          }}
        >
          Upgrade to Pro →
        </a>
      </div>
    </div>
  );
}
