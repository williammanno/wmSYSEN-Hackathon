import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { trackShipment, getNodes, getDestinations, getLanes } from '../api/client';
import { formatDate } from '../utils/formatDate';
import DashCard from './DashCard';
import ResultCard from './ResultCard';
import ShippingProgress from './ShippingProgress';
import './ImportExport.css';
import './PlanShipment.css';
import './TrackShipment.css';

function getProgressPercent(dateShipped, transitDaysMax) {
  if (!dateShipped || !transitDaysMax || transitDaysMax <= 0) return 0;
  const shipped = new Date(dateShipped);
  const now = new Date();
  const daysElapsed = Math.floor((now - shipped) / (1000 * 60 * 60 * 24));
  const progress = Math.round((daysElapsed / transitDaysMax) * 100);
  return Math.min(100, Math.max(0, progress));
}

export default function TrackShipment() {
  const [nodes, setNodes] = useState([]);
  const [dests, setDests] = useState([]);
  const [lanes, setLanes] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    origin_id: '',
    destination_id: '',
    route_id: '',
    date_shipped: '',
  });

  useEffect(() => {
    getNodes().then(setNodes);
    getDestinations().then(setDests);
    getLanes().then(setLanes);
  }, []);

  useEffect(() => {
    if (nodes.length && !form.origin_id) setForm((f) => ({ ...f, origin_id: nodes[0].id }));
    if (dests.length && !form.destination_id) setForm((f) => ({ ...f, destination_id: dests[0].id }));
  }, [nodes, dests, form.origin_id, form.destination_id]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    trackShipment({
      origin_id: form.origin_id,
      destination_id: form.destination_id,
      route_id: form.route_id || undefined,
      date_shipped: form.date_shipped || undefined,
    })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const relevantLanes = lanes.filter(
    (l) => l.origin_id === form.origin_id && l.destination_id === form.destination_id
  );

  return (
    <main className="workflow-page">
      <header className="workflow-page__header">
        <h1>Track Shipment</h1>
        <Link to="/" className="workflow-page__back">← Back</Link>
      </header>
      <form className="plan-form" onSubmit={handleSubmit}>
        <div className="plan-form__row">
          <label>Origin</label>
          <select
            value={form.origin_id}
            onChange={(e) => setForm((f) => ({ ...f, origin_id: e.target.value }))}
          >
            {nodes.map((n) => (
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
            {dests.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        {relevantLanes.length > 0 && (
          <div className="plan-form__row">
            <label>Route (optional)</label>
            <select
              value={form.route_id}
              onChange={(e) => setForm((f) => ({ ...f, route_id: e.target.value }))}
            >
              <option value="">Auto-select</option>
              {relevantLanes.map((l) => (
                <option key={l.lane_id} value={l.lane_id}>
                  {l.mode} {l.route_type} ({l.transit_days_min}-{l.transit_days_max} days)
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="plan-form__row">
          <label>Date Shipped</label>
          <input
            type="date"
            value={form.date_shipped}
            onChange={(e) => setForm((f) => ({ ...f, date_shipped: e.target.value }))}
            className="plan-form__input"
          />
        </div>
        <button type="submit" className="button plan-form__submit" disabled={loading}>
          Track Shipment
        </button>
      </form>
      {loading && (
        <div className="workflow-page__loading">
          <div className="loading">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <p className="workflow-page__loading-text">Estimating arrival…</p>
        </div>
      )}
      {error && (
        <ResultCard title="Error" accentColor="#ec4899">{error}</ResultCard>
      )}
      {result && (
        <section className="track-result">
          <div className="track-result__cards">
            <DashCard
              title="Days Ago Shipped"
              value={result.days_ago_shipped != null ? `${result.days_ago_shipped}` : '—'}
              subtitle={
                form.date_shipped
                  ? result.days_ago_shipped === 0
                    ? 'Shipped today'
                    : `Shipped ${result.days_ago_shipped} day${result.days_ago_shipped !== 1 ? 's' : ''} ago`
                  : 'Enter date shipped'
              }
              accentColor="#14b8a6"
            />
            <DashCard
              title="Estimated Arrival"
              value={`${result.estimated_arrival_days_min}–${result.estimated_arrival_days_max}`}
              subtitle="Days in transit"
              accentColor="#ec4899"
            />
            <DashCard
              title="Expected Arrival"
              value={result.estimated_arrival_date ? formatDate(result.estimated_arrival_date) : '—'}
              subtitle={result.estimated_arrival_date ? 'Based on ship date' : 'Enter date shipped'}
              accentColor="#a855f7"
            />
            <DashCard
              title="Risk Factor"
              value={`${result.risk_factor}/10`}
              subtitle={result.risk_factor <= 3 ? 'Low risk' : result.risk_factor <= 6 ? 'Moderate risk' : 'Elevated risk'}
              accentColor="#f59e0b"
            />
          </div>
          <ShippingProgress
            progress={getProgressPercent(
              form.date_shipped,
              result.estimated_arrival_days_max ?? result.estimated_arrival_days_min ?? 10
            )}
          />
          <ResultCard title="Tracking Summary" accentColor="#14b8a6">
            {result.plan}
          </ResultCard>
          <ResultCard title="Possible Delay Factors" accentColor="#f59e0b">
            <ul>
              {(result.delay_factors || []).map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          </ResultCard>
        </section>
      )}
    </main>
  );
}
