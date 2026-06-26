import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "SOURCE_DATABASE",
        "TARGET_PATH",
    ],
)

source_database = args["SOURCE_DATABASE"]
target_path = args["TARGET_PATH"].rstrip("/")

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


def read_catalog_table(table_name: str):
    """
    Reads a table from the AWS Glue Data Catalog and converts it to a Spark DataFrame.
    """
    return glue_context.create_dynamic_frame.from_catalog(
        database=source_database,
        table_name=table_name,
    ).toDF()


# ----------------------------
# Read raw tables
# ----------------------------

customers_raw = read_catalog_table("customers")
products_raw = read_catalog_table("products")
orders_raw = read_catalog_table("orders")
order_items_raw = read_catalog_table("order_items")
payments_raw = read_catalog_table("payments")
refunds_raw = read_catalog_table("refunds")


# ----------------------------
# Clean / normalize tables
# ----------------------------

customers = (
    customers_raw
    .select(
        F.col("customer_id").cast("long").alias("customer_id"),
        F.col("customer_name"),
        F.col("email"),
        F.col("state").alias("customer_state"),
        F.to_date("signup_date").alias("signup_date"),
    )
    .dropDuplicates(["customer_id"])
)

products = (
    products_raw
    .select(
        F.col("product_id").cast("long").alias("product_id"),
        F.col("product_name"),
        F.col("category"),
        F.col("price").cast("double").alias("catalog_price"),
    )
    .dropDuplicates(["product_id"])
)

orders = (
    orders_raw
    .select(
        F.col("order_id").cast("long").alias("order_id"),
        F.col("customer_id").cast("long").alias("customer_id"),
        F.to_date("order_date").alias("order_date"),
        F.lower(F.col("order_status")).alias("order_status"),
        F.lower(F.col("region")).alias("region"),
    )
    .dropDuplicates(["order_id"])
)

order_items = (
    order_items_raw
    .select(
        F.col("order_item_id").cast("long").alias("order_item_id"),
        F.col("order_id").cast("long").alias("order_id"),
        F.col("product_id").cast("long").alias("product_id"),
        F.col("quantity").cast("int").alias("quantity"),
        F.col("unit_price").cast("double").alias("unit_price"),
    )
    .dropDuplicates(["order_item_id"])
    .filter(F.col("quantity") > 0)
)

payments = (
    payments_raw
    .select(
        F.col("payment_id").cast("long").alias("payment_id"),
        F.col("order_id").cast("long").alias("order_id"),
        F.lower(F.col("payment_method")).alias("payment_method"),
        F.lower(F.col("payment_status")).alias("payment_status"),
        F.col("amount").cast("double").alias("payment_amount"),
    )
    .dropDuplicates(["payment_id"])
)

refunds = (
    refunds_raw
    .select(
        F.col("refund_id").cast("long").alias("refund_id"),
        F.col("order_id").cast("long").alias("order_id"),
        F.to_date("refund_date").alias("refund_date"),
        F.col("refund_amount").cast("double").alias("refund_amount"),
        F.lower(F.col("refund_reason")).alias("refund_reason"),
    )
    .dropDuplicates(["refund_id"])
)


# ----------------------------
# Aggregate payment/refund data to order level
# ----------------------------

payments_by_order = (
    payments
    .groupBy("order_id")
    .agg(
        F.first("payment_method", ignorenulls=True).alias("payment_method"),
        F.first("payment_status", ignorenulls=True).alias("payment_status"),
        F.sum("payment_amount").alias("payment_amount"),
        F.max(
            F.when(F.col("payment_status") == "paid", F.lit(1)).otherwise(F.lit(0))
        ).alias("has_paid_payment"),
        F.max(
            F.when(F.col("payment_status") == "refunded", F.lit(1)).otherwise(F.lit(0))
        ).alias("has_refunded_payment"),
    )
)

refunds_by_order = (
    refunds
    .groupBy("order_id")
    .agg(
        F.sum("refund_amount").alias("total_refund_amount"),
        F.first("refund_reason", ignorenulls=True).alias("refund_reason"),
        F.max("refund_date").alias("latest_refund_date"),
    )
)


# ----------------------------
# Build curated fact_sales table
# ----------------------------

fact_sales = (
    order_items
    .join(orders, on="order_id", how="inner")
    .join(products, on="product_id", how="left")
    .join(customers, on="customer_id", how="left")
    .join(payments_by_order, on="order_id", how="left")
    .join(refunds_by_order, on="order_id", how="left")
    .withColumn(
        "line_item_revenue",
        F.round(F.col("quantity") * F.col("unit_price"), 2),
    )
    .withColumn(
        "is_completed_order",
        F.col("order_status") == F.lit("completed"),
    )
    .withColumn(
        "is_paid_order",
        F.col("has_paid_payment") == F.lit(1),
    )
    .withColumn(
        "is_refunded",
        (F.col("has_refunded_payment") == F.lit(1))
        | (F.col("total_refund_amount") > F.lit(0)),
    )
    .withColumn(
        "recognized_revenue",
        F.when(
            (F.col("order_status") == "completed")
            & (F.col("has_paid_payment") == 1),
            F.col("line_item_revenue"),
        ).otherwise(F.lit(0.0)),
    )
    .withColumn("order_year", F.year("order_date"))
    .withColumn("order_month", F.month("order_date"))
    .select(
        "order_id",
        "order_item_id",
        "customer_id",
        "customer_state",
        "region",
        "order_date",
        "order_year",
        "order_month",
        "order_status",
        "product_id",
        "product_name",
        "category",
        "quantity",
        "unit_price",
        "line_item_revenue",
        "recognized_revenue",
        "payment_method",
        "payment_status",
        "payment_amount",
        "is_completed_order",
        "is_paid_order",
        "is_refunded",
        "total_refund_amount",
        "refund_reason",
        "latest_refund_date",
    )
)


# ----------------------------
# Write curated output to S3 as Parquet
# ----------------------------

output_path = f"{target_path}/fact_sales/"

print(f"Writing fact_sales to: {output_path}")

(
    fact_sales
    .coalesce(1)  # restrict to 1 output file for easier testing; in production, remove this line for better parallelism
    .write
    .mode("overwrite")
    .partitionBy("order_year", "order_month")
    .parquet(output_path)
)

print("ETL job completed successfully.")

job.commit()