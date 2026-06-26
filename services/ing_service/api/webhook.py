
from fastapi import APIRouter, Request
from loguru import logger
from services.ing_service.adapters.registry import get_adapter
from services.ing_service.ingest_event import insert_event

router = APIRouter()


@router.post("/webhook/github")
async def github_webhook(request: Request):
    try:
        data = await request.json()

        logger.info("✅ Received event")
        logger.info("🔍 Raw payload:")
        logger.info(data)

        # ✅ Get adapter
        adapter = get_adapter(data)
        logger.info(f"✅ Adapter selected: {adapter.__class__.__name__}")

        # ✅ Transform event
        event = adapter.transform(data)

        logger.info("✅ Transformed event:")
        logger.info(event)

        # ✅ ✅ THIS LINE WAS MISSING 🔥
        insert_event(event)

        logger.info("✅ Event inserted into DB")

        return {"status": "success"}

    except Exception as e:
        logger.exception(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}
