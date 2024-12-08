from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from db import SessionDep
from models import Stage, StageCreate

# Crear el router
router = APIRouter(
    prefix="/stages",
    tags=["Stages"]
)

@router.post("/create", response_model=Stage)
def create_stage(stage: StageCreate, session: SessionDep):
    """
    Endpoint para crear un nuevo stage.
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
            status_code=400, detail="A stage with this name already exists."
        )

    return new_stage
