
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from typing import Optional
import json

from services.ing_service.adapters.registry import get_adapter

router = APIRouter()


# ✅ Generic payload model (works for all systems)
class GenericWebhookPayload(BaseModel):
    repository: Optional[dict] = None
    pusher: Optional[dict] = None
    head_commit: Optional[dict] = None

    job: Optional[dict] = None
    build: Optional[dict] = None

    eventType: Optional[str] = None
    resource: Optional[dict] = None


@router.post("/webhook/github")
async def github_webhook(payload: GenericWebhookPayload):
    try:
        #  Convert incoming payload
        data = payload.dict(exclude_unset=True)

        logger.info("✅ Received event")

        # Log raw payload (important for debugging)
        logger.info("🔍 Raw payload:")
        logger.info(json.dumps(data, indent=2))

        #  Get correct adapter
        adapter = get_adapter(data)

        if not adapter:
            logger.warning("❌ No adapter matched")
            raise HTTPException(status_code=400, detail="No adapter found")

        logger.info(f"✅ Adapter selected: {adapter.__class__.__name__}")

        #  Transform event
        event = adapter.transform(data)
        
        print("\n✅ EVENT RECEIVED:")
        print(event)

        print("\n✅ RAW PAYLOAD:")
        print(data)


        #  Pretty print transformed event
        logger.info(" Transformed event:")
        logger.info(json.dumps(event, indent=2))

        #  (Optional) Future integrations
        # insert_commit(event)      # PostgreSQL
        # publish_event(event)     # Kafka

        return {
            "status": "processed",
            "adapter": adapter.__class__.__name__,
            "source": event.get("source"),
            "event": event
        }

    
    except Exception as e:
        logger.exception("❌ FULL ERROR TRACE:")
        raise HTTPException(status_code=500, detail=str(e))

