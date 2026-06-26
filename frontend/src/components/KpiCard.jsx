function KpiCard({ label, value }) {
  return (
    <div className="kpi-card">
      <p className="kpi-label">{label}</p>
      <h2 className="kpi-value">{value}</h2>
    </div>
  );
}

export default KpiCard;