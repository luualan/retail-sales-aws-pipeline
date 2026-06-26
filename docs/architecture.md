# Architecture

## RetailLens: AWS Retail Analytics Platform

RetailLens is a full-stack retail analytics platform that transforms raw e-commerce CSV data into curated analytics metrics and serves those metrics through a FastAPI backend and React dashboard.

```mermaid
flowchart TD
    subgraph Local["Local Development"]
        A[Python Sample Data Generator]
        B[Raw CSV Files]
        A --> B
    end

    subgraph S3Raw["Amazon S3 - Raw Zone"]
        C[customers.csv]
        D[products.csv]
        E[orders.csv]
        F[order_items.csv]
        G[payments.csv]
        H[refunds.csv]
    end

    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> H

    subgraph RawCatalog["AWS Glue Raw Catalog"]
        I[retail_raw_crawler]
        J[retail_raw_db]
    end

    C --> I
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    I --> J

    J --> K[Amazon Athena Raw Validation]

    subgraph GlueETL["AWS Glue PySpark ETL"]
        L[retail_sales_etl_job]
    end

    J --> L

    subgraph S3Curated["Amazon S3 - Curated Zone"]
        M[Partitioned Parquet fact_sales]
        N[order_year / order_month partitions]
    end

    L --> M
    M --> N

    subgraph CuratedCatalog["AWS Glue Curated Catalog"]
        O[retail_curated_crawler]
        P[retail_curated_db]
    end

    M --> O
    O --> P

    P --> Q[Amazon Athena Analytics Queries]

    subgraph MetricsServing["DynamoDB Serving Layer"]
        R[retail_analytics_metrics]
        S[summary]
        T[monthly_revenue]
        U[revenue_by_category]
        V[top_products]
        W[refund_rate_by_category]
        X[orders_by_region]
        Y[pipeline_status]
    end

    Q --> R
    R --> S
    R --> T
    R --> U
    R --> V
    R --> W
    R --> X
    R --> Y

    subgraph Backend["FastAPI Backend"]
        Z[Analytics REST APIs]
        AA[Pipeline Status API]
    end

    R --> Z
    R --> AA

    subgraph Frontend["React Frontend"]
        AB[Dashboard Page]
        AC[Products Page]
        AD[Refunds Page]
        AE[Pipeline Page]
    end

    Z --> AB
    Z --> AC
    Z --> AD
    AA --> AE