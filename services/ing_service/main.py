
from fastapi import FastAPI
from loguru import logger
from services.ing_service.api.webhook import router as webhook_router

logger.add("logs/ingestion_{time}.log", rotation="5 MB")
app = FastAPI(title="Ingestion Service")

@app.get("/")
def health():
    return {"status": "Ingestion Service Running"}

app.include_router(webhook_router)
