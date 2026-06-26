from fastapi import APIRouter, HTTPException
from app.services.dynamodb_metrics import get_metric_group, get_metric_item


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get("/summary")
def get_summary():
    item = get_metric_item("summary", "latest")

    if item is None:
        raise HTTPException(status_code=404, detail="Summary metrics not found")

    return item


@router.get("/monthly-revenue")
def get_monthly_revenue():
    return {
        "items": get_metric_group("monthly_revenue")
    }


@router.get("/revenue-by-category")
def get_revenue_by_category():
    return {
        "items": get_metric_group("revenue_by_category")
    }


@router.get("/top-products")
def get_top_products():
    return {
        "items": get_metric_group("top_products")
    }


@router.get("/refund-rate-by-category")
def get_refund_rate_by_category():
    return {
        "items": get_metric_group("refund_rate_by_category")
    }


@router.get("/orders-by-region")
def get_orders_by_region():
    return {
        "items": get_metric_group("orders_by_region")
    }