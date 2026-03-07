import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { planShipment, getNodes, getDestinations, getImportExportSummary } from '../api/client';
import { formatDate } from '../utils/formatDate';
import DashCard from './DashCard';
import ResultCard from './ResultCard';
import './ImportExport.css';
import './PlanShipment.css';

export default function PlanShipment() {
  const [nodes, setNodes] = useState([]);
  const [dests, setDests] = useState([]);
  const [contextData, setContextData] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    company: 'Intel',
    origin_id: '',
    destination_id: '',
    part_type: 'packaged IC',
    priority: 'standard',
    notes: '',
    concerns: '',
  });

  useEffect(() => {
    // Load nodes and destinations first so dropdowns populate quickly.
    // Defer import-export summary (weather, news, LLM) until after so it doesn't block the backend.
    Promise.all([getNodes(), getDestinations()])
      .then(([n, d]) => {
        setNodes(n);
        setDests(d);
        getImportExportSummary('Taiwan').then(setContextData).catch(() => setContextData(null));
      })
      .catch(() => {});
  }, []);

  const companyNodes = nodes.filter((n) => n.company === form.company);
  const companyDests = dests.filter((d) => d.company === form.company);
  const originOptions = companyNodes.length ? companyNodes : nodes;
  const destinationOptions = companyDests.length ? companyDests : dests;

  useEffect(() => {
    if (!originOptions.length || !destinationOptions.length) return;
    setForm((f) => {
      const originValid = originOptions.some((n) => n.id === f.origin_id);
      const destinationValid = destinationOptions.some((d) => d.id === f.destination_id);
      const nextOriginId = originValid ? f.origin_id : originOptions[0].id;
      const nextDestinationId = destinationValid ? f.destination_id : destinationOptions[0].id;

      if (nextOriginId === f.origin_id && nextDestinationId === f.destination_id) {
        return f;
      }
      return { ...f, origin_id: nextOriginId, destination_id: nextDestinationId };
    });
  }, [originOptions, destinationOptions]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    planShipment(form)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <main className="workflow-page">
      <header className="workflow-page__header">
        <h1>Plan Shipment</h1>
        <Link to="/" className="workflow-page__back">← Back</Link>
      </header>
      <form className="plan-form" onSubmit={handleSubmit}>
        <div className="plan-form__columns">
          <div className="plan-form__column">
            <div className="plan-form__row">
              <label>Company</label>
              <select
                value={form.company}
                onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
              >
                <option value="Intel">Intel</option>
                <option value="Broadcom">Broadcom</option>
                <option value="Nvidia">Nvidia</option>
              </select>
            </div>
            <div className="plan-form__row">
              <label>Origin</label>
              <select
                value={form.origin_id}
                onChange={(e) => setForm((f) => ({ ...f, origin_id: e.target.value }))}
              >
                {originOptions.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
            </div>
            <div className="plan-form__row">
              <label>Destination</label>
              <select
                value={form.destination_id}
                onChange={(e) => setForm((f) => ({ ...f, destination_id: e.target.value }))}
              >
                {destinationOptions.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="plan-form__row">
              <label>Part Type</label>
              <select
                value={form.part_type}
                onChange={(e) => setForm((f) => ({ ...f, part_type: e.target.value }))}
              >
                <option value="wafer">Wafer</option>
                <option value="packaged IC">Packaged IC</option>
                <option value="photomask">Photomask</option>
                <option value="spare part">Spare Part</option>
              </select>
            </div>
            <button type="submit" className="button plan-form__submit" disabled={loading}>
              Generate Plan
            </button>
          </div>

          <div className="plan-form__column">
            <div className="plan-form__row">
              <label>Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="Shipment details..."
                rows={2}
              />
            </div>
            <div className="plan-form__row">
              <label>Concerns</label>
              <textarea
                value={form.concerns}
                onChange={(e) => setForm((f) => ({ ...f, concerns: e.target.value }))}
                placeholder="Any concerns?"
                rows={2}
              />
            </div>
          </div>
        </div>
      </form>
      {loading && (
        <div className="workflow-page__loading">
          <div className="loading">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <p className="workflow-page__loading-text">Generating plan…</p>
        </div>
      )}
      {error && (
        <ResultCard title="Error" accentColor="#ec4899">{error}</ResultCard>
      )}
      {result && (
        <>
          {contextData && (
            <div className="plan-context-cards">
              <DashCard
                title="Weather Forecast"
                value={contextData?.weather_event?.event || '—'}
                subtitle={
                  contextData?.weather_event
                    ? `${contextData.weather_event.region}${contextData.weather_event.date ? ` · ${formatDate(contextData.weather_event.date)}` : ''} · ${contextData.weather_event.severity}`
                    : 'No data'
                }
                accentColor="#f59e0b"
              />
              <DashCard
                title="Top News Headline"
                value={(contextData?.headlines?.[0] || '—').slice(0, 25) + ((contextData?.headlines?.[0]?.length || 0) > 25 ? '…' : '')}
                subtitle="Geopolitical"
                accentColor="#a855f7"
              />
              <DashCard
                title="Active Risk Events"
                value={`${contextData?.stats?.risk_events?.length ?? 0}/10`}
                subtitle="From recent shipments"
                accentColor="#ec4899"
              />
            </div>
          )}

          <div className="plan-risk-cards">
            <DashCard
              title="Weather Risk"
              value={`${Math.round((result?.risk_scores?.weather_risk ?? 0) * 100)}%`}
              subtitle="Forecast-driven risk"
              accentColor="#f59e0b"
            />
            <DashCard
              title="Geopolitical Risk"
              value={`${Math.round((result?.risk_scores?.geopolitical_risk ?? 0) * 100)}%`}
              subtitle="Regional stability"
              accentColor="#a855f7"
            />
            <DashCard
              title="Port Congestion"
              value={`${Math.round((result?.risk_scores?.port_congestion ?? 0) * 100)}%`}
              subtitle="Port and handoff delays"
              accentColor="#0ea5e9"
            />
            <DashCard
              title="Labor Risk"
              value={`${Math.round((result?.risk_scores?.labor_risk ?? 0) * 100)}%`}
              subtitle="Carrier/staff capacity"
              accentColor="#ec4899"
            />
            <DashCard
              title="Composite Risk"
              value={`${Math.round((result?.risk_scores?.composite_risk ?? 0) * 100)}%`}
              subtitle="Weighted route risk score"
              accentColor="#14b8a6"
            />
          </div>

          <section className="workflow-page__cards" style={{ marginTop: '2rem' }}>
            <ResultCard title="Shipment Plan" accentColor="#14b8a6">
              {result.plan}
            </ResultCard>
            {(result.recommendations?.length > 0) && (
              <ResultCard title="Route Options" accentColor="#0ea5e9">
                <div className="plan-recommendations">
                  {result.recommendations.map((r) => (
                    <div key={r.rank} className="plan-recommendation-item">
                      <strong>#{r.rank} {r.mode} ({r.route_type})</strong> — {r.days_min}–{r.days_max} days, score {r.score}, {r.cost_tier}. {r.rationale}
                    </div>
                  ))}
                </div>
              </ResultCard>
            )}
            <ResultCard title="Risk Factors" accentColor="#f59e0b">
              <ul>
                {(result.risk_factors || []).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </ResultCard>
          </section>
        </>
      )}
    </main>
  );
}
