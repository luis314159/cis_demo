import os
import shutil
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlmodel import SQLModel, select, and_
import time
from datetime import datetime, timezone
from models import DefectImage, DefectImageCreate, DefectRecord, DefectRecordCreate, DefectRecordRead, DefectRecordUpdate, DefectRecordResponse, Job, Product, Process, Issue, User, Status, CorrectionProcess, CompleteDefectRecordResponse
from db import SessionDep
from sqlalchemy.orm import aliased
from pathlib import Path
import logging
import json

# Set up a logger
logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/defect-records", tags=["Defect Records"])

@router.post("/add_defect_record", response_model=DefectRecord)
def create_defect_record(defect_record: DefectRecordCreate, session: SessionDep, status_code = status.HTTP_201_CREATED):
    """
    ## Create a new defect record

    Registers a new defect report in the system with technical details and status information.

    ### Parameters:
    - **defect_record** (DefectRecordCreate): Defect creation data including:
        - product_id: Product id related to Defect Record
        - job_id: Job id related to Defect Record
        - process_id: Process id related to Defect Record
        - inspector_user_id: User id of person who inspected the piece related to Defect Record
        - issue_by_user_id: User id of person who made the mistake the piece related to Defect Record
        - issue_id: Issue id related to Defect Record
        - status_id: Status id related to Defect Record
        - date_opened: Defect record opened date

    ### Returns:
    - **DefectRecord**: Created defect record details

    ### Example Request:
    ```json
    {
        "product_id": 0,
        "job_id": 0,
        "process_id": 0,
        "inspector_user_id": 0,
        "issue_by_user_id": 0,
        "issue_id": 0,
        "correction_process_id": 0,
        "status_id": 0,
        "date_closed": "2025-04-06T22:41:59.075Z",
        "date_opened": "2025-04-06T22:41:59.075Z"
    }
    ```

    ### Example Response:
    ```json
    {
        "product_id": 0,
        "job_id": 0,
        "process_id": 0,
        "inspector_user_id": 0,
        "issue_by_user_id": 0,
        "issue_id": 0,
        "correction_process_id": 0,
        "status_id": 0,
        "date_closed": "2025-04-06T22:41:59.076Z",
        "date_opened": "2025-04-06T22:41:59.076Z",
        "defect_record_id": 0
    }
    ```
    """
    # Crea una instancia del modelo de base de datos
    db_defect_record = DefectRecord.model_validate(defect_record.model_dump())
    
    # Guarda en la base de datos
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.get("/", response_model=list[DefectRecordRead], status_code = status.HTTP_200_OK)
def get_all_defect_records(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
):
    # Obtiene todos los registros con paginación
    defect_records = session.exec(
        select(DefectRecord)
        .offset(skip)
        .limit(limit)
    ).all()
    return defect_records

@router.get("/{defect_record_id}", response_model=DefectRecordRead, status_code = status.HTTP_200_OK)
def get_defect_record(
    defect_record_id: int, 
    session: SessionDep
):
    # Busca por ID
    defect_record = session.get(DefectRecord, defect_record_id)
    if not defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    return defect_record

@router.get("/search/{job_code}/{product_name}", 
          response_model=list[DefectRecordResponse], 
          status_code=status.HTTP_200_OK)
def search_defect_records(
    job_code: str,
    product_name: str,
    session: SessionDep
):
    Inspector = aliased(User)
    Issuer = aliased(User)
    
    query = (
    select(
        DefectRecord.defect_record_id,
        Job.job_code.label("job_code"),
        Product.product_name.label("product"),
        Inspector.username.label("inspectBy"),
        Issuer.username.label("issueBy"),
        Issue.issue_description.label("issue"),
        CorrectionProcess.correction_process_description.label("todo"),
        Status.status_name.label("status"),
        Process.process_name.label("process"),
        DefectRecord.date_opened,
        DefectRecord.date_closed
        )
        .join(Job, DefectRecord.job_id == Job.job_id)
        .join(Product, DefectRecord.product_id == Product.product_id)
        .join(Inspector, DefectRecord.inspector_user_id == Inspector.user_id)
        .join(Issuer, DefectRecord.issue_by_user_id == Issuer.user_id)
        .join(Issue, DefectRecord.issue_id == Issue.issue_id)
        .join(Process, Issue.process_id == Process.process_id) 
        .join(CorrectionProcess, DefectRecord.correction_process_id == CorrectionProcess.correction_process_id)
        .join(Status, DefectRecord.status_id == Status.status_id)
        .where( 
            and_(
                Job.job_code == job_code,
                Product.product_name == product_name
            )
        )
    )

    results = session.exec(query).all()

    if not results:
        raise HTTPException(status_code=404, detail="No defect records found")

    return results

@router.get("/search/{job_code}/{product_name}/{process_name}", response_model=list[DefectRecordRead], status_code = status.HTTP_200_OK)
def search_defect_records(
    job_code: str,
    product_name: str,
    process_name: str,
    session: SessionDep
):
    # Realizamos la consulta usando select y joins
    query = (
        select(DefectRecord)
        .join(Job, DefectRecord.job_id == Job.job_id)
        .join(Product, DefectRecord.product_id == Product.product_id)
        .join(Issue, DefectRecord.issue_id == Issue.issue_id)
        .join(Process, Issue.process_id == Process.process_id)
        .where(Job.job_code == job_code)
        .where(Product.product_name == product_name)
        .where(Process.process_name == process_name)
    )

    # Ejecutamos la consulta
    results = session.exec(query).all()

    # Si no encontramos resultados, lanzamos una excepción 404
    if not results:
        raise HTTPException(status_code=404, detail="No defect records found")

    return results


@router.get("/complete/{job_serial}/{product_name}", response_model=list[CompleteDefectRecordResponse], status_code = status.HTTP_200_OK)
def get_defect_code(
    *,
    session: SessionDep,
    job_serial: str,
    product_name: str
):
    # Primero buscamos el producto por su nombre
    product_query = select(Product).where(Product.product_name == product_name)
    product = session.exec(product_query).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Luego buscamos el job por su código y producto_id
    job_query = select(Job).where(
        and_(
            Job.job_code == job_serial,
            Job.product_id == product.product_id
        )
    )
    job = session.exec(job_query).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    # Finalmente, buscamos el defect_record asociado a este job
    defect_query = select(DefectRecord).where(
        and_(
            DefectRecord.job_id == job.job_id,
            DefectRecord.product_id == product.product_id
        )
    )
    defect_records = session.exec(defect_query).all()
    
    if not defect_records:
        raise HTTPException(status_code=404, detail="No se encontraron registros de defectos")
    
    # Retornamos los defect_records
    return defect_records

    
@router.put("/{defect_record_id}", response_model=DefectRecordRead, status_code = status.HTTP_202_ACCEPTED)
def update_defect_record(
    defect_record_id: int,
    defect_record_data: DefectRecordUpdate,
    session: SessionDep
):
    # Obtiene el registro existente
    db_defect_record = session.get(DefectRecord, defect_record_id)
    if not db_defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    
    # Actualiza los campos proporcionados
    update_data = defect_record_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_defect_record, key, value)
    
    # Actualiza la fecha de modificación
    db_defect_record.updated_at = datetime.now(datetime.timezone.utc)
    
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.delete("/{defect_record_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_defect_record(
    defect_record_id: int,
    session: SessionDep
):
    # Busca y elimina el registro
    defect_record = session.get(DefectRecord, defect_record_id)
    if not defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    
    session.delete(defect_record)
    session.commit()
    
    return {"message": "Defect record deleted successfully"}

# Definición del modelo de respuesta
class DefectRecordCreationResponse(SQLModel):
    defect_record_id: int
    product_name: str
    job_code: str
    defect_images: list[str]
    location_images: list[str]


@router.post("/create-defect-record", response_model=DefectRecordCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_defect_record(
    *,
    session: SessionDep,
    product_id: int = Form(...),
    job_id: int = Form(...),
    inspector_user_id: int = Form(...),
    issue_by_user_id: int = Form(...),
    issue_id: int = Form(...),
    correction_process_id: int = Form(...),
    status_id: int = Form(...),
    defect_images: list[UploadFile] = File(...),
    location_images: list[UploadFile] = File(...)
):
    """
    Crea un nuevo registro de defecto con sus imágenes asociadas.
    Permite subir múltiples imágenes de defecto y ubicación.
    """
    # 1. Crear el registro de defecto
    defect_record_data = DefectRecordCreate(
        product_id=product_id,
        job_id=job_id,
        inspector_user_id=inspector_user_id,
        issue_by_user_id=issue_by_user_id,
        issue_id=issue_id,
        correction_process_id=correction_process_id,
        status_id=status_id
    )
    
    defect_record = DefectRecord.model_validate(defect_record_data)
    session.add(defect_record)
    session.commit()
    session.refresh(defect_record)
    
    # 2. Obtener información adicional para construir la ruta
    product_query = select(Product).where(Product.product_id == product_id)
    product = session.exec(product_query).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    job_query = select(Job).where(Job.job_id == job_id)
    job = session.exec(job_query).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    # 3. Construir la ruta base para guardar las imágenes
    # IMPORTANTE: Usar una ruta relativa desde la raíz del proyecto
    defect_folder_name = f"{product.product_name}_{job.job_code}_{defect_record.defect_record_id}"
    base_path = Path.cwd() / "static" / "punch_list" / product.product_name / job.job_code / defect_folder_name
    
    # Asegurarse de que existen todos los directorios
    (base_path / "defect_image").mkdir(parents=True, exist_ok=True)
    (base_path / "location_image").mkdir(parents=True, exist_ok=True)
    
    # 4. Guardar las imágenes
    defect_image_urls = []
    location_image_urls = []
    
    # 4.1 Guardar las imágenes de defecto (DEFECT IMAGE, id=3)
    for i, defect_image in enumerate(defect_images):
        timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
        file_extension = Path(defect_image.filename).suffix if defect_image.filename else ".jpg"
        defect_image_filename = f"defect_{timestamp}{file_extension}"
        defect_image_path = base_path / "defect_image" / defect_image_filename
        
        # Guardar el archivo
        with open(defect_image_path, "wb") as f:
            content = await defect_image.read()
            f.write(content)
        await defect_image.seek(0)  # Reset file pointer
        
        # URL para guardar en la base de datos (ruta relativa desde el directorio static)
        relative_url = f"/static/punch_list/{product.product_name}/{job.job_code}/{defect_folder_name}/defect_image/{defect_image_filename}"
        
        # Crear registro en la base de datos para la imagen de defecto
        defect_image_data = DefectImageCreate(
            defect_record_id=defect_record.defect_record_id,
            image_type_id=3,  # DEFECT IMAGE
            image_url=relative_url
        )
        defect_image_db = DefectImage.model_validate(defect_image_data)
        session.add(defect_image_db)
        defect_image_urls.append(relative_url)
    
    # 4.2 Guardar las imágenes de ubicación (LOCATION IMAGE, id=2)
    for i, location_image in enumerate(location_images):
        timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
        file_extension = Path(location_image.filename).suffix if location_image.filename else ".jpg"
        location_image_filename = f"location_{timestamp}{file_extension}"
        location_image_path = base_path / "location_image" / location_image_filename
        
        # Guardar el archivo
        with open(location_image_path, "wb") as f:
            content = await location_image.read()
            f.write(content)
        await location_image.seek(0)  # Reset file pointer
        
        # URL para guardar en la base de datos (ruta relativa desde el directorio static)
        relative_url = f"/static/punch_list/{product.product_name}/{job.job_code}/{defect_folder_name}/location_image/{location_image_filename}"
        
        # Crear registro en la base de datos para la imagen de ubicación
        location_image_data = DefectImageCreate(
            defect_record_id=defect_record.defect_record_id,
            image_type_id=2,  # LOCATION IMAGE
            image_url=relative_url
        )
        location_image_db = DefectImage.model_validate(location_image_data)
        session.add(location_image_db)
        location_image_urls.append(relative_url)
    
    # Confirmar cambios en la base de datos
    session.commit()
    
    # 5. Preparar respuesta
    response = DefectRecordCreationResponse(
        defect_record_id=defect_record.defect_record_id,
        product_name=product.product_name,
        job_code=job.job_code,
        defect_images=defect_image_urls,
        location_images=location_image_urls
    )
    
    return response    

class DefectRecordUpdateResponse(SQLModel):
    defect_record_id: int
    product_name: str
    job_code: str
    defect_images: list[str]
    location_images: list[str]
    solved_images: list[str]

@router.patch("/defect-record/{defect_record_id}", response_model=DefectRecordUpdateResponse, status_code=status.HTTP_200_OK)
async def update_defect_record(
    *,
    session: SessionDep,
    defect_record_id: int,
    product_id: Optional[int] = Form(None),
    job_id: Optional[int] = Form(None),
    inspector_user_id: Optional[int] = Form(None),
    issue_by_user_id: Optional[int] = Form(None),
    issue_id: Optional[int] = Form(None),
    correction_process_id: Optional[int] = Form(None),
    status_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    defect_images: Optional[list[UploadFile]] = File(None),
    location_images: Optional[list[UploadFile]] = File(None),
    solved_images: Optional[list[UploadFile]] = File(None),
    close_record: Optional[bool] = Form(False)
):
    """
    Actualiza parcialmente un registro de defecto existente.
    Permite modificar cualquier campo y opcionalmente añadir nuevas imágenes.
    Soporta tres tipos de imágenes:
    - solved_images (ID=1): Imágenes de la solución implementada
    - location_images (ID=2): Imágenes de la ubicación del defecto
    - defect_images (ID=3): Imágenes del defecto mismo
    """
    # Log all input parameters
    logger.debug(f"=== START DEBUG: update_defect_record ===")
    logger.debug(f"defect_record_id: {defect_record_id}")
    logger.debug(f"product_id: {product_id}")
    logger.debug(f"job_id: {job_id}")
    logger.debug(f"inspector_user_id: {inspector_user_id}")
    logger.debug(f"issue_by_user_id: {issue_by_user_id}")
    logger.debug(f"issue_id: {issue_id}")
    logger.debug(f"correction_process_id: {correction_process_id}")
    logger.debug(f"status_id: {status_id}")
    logger.debug(f"description: {description}")
    logger.debug(f"close_record: {close_record}")
    
    # Log information about uploaded files
    if defect_images:
        defect_images_info = [{"filename": img.filename, "content_type": img.content_type, "size": 0} for img in defect_images]
        logger.debug(f"defect_images: {json.dumps(defect_images_info)}")
    else:
        logger.debug("defect_images: None")
        
    if location_images:
        location_images_info = [{"filename": img.filename, "content_type": img.content_type, "size": 0} for img in location_images]
        logger.debug(f"location_images: {json.dumps(location_images_info)}")
    else:
        logger.debug("location_images: None")
        
    if solved_images:
        solved_images_info = [{"filename": img.filename, "content_type": img.content_type, "size": 0} for img in solved_images]
        logger.debug(f"solved_images: {json.dumps(solved_images_info)}")
    else:
        logger.debug("solved_images: None")

    # 1. Buscar el registro de defecto existente
    defect_record_query = select(DefectRecord).where(DefectRecord.defect_record_id == defect_record_id)
    defect_record = session.exec(defect_record_query).first()
    
    if not defect_record:
        logger.error(f"Registro de defecto no encontrado: {defect_record_id}")
        raise HTTPException(status_code=404, detail="Registro de defecto no encontrado")
    
    logger.debug(f"Defect record found: {defect_record.defect_record_id}")
    
    # 2. Preparar datos para actualización
    update_data = DefectRecordUpdate()
    
    # Actualizar cada campo si se proporciona un nuevo valor
    if product_id is not None:
        # Verificar que el producto existe
        product_query = select(Product).where(Product.product_id == product_id)
        product = session.exec(product_query).first()
        if not product:
            logger.error(f"Producto no encontrado: {product_id}")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        logger.debug(f"Product validated: {product.product_id} - {product.product_name}")
        update_data.product_id = product_id
    
    if job_id is not None:
        # Verificar que el job existe
        job_query = select(Job).where(Job.job_id == job_id)
        job = session.exec(job_query).first()
        if not job:
            logger.error(f"Job no encontrado: {job_id}")
            raise HTTPException(status_code=404, detail="Job no encontrado")
        logger.debug(f"Job validated: {job.job_id} - {job.job_code}")
        update_data.job_id = job_id
    
    if inspector_user_id is not None:
        logger.debug(f"Setting inspector_user_id: {inspector_user_id}")
        update_data.inspector_user_id = inspector_user_id
    
    if issue_by_user_id is not None:
        logger.debug(f"Setting issue_by_user_id: {issue_by_user_id}")
        update_data.issue_by_user_id = issue_by_user_id
    
    if issue_id is not None:
        # Verificar que el issue existe
        issue_query = select(Issue).where(Issue.issue_id == issue_id)
        issue = session.exec(issue_query).first()
        if not issue:
            logger.error(f"Issue no encontrado: {issue_id}")
            raise HTTPException(status_code=404, detail="Issue no encontrado")
        logger.debug(f"Issue validated: {issue.issue_id}")
        update_data.issue_id = issue_id
    
    if correction_process_id is not None:
        # Verificar que el correction process existe
        cp_query = select(CorrectionProcess).where(CorrectionProcess.correction_process_id == correction_process_id)
        cp = session.exec(cp_query).first()
        if not cp:
            logger.error(f"Proceso de corrección no encontrado: {correction_process_id}")
            raise HTTPException(status_code=404, detail="Proceso de corrección no encontrado")
        logger.debug(f"Correction process validated: {cp.correction_process_id}")
        update_data.correction_process_id = correction_process_id
    
    if status_id is not None:
        # Verificar que el status existe
        status_query = select(Status).where(Status.status_id == status_id)
        status = session.exec(status_query).first()
        if not status:
            logger.error(f"Estado no encontrado: {status_id}")
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        logger.debug(f"Status validated: {status.status_id}")
        update_data.status_id = status_id

    if description is not None:
        logger.debug(f"Setting description: {description[:50]}...")
        update_data.description = description
    
    if close_record:
        logger.debug("Setting date_closed to current datetime")
        update_data.date_closed = datetime.now(timezone.utc)
    
    # 3. Actualizar el registro con los nuevos datos
    logger.debug("Applying updates to defect record")
    update_dict = update_data.dict(exclude_unset=True)
    logger.debug(f"Update dictionary: {update_dict}")
    
    for key, value in update_dict.items():
        setattr(defect_record, key, value)
    
    # 4. Procesar nuevas imágenes si se proporcionan
    defect_image_urls = []
    location_image_urls = []
    solved_image_urls = []
    
    # Obtener información necesaria para construir la ruta de las imágenes
    product = defect_record.product
    job = defect_record.job
    
    logger.debug(f"Product info: {product.product_name}")
    logger.debug(f"Job info: {job.job_code}")
    
    if defect_images or location_images or solved_images:
        # Construir la ruta base para guardar las imágenes
        defect_folder_name = f"{product.product_name}_{job.job_code}_{defect_record.defect_record_id}"
        base_path = Path.cwd() / "static" / "punch_list" / product.product_name / job.job_code / defect_folder_name
        
        logger.debug(f"Image base path: {base_path}")
        
        # Asegurarse de que existen todos los directorios
        (base_path / "defect_image").mkdir(parents=True, exist_ok=True)
        (base_path / "location_image").mkdir(parents=True, exist_ok=True)
        (base_path / "solved_image").mkdir(parents=True, exist_ok=True)
        
        # 4.1 Guardar las nuevas imágenes de defecto (DEFECT IMAGE, id=3)
        if defect_images:
            logger.debug(f"Processing {len(defect_images)} defect images")
            for i, defect_image in enumerate(defect_images):
                # Saltar archivos vacíos
                if defect_image.filename == "":
                    logger.debug(f"Skipping empty defect image at index {i}")
                    continue
                    
                timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
                file_extension = Path(defect_image.filename).suffix if defect_image.filename else ".jpg"
                defect_image_filename = f"defect_{timestamp}{file_extension}"
                defect_image_path = base_path / "defect_image" / defect_image_filename
                
                logger.debug(f"Saving defect image {i+1}: {defect_image_filename}")
                
                # Guardar el archivo
                try:
                    with open(defect_image_path, "wb") as f:
                        content = await defect_image.read()
                        f.write(content)
                    await defect_image.seek(0)  # Reset file pointer
                    logger.debug(f"Saved defect image: {defect_image_path}")
                except Exception as e:
                    logger.error(f"Error saving defect image: {str(e)}")
                    continue
                
                # URL para guardar en la base de datos (ruta relativa desde el directorio static)
                relative_url = f"/static/punch_list/{product.product_name}/{job.job_code}/{defect_folder_name}/defect_image/{defect_image_filename}"
                
                # Crear registro en la base de datos para la imagen de defecto
                defect_image_data = DefectImageCreate(
                    defect_record_id=defect_record.defect_record_id,
                    image_type_id=3,  # DEFECT IMAGE
                    image_url=relative_url
                )
                defect_image_db = DefectImage.model_validate(defect_image_data)
                session.add(defect_image_db)
                defect_image_urls.append(relative_url)
                logger.debug(f"Added defect image to database: {relative_url}")
        
        # 4.2 Guardar las nuevas imágenes de ubicación (LOCATION IMAGE, id=2)
        if location_images:
            logger.debug(f"Processing {len(location_images)} location images")
            for i, location_image in enumerate(location_images):
                # Saltar archivos vacíos
                if location_image.filename == "":
                    logger.debug(f"Skipping empty location image at index {i}")
                    continue
                    
                timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
                file_extension = Path(location_image.filename).suffix if location_image.filename else ".jpg"
                location_image_filename = f"location_{timestamp}{file_extension}"
                location_image_path = base_path / "location_image" / location_image_filename
                
                logger.debug(f"Saving location image {i+1}: {location_image_filename}")
                
                # Guardar el archivo
                try:
                    with open(location_image_path, "wb") as f:
                        content = await location_image.read()
                        f.write(content)
                    await location_image.seek(0)  # Reset file pointer
                    logger.debug(f"Saved location image: {location_image_path}")
                except Exception as e:
                    logger.error(f"Error saving location image: {str(e)}")
                    continue
                
                # URL para guardar en la base de datos (ruta relativa desde el directorio static)
                relative_url = f"/static/punch_list/{product.product_name}/{job.job_code}/{defect_folder_name}/location_image/{location_image_filename}"
                
                # Crear registro en la base de datos para la imagen de ubicación
                location_image_data = DefectImageCreate(
                    defect_record_id=defect_record.defect_record_id,
                    image_type_id=2,  # LOCATION IMAGE
                    image_url=relative_url
                )
                location_image_db = DefectImage.model_validate(location_image_data)
                session.add(location_image_db)
                location_image_urls.append(relative_url)
                logger.debug(f"Added location image to database: {relative_url}")
                
        # 4.3 Guardar las nuevas imágenes de solución (SOLVED IMAGE, id=1)
        if solved_images:
            logger.debug(f"Processing {len(solved_images)} solved images")
            for i, solved_image in enumerate(solved_images):
                # Saltar archivos vacíos
                if solved_image.filename == "":
                    logger.debug(f"Skipping empty solved image at index {i}")
                    continue
                    
                timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
                file_extension = Path(solved_image.filename).suffix if solved_image.filename else ".jpg"
                solved_image_filename = f"solved_{timestamp}{file_extension}"
                solved_image_path = base_path / "solved_image" / solved_image_filename
                
                logger.debug(f"Saving solved image {i+1}: {solved_image_filename}")
                
                # Guardar el archivo
                try:
                    with open(solved_image_path, "wb") as f:
                        content = await solved_image.read()
                        f.write(content)
                    await solved_image.seek(0)  # Reset file pointer
                    logger.debug(f"Saved solved image: {solved_image_path}")
                except Exception as e:
                    logger.error(f"Error saving solved image: {str(e)}")
                    continue
                
                # URL para guardar en la base de datos (ruta relativa desde el directorio static)
                relative_url = f"/static/punch_list/{product.product_name}/{job.job_code}/{defect_folder_name}/solved_image/{solved_image_filename}"
                
                # Crear registro en la base de datos para la imagen de solución
                solved_image_data = DefectImageCreate(
                    defect_record_id=defect_record.defect_record_id,
                    image_type_id=1,  # SOLVED IMAGE
                    image_url=relative_url
                )
                solved_image_db = DefectImage.model_validate(solved_image_data)
                session.add(solved_image_db)
                solved_image_urls.append(relative_url)
                logger.debug(f"Added solved image to database: {relative_url}")
    
    # 5. Confirmar los cambios en la base de datos
    logger.debug("Committing changes to database")
    try:
        session.commit()
        session.refresh(defect_record)
        logger.debug("Database commit successful")
    except Exception as e:
        logger.error(f"Error committing to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al guardar los cambios: {str(e)}")
    
    # 6. Preparar la respuesta
    logger.debug(f"Preparing response with {len(defect_image_urls)} defect images, {len(location_image_urls)} location images, and {len(solved_image_urls)} solved images")
    
    # 7. Preparar la respuesta usando el modelo definido
    response = DefectRecordUpdateResponse(
        defect_record_id=defect_record.defect_record_id,
        product_name=product.product_name,
        job_code=job.job_code,
        defect_images=defect_image_urls,
        location_images=location_image_urls,
        solved_images=solved_image_urls
    )
    
    logger.debug(f"Response prepared: defect_record_id={response.defect_record_id}")
    logger.debug(f"=== END DEBUG: update_defect_record ===")
    
    return response