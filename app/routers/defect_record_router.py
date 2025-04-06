from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from models import DefectRecord, DefectRecordCreate, DefectRecordRead, DefectRecordUpdate, Job, Product
from db import SessionDep

router = APIRouter(prefix="/defect-records", tags=["Defect Records"])

@router.post("/add_defect_record", response_model=DefectRecord)
def create_defect_record(defect_record: DefectRecordCreate, session: SessionDep):
    # Crea una instancia del modelo de base de datos
    db_defect_record = DefectRecord.model_validate(defect_record.model_dump())
    
    # Guarda en la base de datos
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.get("/", response_model=List[DefectRecordRead])
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

@router.get("/{defect_record_id}", response_model=DefectRecordRead)
def get_defect_record(
    defect_record_id: int, 
    session: SessionDep
):
    # Busca por ID
    defect_record = session.get(DefectRecord, defect_record_id)
    if not defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    return defect_record

@router.get("/search/{job_code}/{product_id}", response_model=list[DefectRecordRead])
def search_defect_records(
    job_code: str,
    product_id: int,
    session: SessionDep
):
    # Realizamos la consulta usando select y joins
    query = (
        select(DefectRecord)
        .join(Job, DefectRecord.job_id == Job.job_id)
        .join(Product, DefectRecord.product_id == Product.product_id)
        .where(Job.job_code == job_code)
        .where(Product.product_id == product_id)
    )

    # Ejecutamos la consulta
    results = session.exec(query).all()

    # Si no encontramos resultados, lanzamos una excepción 404
    if not results:
        raise HTTPException(status_code=404, detail="No defect records found")

    return results


@router.put("/{defect_record_id}", response_model=DefectRecordRead)
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
    update_data = defect_record_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_defect_record, key, value)
    
    # Actualiza la fecha de modificación
    db_defect_record.updated_at = datetime.utcnow()
    
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.delete("/{defect_record_id}")
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