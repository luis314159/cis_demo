from fastapi import APIRouter, HTTPException, status
from sqlmodel import Field, select
from db import SessionDep
from models import (
    DefectRecord, Job, Item, JobComplete, JobStatus, JobStatusResponse, JobStatusUpdate, 
    ProcessStage, StageStatus, ItemStageStatus, Object, Stage, Process, Product,
    BatchJobStatusUpdate, BatchJobStatusResponse, JobWithProduct
)
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
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

# ========================================
# ENDPOINTS ESPECÍFICOS (PRIMERO)
# ========================================

@router.get("/list", response_model=list[JobWithProduct],
           summary="Get list of all jobs",
           response_description="Returns list of all jobs with basic information",
           responses={
               200: {"description": "Jobs retrieved successfully"},
               500: {"description": "Internal server error"}
           }
)
def list_jobs(session: SessionDep):
    """
    ## Get list of all jobs
    
    Returns a list of all jobs in the system with basic information including:
    - Job code and ID
    - Current status
    - Creation date
    - Associated product information
    
    ### Returns:
    - **List[JobWithProduct]**: List of jobs with product information
    
    ### Example Response:
    ```json
    [
        {
            "job_id": 1,
            "job_code": "JOB001",
            "status": true,
            "created_at": "2023-08-20T15:30:00Z",
            "product_name": "Steel Plate",
            "product_id": 1
        }
    ]
    ```
    """
    logger.info("Retrieving list of all jobs")
    
    try:
        # Query para obtener jobs con información del producto
        query = select(
            Job.job_id,
            Job.job_code,
            Job.status,
            Job.created_at,
            Job.product_id,
            Product.product_name
        ).outerjoin(Product, Job.product_id == Product.product_id)\
         .order_by(Job.created_at.desc())
        
        results = session.exec(query).all()
        
        # Convertir resultados a lista de JobWithProduct
        jobs = []
        for result in results:
            job_data = JobWithProduct(
                job_id=result.job_id,
                job_code=result.job_code,
                status=result.status,
                created_at=result.created_at,
                product_id=result.product_id,
                product_name=result.product_name
            )
            jobs.append(job_data)
        
        logger.info(f"Retrieved {len(jobs)} jobs successfully")
        return jobs
        
    except Exception as e:
        error_message = f"Error retrieving jobs list: {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

@router.get("/list-simple", response_model=list[JobList],
           summary="Get simple list of job codes",
           tags=["Jobs"]
)
def list_jobs_simple(session: SessionDep):
    """
    ## Get simple list of job codes
    
    Returns only job codes - useful for dropdowns or simple listings.
    """
    try:
        jobs = session.exec(select(Job.job_code).order_by(Job.created_at.desc())).all()
        return [JobList(job_code=job_code) for job_code in jobs]
    except Exception as e:
        logger.error(f"Error retrieving simple jobs list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving jobs list: {str(e)}"
        )

@router.patch("/batch/status", response_model=BatchJobStatusResponse,
        summary="Update the status of multiple jobs at once",
        response_description="Returns the result of batch status update",
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

# ========================================
# ENDPOINTS CON PARÁMETROS DINÁMICOS (AL FINAL)
# ========================================

@router.get("/{job_code}/status", response_model=JobStatus,
        summary="Get the status of objects in a job",
        response_description="Returns the status of objects in the specified job",
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

@router.get("/{job_code}/status-only", response_model=dict,
        summary="Get only the current status of a job",
        response_description="Returns only the current status boolean value",
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

@router.patch("/{job_code}/status", response_model=JobStatusResponse,
        summary="Update the status of a job",
        response_description="Returns the updated job status",
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

@router.delete("/{job_code}",
        summary="Delete a job and its related items and objects",
        response_description="Confirmation message after deleting the job and its related data",
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
    5. Delete all defect records related to the job.
    6. Delete the job.
    7. Commit the changes to the database.
    """
    logger.info(f"Starting deletion process for job_code: {job_code}")
    
    # Verificar si el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        logger.warning(f"Job not found for deletion: {job_code}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El Job no existe.")

    logger.info(f"Job found for deletion - job_id: {job.job_id}")

    try:
        # Obtener los Items relacionados al Job
        items = session.exec(select(Item).where(Item.job_id == job.job_id)).all()
        logger.info(f"Found {len(items)} items to delete")

        # Eliminar los Objects relacionados a los Items
        for item in items:
            objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
            logger.debug(f"Deleting {len(objects)} objects for item {item.item_id}")
            for obj in objects:
                session.delete(obj)

        # Eliminar los Items relacionados al Job
        for item in items:
            logger.debug(f"Deleting item {item.item_id}")
            session.delete(item)

        # Eliminar DefectRecords relacionados al Job
        defects = session.exec(select(DefectRecord).where(DefectRecord.job_id == job.job_id)).all()
        logger.info(f"Found {len(defects)} defect records to delete")
        for defect in defects:
            logger.debug(f"Deleting defect record {defect.defect_record_id}")
            session.delete(defect)

        # Eliminar el Job
        logger.info(f"Deleting job {job.job_id}")
        session.delete(job)

        # Confirmar los cambios
        session.commit()
        logger.info(f"Successfully deleted job {job_code} and all related data")

        return {"message": f"El Job '{job_code}' y todos los datos relacionados fueron eliminados exitosamente."}
        
    except Exception as e:
        # Rollback en caso de error
        session.rollback()
        error_message = f"Error deleting job {job_code}: {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )
    
@router.get("/list-complete-product", response_model=list[JobComplete],
           summary="Get complete list of all jobs with all fields",
           response_description="Returns complete list of all jobs with all information",
           responses={
               200: {"description": "Jobs retrieved successfully"},
               500: {"description": "Internal server error"}
           }
)
def list_jobs_complete(session: SessionDep):
    """
    ## Get complete list of all jobs with all fields
    
    Returns a complete list of all jobs in the system with ALL information
    """
    logger.info("Retrieving complete list of all jobs")
    
    try:
        # ✅ Obtener todos los jobs con todas sus propiedades
        jobs = session.exec(
            select(Job).order_by(Job.created_at.desc())
        ).all()
        
        logger.info(f"Found {len(jobs)} jobs in database")
        
        # ✅ Construir lista completa manualmente
        complete_jobs = []
        
        for job in jobs:
            logger.debug(f"Processing job: {job.job_code}")
            
            # ✅ Obtener producto relacionado
            product_name = None
            if job.product_id:
                try:
                    product = session.get(Product, job.product_id)
                    if product:
                        product_name = product.product_name
                        logger.debug(f"Product found for job {job.job_code}: {product_name}")
                    else:
                        logger.warning(f"Product ID {job.product_id} not found for job {job.job_code}")
                except Exception as e:
                    logger.error(f"Error getting product for job {job.job_code}: {e}")
            
            # ✅ Crear objeto JobComplete con TODOS los campos
            job_data = JobComplete(
                job_id=job.job_id,
                job_code=job.job_code,
                status=job.status,
                created_at=job.created_at,
                product_id=job.product_id,
                product_name=product_name,
                process_order_id=job.process_order_id
            )
            
            complete_jobs.append(job_data)
            
            # ✅ Log detallado para debug
            logger.debug(f"Job {job.job_code} processed: status={job.status}, product={product_name}, created={job.created_at}")
        
        logger.info(f"Successfully processed {len(complete_jobs)} complete jobs")
        
        # ✅ Log de muestra
        if complete_jobs:
            sample = complete_jobs[0]
            logger.info(f"Sample job data: {sample.model_dump()}")
        
        return complete_jobs
        
    except Exception as e:
        error_message = f"Error retrieving complete jobs list: {str(e)}"
        logger.error(error_message)
        logger.error(f"Exception type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

# ✅ ENDPOINT DE DEBUG MEJORADO
@router.get("/debug-data", 
           summary="Debug endpoint to check job data",
           include_in_schema=False
)
def debug_job_data(session: SessionDep):
    """
    Endpoint temporal para debuggear los datos de jobs
    """
    try:
        # ✅ Verificar jobs
        jobs = session.exec(select(Job)).all()
        
        # ✅ Verificar productos
        products = session.exec(select(Product)).all()
        
        debug_data = {
            "database_info": {
                "total_jobs": len(jobs),
                "total_products": len(products)
            },
            "jobs_sample": [],
            "products_sample": []
        }
        
        # ✅ Muestra de jobs
        for job in jobs[:3]:
            job_info = {
                "job_id": job.job_id,
                "job_code": job.job_code,
                "status": job.status,
                "created_at": str(job.created_at) if job.created_at else None,
                "product_id": job.product_id,
                "process_order_id": getattr(job, 'process_order_id', None)
            }
            
            # ✅ Verificar producto relacionado
            if job.product_id:
                product = session.get(Product, job.product_id)
                job_info["product_exists"] = product is not None
                job_info["product_name"] = product.product_name if product else "NOT_FOUND"
            else:
                job_info["product_exists"] = False
                job_info["product_name"] = "NO_PRODUCT_ID"
            
            debug_data["jobs_sample"].append(job_info)
        
        # ✅ Muestra de productos
        for product in products[:3]:
            product_info = {
                "product_id": product.product_id,
                "product_name": product.product_name
            }
            debug_data["products_sample"].append(product_info)
        
        return debug_data
        
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
        }
