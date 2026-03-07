import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { planShipment, getNodes, getDestinations } from '../api/client';
import ResultCard from './ResultCard';
import './ImportExport.css';
import './PlanShipment.css';

export default function PlanShipment() {
  const [nodes, setNodes] = useState([]);
  const [dests, setDests] = useState([]);
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
    getNodes().then(setNodes);
    getDestinations().then(setDests);
  }, []);

  useEffect(() => {
    if (nodes.length && !form.origin_id) setForm((f) => ({ ...f, origin_id: nodes[0].id }));
    if (dests.length && !form.destination_id) setForm((f) => ({ ...f, destination_id: dests[0].id }));
  }, [nodes, dests, form.origin_id, form.destination_id]);

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
            {(nodes.filter((n) => n.company === form.company).length
              ? nodes.filter((n) => n.company === form.company)
              : nodes
            ).map((n) => (
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
            {(dests.filter((d) => d.company === form.company).length
              ? dests.filter((d) => d.company === form.company)
              : dests
            ).map((d) => (
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
        <div className="plan-form__row">
          <label>Priority</label>
          <select
            value={form.priority}
            onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
          >
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="standard">Standard</option>
          </select>
        </div>
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
        <button type="submit" className="button plan-form__submit" disabled={loading}>
          Generate Plan
        </button>
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
        <section className="workflow-page__cards" style={{ marginTop: '2rem' }}>
          <ResultCard title="Shipment Plan" accentColor="#14b8a6">
            {result.plan}
          </ResultCard>
          <ResultCard title="Risk Factors" accentColor="#f59e0b">
            <ul>
              {(result.risk_factors || []).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </ResultCard>
        </section>
      )}
    </main>
  );
}
