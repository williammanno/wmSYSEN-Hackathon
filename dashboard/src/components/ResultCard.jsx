import './ResultCard.css';

export default function ResultCard({ title, children, accentColor = '#14b8a6' }) {
  return (
    <article className="result-card" style={{ '--accent': accentColor }}>
      <h3 className="result-card__title">{title}</h3>
      <div className="result-card__body">{children}</div>
    </article>
  );
}
