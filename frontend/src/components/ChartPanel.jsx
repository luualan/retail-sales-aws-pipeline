function ChartPanel({ title, subtitle, children }) {
  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>

      <div className="chart-container">{children}</div>
    </div>
  );
}

export default ChartPanel;