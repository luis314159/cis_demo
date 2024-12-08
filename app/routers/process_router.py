from fastapi import APIRouter
from sqlmodel import select
from models import Process  
from db import SessionDep
from fastapi import HTTPException

router = APIRouter(
    prefix="/processes",
    tags=["Process"]
)


@router.get('', response_model=list[Process])
def list_processes(session: SessionDep):
    processes = session.exec(select(Process)).all()
    return processes

from models import ProcessStage, Process, Stage

@router.post('/{process_name}/order-stages')
def order_stages(process_name: str, stage_order: list[str], session: SessionDep):
    """
    Parámetros:
        - process_name: Nombre del proceso al que se le asignarán las etapas.
        - stage_order: Lista de nombres de las etapas en el orden deseado.
    """
    # Verificar que el Process exista
    process = session.exec(select(Process).where(Process.process_name == process_name)).first()
    if not process:
        raise HTTPException(status_code=404, detail="El Process no existe.")

    # Verificar que todos los nombres de Stage existan
    stages = session.exec(select(Stage).where(Stage.stage_name.in_(stage_order))).all()
    stage_map = {stage.stage_name: stage for stage in stages}
    if len(stages) != len(stage_order):
        missing_stages = set(stage_order) - set(stage_map.keys())
        raise HTTPException(status_code=400, detail=f"Uno o más Stages no existen: {', '.join(missing_stages)}")

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

@router.get("/{process_name}/stages-order", response_model=list[dict])
def get_stages_order(process_name: str, session: SessionDep):
    """
    Endpoint para listar el orden de los Stages para un Process dado.
    Parámetros:
        - process_name: Nombre del proceso.
    """
    # Verificar que el Process exista
    process = session.exec(select(Process).where(Process.process_name == process_name)).first()
    if not process:
        raise HTTPException(status_code=404, detail="El Process no existe.")

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