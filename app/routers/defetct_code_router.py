from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, Session
from models import DefectCode, DefectCodeCreate, DefectCodeUpdate, PunchList, User
from db import SessionDep
from auth import get_current_active_user
from typing import List

router = APIRouter(
    prefix="/defect-codes",
    tags=["Defect Codes"]
)


@router.post("", response_model=DefectCode, status_code=status.HTTP_201_CREATED,
            summary="Create new defect code",
            response_description="Returns the created defect code",
            responses={
                201: {"description": "Defect code created successfully"},
                400: {"description": "Defect code already exists"}
            }
)
def create_defect_code(
    defect_code: DefectCodeCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Create a new defect code
    
    Adds a new defect code to the system for classifying punch list items.
    
    ### Parameters:
    - **defect_code** (DefectCodeCreate): Defect code creation data including:
        - code: Numeric code identifier
        - description: Description of the defect type
    
    ### Returns:
    - **DefectCode**: Created defect code details
    
    ### Example Request:
    ```json
    {
        "code": 101,
        "description": "Surface Irregularity"
    }
    ```
    """
    # Verificar si el código ya existe
    existing_code = session.exec(select(DefectCode).where(DefectCode.code == defect_code.code)).first()
    if existing_code:
        raise HTTPException(status_code=400, detail="Defect code already exists")
    
    # Crear el nuevo código de defecto
    new_defect_code = DefectCode(
        code=defect_code.code,
        description=defect_code.description
    )
    
    session.add(new_defect_code)
    session.commit()
    session.refresh(new_defect_code)
    
    return new_defect_code


@router.get("", response_model=List[DefectCode],
            summary="Get all defect codes",
            response_description="Returns a list of all defect codes"
)
def get_all_defect_codes(
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Get all defect codes
    
    Retrieves all defect codes registered in the system.
    
    ### Returns:
    - **List[DefectCode]**: List of all defect codes
    """
    defect_codes = session.exec(select(DefectCode)).all()
    return defect_codes


@router.get("/{defect_code_id}", response_model=DefectCode,
            summary="Get defect code by ID",
            response_description="Returns the requested defect code",
            responses={
                404: {"description": "Defect code not found"}
            }
)
def get_defect_code(
    defect_code_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Get defect code by ID
    
    Retrieves a specific defect code by its ID.
    
    ### Parameters:
    - **defect_code_id**: ID of the defect code to retrieve
    
    ### Returns:
    - **DefectCode**: The requested defect code
    """
    defect_code = session.exec(select(DefectCode).where(DefectCode.defect_code_id == defect_code_id)).first()
    if not defect_code:
        raise HTTPException(status_code=404, detail="Defect code not found")
    
    return defect_code


@router.put("/{defect_code_id}", response_model=DefectCode,
            summary="Update defect code",
            response_description="Returns the updated defect code",
            responses={
                404: {"description": "Defect code not found"}
            }
)
def update_defect_code(
    defect_code_id: int,
    defect_code_update: DefectCodeUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Update defect code
    
    Updates an existing defect code with new information.
    
    ### Parameters:
    - **defect_code_id**: ID of the defect code to update
    - **defect_code_update** (DefectCodeUpdate): Updated defect code data
    
    ### Returns:
    - **DefectCode**: The updated defect code
    """
    defect_code = session.exec(select(DefectCode).where(DefectCode.defect_code_id == defect_code_id)).first()
    if not defect_code:
        raise HTTPException(status_code=404, detail="Defect code not found")
    
    # Actualizar los valores
    defect_code_data = defect_code_update.model_dump(exclude_unset=True)
    for key, value in defect_code_data.items():
        setattr(defect_code, key, value)
    
    session.add(defect_code)
    session.commit()
    session.refresh(defect_code)
    
    return defect_code


@router.delete("/{defect_code_id}", status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete defect code",
            response_description="No content, defect code successfully deleted",
            responses={
                404: {"description": "Defect code not found"},
                400: {"description": "Cannot delete defect code that is in use"}
            }
)
def delete_defect_code(
    defect_code_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Delete defect code
    
    Removes a defect code from the system if it is not in use.
    
    ### Parameters:
    - **defect_code_id**: ID of the defect code to delete
    
    ### Returns:
    - No content (204)
    """
    defect_code = session.exec(select(DefectCode).where(DefectCode.defect_code_id == defect_code_id)).first()
    if not defect_code:
        raise HTTPException(status_code=404, detail="Defect code not found")
    
    # Verificar si el código está en uso (hay punch lists que lo usan)
    punch_lists_with_code = session.exec(
        select(PunchList).where(PunchList.defect_code_id == defect_code_id)
    ).first()
    
    if punch_lists_with_code:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete defect code that is in use by existing punch list items"
        )
    
    session.delete(defect_code)
    session.commit()
    
    return None