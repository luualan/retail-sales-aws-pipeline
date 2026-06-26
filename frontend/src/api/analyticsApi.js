import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export async function getHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}

export async function getSummary() {
  const response = await apiClient.get("/analytics/summary");
  return response.data;
}

export async function getMonthlyRevenue() {
  const response = await apiClient.get("/analytics/monthly-revenue");
  return response.data.items;
}

export async function getRevenueByCategory() {
  const response = await apiClient.get("/analytics/revenue-by-category");
  return response.data.items;
}

export async function getTopProducts() {
  const response = await apiClient.get("/analytics/top-products");
  return response.data.items;
}

export async function getRefundRateByCategory() {
  const response = await apiClient.get("/analytics/refund-rate-by-category");
  return response.data.items;
}

export async function getOrdersByRegion() {
  const response = await apiClient.get("/analytics/orders-by-region");
  return response.data.items;
}

export async function getPipelineStatus() {
  const response = await apiClient.get("/pipeline/status");
  return response.data;
}