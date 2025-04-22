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

@router.patch("/defect-record/{defect_record_id}", status_code=status.HTTP_200_OK)
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
    # 1. Buscar el registro de defecto existente
    defect_record_query = select(DefectRecord).where(DefectRecord.defect_record_id == defect_record_id)
    defect_record = session.exec(defect_record_query).first()
    
    if not defect_record:
        raise HTTPException(status_code=404, detail="Registro de defecto no encontrado")
    
    # 2. Preparar datos para actualización
    update_data = DefectRecordUpdate()
    
    # Actualizar cada campo si se proporciona un nuevo valor
    if product_id is not None:
        # Verificar que el producto existe
        product_query = select(Product).where(Product.product_id == product_id)
        product = session.exec(product_query).first()
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        update_data.product_id = product_id
    
    if job_id is not None:
        # Verificar que el job existe
        job_query = select(Job).where(Job.job_id == job_id)
        job = session.exec(job_query).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        update_data.job_id = job_id
    
    if inspector_user_id is not None:
        update_data.inspector_user_id = inspector_user_id
    
    if issue_by_user_id is not None:
        update_data.issue_by_user_id = issue_by_user_id
    
    if issue_id is not None:
        # Verificar que el issue existe
        issue_query = select(Issue).where(Issue.issue_id == issue_id)
        if not session.exec(issue_query).first():
            raise HTTPException(status_code=404, detail="Issue no encontrado")
        update_data.issue_id = issue_id
    
    if correction_process_id is not None:
        # Verificar que el correction process existe
        cp_query = select(CorrectionProcess).where(CorrectionProcess.correction_process_id == correction_process_id)
        if not session.exec(cp_query).first():
            raise HTTPException(status_code=404, detail="Proceso de corrección no encontrado")
        update_data.correction_process_id = correction_process_id
    
    if status_id is not None:
        # Verificar que el status existe
        status_query = select(Status).where(Status.status_id == status_id)
        if not session.exec(status_query).first():
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        update_data.status_id = status_id
    
    if description is not None:
        update_data.description = description
    
    if close_record:
        update_data.date_closed = datetime.now(timezone.utc)
    
    # 3. Actualizar el registro con los nuevos datos
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(defect_record, key, value)
    
    # 4. Procesar nuevas imágenes si se proporcionan
    new_defect_image_urls = []
    new_location_image_urls = []
    new_solved_image_urls = []
    
    # Obtener información necesaria para construir la ruta de las imágenes
    product = defect_record.product
    job = defect_record.job
    
    if defect_images or location_images or solved_images:
        # Construir la ruta base para guardar las imágenes
        defect_folder_name = f"{product.product_name}_{job.job_code}_{defect_record.defect_record_id}"
        base_path = Path.cwd() / "static" / "punch_list" / product.product_name / job.job_code / defect_folder_name
        
        # Asegurarse de que existen todos los directorios
        (base_path / "defect_image").mkdir(parents=True, exist_ok=True)
        (base_path / "location_image").mkdir(parents=True, exist_ok=True)
        (base_path / "solved_image").mkdir(parents=True, exist_ok=True)
        
        # 4.1 Guardar las nuevas imágenes de defecto (DEFECT IMAGE, id=3)
        if defect_images:
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
                new_defect_image_urls.append(relative_url)
        
        # 4.2 Guardar las nuevas imágenes de ubicación (LOCATION IMAGE, id=2)
        if location_images:
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
                new_location_image_urls.append(relative_url)
                
        # 4.3 Guardar las nuevas imágenes de solución (SOLVED IMAGE, id=1)
        if solved_images:
            for i, solved_image in enumerate(solved_images):
                timestamp = int(time.time() * 1000) + i  # Añadir índice para garantizar unicidad
                file_extension = Path(solved_image.filename).suffix if solved_image.filename else ".jpg"
                solved_image_filename = f"solved_{timestamp}{file_extension}"
                solved_image_path = base_path / "solved_image" / solved_image_filename
                
                # Guardar el archivo
                with open(solved_image_path, "wb") as f:
                    content = await solved_image.read()
                    f.write(content)
                await solved_image.seek(0)  # Reset file pointer
                
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
                new_solved_image_urls.append(relative_url)
    
    # 5. Confirmar los cambios en la base de datos
    session.commit()
    
    # 6. Recuperar todas las imágenes asociadas al registro
    all_defect_images = [img.image_url for img in defect_record.images if img.image_type_id == 3]
    all_location_images = [img.image_url for img in defect_record.images if img.image_type_id == 2]
    all_solved_images = [img.image_url for img in defect_record.images if img.image_type_id == 1]
    
    # 7. Preparar la respuesta
    response = {
        "defect_record_id": defect_record.defect_record_id,
        "product_name": product.product_name,
        "job_code": job.job_code,
        "status": defect_record.status.status_name if defect_record.status else None,
        "date_updated": datetime.now(timezone.utc).isoformat(),
        "date_closed": defect_record.date_closed.isoformat() if defect_record.date_closed else None,
        "defect_images": all_defect_images,
        "location_images": all_location_images,
        "solved_images": all_solved_images,
        "new_defect_images": new_defect_image_urls,
        "new_location_images": new_location_image_urls,
        "new_solved_images": new_solved_image_urls
    }
    
    return response