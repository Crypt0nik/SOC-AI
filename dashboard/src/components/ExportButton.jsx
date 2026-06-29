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
      className="px-3 py-1 rounded text-xs font-semibold border border-gray-600 text-gray-400 hover:border-gray-400 hover:text-gray-200 transition-all"
    >
      Export JSON
    </button>
  );
}
