const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${path}`);
  return r.json();
}

export const fetchAlerts = ({ severity, page = 1, pageSize = 20 } = {}) => {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (severity) params.set('severity', severity);
  return apiFetch(`/alerts?${params}`);
};

export const fetchAlert = (id) => apiFetch(`/alerts/${id}`);

export const fetchStats = () => apiFetch('/stats');

export const exportUrl = (severity) =>
  `${BASE}/export${severity ? `?severity=${severity}` : ''}`;

export const deleteAlert = (id) =>
  fetch(`${BASE}/alerts/${id}`, { method: 'DELETE' }).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });

export const deleteAllAlerts = () =>
  fetch(`${BASE}/alerts`, { method: 'DELETE' }).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
