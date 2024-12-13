from fastapi import HTTPException
from models import Stage
from db import SessionDep
from fastapi import APIRouter
from sqlmodel import select
from models import Item, Stage



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


# @router.get("/object/{object_id}", response_model=Object)
# def get_object_by_id(object_id: int, session: SessionDep):
#     # Buscar el Object por su ID
#     obj = session.exec(select(Object).where(Object.object_id == object_id)).first()
#     if not obj:
#         raise HTTPException(status_code=404, detail=f"El Object con ID '{object_id}' no existe.")
#     return obj

