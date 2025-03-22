from fastapi import HTTPException
from db import SessionDep
from fastapi import APIRouter
from sqlmodel import select
from models import Item, Object


router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


@router.get("/item_process/{item_id}",  response_model=list[str],
        summary="Get stage names for a specific item",
        response_description="Returns a list of stage names associated with the item",
        tags=["Items"],  # Agrupa en la sección "Items"
    )#, response_model=str)
def get_item_by_id(item_id: int, session: SessionDep):
    """
    ## Endpoint to retrieve stage names for a specific item

    This endpoint returns a list of stage names associated with the item identified by `item_id`.

    ### Arguments:
    - **item_id** (int): The ID of the item to retrieve stage names for.

    ### Returns:
    - **List[str]**: A list of stage names.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item with the specified ID does not exist.

    ### Example Usage:
    ```http
    GET /items/item_process/1

    Response:
    [
        "Stage 1",
        "Stage 2",
        "Stage 3"
    ]
    """
    # Buscar el Item por su ID
    item = session.exec(select(Item).where(Item.item_id == item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"El Item con ID '{item_id}' no existe.")
    return item.stage_names

@router.get("/item_process_ids/{item_id}",  response_model=list[int],
        summary="Get stage IDs for a specific item",
        response_description="Returns a list of stage IDs associated with the item",
        tags=["Items"],
    )#, response_model=str)
def get_item_by_id(item_id: int, session: SessionDep):
    """
    ## Endpoint to retrieve stage IDs for a specific item

    This endpoint returns a list of stage IDs associated with the item identified by `item_id`.

    ### Arguments:
    - **item_id** (int): The ID of the item to retrieve stage IDs for.

    ### Returns:
    - **List[int]**: A list of stage IDs.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item with the specified ID does not exist.

    ### Example Usage:
    ```http
    GET /items/item_process_ids/1

    Response:
    [
        1,
        2,
        3
    ]
    """
    # Buscar el Item por su ID
    item = session.exec(select(Item).where(Item.item_id == item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"El Item con ID '{item_id}' no existe.")
    return item.stage_ids


@router.delete("/item/{item_id}",
        summary="Delete an item and its related objects",
        response_description="Confirmation message after deleting the item and its related objects",
        tags=["Items"],  # Agrupa en la sección "Items"
        responses={
            200: {"description": "Item and related objects deleted successfully"},
            404: {"description": "Item not found"},
        },
    )
def delete_item(item_id: int, session: SessionDep):
    """
    ## Endpoint to delete an item and its related objects

    This endpoint deletes the item identified by `item_id` and all objects related to it.

    ### Arguments:
    - **item_id** (int): The ID of the item to delete.

    ### Returns:
    - **dict**: A confirmation message.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item with the specified ID does not exist.

    ### Example Usage:
    ```http
    DELETE /items/item/1

    Response:
    {
        "message": "El Item con ID '1' y todos los Objects relacionados fueron eliminados exitosamente."
    }
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
