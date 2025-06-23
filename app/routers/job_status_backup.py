from fastapi import APIRouter, HTTPException, status
from sqlmodel import Field, select
from db import SessionDep
from models import DefectRecord, Job, Item, JobStatus, JobStatusResponse, JobStatusUpdate, ProcessStage, StageStatus, ItemStageStatus, Object, Stage, Process
from sqlmodel import SQLModel
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("job_status_debug.log")
    ]
)
logger = logging.getLogger("job_status_api")

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
    logger.info(f"Procesando solicitud para job_code: {job_code}")

    # Verificar que el Job existe
    logger.debug(f"Consultando job con job_code: {job_code}")
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    job_id = session.exec(select(Job.job_id).where(Job.job_code == job_code)).first()
    
    if not job:
        logger.warning(f"Job no encontrado para job_code: {job_code}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El Job no existe.")
    
    logger.info(f"Job encontrado - job_id: {job_id}, job_code: {job_code}")

    # Obtener todos los Items relacionados al Job
    logger.debug(f"Obteniendo items para job_id: {job_id}")
    items = session.exec(select(Item).where(Item.job_id == job_id)).all()
    
    if not items:
        logger.warning(f"No se encontraron items para job_id: {job_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron Items relacionados al Job.")
    
    logger.info(f"Se encontraron {len(items)} items para job_id: {job_id}")
    
    # Log de características de los items
    for i, item in enumerate(items):
        logger.debug(f"Item {i+1}: item_id={item.item_id}, item_name={item.item_name}, ocr={item.ocr}")
        logger.debug(f"Item {i+1} stage_names: {item.stage_names}, stage_ids: {item.stage_ids}")

    # Diccionario para almacenar el progreso por estación
    progress_data = {}
    logger.debug("Obteniendo todas las etapas")
    stages = session.exec(select(Stage)).all()
    logger.debug(f"Total de etapas en el sistema: {len(stages)}")

    for item in items:
        logger.info(f"Procesando item: {item.item_name} (item_id: {item.item_id})")
        
        # Obtener los objetos relacionados al Item
        logger.debug(f"Consultando objetos para item_id: {item.item_id}")
        objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
        logger.info(f"Se encontraron {len(objects)} objetos para item_id: {item.item_id}")
        
        # Log de objetos encontrados
        for i, obj in enumerate(objects):
            logger.debug(f"Objeto {i+1}: object_id={obj.object_id}, current_stage={obj.current_stage}")

        process_stages = item.stage_names  # ["CUTTING","MACHINING"]
        process_ids = item.stage_ids
        logger.debug(f"Etapas del proceso para item {item.item_name}: {process_stages}")
        logger.debug(f"IDs de las etapas: {process_ids}")

        # Analizar cada estación
        for stage_name, stage in zip(process_stages, process_ids):
            logger.info(f"Analizando etapa: {stage_name} (stage_id: {stage}) para item: {item.item_name}")

            if stage_name not in progress_data:
                logger.debug(f"Inicializando diccionario para la etapa: {stage_name}")
                progress_data[stage_name] = {}

            # Inicializar datos para el item en esta etapa
            if item.item_name not in progress_data[stage_name]:
                logger.debug(f"Inicializando datos para item {item.item_name} en etapa {stage_name}")
                progress_data[stage_name][item.item_name] = {"completed": 0, "pending": 0, "ocr": item.ocr, "ratio": "", "status": False}
            
            # Log de estado inicial
            logger.debug(f"Estado inicial para {item.item_name} en {stage_name}: {progress_data[stage_name][item.item_name]}")

            # Analizar cada objeto y determinar su estado en la etapa
            for obj in objects:
                try:
                    logger.debug(f"Analizando objeto: {obj.object_id}, current_stage: {obj.current_stage}, etapa destino: {stage}")
                    
                    if obj.current_stage == 1:
                        logger.debug(f"Objeto {obj.object_id} en etapa inicial (1), marcado como pendiente en {stage_name}")
                        progress_data[stage_name][item.item_name]["pending"] += 1

                    elif process_ids.index(obj.current_stage) >= process_ids.index(stage):
                        logger.debug(f"Objeto {obj.object_id} ya pasó por la etapa {stage_name}, marcado como completado")
                        progress_data[stage_name][item.item_name]["completed"] += 1
                    else:
                        logger.debug(f"Objeto {obj.object_id} aún no llegó a la etapa {stage_name}, marcado como pendiente")
                        progress_data[stage_name][item.item_name]["pending"] += 1
                except Exception as e:
                    logger.error(f"Error al procesar el objeto {obj.object_id} en etapa {stage_name}: {str(e)}")
                    logger.error(f"process_stages: {process_stages}")
                    logger.error(f"process_ids: {process_ids}")
                    logger.error(f"current_stage: {obj.current_stage}")
                    logger.error(f"stage: {stage}")
            
            # Cálculo de ratio
            completed = progress_data[stage_name][item.item_name]["completed"]
            pending = progress_data[stage_name][item.item_name]["pending"]
            total = completed + pending
            
            logger.debug(f"Etapa {stage_name}, Item {item.item_name}: completed={completed}, pending={pending}, total={total}")
            
            progress_data[stage_name][item.item_name]["ratio"] = f'{completed}/{total}'
            
            if int(pending) == 0:
                logger.debug(f"Todos los objetos completados para {item.item_name} en etapa {stage_name}")
                progress_data[stage_name][item.item_name]["status"] = True
            
            # Log de estado final
            logger.debug(f"Estado final para {item.item_name} en {stage_name}: {progress_data[stage_name][item.item_name]}")

    # Construir la respuesta
    logger.info("Construyendo respuesta final")
    stages = []
    for stage_name, items_data in progress_data.items():
        logger.debug(f"Añadiendo datos de etapa {stage_name} a la respuesta")
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

    response = JobStatus(
        job_code=job.job_code,
        stages=stages
    )
    
    logger.info(f"Retornando respuesta para job_code: {job_code} con {len(stages)} etapas")
    return response

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El Job no existe.")

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

    defects = session.exec(select(DefectRecord).where(DefectRecord.job_id == job.job_id)).all()
    for defect in defects:
        # También puedes borrar imágenes asociadas si es necesario
        session.delete(defect)
        session.delete(job)

    # Confirmar los cambios
    session.commit()

    return {"message": f"El Job '{job_code}' y todos los datos relacionados fueron eliminados exitosamente."}


@router.patch("/{job_code}/status", response_model=JobStatusResponse,
        summary="Update the status of a job",
        response_description="Returns the updated job status",
        tags=["Jobs"],
        responses={
            200: {"description": "Job status updated successfully"},
            404: {"description": "Job not found"},
            400: {"description": "Invalid status value"},
        },
    )
def update_job_status(job_code: str, status_update: JobStatusUpdate, session: SessionDep):
    """
    ## Endpoint to update the status of a job

    This endpoint updates the status of the job identified by `job_code`.
    The status can be changed from active to inactive or vice versa.

    ### Arguments:
    - **job_code** (str): The code of the job to update.
    - **status_update** (JobStatusUpdate): Object containing the new status value.

    ### Returns:
    - **JobStatusResponse**: The updated job information with confirmation message.

    ### Raises:
    - `HTTPException`:
        - `404`: If the job does not exist.
        - `400`: If the status value is invalid.

    ### Example Usage:
    ```http
    PATCH /jobs/JOB123/status
    Content-Type: application/json

    {
        "status": true
    }

    Response:
    {
        "job_code": "JOB123",
        "status": true,
        "message": "Job status updated successfully from False to True"
    }
    ```

    ### Status Values:
    - `true`: Job is active/completed
    - `false`: Job is inactive/pending

    ### Workflow:
    1. Verify that the job exists.
    2. Get the current status of the job.
    3. Update the job status to the new value.
    4. Save changes to the database.
    5. Return confirmation with old and new status information.
    """
    logger.info(f"Updating status for job_code: {job_code} to status: {status_update.status}")

    # Verificar que el Job existe
    logger.debug(f"Looking for job with job_code: {job_code}")
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    
    if not job:
        logger.warning(f"Job not found for job_code: {job_code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Job with code '{job_code}' not found"
        )
    
    logger.info(f"Job found - job_id: {job.job_id}, current status: {job.status}")

    # Guardar el status anterior para el mensaje de respuesta
    old_status = job.status
    
    # Verificar si el status realmente cambió
    if old_status == status_update.status:
        logger.info(f"Status is already {status_update.status}, no changes needed")
        return JobStatusResponse(
            job_code=job.job_code,
            status=job.status,
            message=f"Job status is already {status_update.status}, no changes made"
        )

    try:
        # Actualizar el status del job
        logger.debug(f"Updating job status from {old_status} to {status_update.status}")
        job.status = status_update.status
        
        # Guardar cambios en la base de datos
        session.add(job)
        session.commit()
        session.refresh(job)
        
        logger.info(f"Job status updated successfully - job_code: {job_code}, new status: {job.status}")
        
        # Crear mensaje descriptivo
        status_text = {
            True: "active/completed",
            False: "inactive/pending"
        }
        
        message = f"Job status updated successfully from {status_text[old_status]} ({old_status}) to {status_text[status_update.status]} ({status_update.status})"
        
        return JobStatusResponse(
            job_code=job.job_code,
            status=job.status,
            message=message
        )
        
    except Exception as e:
        # Rollback en caso de error
        session.rollback()
        error_message = f"Error updating job status: {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

# Endpoint adicional para obtener solo el status actual (opcional)
@router.get("/{job_code}/status-only", response_model=dict,
        summary="Get only the current status of a job",
        response_description="Returns only the current status boolean value",
        tags=["Jobs"],
        responses={
            200: {"description": "Job status retrieved successfully"},
            404: {"description": "Job not found"},
        },
    )
def get_job_status_only(job_code: str, session: SessionDep):
    """
    ## Endpoint to get only the current status of a job

    This endpoint returns only the boolean status value of the job, 
    useful for quick status checks without the full job status breakdown.

    ### Arguments:
    - **job_code** (str): The code of the job to check.

    ### Returns:
    - **dict**: Simple object with job_code and current status.

    ### Example Usage:
    ```http
    GET /jobs/JOB123/status-only

    Response:
    {
        "job_code": "JOB123",
        "status": true
    }
    ```
    """
    logger.info(f"Getting status for job_code: {job_code}")

    # Verificar que el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    
    if not job:
        logger.warning(f"Job not found for job_code: {job_code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Job with code '{job_code}' not found"
        )
    
    logger.info(f"Job found - returning status: {job.status}")
    
    return {
        "job_code": job.job_code,
        "status": job.status
    }

# Endpoint para cambiar múltiples jobs a la vez (opcional, útil para operaciones batch)
class BatchJobStatusUpdate(SQLModel):
    job_codes: list[str] = Field(description="List of job codes to update")
    status: bool = Field(description="New status to apply to all jobs")

class BatchJobStatusResponse(SQLModel):
    updated_jobs: list[str] = Field(description="List of successfully updated job codes")
    not_found_jobs: list[str] = Field(description="List of job codes that were not found")
    errors: list[str] = Field(description="List of errors encountered")
    message: str

@router.patch("/batch/status", response_model=BatchJobStatusResponse,
        summary="Update the status of multiple jobs at once",
        response_description="Returns the result of batch status update",
        tags=["Jobs"],
        responses={
            200: {"description": "Batch update completed (may include partial failures)"},
            400: {"description": "Invalid request data"},
        },
    )
def update_multiple_jobs_status(batch_update: BatchJobStatusUpdate, session: SessionDep):
    """
    ## Endpoint to update the status of multiple jobs at once

    This endpoint allows updating the status of multiple jobs in a single request.
    Useful for batch operations.

    ### Arguments:
    - **batch_update** (BatchJobStatusUpdate): Object containing list of job codes and new status.

    ### Returns:
    - **BatchJobStatusResponse**: Summary of the batch operation results.

    ### Example Usage:
    ```http
    PATCH /jobs/batch/status
    Content-Type: application/json

    {
        "job_codes": ["JOB123", "JOB456", "JOB789"],
        "status": true
    }

    Response:
    {
        "updated_jobs": ["JOB123", "JOB456"],
        "not_found_jobs": ["JOB789"],
        "errors": [],
        "message": "Batch update completed: 2 updated, 1 not found, 0 errors"
    }
    ```
    """
    logger.info(f"Starting batch status update for {len(batch_update.job_codes)} jobs to status: {batch_update.status}")

    updated_jobs = []
    not_found_jobs = []
    errors = []

    for job_code in batch_update.job_codes:
        try:
            logger.debug(f"Processing job_code: {job_code}")
            
            # Buscar el job
            job = session.exec(select(Job).where(Job.job_code == job_code)).first()
            
            if not job:
                logger.warning(f"Job not found: {job_code}")
                not_found_jobs.append(job_code)
                continue
            
            # Actualizar status si es diferente
            if job.status != batch_update.status:
                job.status = batch_update.status
                session.add(job)
                logger.debug(f"Updated status for job: {job_code}")
            
            updated_jobs.append(job_code)
            
        except Exception as e:
            error_msg = f"Error updating {job_code}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    try:
        # Commit all changes
        session.commit()
        logger.info(f"Batch update committed: {len(updated_jobs)} jobs updated")
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error committing batch update: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Crear mensaje de resumen
    message = f"Batch update completed: {len(updated_jobs)} updated, {len(not_found_jobs)} not found, {len(errors)} errors"
    
    return BatchJobStatusResponse(
        updated_jobs=updated_jobs,
        not_found_jobs=not_found_jobs,
        errors=errors,
        message=message
    )