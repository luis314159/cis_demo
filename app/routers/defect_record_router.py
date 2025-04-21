import os
import shutil
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlmodel import SQLModel, select, and_
import time
from datetime import datetime
from models import DefectImage, DefectImageCreate, DefectRecord, DefectRecordCreate, DefectRecordRead, DefectRecordUpdate, DefectRecordResponse, Job, Product, Process, Issue, User, Status, CorrectionProcess, CompleteDefectRecordResponse
from db import SessionDep
from sqlalchemy.orm import aliased
from pathlib import Path

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