# RetailLens Backend

This is the FastAPI backend for RetailLens. It exposes REST API endpoints that read precomputed retail analytics metrics from Amazon DynamoDB and return JSON data for the React dashboard.

## What It Does

The backend serves metrics for:

* Executive sales summary
* Monthly revenue
* Revenue by category
* Top products
* Refund rate by category
* Orders by region
* Pipeline status metadata

The API reads from the `retail_analytics_metrics` DynamoDB table. The metrics are generated separately by Athena aggregation queries and loaded into DynamoDB by the project’s metrics loader script.

## Tech Stack

* FastAPI
* Uvicorn
* Boto3
* Amazon DynamoDB

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API locally:

```bash
uvicorn app.main:app --reload --port 8000
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Environment Variables

Create a local `.env` file if needed, or set these values in your deployment platform:

```env
AWS_REGION=us-west-2
DYNAMODB_TABLE=retail_analytics_metrics
```

For deployment, also configure AWS credentials through environment variables or the hosting provider’s secret manager. Do not commit real AWS credentials to GitHub.

## Main Endpoints

```text
GET /health
GET /analytics/summary
GET /analytics/monthly-revenue
GET /analytics/revenue-by-category
GET /analytics/top-products
GET /analytics/refund-rate-by-category
GET /analytics/orders-by-region
GET /pipeline/status
```
