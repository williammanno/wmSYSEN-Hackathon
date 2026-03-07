import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './components/Landing';
import Dashboard from './components/Dashboard';
import ImportExport from './components/ImportExport';
import PlanShipment from './components/PlanShipment';
import TrackShipment from './components/TrackShipment';
import ExploreData from './components/ExploreData';
import './App.css';

function App() {
  return (
    <div className="app">
      <BrowserRouter>
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
