from fastapi import APIRouter, HTTPException
from app.services.dynamodb_metrics import get_metric_item


router = APIRouter(
    prefix="/pipeline",
    tags=["pipeline"],
)


@router.get("/status")
def get_pipeline_status():
    item = get_metric_item("pipeline_status", "latest")

    if item is None:
        raise HTTPException(status_code=404, detail="Pipeline status not found")

    return item