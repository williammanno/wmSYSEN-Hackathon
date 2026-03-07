import { useNavigate } from 'react-router-dom';
import './Landing.css';

const OPTIONS = [
  { id: 'import-export', path: '/import-export', label: 'Do you want to see state of semiconductor importing and exporting?' },
  { id: 'plan', path: '/plan-shipment', label: 'Do you want to plan shipment?' },
  { id: 'track', path: '/track-shipment', label: 'Do you want to track your shipment?' },
  { id: 'explore', path: '/explore-data', label: 'Explore more related data' },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <main className="landing">
      <div className="landing__card">
        <header className="landing__header">
          <h1 className="landing__title">Supply Chain Portal</h1>
          <p className="landing__subtitle">What would you like to do?</p>
        </header>
        <section className="landing__options">
          {OPTIONS.map((option) => (
            <button
              key={option.id}
              className="landing__option button"
              onClick={() => navigate(option.path)}
            >
              {option.label}
            </button>
          ))}
        </section>
      </div>
    </main>
  );
}
