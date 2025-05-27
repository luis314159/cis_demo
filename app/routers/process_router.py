from sqlite3 import IntegrityError
from fastapi import APIRouter, status
from sqlmodel import select
from models import Process, ProcessResponse, ProcessCreate, ProcessUpdate,ProcessOrder
from db import SessionDep
from fastapi import HTTPException
from logs_setup import setup_api_logger

router = APIRouter(
    prefix="/processes",
    tags=["Process"]
)

logger = setup_api_logger("process")

@router.get('', response_model=list[Process],
            summary="List all processes",
            response_description="Returns a list of all available processes",
            status_code= status.HTTP_200_OK
    )
def list_processes(session: SessionDep):
    """
    ## Get all processes

    Retrieves a complete list of all manufacturing processes registered in the system.

    ### Returns:
    - **List[Process]**: List of process objects containing:
        - process_id: Unique identifier
        - process_name: Name of the process
        - description: Process description

    ### Example Response:
    ```json
    [
        {
            "process_id": 1,
            "process_name": "Metal Fabrication",
            "description": "Standard metal fabrication process"
        },
        {
            "process_id": 2,
            "process_name": "Plastic Molding",
            "description": "Injection molding process"
        }
    ]
    ```
    """
    processes = session.exec(select(Process)).all()
    return processes

from models import ProcessStage, Process, Stage

@router.post('/{process_name}/order-stages',
            response_description="Confirmation of stage order update",
            responses={
                status.HTTP_200_OK: {"description": "Stage order updated successfully"},
                status.HTTP_404_NOT_FOUND: {"description": "Process not found"},
                status.HTTP_400_BAD_REQUEST: {"description": "Invalid stage names provided"}
            }
    )
def order_stages(process_name: str, stage_order: list[str], session: SessionDep):
    """
    ## Define stage execution order for a process

    Sets or updates the execution order of stages for a specific manufacturing process.

    ### Parameters:
    - **process_name** (str): Name of the target process
    - **stage_order** (List[str]): Ordered list of stage names

    ### Request Example:
    ```json
    {
        "stage_order": ["Cutting", "Bending", "Welding", "Painting"]
    }
    ```

    ### Responses:
    - **Success**:
    ```json
    {
        "message": "El orden de los Stages para el Process 'Metal Fabrication' fue actualizado correctamente."
    }
    ```
    
    - **Error** (Process not found):
    ```json
    {
        "detail": "El Process no existe."
    }
    ```

    - **Error** (Invalid stages):
    ```json
    {
        "detail": "Uno o más Stages no existen: Painting"
    }
    ```

    ### Workflow:
    1. Validate process existence
    2. Verify all stage names exist
    3. Delete previous stage order (if exists)
    4. Create new stage order relationships
    5. Commit changes to database
    """
    # Verificar que el Process exista
    process = session.exec(select(Process).where(Process.process_name == process_name)).first()
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El Process no existe.")

    # Verificar que todos los nombres de Stage existan
    stages = session.exec(select(Stage).where(Stage.stage_name.in_(stage_order))).all()
    stage_map = {stage.stage_name: stage for stage in stages}
    if len(stages) != len(stage_order):
        missing_stages = set(stage_order) - set(stage_map.keys())
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Uno o más Stages no existen: {', '.join(missing_stages)}")

    # Verificar si ya existía un orden previo
    existing_order = session.exec(select(ProcessStage).where(ProcessStage.process_id == process.process_id)).all()
    if existing_order:
        # Eliminar el orden previo
        session.exec(select(ProcessStage).where(ProcessStage.process_id == process.process_id)).delete()
        session.commit()

    # Crear el nuevo orden
    for order, stage_name in enumerate(stage_order, start=1):
        stage_id = stage_map[stage_name].stage_id
        process_stage = ProcessStage(process_id=process.process_id, stage_id=stage_id, order=order)
        session.add(process_stage)

    session.commit()
    return {"message": f"El orden de los Stages para el Process '{process_name}' fue actualizado correctamente."}

@router.get("/{process_name}/stages-order", response_model=list[dict],
            summary="Get stage execution order for a process",
            response_description="Ordered list of stages with details",
            tags=["Process"],
            responses={
                status.HTTP_200_OK: {
                    "description": "Successfully retrieved stage order",
                    "content": {
                        "application/json": {
                            "example": [
                                {
                                    "order": 1,
                                    "stage_id": 3,
                                    "stage_name": "Cutting"
                                },
                                {
                                    "order": 2,
                                    "stage_id": 5,
                                    "stage_name": "Bending"
                                }
                            ]
                        }
                    }
                },
                status.HTTP_404_NOT_FOUND: {
                    "description": "Process not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "El Process no existe."}
                        }
                    }
                }
            }
    )
def get_stages_order(process_name: str, session: SessionDep):
    """
    ## Retrieve stage execution order for a process

    Returns the defined execution sequence of stages for a specific manufacturing process.

    ### Parameters:
    - **process_name** (str): Name of the target process

    ### Returns:
    - **List[StageOrderResponse]**: Ordered list containing:
        - order: Execution sequence number
        - stage_id: Unique identifier of the stage
        - stage_name: Name of the stage

    ### Example Usage:
    ```http
    GET /processes/metal-fabrication/stages-order
    ```

    ### Example Response:
    ```json
    [
        {
            "order": 1,
            "stage_id": 3,
            "stage_name": "Cutting"
        },
        {
            "order": 2,
            "stage_id": 5,
            "stage_name": "Bending"
        },
        {
            "order": 3,
            "stage_id": 7,
            "stage_name": "Welding"
        }
    ]
    ```

    ### Empty State Response:
    ```json
    {
        "message": "No hay stages asignados para el Process 'metal-fabrication'."
    }
    ```

    ### Workflow:
    1. Validate process existence
    2. Retrieve stage order relationships
    3. Enrich with stage details
    4. Return ordered list
    """
    # Verificar que el Process exista
    process = session.exec(select(Process).where(Process.process_name == process_name)).first()
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El Process no existe.")

    # Obtener el orden de los stages asociados al Process
    process_stages = session.exec(
        select(ProcessStage)
        .where(ProcessStage.process_id == process.process_id)
        .order_by(ProcessStage.order)
    ).all()

    if not process_stages:
        return {"message": f"No hay stages asignados para el Process '{process_name}'."}

    # Obtener detalles de los Stages en el orden especificado
    stages_order = [
        {
            "order": ps.order,
            "stage_id": ps.stage_id,
            "stage_name": session.exec(select(Stage).where(Stage.stage_id == ps.stage_id)).first().stage_name
        }
        for ps in process_stages
    ]

    return stages_order

@router.post(
    "/create_process", 
    response_model=ProcessResponse,
    summary="Create a new process",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Process created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "process_id": 1,
                        "process_name": "Example Process",
                        "process_stages": []
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Process already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "El proceso ya está registrado."
                    }
                }
            }
        }
    }
)
def create_process(
    process_data: ProcessCreate, 
    session: SessionDep
):
    """
    ## Create a new process
    Creates a new process with a unique name. Processes are initially created without stages.
    """
    existing_process = session.exec(select(Process).where(Process.process_name == process_data.process_name)).first()
    if existing_process:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El proceso ya está registrado.")
    
    process = Process.model_validate(process_data)

    session.add(process)
    session.commit()
    session.refresh(process)
    
    return process

@router.get(
    "/{process_id}",
    response_model=ProcessResponse,
    summary="Retrieve a process by ID",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Process details",
            "content": {
                "application/json": {
                    "example": {
                        "process_id": 1,
                        "process_name": "manufacturing_flow",
                        "process_stages": []
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Process not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Proceso no encontrado"}
                }
            }
        }
    }
)
def get_process_by_id(process_id: int, session: SessionDep):
    """
    ## Get a single process
    
    Retrieves detailed information about a specific process by its ID.
    
    ### Parameters:
    - **process_id** (int): ID of the process to retrieve
    
    ### Raises:
    - status.HTTP_404_NOT_FOUND: If process doesn't exist
    """
    process = session.get(Process, process_id)
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proceso no encontrado")
    return process

@router.put("/{process_id}", response_model=ProcessResponse)
def update_process(
    process_id: int,
    process_data: ProcessUpdate,
    session: SessionDep
):
    """Update a process name while maintaining its unique constraint."""
    process = session.get(Process, process_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Proceso no encontrado"
        )
    
    if process_data.process_name and process_data.process_name != process.process_name:
        process.process_name = process_data.process_name

    
    if process_data.process_order_id and process_data.process_order_id != process.process_order_id:
        process_id = process_data.process_order_id
        existing_order = session.get(ProcessOrder, process_id)
        logger.info(existing_order)
        if not existing_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process order ID {process_id} does not exist"
            )
        process.process_order_id = process_data.process_order_id
    
    try:
        session.commit()
        session.refresh(process)
        return process
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre del proceso ya está registrado"
        )

@router.delete(
    "/{process_id}",
    summary="Delete a process",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Process deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Process not found"}
    }
)
def delete_process(process_id: int, session: SessionDep):
    """
    ## Delete a process
    
    Permanently removes a process from the system.
    
    ### Parameters:
    - **process_id** (int): ID of the process to delete
    
    ### Raises:
    - status.HTTP_404_NOT_FOUND: If process doesn't exist
    """
    process = session.get(Process, process_id)
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proceso no encontrado")
    
    session.delete(process)
    session.commit()
    return None