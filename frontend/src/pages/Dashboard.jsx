import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getMonthlyRevenue,
  getOrdersByRegion,
  getRevenueByCategory,
  getSummary,
} from "../api/analyticsApi";
import ChartPanel from "../components/ChartPanel";
import KpiCard from "../components/KpiCard";
import LoadingSkeleton from "../components/LoadingSkeleton";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
} from "../utils/formatters";

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [monthlyRevenue, setMonthlyRevenue] = useState([]);
  const [revenueByCategory, setRevenueByCategory] = useState([]);
  const [ordersByRegion, setOrdersByRegion] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [
          summaryData,
          monthlyRevenueData,
          revenueByCategoryData,
          ordersByRegionData,
        ] = await Promise.all([
          getSummary(),
          getMonthlyRevenue(),
          getRevenueByCategory(),
          getOrdersByRegion(),
        ]);

        setSummary(summaryData);
        setMonthlyRevenue(monthlyRevenueData);
        setRevenueByCategory(revenueByCategoryData);
        setOrdersByRegion(ordersByRegionData);
      } catch (error) {
        console.error(error);
        setErrorMessage("Unable to load dashboard data.");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const sortedMonthlyRevenue = useMemo(() => {
    return [...monthlyRevenue].sort((a, b) =>
      a.metric_key.localeCompare(b.metric_key),
    );
  }, [monthlyRevenue]);

  const sortedRevenueByCategory = useMemo(() => {
    return [...revenueByCategory].sort((a, b) => b.revenue - a.revenue);
  }, [revenueByCategory]);

  const sortedOrdersByRegion = useMemo(() => {
    return [...ordersByRegion].sort((a, b) => b.total_orders - a.total_orders);
  }, [ordersByRegion]);

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">Executive Overview</p>
            <h1>Retail Sales Dashboard</h1>
            <p>Loading precomputed retail analytics from DynamoDB...</p>
          </div>
        </div>

        <LoadingSkeleton rows={4} />
      </section>
    );
  }

  if (errorMessage) {
    return (
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">Executive Overview</p>
            <h1>Retail Sales Dashboard</h1>
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
          <p className="eyebrow">Executive Overview</p>
          <h1>Retail Sales Dashboard</h1>
          <p>
            Sales, revenue, regional, and category metrics served from
            DynamoDB through FastAPI.
          </p>
        </div>

        <div className="source-pill">
          <span>Data refreshed</span>
          <strong>{formatDateTime(summary?.last_updated)}</strong>
        </div>
      </div>

      <div className="kpi-grid">
        <KpiCard
          label="Total Revenue"
          value={formatCurrency(summary?.total_revenue)}
        />
        <KpiCard
          label="Total Orders"
          value={formatNumber(summary?.total_orders)}
        />
        <KpiCard
          label="Avg Order Value"
          value={formatCurrency(summary?.avg_order_value)}
        />
        <KpiCard
          label="Refund Rate"
          value={formatPercent(summary?.refund_rate_percent)}
        />
      </div>

      <div className="chart-grid">
        <ChartPanel
          title="Monthly Revenue"
          subtitle="Recognized revenue from completed/paid sales by month."
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sortedMonthlyRevenue}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric_key" />
              <YAxis tickFormatter={(value) => `$${value / 1000}k`} />
              <Tooltip
                formatter={(value) => [formatCurrency(value), "Revenue"]}
                labelFormatter={(label) => `Month: ${label}`}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                strokeWidth={3}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel
          title="Revenue by Category"
          subtitle="Category-level revenue from curated sales data."
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sortedRevenueByCategory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis tickFormatter={(value) => `$${value / 1000}k`} />
              <Tooltip
                formatter={(value) => [formatCurrency(value), "Revenue"]}
              />
              <Bar dataKey="revenue" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel
          title="Orders by Region"
          subtitle="Total order volume grouped by customer region."
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sortedOrdersByRegion}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis tickFormatter={(value) => formatNumber(value)} />
              <Tooltip
                formatter={(value) => [formatNumber(value), "Orders"]}
              />
              <Bar dataKey="total_orders" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>
    </section>
  );
}

export default Dashboard;