from sqlite3 import IntegrityError
from fastapi import APIRouter, HTTPException, status
from db import SessionDep
from sqlmodel import select
import logging
from models import Product, ProductCreate
from typing import List, Optional


from db import SessionDep
from models import Status, StatusCreate, PublicStatus, StatusResponse, Product

from logging import getLogger

logger = getLogger(__name__)

# Crear el router
router = APIRouter(
    prefix="/status",
    tags=["Status"]
)

@router.post("/create", response_model=Status,
            summary="Create a new status",
            response_description="Returns the newly created status",
            responses={
                200: {"description": "Status created successfully"},
                400: {"description": "A status with this name already exists"},
            },
    )
def create_status(status: StatusCreate, session: SessionDep):
    """
    ## Endpoint to create a new status

    This endpoint creates a new status in the system. It validates the input data and ensures that
    no duplicate status names exist.

    ### Arguments:
    - **status** (StatusCreate): The data required to create a new status.

    ### Returns:
    - **Status**: The newly created status object.

    ### Raises:
    - `HTTPException`:
        - `400`: If a status with the same name already exists.

    ### Example Usage:
    ```http
    POST /status/create
    Body:
    {
        "status_name": "In Progress"
    }

    Response:
    {
        "status_id": 1,
        "status_name": "In Progress"
    }
    ```

    ### Workflow:
    1. Validate the input data using the `StatusCreate` model.
    2. Check if a status with the same name already exists.
    3. If the name is unique, create and save the new status in the database.
    4. Return the newly created status.
    """
    # Crear una nueva instancia del modelo Status
    new_status = Status.model_validate(status)

    try:
        # Agregar el nuevo status a la base de datos
        session.add(new_status)
        session.commit()
        session.refresh(new_status)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A status with this name already exists."
        )

    return new_status

# In your status_router.py
@router.get("/",response_model=List[Status], status_code=status.HTTP_200_OK)
def list_statuses(db: SessionDep):
    try:

        statuses = db.exec(select(Status)).all()

        if not statuses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Statuses not found: {str(e)}")

        return statuses
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{status_id}", response_model=Status,
           summary="Get status by ID",
           response_description="Returns the status with the specified ID",
           responses={
               404: {"description": "Status not found"},
           })
def get_status_by_id(status_id: int, session: SessionDep):
    """
    ## Endpoint to get a status by its ID

    This endpoint retrieves a specific status from the database based on its ID.

    ### Arguments:
    - **status_id** (int): The ID of the status to retrieve.

    ### Returns:
    - **Status**: The status object with the specified ID.

    ### Raises:
    - `HTTPException`:
        - `404`: If the status with the specified ID is not found.

    ### Example Usage:
    ```http
    GET /status/1

    Response:
    {
        "status_id": 1,
        "status_name": "In Progress"
    }
    ```
    """
    # Buscar el status en la base de datos
    status_obj = session.get(Status, status_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found"
        )
    return status_obj

@router.put("/{status_id}", response_model=Status,
           summary="Update a status",
           response_description="Returns the updated status",
           responses={
               404: {"description": "Status not found"},
               400: {"description": "A status with this name already exists"},
           })
def update_status(status_id: int, status_data: StatusCreate, session: SessionDep):
    """
    ## Endpoint to update a status

    This endpoint updates an existing status in the system. It validates the input data and ensures that
    no duplicate status names exist.

    ### Arguments:
    - **status_id** (int): The ID of the status to update.
    - **status_data** (StatusCreate): The new data for the status.

    ### Returns:
    - **Status**: The updated status object.

    ### Raises:
    - `HTTPException`:
        - `404`: If the status with the specified ID is not found.
        - `400`: If a status with the same name already exists.

    ### Example Usage:
    ```http
    PUT /status/1
    Body:
    {
        "status_name": "Completed"
    }

    Response:
    {
        "status_id": 1,
        "status_name": "Completed"
    }
    ```

    ### Workflow:
    1. Validate the input data using the `StatusCreate` model.
    2. Check if the status with the specified ID exists.
    3. Update the status with the new data.
    4. Return the updated status.
    """
    # Buscar el status en la base de datos
    status_obj = session.get(Status, status_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found"
        )
    
    # Actualizar los datos del status
    status_data_dict = status_data.model_dump(exclude_unset=True)
    for key, value in status_data_dict.items():
        setattr(status_obj, key, value)
    
    try:
        session.add(status_obj)
        session.commit()
        session.refresh(status_obj)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A status with this name already exists."
        )
    
    return status_obj

@router.delete("/{status_id}", 
              summary="Delete a status",
              response_description="Status deleted successfully",
              responses={
                  404: {"description": "Status not found"},
                  400: {"description": "Cannot delete status that has defect records associated with it"},
              })
def delete_status(status_id: int, session: SessionDep):
    """
    ## Endpoint to delete a status

    This endpoint deletes a status from the database. It validates that the status exists and that
    it is not associated with any defect records.

    ### Arguments:
    - **status_id** (int): The ID of the status to delete.

    ### Returns:
    - **dict**: A message confirming the deletion.

    ### Raises:
    - `HTTPException`:
        - `404`: If the status with the specified ID is not found.
        - `400`: If the status is associated with defect records.

    ### Example Usage:
    ```http
    DELETE /status/1

    Response:
    {
        "message": "Status deleted successfully"
    }
    ```

    ### Workflow:
    1. Check if the status with the specified ID exists.
    2. Check if the status is associated with any defect records.
    3. Delete the status from the database.
    4. Return a confirmation message.
    """
    # Buscar el status en la base de datos
    status_obj = session.get(Status, status_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found"
        )
    
    # Verificar si el status tiene defect records asociados
    if status_obj.defect_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete status that has defect records associated with it"
        )
    
    # Eliminar el status
    session.delete(status_obj)
    session.commit()
    
    return {"message": "Status deleted successfully"}