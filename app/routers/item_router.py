from fastapi import HTTPException
from db import SessionDep
from fastapi import APIRouter
from sqlmodel import select
from models import Item, Object


router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


@router.get("/item_process/{item_id}",  response_model=list[str])#, response_model=str)
def get_item_by_id(item_id: int, session: SessionDep):
    # Buscar el Item por su ID
    item = session.exec(select(Item).where(Item.item_id == item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"El Item con ID '{item_id}' no existe.")
    return item.stage_names

@router.get("/item_process_ids/{item_id}",  response_model=list[int])#, response_model=str)
def get_item_by_id(item_id: int, session: SessionDep):
    # Buscar el Item por su ID
    item = session.exec(select(Item).where(Item.item_id == item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"El Item con ID '{item_id}' no existe.")
    return item.stage_ids


@router.delete("/item/{item_id}")
def delete_item(item_id: int, session: SessionDep):
    """
    Endpoint para eliminar un Item y todos los Objects relacionados.

    Parámetros:
        - item_id: ID del Item que se desea eliminar.
    """
    # Verificar si el Item existe
    item = session.exec(select(Item).where(Item.item_id == item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="El Item no existe.")

    # Eliminar los Objects relacionados al Item
    session.exec(select(Object).where(Object.item_id == item.item_id)).delete()

    # Eliminar el Item
    session.delete(item)
    session.commit()

    return {"message": f"El Item con ID '{item_id}' y todos los Objects relacionados fueron eliminados exitosamente."}
