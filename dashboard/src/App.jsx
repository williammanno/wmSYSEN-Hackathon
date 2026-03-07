import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './components/Landing';
import Dashboard from './components/Dashboard';
import ImportExport from './components/ImportExport';
import PlanShipment from './components/PlanShipment';
import TrackShipment from './components/TrackShipment';
import ExploreData from './components/ExploreData';
import './App.css';

// Derive basename when app is served at subpath (e.g. Posit Connect: /content/123/app/)
function getBasename() {
  const path = window.location.pathname.replace(/\/$/, '');
  const parts = path.split('/').filter(Boolean);
  const routes = ['dashboard', 'import-export', 'plan-shipment', 'track-shipment', 'explore-data'];
  const last = parts[parts.length - 1];
  if (parts.length > 1 && routes.includes(last)) {
    parts.pop();
  }
  return parts.length ? '/' + parts.join('/') : '/';
}

function App() {
  return (
    <div className="app">
      <BrowserRouter basename={getBasename()}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/import-export" element={<ImportExport />} />
          <Route path="/plan-shipment" element={<PlanShipment />} />
          <Route path="/track-shipment" element={<TrackShipment />} />
          <Route path="/explore-data" element={<ExploreData />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
