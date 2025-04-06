from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from db import SessionDep
from models import Stage, StageCreate

# Crear el router
router = APIRouter(
    prefix="/stages",
    tags=["Stages"]
)

@router.post("/create", response_model=Stage,
            summary="Create a new stage",
            response_description="Returns the newly created stage",
            tags=["Stages"],  # Agrupa en la sección "Stages"
            responses={
                200: {"description": "Stage created successfully"},
                400: {"description": "A stage with this name already exists"},
            },
    )
def create_stage(stage: StageCreate, session: SessionDep):
    """
    ## Endpoint to create a new stage

    This endpoint creates a new stage in the system. It validates the input data and ensures that
    no duplicate stage names exist.

    ### Arguments:
    - **stage** (StageCreate): The data required to create a new stage.

    ### Returns:
    - **Stage**: The newly created stage object.

    ### Raises:
    - `HTTPException`:
        - `400`: If a stage with the same name already exists.

    ### Example Usage:
    ```http
    POST /stages/create
    Body:
    {
        "name": "Stage 1",
        "description": "Initial stage of the process"
    }

    Response:
    {
        "stage_id": 1,
        "name": "Stage 1",
        "description": "Initial stage of the process"
    }
    ```

    ### Workflow:
    1. Validate the input data using the `StageCreate` model.
    2. Check if a stage with the same name already exists.
    3. If the name is unique, create and save the new stage in the database.
    4. Return the newly created stage.
    """
    # Crear una nueva instancia del modelo Stage
    new_stage = Stage.model_validate(stage)

    try:
        # Agregar el nuevo stage a la base de datos
        session.add(new_stage)
        session.commit()
        session.refresh(new_stage)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST , detail="A stage with this name already exists."
        )

    return new_stage
