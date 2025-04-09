from typing import Annotated, Optional
from fastapi import APIRouter, status, HTTPException, Path
from sqlmodel import Session, select
from db import SessionDep

from models import CorrectionProcess, CorrectionProcessBase, CorrectionProcessCreate, CorrectionProcessResponse, CorrectionProcessUpdate

router = APIRouter(prefix="/correction-processes", tags=["Correction Processes"])


@router.post(
    "/",
    response_model=CorrectionProcessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new correction process",
    response_description="Created correction process details"
)
def create_correction_process(
    session: SessionDep, 
    process: CorrectionProcessCreate
):
    """
    ## Create a new correction process
    
    Creates a new entry in the correction process registry with the provided description.
    
    ### Parameters:
    - **process**: CorrectionProcessCreate object with required description
    
    ### Returns:
    - **CorrectionProcessResponse**: Created correction process with generated ID
    """
    db_process = CorrectionProcess.model_validate(process)
    session.add(db_process)
    session.commit()
    session.refresh(db_process)
    return db_process

@router.get(
    "/",
    response_model=list[CorrectionProcessResponse],
    summary="List all correction processes",
    response_description="List of all correction processes"
)
def list_correction_processes(session: SessionDep):
    """
    ## Get all correction processes
    
    Retrieves a complete list of all registered correction processes.
    """
    processes = session.exec(select(CorrectionProcess)).all()
    return processes

@router.get(
    "/{correction_process_id}",
    response_model=CorrectionProcessResponse,
    summary="Get correction process by ID",
    responses={404: {"description": "Correction process not found"}}
)
def get_correction_process(
    session: SessionDep,
    correction_process_id: Annotated[int, Path(title="ID of the correction process", gt=0)]
):
    """
    ## Get specific correction process
    
    Retrieves detailed information for a specific correction process by its ID.
    """
    process = session.get(CorrectionProcess, correction_process_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction process not found"
        )
    return process

@router.put(
    "/{correction_process_id}",
    response_model=CorrectionProcessResponse,
    summary="Update correction process",
    responses={
        404: {"description": "Correction process not found"},
        400: {"description": "Invalid input data"}
    }
)
def update_correction_process(
    session: SessionDep,
    correction_process_id: Annotated[int, Path(title="ID of the correction process", gt=0)],
    process_data: CorrectionProcessUpdate
):
    """
    ## Update existing correction process
    
    Updates the description of an existing correction process.
    """
    db_process = session.get(CorrectionProcess, correction_process_id)
    if not db_process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction process not found"
        )
        
    process_data_dict = process_data.dict(exclude_unset=True)
    for key, value in process_data_dict.items():
        setattr(db_process, key, value)
        
    session.add(db_process)
    session.commit()
    session.refresh(db_process)
    return db_process

@router.delete(
    "/{correction_process_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete correction process",
    responses={404: {"description": "Correction process not found"}}
)
def delete_correction_process(
    session: SessionDep,
    correction_process_id: Annotated[int, Path(title="ID of the correction process", gt=0)]
):
    """
    ## Delete correction process
    
    Permanently removes a correction process from the system by its ID.
    """
    process = session.get(CorrectionProcess, correction_process_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction process not found"
        )
    session.delete(process)
    session.commit()