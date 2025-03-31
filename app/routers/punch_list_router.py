from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import select, Session
from models import PunchList, PunchListCreate, PunchListUpdate, PunchListResponse, Object, Job, DefectCode, User
from auth import get_current_active_user
from typing import List, Optional
import os
from datetime import datetime
import shutil
from uuid import uuid4
from db import SessionDep

router = APIRouter(
    prefix="/punch-list",
    tags=["Punch Lists"]
)

# Helper function para guardar imágenes
async def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    """Guarda un archivo subido y devuelve la ruta"""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Generar un nombre único para el archivo
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(folder, unique_filename)
    
    # Guardar el archivo
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


@router.post("", response_model=PunchListResponse, status_code=status.HTTP_201_CREATED,
            summary="Create new punch list item",
            response_description="Returns the created punch list item",
            responses={
                201: {"description": "Punch list item created successfully"},
                404: {"description": "Job, object or defect code not found"}
            }
)
async def create_punch_list(
    session: SessionDep,
    job_id: int = Form(...),
    object_id: int = Form(...),
    defect_code_id: int = Form(...),
    description: str = Form(...),
    inspected_by: str = Form(...),
    issue: str = Form(...),
    todolist: str = Form(...),
    by_when: str = Form(...),  # Format: YYYY-MM-DD
    picture_before_repair: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Create a new punch list item
    
    Creates a new item in the punch list system for tracking issues and repairs.
    
    ### Parameters:
    - **job_id**: ID of the related job
    - **object_id**: ID of the related object
    - **defect_code_id**: ID of the defect code
    - **description**: Description of the product (e.g., "Tank")
    - **inspected_by**: Inspector number
    - **issue**: Description of the issue
    - **todolist**: Tasks to be done (e.g., "rework")
    - **by_when**: Estimated completion date (YYYY-MM-DD)
    - **picture_before_repair**: Optional image of issue before repair
    
    ### Returns:
    - **PunchListResponse**: Created punch list item details
    """
    # Verificar si el job existe
    job = session.exec(select(Job).where(Job.job_id == job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verificar si el object existe
    obj = session.exec(select(Object).where(Object.object_id == object_id)).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Verificar si el defect code existe
    defect_code = session.exec(select(DefectCode).where(DefectCode.defect_code_id == defect_code_id)).first()
    if not defect_code:
        raise HTTPException(status_code=404, detail="Defect code not found")
    
    # Procesar la fecha
    try:
        by_when_date = datetime.strptime(by_when, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Guardar la imagen si se proporciona
    picture_path = None
    if picture_before_repair:
        picture_path = await save_upload_file(
            picture_before_repair, 
            "uploads/punch_list/before"
        )
    
    # Crear el punch list item
    punch_list = PunchList(
        job_id=job_id,
        object_id=object_id,
        defect_code_id=defect_code_id,
        description=description,
        inspected_by=inspected_by,
        issue=issue,
        todolist=todolist,
        by_when=by_when_date,
        picture_before_repair=picture_path,
        status="Open"
    )
    
    session.add(punch_list)
    session.commit()
    session.refresh(punch_list)
    
    return punch_list


@router.get("", response_model=List[PunchListResponse],
            summary="Get all punch list items",
            response_description="Returns a list of all punch list items"
)
def get_all_punch_lists(
    session: SessionDep,
    status: Optional[str] = None,
    job_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Get all punch list items
    
    Retrieves all punch list items, with optional filtering by status or job.
    
    ### Parameters:
    - **status**: Optional filter by status (Open, In Progress, Closed)
    - **job_id**: Optional filter by job ID
    
    ### Returns:
    - **List[PunchListResponse]**: List of punch list items
    """
    query = select(PunchList)
    
    # Aplicar filtros opcionales
    if status:
        query = query.where(PunchList.status == status)
    if job_id:
        query = query.where(PunchList.job_id == job_id)
    
    punch_lists = session.exec(query).all()
    return punch_lists


@router.get("/{punch_list_id}", response_model=PunchListResponse,
            summary="Get punch list item by ID",
            response_description="Returns the requested punch list item",
            responses={
                404: {"description": "Punch list item not found"}
            }
)
def get_punch_list(
    punch_list_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Get punch list item by ID
    
    Retrieves a specific punch list item by its ID.
    
    ### Parameters:
    - **punch_list_id**: ID of the punch list item to retrieve
    
    ### Returns:
    - **PunchListResponse**: The requested punch list item
    """
    punch_list = session.exec(select(PunchList).where(PunchList.punch_list_id == punch_list_id)).first()
    if not punch_list:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    
    return punch_list


@router.put("/{punch_list_id}", response_model=PunchListResponse,
            summary="Update punch list item",
            response_description="Returns the updated punch list item",
            responses={
                404: {"description": "Punch list item not found"}
            }
)
async def update_punch_list(
    session: SessionDep,
    punch_list_id: int,
    description: Optional[str] = Form(None),
    issue: Optional[str] = Form(None),
    todolist: Optional[str] = Form(None),
    by_when: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    date_close: Optional[str] = Form(None),
    picture_after_repair: Optional[UploadFile] = File(None),
    inspector_validation_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Update punch list item
    
    Updates an existing punch list item with new information.
    
    ### Parameters:
    - **punch_list_id**: ID of the punch list item to update
    - **description**: Optional new description
    - **issue**: Optional new issue description
    - **todolist**: Optional new tasks
    - **by_when**: Optional new estimated date (YYYY-MM-DD)
    - **status**: Optional new status (Open, In Progress, Closed)
    - **date_close**: Optional closing date (YYYY-MM-DD)
    - **picture_after_repair**: Optional image after repair
    - **inspector_validation_image**: Optional inspector selfie for validation
    
    ### Returns:
    - **PunchListResponse**: The updated punch list item
    """
    punch_list = session.exec(select(PunchList).where(PunchList.punch_list_id == punch_list_id)).first()
    if not punch_list:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    
    # Actualizar los campos proporcionados
    if description:
        punch_list.description = description
    if issue:
        punch_list.issue = issue
    if todolist:
        punch_list.todolist = todolist
    if by_when:
        try:
            punch_list.by_when = datetime.strptime(by_when, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid by_when date format. Use YYYY-MM-DD")
    if status:
        punch_list.status = status
    if date_close:
        try:
            punch_list.date_close = datetime.strptime(date_close, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_close format. Use YYYY-MM-DD")
    
    # Procesar las imágenes
    if picture_after_repair:
        picture_path = await save_upload_file(
            picture_after_repair, 
            "uploads/punch_list/after"
        )
        punch_list.picture_after_repair = picture_path
    
    if inspector_validation_image:
        image_path = await save_upload_file(
            inspector_validation_image, 
            "uploads/punch_list/validation"
        )
        punch_list.inspector_validation_image = image_path
    
    session.add(punch_list)
    session.commit()
    session.refresh(punch_list)
    
    return punch_list


@router.delete("/{punch_list_id}", status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete punch list item",
            response_description="No content, item successfully deleted",
            responses={
                404: {"description": "Punch list item not found"}
            }
)
def delete_punch_list(
    punch_list_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Delete punch list item
    
    Removes a punch list item from the system.
    
    ### Parameters:
    - **punch_list_id**: ID of the punch list item to delete
    
    ### Returns:
    - No content (204)
    """
    punch_list = session.exec(select(PunchList).where(PunchList.punch_list_id == punch_list_id)).first()
    if not punch_list:
        raise HTTPException(status_code=404, detail="Punch list item not found")
    
    session.delete(punch_list)
    session.commit()
    
    return None


@router.get("/job/{job_id}", response_model=List[PunchListResponse],
            summary="Get punch list items by job",
            response_description="Returns punch list items for a specific job"
)
def get_punch_lists_by_job(session: SessionDep,
    job_id: int,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    ## Get punch list items by job
    
    Retrieves all punch list items associated with a specific job.
    
    ### Parameters:
    - **job_id**: ID of the job
    - **status**: Optional filter by status (Open, In Progress, Closed)
    
    ### Returns:
    - **List[PunchListResponse]**: List of punch list items for the job
    """
    query = select(PunchList).where(PunchList.job_id == job_id)
    
    if status:
        query = query.where(PunchList.status == status)
    
    punch_lists = session.exec(query).all()
    return punch_lists