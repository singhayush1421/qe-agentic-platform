
from fastapi import FastAPI, Request, HTTPException
from services.ing_service.ingest_event import insert_event
from loguru import logger


app = FastAPI()


# -----------------------------------
# ✅ HEALTH CHECK
# -----------------------------------
@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# -----------------------------------
# ✅ EVENT INGESTION ENDPOINT
# -----------------------------------
@app.post("/event")
async def receive_event(request: Request):

    try:
        # ✅ Parse JSON safely
        event = await request.json()

        logger.info("📩 Event received at /event endpoint")

        # ✅ Validate basic structure
        if not isinstance(event, dict):
            raise HTTPException(status_code=400, detail="Invalid event format")

        if "event_id" not in event:
            raise HTTPException(status_code=400, detail="Missing event_id")

        # ✅ Store in DB
        insert_event(event)

        logger.info(f"✅ Event stored: {event.get('event_id')}")

        return {
            "status": "stored",
            "event_id": event.get("event_id")
        }

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"❌ Error processing event: {e}")
        logger.info("🔥 Calling insert_event()")

        raise HTTPException(
            status_code=500,
            detail="Internal Server Error while storing event"
        )
