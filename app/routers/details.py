from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import select
from db import SessionDep
from models import Item, Object

# Crear el router
router = APIRouter(
    prefix="/details",
    tags=["Details"]
)

@router.get("/item/{ocr}", response_model=Item,
        summary="Get item details by OCR",
        response_description="Returns the details of the item identified by OCR",
        tags=["Details"],  # Agrupa en la sección "Details"
        responses={
            200: {"description": "Successfully returned the item details"},
            404: {"description": "Item with the specified OCR does not exist"},
        },
    )
def get_item_by_id(ocr: str, session: SessionDep):
    """
    ## Endpoint to retrieve item details by OCR

    This endpoint retrieves the details of the item identified by its OCR (Optical Character Recognition) code.

    ### Arguments:
    - **ocr** (str): The OCR code of the item to retrieve.

    ### Returns:
    - **Item**: The details of the item.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item with the specified OCR does not exist.

    ### Example Usage:
    ```http
    GET /details/item/123456

    Response:
    {
        "item_id": 1,
        "ocr": "123456",
        "name": "Item 1",
        "description": "Description of Item 1"
    }
    ```

    ### Workflow:
    1. Query the database to retrieve the item with the specified OCR.
    2. If the item exists, return its details.
    3. If the item does not exist, return a `404` error.
    """
    # Buscar el Item por su ID
    item = session.exec(select(Item).where(Item.ocr == ocr)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El Item con ocr '{ocr}' no existe.")
    return item

@router.get("/object/{object_id}", response_model=Object,
        summary="Get object details by ID",
        response_description="Returns the details of the object identified by ID",
        tags=["Details"],  # Agrupa en la sección "Details"
        responses={
            200: {"description": "Successfully returned the object details"},
            404: {"description": "Object with the specified ID does not exist"},
        },
    )
def get_object_by_id(object_id: int, session: SessionDep):
    """
    ## Endpoint to retrieve object details by ID

    This endpoint retrieves the details of the object identified by its ID.

    ### Arguments:
    - **object_id** (int): The ID of the object to retrieve.

    ### Returns:
    - **Object**: The details of the object.

    ### Raises:
    - `HTTPException`:
        - `404`: If the object with the specified ID does not exist.

    ### Example Usage:
    ```http
    GET /details/object/1

    Response:
    {
        "object_id": 1,
        "name": "Object 1",
        "description": "Description of Object 1"
    }
    ```

    ### Workflow:
    1. Query the database to retrieve the object with the specified ID.
    2. If the object exists, return its details.
    3. If the object does not exist, return a `404` error.
    """
    # Buscar el Object por su ID
    obj = session.exec(select(Object).where(Object.object_id == object_id)).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El Object con ID '{object_id}' no existe.")
    return obj
