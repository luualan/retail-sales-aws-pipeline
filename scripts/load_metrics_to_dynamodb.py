import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3


AWS_REGION = "us-west-2"

ATHENA_DATABASE = "retail_curated_db"
ATHENA_TABLE = "curated"  # change to "fact_sales" if your Athena table is named fact_sales
ATHENA_OUTPUT_LOCATION = "s3://retail-sales-aws-pipeline-alan-20260623/athena-results/"

DYNAMODB_TABLE = "retail_analytics_metrics"


athena = boto3.client("athena", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
metrics_table = dynamodb.Table(DYNAMODB_TABLE)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_decimal(value: Any) -> Any:
    """
    DynamoDB does not accept Python float.
    Convert numeric values to Decimal.
    """
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal(str(round(value, 4)))

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned == "":
            return None

        try:
            # Convert strings that look numeric into Decimal.
            return Decimal(cleaned)
        except Exception:
            return value

    return value


def clean_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    Remove nulls and convert numeric values to DynamoDB-safe values.

    Important:
    metric_name and metric_key are DynamoDB key fields.
    They must stay as strings because the table schema defines them as String keys.
    """
    cleaned = {}

    for key, value in item.items():
        if value is None:
            continue

        if key in {"metric_name", "metric_key"}:
            cleaned[key] = str(value)
        else:
            cleaned[key] = to_decimal(value)

    return cleaned


def run_athena_query(sql: str) -> list[dict[str, Any]]:
    """
    Helper that takes SQL string, runs it in Athena, and returns the results as a list of dicts.
    Athena starts query
    Script waits/polls until query is done 
    Script fetches result rows
    Script converts rows into list[dict]
    """
    print("Running Athena query...")
    print(sql)

    start_response = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_LOCATION},
    )

    query_execution_id = start_response["QueryExecutionId"]

    while True:
        status_response = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )

        status = status_response["QueryExecution"]["Status"]["State"]

        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(1)

    if status != "SUCCEEDED":
        reason = status_response["QueryExecution"]["Status"].get(
            "StateChangeReason",
            "Unknown error",
        )
        raise RuntimeError(f"Athena query failed: {status}. Reason: {reason}")

    paginator = athena.get_paginator("get_query_results")
    pages = paginator.paginate(QueryExecutionId=query_execution_id)

    results = []
    columns = None
    is_first_row = True

    for page in pages:
        if columns is None:
            columns = [
                col["Name"]
                for col in page["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
            ]

        for row in page["ResultSet"]["Rows"]:
            values = []
            for cell in row.get("Data", []):
                values.append(cell.get("VarCharValue"))

            # Athena includes the header row in GetQueryResults. Skip including it in the results.
            if is_first_row:
                is_first_row = False
                if values == columns:
                    continue

            record = {}
            for index, column_name in enumerate(columns):
                record[column_name] = values[index] if index < len(values) else None

            results.append(record)

    return results


def clear_metric_group(metric_name: str) -> None:
    """
    Delete old items for a metric group so stale rows don't remain after refresh.
    """
    response = metrics_table.query(
        KeyConditionExpression="metric_name = :metric_name",
        ExpressionAttributeValues={":metric_name": metric_name},
    )

    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = metrics_table.query(
            KeyConditionExpression="metric_name = :metric_name",
            ExpressionAttributeValues={":metric_name": metric_name},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    if not items:
        return

    with metrics_table.batch_writer() as batch:
        for item in items:
            batch.delete_item(
                Key={
                    "metric_name": item["metric_name"],
                    "metric_key": item["metric_key"],
                }
            )

    print(f"Deleted {len(items)} old items for metric group: {metric_name}")


def write_metric_items(metric_name: str, rows: list[dict[str, Any]]) -> None:
    """
    Write a list of dicts to DynamoDB for a given metric group.
    Each dict must have a "metric_key" field that is unique within the metric group.
    """
    clear_metric_group(metric_name)

    refreshed_at = now_utc()

    with metrics_table.batch_writer() as batch:
        for row in rows:
            item = {
                "metric_name": metric_name,
                "last_updated": refreshed_at,
                **row,
            }

            batch.put_item(Item=clean_item(item))

    print(f"Wrote {len(rows)} items for metric group: {metric_name}")


def load_summary() -> None:
    sql = f"""
    SELECT
        'latest' AS metric_key,
        ROUND(SUM(recognized_revenue), 2) AS total_revenue,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(recognized_revenue) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
        ROUND(
            SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS refund_rate_percent
    FROM {ATHENA_TABLE}
    """

    rows = run_athena_query(sql)
    write_metric_items("summary", rows)


def load_monthly_revenue() -> None:
    sql = f"""
    SELECT
        CONCAT(CAST(order_year AS VARCHAR), '-', LPAD(CAST(order_month AS VARCHAR), 2, '0')) AS metric_key,
        CAST(order_year AS VARCHAR) AS order_year,
        LPAD(CAST(order_month AS VARCHAR), 2, '0') AS order_month,
        ROUND(SUM(recognized_revenue), 2) AS revenue
    FROM {ATHENA_TABLE}
    GROUP BY order_year, order_month
    ORDER BY order_year, order_month
    """

    rows = run_athena_query(sql)
    write_metric_items("monthly_revenue", rows)


def load_revenue_by_category() -> None:
    sql = f"""
    SELECT
        category AS metric_key,
        category,
        ROUND(SUM(recognized_revenue), 2) AS revenue
    FROM {ATHENA_TABLE}
    GROUP BY category
    ORDER BY revenue DESC
    """

    rows = run_athena_query(sql)
    write_metric_items("revenue_by_category", rows)


def load_top_products() -> None:
    sql = f"""
    SELECT
        LPAD(CAST(ROW_NUMBER() OVER (ORDER BY SUM(recognized_revenue) DESC) AS VARCHAR), 3, '0') AS metric_key,
        product_name,
        category,
        SUM(quantity) AS units_sold,
        ROUND(SUM(recognized_revenue), 2) AS revenue
    FROM {ATHENA_TABLE}
    GROUP BY product_name, category
    ORDER BY revenue DESC
    LIMIT 10
    """

    rows = run_athena_query(sql)
    write_metric_items("top_products", rows)


def load_refund_rate_by_category() -> None:
    sql = f"""
    SELECT
        category AS metric_key,
        category,
        COUNT(*) AS line_items,
        SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) AS refunded_line_items,
        ROUND(
            SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS refund_rate_percent
    FROM {ATHENA_TABLE}
    GROUP BY category
    ORDER BY refund_rate_percent DESC
    """

    rows = run_athena_query(sql)
    write_metric_items("refund_rate_by_category", rows)


def load_orders_by_region() -> None:
    sql = f"""
    SELECT
        region AS metric_key,
        region,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(recognized_revenue), 2) AS revenue
    FROM {ATHENA_TABLE}
    GROUP BY region
    ORDER BY revenue DESC
    """

    rows = run_athena_query(sql)
    write_metric_items("orders_by_region", rows)


def load_pipeline_status() -> None:
    """
    Simple metadata item for the frontend Pipeline page.
    Later, make this read actual Glue job run status.
    """
    rows = [
        {
            "metric_key": "latest",
            "raw_database": "retail_raw_db",
            "curated_database": "retail_curated_db",
            "curated_table": ATHENA_TABLE,
            "dynamodb_table": DYNAMODB_TABLE,
            "s3_curated_path": "s3://retail-sales-aws-pipeline-alan-20260623/curated/fact_sales/",
            "athena_output_location": ATHENA_OUTPUT_LOCATION,
            "status": "metrics_loaded",
        }
    ]

    write_metric_items("pipeline_status", rows)


def main() -> None:
    load_summary()
    load_monthly_revenue()
    load_revenue_by_category()
    load_top_products()
    load_refund_rate_by_category()
    load_orders_by_region()
    load_pipeline_status()

    print("Finished loading all metrics into DynamoDB.")


if __name__ == "__main__":
    main()