import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, AreaChart, Area } from 'recharts';
import DashCard from './DashCard';
import './ExploreData.css';

const BASE = 'https://comtradeapi.un.org/public/v1/preview/C/A/HS';

const HS_CODES = {
  '8542': 'Integrated Circuits',
  '8541': 'Semiconductors / Diodes',
  '8532': 'Capacitors',
  '8533': 'Resistors',
  '8534': 'Printed Circuits',
};

const TOP_REPORTERS = [
  { code: '156', name: 'China' },
  { code: '158', name: 'Taiwan' },
  { code: '410', name: 'South Korea' },
  { code: '528', name: 'Netherlands' },
  { code: '392', name: 'Japan' },
  { code: '840', name: 'USA' },
  { code: '276', name: 'Germany' },
  { code: '458', name: 'Malaysia' },
];

const CHART_COLORS = ['#14b8a6', '#4fc3f7', '#f59e0b', '#a855f7', '#00e5ff', '#ec4899', '#ff9800', '#ff69b4'];

function generateMockFlows(reporter, hsCode) {
  const seed = (reporter.charCodeAt(0) + parseInt(hsCode)) % 7;
  const base = (seed + 1) * 8000 + Math.random() * 5000;
  return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, i) => ({
    month,
    exports: Math.round(base * (0.85 + Math.sin(i / 2) * 0.2 + Math.random() * 0.15)),
    imports: Math.round(base * 0.6 * (0.9 + Math.cos(i / 3) * 0.15 + Math.random() * 0.1)),
  }));
}

function generateCountryFlows() {
  return TOP_REPORTERS.map((r) => ({
    name: r.name,
    exports: Math.round(20000 + Math.random() * 80000),
    imports: Math.round(15000 + Math.random() * 60000),
    balance: 0,
  })).map((d) => ({ ...d, balance: d.exports - d.imports })).sort((a, b) => b.exports - a.exports);
}

const fmt = (n) => (n >= 1e9 ? `$${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : `$${(n / 1e3).toFixed(0)}K`);

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="explore-tooltip">
      <div className="explore-tooltip__label">{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>
          {p.name}: {fmt(p.value * 1e6)}
        </div>
      ))}
    </div>
  );
}

export default function ExploreData() {
  const [selectedHS, setSelectedHS] = useState('8542');
  const [selectedReporter, setSelectedReporter] = useState(TOP_REPORTERS[1]);
  const [year, setYear] = useState('2023');
  const [tradeFlow, setTradeFlow] = useState('X');
  const [monthlyData, setMonthlyData] = useState([]);
  const [countryData, setCountryData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('demo');

  const tickerData = [
    { label: 'IC Global Exports', value: '$892B', change: 3.4 },
    { label: 'Taiwan → USA', value: '$186B', change: 7.2 },
    { label: 'Korea → China', value: '$94B', change: -2.1 },
    { label: 'NL (ASML) Exports', value: '$38B', change: 12.5 },
    { label: 'Japan Semicon', value: '$71B', change: 1.8 },
    { label: 'US Imports HS8542', value: '$203B', change: -0.9 },
    { label: 'Malaysia HS8541', value: '$22B', change: 5.3 },
    { label: 'Germany ICs', value: '$18B', change: 2.1 },
  ];

  const fetchLiveData = useCallback(async () => {
    setLoading(true);
    try {
      const url = `${BASE}?reporterCode=${selectedReporter.code}&cmdCode=${selectedHS}&flowCode=${tradeFlow}&period=${year}`;
      const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
      if (!res.ok) throw new Error('API error');
      const json = await res.json();
      if (json?.data?.length > 0) {
        const totalVal = json.data.reduce((s, d) => s + (d.primaryValue || 0), 0);
        setMonthlyData(
          generateMockFlows(selectedReporter.name, selectedHS).map((m, i) => ({
            ...m,
            exports: Math.round(totalVal / 12 * (0.85 + Math.sin(i / 2) * 0.2)),
            imports: Math.round(totalVal / 20 * (0.9 + Math.cos(i / 3) * 0.15)),
          }))
        );
        setApiStatus('live');
      } else {
        throw new Error('No data');
      }
    } catch {
      setApiStatus('demo');
      setMonthlyData(generateMockFlows(selectedReporter.name, selectedHS));
    }
    setCountryData(generateCountryFlows());
    setLoading(false);
  }, [selectedHS, selectedReporter, year, tradeFlow]);

  useEffect(() => {
    fetchLiveData();
  }, [fetchLiveData]);

  const totalExports = monthlyData.reduce((s, d) => s + d.exports, 0) * 1e6;
  const totalImports = monthlyData.reduce((s, d) => s + d.imports, 0) * 1e6;
  const balance = totalExports - totalImports;

  return (
    <main className="workflow-page explore-page">
      <header className="workflow-page__header">
        <h1>Explore More Related Data</h1>
        <Link to="/" className="workflow-page__back">← Back</Link>
      </header>

      <div className="explore-ticker">
        <div className="explore-ticker__scroll">
          {tickerData.concat(tickerData).map((d, i) => (
            <span key={i} className={`explore-ticker__item ${d.change >= 0 ? 'positive' : 'negative'}`}>
              <span className="explore-ticker__label">{d.label}</span>
              <span className="explore-ticker__value">{d.value}</span>
              <span className="explore-ticker__change">{d.change >= 0 ? '▲' : '▼'} {Math.abs(d.change).toFixed(1)}%</span>
            </span>
          ))}
        </div>
      </div>

      <div className="explore-controls">
        <div className="explore-controls__group">
          <span className="explore-controls__label">HS CODE</span>
          <select value={selectedHS} onChange={(e) => setSelectedHS(e.target.value)} className="explore-controls__select">
            {Object.entries(HS_CODES).map(([k, v]) => (
              <option key={k} value={k}>{k} — {v}</option>
            ))}
          </select>
        </div>
        <div className="explore-controls__group">
          <span className="explore-controls__label">REPORTER</span>
          <select
            value={selectedReporter.code}
            onChange={(e) => setSelectedReporter(TOP_REPORTERS.find((r) => r.code === e.target.value))}
            className="explore-controls__select"
          >
            {TOP_REPORTERS.map((r) => (
              <option key={r.code} value={r.code}>{r.name}</option>
            ))}
          </select>
        </div>
        <div className="explore-controls__group">
          <span className="explore-controls__label">YEAR</span>
          <select value={year} onChange={(e) => setYear(e.target.value)} className="explore-controls__select">
            {['2019', '2020', '2021', '2022', '2023'].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div className="explore-controls__group">
          <span className="explore-controls__label">FLOW</span>
          <select value={tradeFlow} onChange={(e) => setTradeFlow(e.target.value)} className="explore-controls__select">
            <option value="X">Exports</option>
            <option value="M">Imports</option>
            <option value="X,M">Both</option>
          </select>
        </div>
        <button onClick={fetchLiveData} disabled={loading} className="button explore-controls__refresh">
          {loading ? 'Loading…' : '↻ Refresh'}
        </button>
      </div>

      <div className="explore-kpi">
        <DashCard title="Total Exports" value={fmt(totalExports)} subtitle={`${selectedReporter.name} · ${year}`} accentColor="#14b8a6" />
        <DashCard title="Total Imports" value={fmt(totalImports)} subtitle={`${selectedReporter.name} · ${year}`} accentColor="#4fc3f7" />
        <DashCard
          title="Trade Balance"
          value={fmt(Math.abs(balance))}
          subtitle={balance >= 0 ? 'Surplus' : 'Deficit'}
          accentColor={balance >= 0 ? '#14b8a6' : '#ec4899'}
        />
        <DashCard title="HS Product" value={selectedHS} subtitle={HS_CODES[selectedHS]} accentColor="#f59e0b" />
      </div>

      <div className="explore-charts">
        <article className="explore-card">
          <div className="explore-card__header">
            <h3 className="explore-card__title">Monthly Trade Flow — {selectedReporter.name}</h3>
            <span className="explore-card__badge">{year}</span>
          </div>
          <div className="explore-card__chart">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={monthlyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gEx" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gIm" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4fc3f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4fc3f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}B`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="exports" name="Exports" stroke="#14b8a6" fill="url(#gEx)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="imports" name="Imports" stroke="#4fc3f7" fill="url(#gIm)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="explore-card__legend">
            <span style={{ color: '#14b8a6' }}>▬ Exports</span>
            <span style={{ color: '#4fc3f7' }}>▬ Imports</span>
          </div>
        </article>

        <article className="explore-card">
          <div className="explore-card__header">
            <h3 className="explore-card__title">Country Rankings — Exports</h3>
            <span className="explore-card__badge">HS {selectedHS}</span>
          </div>
          <div className="explore-card__list">
            {countryData.slice(0, 8).map((c, i) => {
              const maxVal = countryData[0]?.exports || 1;
              const pct = (c.exports / maxVal) * 100;
              return (
                <div key={c.name} className="explore-card__row">
                  <div className="explore-card__row-top">
                    <span className="explore-card__row-label">
                      <span className="explore-card__row-num">{String(i + 1).padStart(2, '0')}</span>
                      {c.name}
                    </span>
                    <span className="explore-card__row-value" style={{ color: CHART_COLORS[i] }}>{fmt(c.exports * 1e6)}</span>
                  </div>
                  <div className="explore-card__bar">
                    <div className="explore-card__bar-fill" style={{ width: `${pct}%`, background: CHART_COLORS[i] }} />
                  </div>
                </div>
              );
            })}
          </div>
        </article>
      </div>

      <div className="explore-charts">
        <article className="explore-card">
          <h3 className="explore-card__title">Trade Balance by Country</h3>
          <div className="explore-card__chart">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={countryData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}B`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="balance" name="Balance" radius={[2, 2, 0, 0]}>
                  {countryData.map((d, i) => (
                    <Cell key={i} fill={d.balance >= 0 ? '#14b8a6' : '#ec4899'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="explore-card">
          <h3 className="explore-card__title">HS Product Breakdown</h3>
          <div className="explore-card__list">
            {Object.entries(HS_CODES).map(([code, name], i) => {
              const val = Math.round(30 + Math.random() * 70);
              return (
                <div key={code} className="explore-card__row clickable" onClick={() => setSelectedHS(code)}>
                  <div className="explore-card__row-top">
                    <span className={`explore-card__row-label ${selectedHS === code ? 'active' : ''}`} style={selectedHS === code ? { color: CHART_COLORS[i] } : {}}>
                      {selectedHS === code ? '► ' : '  '}{code}
                    </span>
                    <span className="explore-card__row-value">{name.split('/')[0].trim()}</span>
                    <span className="explore-card__row-value" style={{ color: CHART_COLORS[i] }}>{val}%</span>
                  </div>
                  <div className="explore-card__bar">
                    <div className="explore-card__bar-fill" style={{ width: `${val}%`, background: CHART_COLORS[i] + '99' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="explore-card">
          <h3 className="explore-card__title">Market Context</h3>
          <div className="explore-card__events">
            {[
              { date: '2024 Q4', text: 'US CHIPS Act investment reaches $52B disbursement', color: '#14b8a6' },
              { date: '2024 Q3', text: 'ASML restricts EUV exports to China under Dutch rules', color: '#ec4899' },
              { date: '2024 Q2', text: 'Samsung announces $17B Texas fab expansion', color: '#4fc3f7' },
              { date: '2024 Q1', text: 'TSMC Arizona N4 production ramp begins', color: '#f59e0b' },
              { date: '2023 Q4', text: 'US-China trade restrictions on advanced chips expand', color: '#ec4899' },
            ].map((item, i) => (
              <div key={i} className="explore-card__event">
                <span className="explore-card__event-date" style={{ color: item.color }}>{item.date}</span>
                <span className="explore-card__event-text">{item.text}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <footer className="explore-footer">
        <span>{apiStatus === 'live' ? '● LIVE — UN Comtrade' : '◎ DEMO — UN Comtrade Preview'}</span>
        <span>Data: UN Comtrade · HS Classification 2022</span>
      </footer>
    </main>
  );
}
