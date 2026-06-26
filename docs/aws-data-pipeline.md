Retail Sales AWS Data Pipeline

This project is a hands-on AWS data engineering pipeline that processes raw e-commerce sales data using Amazon S3, AWS Glue, AWS Glue Data Catalog, Glue PySpark, Parquet, and Amazon Athena.

The goal is to simulate a real retail analytics pipeline where raw CSV files are uploaded to a data lake, cataloged, transformed into curated Parquet data, and queried using SQL.

Architecture
flowchart TD
    A[Local CSV Data Generator] --> B[Amazon S3 Raw Zone]

    B --> C[AWS Glue Raw Crawler]
    C --> D[AWS Glue Data Catalog - retail_raw_db]

    D --> E[Amazon Athena Raw Validation Queries]

    D --> F[AWS Glue PySpark ETL Job]
    F --> G[Amazon S3 Curated Zone - Partitioned Parquet]

    G --> H[AWS Glue Curated Crawler]
    H --> I[AWS Glue Data Catalog - retail_curated_db]

    I --> J[Amazon Athena Analytics Queries]

    J --> K[Business Metrics: Revenue, Refund Rate, Top Products]
AWS Services Used
Amazon S3

Amazon S3 is used as the data lake storage layer.

The project uses two main S3 zones:

raw/
curated/

The raw zone stores original CSV files. The curated zone stores transformed Parquet files.

Example S3 layout:

s3:/your-retail-analytics-bucket/raw/customers/customers.csv
s3:/your-retail-analytics-bucket/raw/products/products.csv
s3:/your-retail-analytics-bucket/raw/orders/orders.csv
s3:/your-retail-analytics-bucket/raw/order_items/order_items.csv
s3:/your-retail-analytics-bucket/raw/payments/payments.csv
s3:/your-retail-analytics-bucket/raw/refunds/refunds.csv

s3:/your-retail-analytics-bucket/curated/fact_sales/
AWS Glue Crawler

AWS Glue Crawlers scan data in S3, infer schemas, and create table metadata in the AWS Glue Data Catalog.

This project uses two crawlers:

retail_raw_crawler
retail_curated_crawler

The raw crawler catalogs CSV files. The curated crawler catalogs partitioned Parquet output.

AWS Glue Data Catalog

The Glue Data Catalog stores metadata for the data lake tables.

Databases used:

retail_raw_db
retail_curated_db

The actual data remains in S3. The Data Catalog stores table names, schemas, file formats, S3 locations, and partition metadata.

AWS Glue PySpark Job

The Glue ETL job reads raw tables from the Glue Data Catalog, cleans and joins the data, and writes a curated analytics table back to S3 as Parquet.

Job name:

retail_sales_etl_job

The job combines:

customers
products
orders
order_items
payments
refunds

into a curated sales fact table.

Amazon Athena

Athena is used to query both raw and curated data with SQL.

Example use cases:

Validate row counts
Inspect raw data
Query revenue by category
Query daily revenue
Query refund rate
Query top products
Data Model

The raw e-commerce dataset includes:

File	Description
customers.csv	Customer profile data
products.csv	Product catalog data
orders.csv	One row per customer order
order_items.csv	One row per product line item inside an order
payments.csv	Payment status and amount per order
refunds.csv	Refund details for refunded orders

Relationships:

customers.customer_id = orders.customer_id
orders.order_id = order_items.order_id
order_items.product_id = products.product_id
orders.order_id = payments.order_id
orders.order_id = refunds.order_id
ETL Logic

The Glue PySpark job performs the following transformations:

Casts IDs, dates, prices, and amounts to correct types
Lowercases status and region values
Removes duplicate records
Filters invalid negative quantities
Joins orders, order items, products, customers, payments, and refunds
Calculates line item revenue
Calculates recognized revenue
Flags completed, paid, and refunded orders
Writes curated Parquet partitioned by order_year and order_month

Curated output columns include:

order_id
order_item_id
customer_id
customer_state
region
order_date
order_year
order_month
order_status
product_id
product_name
category
quantity
unit_price
line_item_revenue
recognized_revenue
payment_method
payment_status
payment_amount
is_completed_order
is_paid_order
is_refunded
total_refund_amount
refund_reason
latest_refund_date
Athena Queries
Preview curated data
SELECT *
FROM curated
LIMIT 10;
Count rows
SELECT COUNT(*) AS row_count
FROM curated;
Revenue by category
SELECT
    category,
    ROUND(SUM(recognized_revenue), 2) AS revenue
FROM curated
GROUP BY category
ORDER BY revenue DESC;
Daily revenue
SELECT
    order_date,
    ROUND(SUM(recognized_revenue), 2) AS daily_revenue
FROM curated
GROUP BY order_date
ORDER BY order_date;
Revenue by month

Partition columns may be detected as strings by the Glue crawler, so order_year is filtered as '2026'.

SELECT
    CAST(order_month AS INTEGER) AS order_month,
    ROUND(SUM(recognized_revenue), 2) AS revenue
FROM curated
WHERE order_year = '2026'
GROUP BY CAST(order_month AS INTEGER)
ORDER BY CAST(order_month AS INTEGER);
Top products
SELECT
    product_name,
    category,
    SUM(quantity) AS units_sold,
    ROUND(SUM(recognized_revenue), 2) AS revenue
FROM curated
GROUP BY product_name, category
ORDER BY revenue DESC
LIMIT 10;
Refund rate by category
SELECT
    category,
    COUNT(*) AS line_items,
    SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) AS refunded_line_items,
    ROUND(
        SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS refund_rate_percent
FROM curated
GROUP BY category
ORDER BY refund_rate_percent DESC;
Key Concepts Learned

This project demonstrates:

S3 as a raw and curated data lake
Glue Crawlers for schema discovery
Glue Data Catalog as the metadata layer
Athena for serverless SQL over S3
Glue PySpark for ETL
Parquet as an analytics-optimized file format
Partitioning by year and month
IAM role permissions for Glue jobs
Separation of raw and curated data zones
Interview Summary

I built an AWS retail sales analytics pipeline that ingests raw e-commerce CSV files into S3, catalogs them with AWS Glue Crawlers, transforms them with a Glue PySpark ETL job, writes curated partitioned Parquet data back to S3, and queries business metrics in Athena.

The project helped me map my Azure Synapse and PySpark experience to the AWS data engineering stack: S3 for data lake storage, Glue for cataloging and ETL, IAM roles for service permissions, and Athena for SQL analytics.