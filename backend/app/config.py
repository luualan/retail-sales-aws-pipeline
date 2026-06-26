import os


AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "retail_analytics_metrics")