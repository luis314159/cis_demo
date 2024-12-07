from typing import List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.object import Item

async def get_items_by_ocr(ocr: str, session: AsyncSession) -> List[Item]:
    """
    Obtiene una lista de Items filtrados por el campo OCR.

    Args:
        ocr (str): El valor del campo OCR a buscar.
        session (AsyncSession): Sesión de la base de datos asincrónica.

    Returns:
        List[Item]: Lista de objetos Item que coinciden con el OCR proporcionado.
    """
    query = select(Item).where(Item.ocr == ocr)
    result = await session.execute(query)
    items = result.scalars().all()  # `scalars` devuelve los objetos mapeados por el ORM
    return items
