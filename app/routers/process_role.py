from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlmodel import select, Session, and_
from models import ProcessRole, Process, Role, User
from db import SessionDep
from auth import get_current_active_user
from models import ProcessRoleBase, ProcessRoleCreate, ProcessRoleResponse
from typing import Annotated, Optional, List
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/process-roles",
    tags=["Process Roles"]
)

@router.post("/", response_model=ProcessRoleResponse,
            summary="Create process-role association",
            response_description="Returns the created process-role association",
            status_code=status.HTTP_201_CREATED,
            responses={
                201: {"description": "Process-role association created successfully"},
                400: {"description": "Invalid data or association already exists"},
                404: {"description": "Process or role not found"}
            }
)
def create_process_role(
    process_role_data: ProcessRoleCreate, 
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Create a new process-role association

    Associates a role with a process, allowing users with that role to work on that process.

    ### Parameters:
    - **process_role_data** (ProcessRoleCreate): Association data including:
        - process_id: ID of the process
        - role_id: ID of the role

    ### Returns:
    - **ProcessRoleResponse**: Created association details

    ### Example Request:
    ```json
    {
        "process_id": 1,
        "role_id": 2
    }
    ```

    ### Example Response:
    ```json
    {
        "id": 1,
        "process_id": 1,
        "role_id": 2
    }
    ```
    """
    logger.info(f"Creating process-role association: process_id={process_role_data.process_id}, role_id={process_role_data.role_id}")
    
    try:
        # Verificar que el proceso existe
        process = session.get(Process, process_role_data.process_id)
        if not process:
            logger.warning(f"Process with ID {process_role_data.process_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process with ID {process_role_data.process_id} not found"
            )

        # Verificar que el rol existe
        role = session.get(Role, process_role_data.role_id)
        if not role:
            logger.warning(f"Role with ID {process_role_data.role_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {process_role_data.role_id} not found"
            )

        # Verificar que la asociación no existe ya
        existing_association = session.exec(
            select(ProcessRole).where(
                and_(
                    ProcessRole.process_id == process_role_data.process_id,
                    ProcessRole.role_id == process_role_data.role_id
                )
            )
        ).first()

        if existing_association:
            logger.warning(f"Process-role association already exists: process_id={process_role_data.process_id}, role_id={process_role_data.role_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This process-role association already exists"
            )

        # Crear la nueva asociación
        process_role = ProcessRole(
            process_id=process_role_data.process_id,
            role_id=process_role_data.role_id
        )

        session.add(process_role)
        session.commit()
        session.refresh(process_role)

        logger.info(f"Process-role association created successfully with ID: {process_role.id}")
        return process_role

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Database error creating process-role association: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating process-role association"
        )


@router.get("/", response_model=List[ProcessRoleResponse],
           summary="List all process-role associations",
           response_description="Returns list of all process-role associations",
           status_code=status.HTTP_200_OK
)
def list_process_roles(session: SessionDep):
    """
    ## Get all process-role associations

    Retrieves a complete list of all process-role associations in the system.

    ### Returns:
    - **List[ProcessRoleResponse]**: List of all process-role associations

    ### Example Response:
    ```json
    [
        {
            "id": 1,
            "process_id": 1,
            "role_id": 2
        },
        {
            "id": 2,
            "process_id": 1,
            "role_id": 3
        }
    ]
    ```
    """
    logger.info("Retrieving all process-role associations")
    
    try:
        process_roles = session.exec(select(ProcessRole)).all()
        logger.info(f"Retrieved {len(process_roles)} process-role associations")
        return process_roles
    
    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Database error retrieving process-role associations: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving process-role associations"
        )


@router.get("/{association_id}", response_model=ProcessRoleResponse,
           summary="Get process-role association by ID",
           response_description="Returns the specified process-role association",
           responses={
               200: {"description": "Association found successfully"},
               404: {"description": "Association not found"}
           }
)
def get_process_role(association_id: int, session: SessionDep):
    """
    ## Get process-role association by ID

    Retrieves a specific process-role association by its unique identifier.

    ### Parameters:
    - **association_id** (int): Unique identifier of the association

    ### Returns:
    - **ProcessRoleResponse**: Association object with the specified ID

    ### Example Response:
    ```json
    {
        "id": 1,
        "process_id": 1,
        "role_id": 2
    }
    ```
    """
    logger.info(f"Retrieving process-role association with ID: {association_id}")
    
    process_role = session.get(ProcessRole, association_id)
    if not process_role:
        logger.warning(f"Process-role association with ID {association_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process-role association not found"
        )
    
    return process_role


@router.put("/{association_id}", response_model=ProcessRoleResponse,
           summary="Update process-role association",
           response_description="Returns the updated process-role association",
           responses={
               200: {"description": "Association updated successfully"},
               400: {"description": "Invalid data or association already exists"},
               404: {"description": "Association, process, or role not found"}
           }
)
def update_process_role(
    association_id: int,
    process_role_data: ProcessRoleBase,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Update an existing process-role association

    Updates the process or role in an existing association.

    ### Parameters:
    - **association_id** (int): Unique identifier of the association to update
    - **process_role_data** (ProcessRoleBase): New association data

    ### Example Request:
    ```json
    {
        "process_id": 2,
        "role_id": 3
    }
    ```

    ### Example Response:
    ```json
    {
        "id": 1,
        "process_id": 2,
        "role_id": 3
    }
    ```
    """
    logger.info(f"Updating process-role association with ID: {association_id}")
    
    try:
        # Buscar la asociación existente
        process_role = session.get(ProcessRole, association_id)
        if not process_role:
            logger.warning(f"Process-role association with ID {association_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process-role association not found"
            )

        # Verificar que el proceso existe
        process = session.get(Process, process_role_data.process_id)
        if not process:
            logger.warning(f"Process with ID {process_role_data.process_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process with ID {process_role_data.process_id} not found"
            )

        # Verificar que el rol existe
        role = session.get(Role, process_role_data.role_id)
        if not role:
            logger.warning(f"Role with ID {process_role_data.role_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {process_role_data.role_id} not found"
            )

        # Verificar que no existe otra asociación con los mismos datos (excepto la actual)
        existing_association = session.exec(
            select(ProcessRole).where(
                and_(
                    ProcessRole.process_id == process_role_data.process_id,
                    ProcessRole.role_id == process_role_data.role_id,
                    ProcessRole.id != association_id
                )
            )
        ).first()

        if existing_association:
            logger.warning(f"Another process-role association already exists with same data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another association with the same process and role already exists"
            )

        # Actualizar la asociación
        process_role.process_id = process_role_data.process_id
        process_role.role_id = process_role_data.role_id

        session.add(process_role)
        session.commit()
        session.refresh(process_role)

        logger.info(f"Process-role association {association_id} updated successfully")
        return process_role

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Database error updating process-role association: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating process-role association"
        )


@router.delete("/{association_id}",
              summary="Delete process-role association",
              response_description="No content returned",
              status_code=status.HTTP_204_NO_CONTENT,
              responses={
                  204: {"description": "Association deleted successfully"},
                  404: {"description": "Association not found"}
              }
)
def delete_process_role(
    association_id: int,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Delete a process-role association

    Removes a process-role association from the system.

    ### Parameters:
    - **association_id** (int): Unique identifier of the association to delete

    ### Returns:
    - **204 No Content**: Association was successfully deleted
    """
    logger.info(f"Deleting process-role association with ID: {association_id}")
    
    try:
        process_role = session.get(ProcessRole, association_id)
        if not process_role:
            logger.warning(f"Process-role association with ID {association_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process-role association not found"
            )

        session.delete(process_role)
        session.commit()

        logger.info(f"Process-role association {association_id} deleted successfully")
        return None

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        logger.error(f"Database error deleting process-role association: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting process-role association"
        )


# Endpoints adicionales útiles

@router.get("/by-process/{process_id}", response_model=List[ProcessRoleResponse],
           summary="Get roles associated with a process",
           response_description="Returns list of role associations for the specified process",
           responses={
               200: {"description": "Roles retrieved successfully"},
               404: {"description": "Process not found"}
           }
)
def get_roles_by_process(process_id: int, session: SessionDep):
    """
    ## Get all roles associated with a specific process

    Retrieves all role associations for a given process.

    ### Parameters:
    - **process_id** (int): Unique identifier of the process

    ### Returns:
    - **List[ProcessRoleResponse]**: List of role associations for the process

    ### Example Response:
    ```json
    [
        {
            "id": 1,
            "process_id": 1,
            "role_id": 2
        },
        {
            "id": 2,
            "process_id": 1,
            "role_id": 3
        }
    ]
    ```
    """
    logger.info(f"Retrieving roles for process ID: {process_id}")
    
    # Verificar que el proceso existe
    process = session.get(Process, process_id)
    if not process:
        logger.warning(f"Process with ID {process_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with ID {process_id} not found"
        )

    try:
        process_roles = session.exec(
            select(ProcessRole).where(ProcessRole.process_id == process_id)
        ).all()
        
        logger.info(f"Found {len(process_roles)} roles associated with process {process_id}")
        return process_roles

    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Database error retrieving roles by process: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving roles by process"
        )


@router.get("/by-role/{role_id}", response_model=List[ProcessRoleResponse],
           summary="Get processes associated with a role",
           response_description="Returns list of process associations for the specified role",
           responses={
               200: {"description": "Processes retrieved successfully"},
               404: {"description": "Role not found"}
           }
)
def get_processes_by_role(role_id: int, session: SessionDep):
    """
    ## Get all processes associated with a specific role

    Retrieves all process associations for a given role.

    ### Parameters:
    - **role_id** (int): Unique identifier of the role

    ### Returns:
    - **List[ProcessRoleResponse]**: List of process associations for the role

    ### Example Response:
    ```json
    [
        {
            "id": 1,
            "process_id": 1,
            "role_id": 2
        },
        {
            "id": 3,
            "process_id": 2,
            "role_id": 2
        }
    ]
    ```
    """
    logger.info(f"Retrieving processes for role ID: {role_id}")
    
    # Verificar que el rol existe
    role = session.get(Role, role_id)
    if not role:
        logger.warning(f"Role with ID {role_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )

    try:
        process_roles = session.exec(
            select(ProcessRole).where(ProcessRole.role_id == role_id)
        ).all()
        
        logger.info(f"Found {len(process_roles)} processes associated with role {role_id}")
        return process_roles

    except SQLAlchemyError as e:
        error_message = str(e)
        logger.error(f"Database error retrieving processes by role: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving processes by role"
        )