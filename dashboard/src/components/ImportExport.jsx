import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getImportExportSummary } from '../api/client';
import { formatDate } from '../utils/formatDate';
import DashCard from './DashCard';
import ResultCard from './ResultCard';
import './ImportExport.css';
import './ImportExportCards.css';

export default function ImportExport() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getImportExportSummary('Taiwan')
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="workflow-page">
        <div className="workflow-page__loading">
          <div className="loading">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <p className="workflow-page__loading-text">Loading weather, news & AI summary…</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="workflow-page">
        <ResultCard title="Error" accentColor="#ec4899">
          {error}. Ensure the backend is running: <code>cd backend && uvicorn main:app --reload</code>
        </ResultCard>
        <Link to="/" className="workflow-page__back">← Back</Link>
      </main>
    );
  }

  return (
    <main className="workflow-page">
      <header className="workflow-page__header">
        <h1>Semiconductor Import/Export State</h1>
        <Link to="/" className="workflow-page__back">← Back</Link>
      </header>
      <div className="import-export__cards">
        <DashCard
          title="AI Summary"
          value="Overview"
          subtitle="Semiconductor import/export state"
          accentColor="#14b8a6"
        />
        <DashCard
          title="Weather Forecast"
          value={data?.weather_event?.event || '—'}
          subtitle={
            data?.weather_event
              ? `${data.weather_event.region}${data.weather_event.date ? ` · ${formatDate(data.weather_event.date)}` : ''} · ${data.weather_event.severity}`
              : 'No data'
          }
          accentColor="#f59e0b"
        />
        <DashCard
          title="Top News Headline"
          value={(data?.headlines?.[0] || '—').slice(0, 40) + ((data?.headlines?.[0]?.length || 0) > 40 ? '…' : '')}
          subtitle="Geopolitical"
          accentColor="#a855f7"
        />
        <DashCard
          title="Active Risk Events"
          value={data?.stats?.risk_events?.length ?? 0}
          subtitle="From recent shipments"
          accentColor="#ec4899"
        />
      </div>
      <section className="workflow-page__cards">
        <ResultCard title="AI Summary" accentColor="#14b8a6">
          {data?.summary || 'No summary available.'}
        </ResultCard>
        <ResultCard title="All Headlines" accentColor="#a855f7">
        <ul>
          {(data?.headlines || []).map((h, i) => (
            <li key={i}>{h}</li>
          ))}
        </ul>
        </ResultCard>
      </section>
    </main>
  );
}
