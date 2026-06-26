from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import AWS_REGION, DYNAMODB_TABLE
from app.routes.analytics import router as analytics_router
from app.routes.pipeline import router as pipeline_router


app = FastAPI(
    title="RetailLens Analytics API",
    description="FastAPI backend for the AWS retail sales analytics dashboard.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://retail-sales-aws-pipeline.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "RetailLens Analytics API",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "retaillens-analytics-api",
        "aws_region": AWS_REGION,
        "dynamodb_table": DYNAMODB_TABLE,
    }


app.include_router(analytics_router)
app.include_router(pipeline_router)