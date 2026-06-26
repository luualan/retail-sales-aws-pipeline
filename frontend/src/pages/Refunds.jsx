import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getRefundRateByCategory } from "../api/analyticsApi";
import ChartPanel from "../components/ChartPanel";
import LoadingSkeleton from "../components/LoadingSkeleton";
import {
  formatDateTime,
  formatNumber,
  formatPercent,
} from "../utils/formatters";

function Refunds() {
  const [refunds, setRefunds] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadRefunds() {
      try {
        const data = await getRefundRateByCategory();
        setRefunds(data);
      } catch (error) {
        console.error(error);
        setErrorMessage("Unable to load refund data.");
      } finally {
        setIsLoading(false);
      }
    }

    loadRefunds();
  }, []);

  const sortedRefunds = useMemo(() => {
    return [...refunds].sort(
      (a, b) => b.refund_rate_percent - a.refund_rate_percent,
    );
  }, [refunds]);

  const highestRefundCategory = sortedRefunds[0];
  const totalLineItems = sortedRefunds.reduce(
    (sum, item) => sum + Number(item.line_items || 0),
    0,
  );
  const totalRefundedLineItems = sortedRefunds.reduce(
    (sum, item) => sum + Number(item.refunded_line_items || 0),
    0,
  );
  const overallRefundRate =
    totalLineItems > 0
      ? ((totalRefundedLineItems * 100) / totalLineItems).toFixed(2)
      : 0;

  const lastUpdated = sortedRefunds[0]?.last_updated;

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">Quality Analytics</p>
            <h1>Refund Analytics</h1>
            <p>Loading refund metrics from DynamoDB...</p>
          </div>
        </div>

        <LoadingSkeleton rows={3} />
      </section>
    );
  }

  if (errorMessage) {
    return (
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">Quality Analytics</p>
            <h1>Refund Analytics</h1>
          </div>
        </div>

        <p className="error-message">{errorMessage}</p>
      </section>
    );
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <p className="eyebrow">Quality Analytics</p>
          <h1>Refund Analytics</h1>
          <p>
            Category-level refund behavior computed from curated sales and
            refund data.
          </p>
        </div>

        <div className="source-pill">
          <span>Data refreshed</span>
          <strong>{formatDateTime(lastUpdated)}</strong>
        </div>
      </div>

      <div className="kpi-grid kpi-grid-three">
        <div className="kpi-card">
          <p className="kpi-label">Overall Refund Rate</p>
          <h2 className="kpi-value">{formatPercent(overallRefundRate)}</h2>
        </div>

        <div className="kpi-card">
          <p className="kpi-label">Refunded Line Items</p>
          <h2 className="kpi-value">{formatNumber(totalRefundedLineItems)}</h2>
        </div>

        <div className="kpi-card">
          <p className="kpi-label">Highest Refund Category</p>
          <h2 className="kpi-value">{highestRefundCategory?.category || "N/A"}</h2>
        </div>
      </div>

      <ChartPanel
        title="Refund Rate by Category"
        subtitle="Percentage of line items associated with refunded orders."
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sortedRefunds}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis tickFormatter={(value) => `${value}%`} />
            <Tooltip
              formatter={(value) => [`${value}%`, "Refund rate"]}
            />
            <Bar dataKey="refund_rate_percent" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h2>Refund Detail</h2>
            <p>Refunded line items compared against total line items.</p>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Line Items</th>
                <th>Refunded Line Items</th>
                <th>Refund Rate</th>
              </tr>
            </thead>
            <tbody>
              {sortedRefunds.map((item) => (
                <tr key={item.metric_key}>
                  <td>
                    <span className="tag">{item.category}</span>
                  </td>
                  <td>{formatNumber(item.line_items)}</td>
                  <td>{formatNumber(item.refunded_line_items)}</td>
                  <td>{formatPercent(item.refund_rate_percent)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default Refunds;