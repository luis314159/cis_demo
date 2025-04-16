from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, and_
from datetime import datetime
from models import DefectRecord, DefectRecordCreate, DefectRecordRead, DefectRecordUpdate, DefectRecordResponse, Job, Product, Process, Issue, User, Status, CorrectionProcess, CompleteDefectRecordResponse
from db import SessionDep
from sqlalchemy.orm import aliased

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
            Process.process_name.label("process"),  # Campo process
            DefectRecord.date_opened,  # Campo date_opened
            DefectRecord.date_closed,  # Campo date_closed
            Status.status_name.label("status"),  # Campo status
            Inspector.username.label("inspectBy"),  # Campo inspectBy
            Issuer.username.label("issueBy"),  # Campo issueBy
            CorrectionProcess.correction_process_description.label("todo")  # Campo todo (según tu aclaración)
        )
        .join(Job, DefectRecord.job_id == Job.job_id)
        .join(Product, DefectRecord.product_id == Product.product_id)
        .join(Inspector, DefectRecord.inspector_user_id == Inspector.user_id)
        .join(Issuer, DefectRecord.issue_by_user_id == Issuer.user_id)
        .join(Issue, DefectRecord.issue_id == Issue.issue_id)
        .join(CorrectionProcess, DefectRecord.correction_process_id == CorrectionProcess.correction_process_id)
        .join(Status, DefectRecord.status_id == Status.status_id)
        .where(Job.job_code == job_code)
        .where(Product.product_name == product_name)
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