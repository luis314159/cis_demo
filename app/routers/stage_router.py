from fastapi import HTTPException
from models import Stage, StageCreate
from db import SessionDep
from fastapi import APIRouter
from sqlmodel import select


router = APIRouter(
    prefix="/stages",
    tags=["Stages"]
)

@router.post('/new', response_model=Stage,
        summary="Create a new stage",
        response_description="Returns the newly created stage",
        tags=["Stages"],  # Agrupa en la sección "Stages"
        responses={
            200: {"description": "Stage created successfully"},
            400: {"description": "A stage with this name already exists"},
        },
    )
def add_stage(stage_data: StageCreate, session: SessionDep):
    """
    ## Endpoint to create a new stage

    This endpoint creates a new stage in the system. It validates the input data and ensures that
    no duplicate stage names exist.

    ### Arguments:
    - **stage_data** (StageCreate): The data required to create a new stage.

    ### Returns:
    - **Stage**: The newly created stage object.

    ### Raises:
    - `HTTPException`:
        - `400`: If a stage with the same name already exists.

    ### Example Usage:
    ```http
    POST /stages/new
    Body:
    {
        "stage_name": "Stage 1",
        "description": "Initial stage of the process"
    }

    Response:
    {
        "stage_id": 1,
        "stage_name": "Stage 1",
        "description": "Initial stage of the process"
    }
    ```

    ### Workflow:
    1. Validate the input data using the `StageCreate` model.
    2. Check if a stage with the same name already exists.
    3. If the name is unique, create and save the new stage in the database.
    4. Return the newly created stage.
    """
    existing_stage = session.exec(select(Stage).where(Stage.stage_name == stage_data.stage_name)).first()
    if existing_stage:
        raise HTTPException(status_code=400, detail="El Stage ya existe.")

    stage = Stage.model_validate(stage_data)
    session.add(stage)
    session.commit()
    session.refresh(stage)
    return stage




@router.get("/list", response_model=list[Stage],
        summary="List all stages",
        response_description="Returns a list of all stages",
        tags=["Stages"],  # Agrupa en la sección "Stages"
        responses={
            200: {"description": "Successfully returned the list of stages"},
        },
    )
def list_stages(session: SessionDep):
    """
    ## Endpoint to list all stages

    This endpoint retrieves a list of all stages available in the system.

    ### Returns:
    - **List[Stage]**: A list of all stages.

    ### Example Usage:
    ```http
    GET /stages/list

    Response:
    [
        {
            "stage_id": 1,
            "stage_name": "Stage 1",
            "description": "Initial stage of the process"
        },
        {
            "stage_id": 2,
            "stage_name": "Stage 2",
            "description": "Second stage of the process"
        },
        ...
    ]
    ```

    ### Workflow:
    1. Query the database to retrieve all stages.
    2. Return the list of stages.
    """
    # Obtener todos los Stages disponibles
    stages = session.exec(select(Stage)).all()
    return stages
