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

import { getTopProducts } from "../api/analyticsApi";
import ChartPanel from "../components/ChartPanel";
import LoadingSkeleton from "../components/LoadingSkeleton";
import {
  formatCurrency,
  formatDateTime,
  formatNumber,
} from "../utils/formatters";

function Products() {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadProducts() {
      try {
        const data = await getTopProducts();
        setProducts(data);
      } catch (error) {
        console.error(error);
        setErrorMessage("Unable to load product data.");
      } finally {
        setIsLoading(false);
      }
    }

    loadProducts();
  }, []);

  const sortedProducts = useMemo(() => {
    return [...products].sort((a, b) => Number(a.metric_key) - Number(b.metric_key));
  }, [products]);

  const chartData = useMemo(() => {
    return sortedProducts.map((product) => ({
      ...product,
      product_label:
        product.product_name.length > 18
          ? `${product.product_name.slice(0, 18)}...`
          : product.product_name,
    }));
  }, [sortedProducts]);

  const lastUpdated = sortedProducts[0]?.last_updated;

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">Product Performance</p>
            <h1>Top Products</h1>
            <p>Loading ranked product metrics from DynamoDB...</p>
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
            <p className="eyebrow">Product Performance</p>
            <h1>Top Products</h1>
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
          <p className="eyebrow">Product Performance</p>
          <h1>Top Products</h1>
          <p>
            Highest-performing products ranked by recognized revenue from the
            curated sales table.
          </p>
        </div>

        <div className="source-pill">
          <span>Data refreshed</span>
          <strong>{formatDateTime(lastUpdated)}</strong>
        </div>
      </div>

      <ChartPanel
        title="Top Products by Revenue"
        subtitle="Top 10 products from Athena aggregations stored in DynamoDB."
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              tickFormatter={(value) => `$${value / 1000}k`}
            />
            <YAxis
              type="category"
              dataKey="product_label"
              width={150}
            />
            <Tooltip
              formatter={(value) => [formatCurrency(value), "Revenue"]}
              labelFormatter={(_, payload) => {
                return payload?.[0]?.payload?.product_name || "Product";
              }}
            />
            <Bar dataKey="revenue" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>

      <div className="panel">
        <div className="panel-header">
          <div>
            <h2>Product Ranking</h2>
            <p>Revenue, units sold, and category details for each product.</p>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Product</th>
                <th>Category</th>
                <th>Units Sold</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {sortedProducts.map((product) => (
                <tr key={product.metric_key}>
                  <td>
                    <span className="rank-pill">#{Number(product.metric_key)}</span>
                  </td>
                  <td>{product.product_name}</td>
                  <td>
                    <span className="tag">{product.category}</span>
                  </td>
                  <td>{formatNumber(product.units_sold)}</td>
                  <td>{formatCurrency(product.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default Products;