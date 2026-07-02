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
        gap: '8px',
      }}>
        {/* Lock icon */}
        <div style={{
          width: '36px', height: '36px', borderRadius: '8px',
          backgroundColor: '#FF660015', border: '1px solid #FF660040',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FF6600" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: T.text, fontWeight: 600, fontSize: '13px', marginBottom: '3px' }}>Pro Feature</div>
          {description && (
            <div style={{ color: T.textMuted, fontSize: '12px', maxWidth: '220px', lineHeight: 1.4 }}>
              {description}
            </div>
          )}
        </div>
        <a
          href="https://github.com/Crypt0nik/SOC-AI"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: '11px', fontWeight: 600,
            color: '#FF6600',
            border: '1px solid #FF6600',
            borderRadius: '5px',
            padding: '4px 12px',
            textDecoration: 'none',
            transition: 'opacity 0.1s',
            opacity: 0.9,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = '1'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '0.9'; }}
        >
          Upgrade to Pro
        </a>
      </div>
    </div>
  );
}
