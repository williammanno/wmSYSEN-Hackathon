// Use relative base when empty so API works when app is served at subpath (e.g. Posit Connect)
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '.').replace(/\/$/, '') || '.';

export async function getImportExportSummary(region = 'Taiwan') {
  const res = await fetch(`${API_BASE}/api/import-export/summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ region }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function planShipment(data) {
  const res = await fetch(`${API_BASE}/api/plan-shipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function trackShipment(data) {
  const res = await fetch(`${API_BASE}/api/track-shipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getNodes() {
  const res = await fetch(`${API_BASE}/api/nodes`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDestinations() {
  const res = await fetch(`${API_BASE}/api/destinations`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getLanes() {
  const res = await fetch(`${API_BASE}/api/lanes`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
