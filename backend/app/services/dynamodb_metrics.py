from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.config import AWS_REGION, DYNAMODB_TABLE


dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
metrics_table = dynamodb.Table(DYNAMODB_TABLE)


def convert_decimal_to_json(value: Any) -> Any:
    """
    DynamoDB returns numbers as Decimal.
    FastAPI cannot JSON-serialize Decimal by default, so convert them.
    """
    if isinstance(value, list):
        return [convert_decimal_to_json(item) for item in value]

    if isinstance(value, dict):
        return {
            key: convert_decimal_to_json(val)
            for key, val in value.items()
        }

    if isinstance(value, Decimal):
        # If Decimal is whole number, return int.
        if value % 1 == 0:
            return int(value)

        # Otherwise return float for chart-friendly JSON.
        return float(value)

    return value


def get_metric_item(metric_name: str, metric_key: str) -> dict[str, Any] | None:
    """
    Read one DynamoDB item using the full primary key.
    Example:
      metric_name = "summary"
      metric_key = "latest"
    """
    response = metrics_table.get_item(
        Key={
            "metric_name": metric_name,
            "metric_key": metric_key,
        }
    )

    item = response.get("Item")

    if item is None:
        return None

    return convert_decimal_to_json(item)


def get_metric_group(metric_name: str) -> list[dict[str, Any]]:
    """
    Query all items for one metric group.
    Example:
      metric_name = "monthly_revenue"
      returns all monthly revenue rows.
    """
    response = metrics_table.query(
        KeyConditionExpression=Key("metric_name").eq(metric_name)
    )

    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = metrics_table.query(
            KeyConditionExpression=Key("metric_name").eq(metric_name),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    return convert_decimal_to_json(items)