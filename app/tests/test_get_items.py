import asyncio
from db.connection import get_session
from services.item_service import get_items_by_ocr

async def test_get_items_by_ocr():
    async with get_session() as session:
        ocr_value = "example_ocr"
        items = await get_items_by_ocr(ocr=ocr_value, session=session)
        print(f"Items encontrados para OCR '{ocr_value}': {items}")

asyncio.run(test_get_items_by_ocr())
