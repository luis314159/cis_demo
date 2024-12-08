from fastapi import HTTPException
from models import Stage, StageCreate
from db import SessionDep
from fastapi import APIRouter
from sqlmodel import select


router = APIRouter(
    prefix="/stages",
    tags=["Stages"]
)

@router.post('/new', response_model=Stage)
def add_stage(stage_data: StageCreate, session: SessionDep):
    existing_stage = session.exec(select(Stage).where(Stage.stage_name == stage_data.stage_name)).first()
    if existing_stage:
        raise HTTPException(status_code=400, detail="El Stage ya existe.")

    stage = Stage.model_validate(stage_data)
    session.add(stage)
    session.commit()
    session.refresh(stage)
    return stage




@router.get("/list", response_model=list[Stage])
def list_stages(session: SessionDep):
    """
    Endpoint para listar todos los Stages disponibles.
    """
    # Obtener todos los Stages disponibles
    stages = session.exec(select(Stage)).all()
    return stages
