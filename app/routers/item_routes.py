from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from services.item_service import get_items_by_ocr
from schemas.item import ItemRead
from db import SessionDep
from sqlmodel import select
from models import Job
from models import Object

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

# @router.get("/test/")
# async def test_endpoint():
#     return {"message": "Test endpoint is working"}

@router.get("/search/", response_model=List[ItemRead])
async def search_items_by_ocr(ocr: str, session: AsyncSession = Depends(get_session)):
    """
    Busca items por el campo 'ocr'.

    :param ocr: El valor del campo 'ocr' a buscar.
    :return: Lista de items que coinciden con el 'ocr' proporcionado.
    """
    items = await get_items_by_ocr(ocr, session)
    if not items:
        raise HTTPException(status_code=404, detail="No se encontraron items con ese OCR")
    return items
