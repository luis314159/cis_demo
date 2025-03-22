from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import Job, Item, JobStatus, ProcessStage, StageStatus, ItemStageStatus, Object, Stage, Process
from sqlmodel import SQLModel

# Crear un modelo de respuesta para listar Jobs
class JobList(SQLModel):
    job_code: str

# Crear el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.get("/{job_code}/status", response_model=JobStatus,
        summary="Get the status of objects in a job",
        response_description="Returns the status of objects in the specified job",
        tags=["Jobs"],  # Agrupa en la sección "Jobs"
        responses={
            200: {"description": "Successfully returned the job status"},
            404: {"description": "Job or related items not found"},
        },
    )
def get_job_status(job_code: str, session: SessionDep):
    """
    ## Endpoint to retrieve the status of objects in a job

    This endpoint retrieves the status of objects in the job identified by `job_code`.
    It provides a detailed breakdown of the progress of each item in the job across different stages.

    ### Arguments:
    - **job_code** (str): The code of the job to retrieve the status for.

    ### Returns:
    - **JobStatus**: The status of the job, including progress by stage and item.

    ### Raises:
    - `HTTPException`:
        - `404`: If the job or related items do not exist.

    ### Example Usage:
    ```http
    GET /jobs/JOB123/status

    Response:
    {
        "job_code": "JOB123",
        "stages": [
            {
                "stage_name": "CUTTING",
                "items": [
                    {
                        "item_name": "Item 1",
                        "item_ocr": "123456",
                        "ratio": "5/10",
                        "status": false
                    },
                    {
                        "item_name": "Item 2",
                        "item_ocr": "789012",
                        "ratio": "10/10",
                        "status": true
                    }
                ]
            },
            {
                "stage_name": "MACHINING",
                "items": [
                    {
                        "item_name": "Item 1",
                        "item_ocr": "123456",
                        "ratio": "3/10",
                        "status": false
                    },
                    {
                        "item_name": "Item 2",
                        "item_ocr": "789012",
                        "ratio": "0/10",
                        "status": false
                    }
                ]
            }
        ]
    }
    ```

    ### Workflow:
    1. Verify that the job exists.
    2. Retrieve all items related to the job.
    3. For each item, analyze the progress across its stages.
    4. Calculate the completion ratio and status for each item in each stage.
    5. Return the job status with detailed progress information.
    """
    # Verificar que el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    job_id = session.exec(select(Job.job_id).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail="El Job no existe.")

    # Obtener todos los Items relacionados al Job
    items = session.exec(select(Item).where(Item.job_id == job_id)).all()
    if not items:
        raise HTTPException(status_code=404, detail="No se encontraron Items relacionados al Job.")

    # Diccionario para almacenar el progreso por estación
    progress_data = {}
    stages = session.exec(select(Stage)).all()

    for item in items:
        # Obtener los objetos relacionados al Item
        objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()

        # Obtener los stages del proceso del Item, en orden
        # process_stages = session.exec(
        #     select(ProcessStage, Stage)
        #     .join(Stage, Stage.stage_id == ProcessStage.stage_id)
        #     .where(ProcessStage.process_id == item.process_id)
        #     .order_by(ProcessStage.order)
        # ).all()

        process_stages = item.stage_names # ["CUTTING","MACHINING"]
        process_ids = item.stage_ids
        #print(process_stages)

        # Analizar cada estación
        for stage_name, stage in zip(process_stages, process_ids):
            


            if stage_name not in progress_data:
                progress_data[stage_name] = {}

            # Inicializar datos para el item en esta etapa
            if item.item_name not in progress_data[stage_name]:
                progress_data[stage_name][item.item_name] = {"completed": 0, "pending": 0, "ocr": item.ocr, "ratio": "", "status": False}
            

            # Analizar cada objeto y determinar su estado en la etapa
            for obj in objects:
                try:
                    if obj.current_stage == 1:
                        progress_data[stage_name][item.item_name]["pending"] += 1

                    elif process_ids.index(obj.current_stage) >=  process_ids.index(stage):
                        progress_data[stage_name][item.item_name]["completed"] += 1
                    else:
                        progress_data[stage_name][item.item_name]["pending"] += 1
                except:
                    pass
                    # print(f"process_stages: {process_stages}")
                    # print(f"process_ids: {process_ids}")
                    # print(f"current_stage: {obj.current_stage}")
                    # print(f"stage: {stage}")

                    # process_stages: ['CUTTING']
                    # process_ids: [2]
                    # current_stage: 2
                    # stage: 2
            
            completed = progress_data[stage_name][item.item_name]["completed"]
            pending = progress_data[stage_name][item.item_name]["pending"]
            total =completed + pending
            progress_data[stage_name][item.item_name]["ratio"] = f'{completed}/{total}'

            
            if int(pending) == 0:
                progress_data[stage_name][item.item_name]["status"] = True

    # Construir la respuesta
    stages = []
    for stage_name, items_data in progress_data.items():
        stages.append(
            StageStatus(
                stage_name=stage_name,
                items=[
                    ItemStageStatus(
                        item_name=item_name,
                        item_ocr=data["ocr"],
                        ratio=data["ratio"],
                        status=data["status"]
                    )
                    for item_name, data in items_data.items()
                ]
            )
        )

    return JobStatus(
        job_code=job.job_code,
        stages=stages
    )

@router.delete("/{job_code}",
        summary="Delete a job and its related items and objects",
        response_description="Confirmation message after deleting the job and its related data",
        tags=["Jobs"],  # Agrupa en la sección "Jobs"
        responses={
            200: {"description": "Job and related data deleted successfully"},
            404: {"description": "Job not found"},
        },
    )
async def delete_job(job_code: str, session: SessionDep):
    """
    ## Endpoint to delete a job and its related items and objects

    This endpoint deletes the job identified by `job_code` and all items and objects related to it.

    ### Arguments:
    - **job_code** (str): The code of the job to delete.

    ### Returns:
    - **dict**: A confirmation message.

    ### Raises:
    - `HTTPException`:
        - `404`: If the job does not exist.

    ### Example Usage:
    ```http
    DELETE /jobs/JOB123

    Response:
    {
        "message": "El Job 'JOB123' y todos los datos relacionados fueron eliminados exitosamente."
    }
    ```

    ### Workflow:
    1. Verify that the job exists.
    2. Retrieve all items related to the job.
    3. Delete all objects related to each item.
    4. Delete all items related to the job.
    5. Delete the job.
    6. Commit the changes to the database.
    """
    # Verificar si el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail="El Job no existe.")

    # Obtener los Items relacionados al Job
    items = session.exec(select(Item).where(Item.job_id == job.job_id)).all()

    # Eliminar los Objects relacionados a los Items
    for item in items:
        objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
        for obj in objects:
            session.delete(obj)

    # Eliminar los Items relacionados al Job
    for item in items:
        session.delete(item)

    # Eliminar el Job
    session.delete(job)

    # Confirmar los cambios
    session.commit()

    return {"message": f"El Job '{job_code}' y todos los datos relacionados fueron eliminados exitosamente."}